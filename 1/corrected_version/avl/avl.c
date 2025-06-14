/*
 * CDDL HEADER START
 *
 * The contents of this file are subject to the terms of the
 * Common Development and Distribution License (the "License").
 * You may not use this file except in compliance with the License.
 *
 * You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
 * or http://www.opensolaris.org/os/licensing.
 * See the License for the specific language governing permissions
 * and limitations under the License.
 *
 * When distributing Covered Code, include this CDDL HEADER in each
 * file and include the License file at usr/src/OPENSOLARIS.LICENSE.
 * If applicable, add the following below this CDDL HEADER, with the
 * fields enclosed by brackets "[]" replaced with your own identifying
 * information: Portions Copyright [yyyy] [name of copyright owner]
 *
 * CDDL HEADER END
 */
/*
 * Copyright 2009 Sun Microsystems, Inc.  All rights reserved.
 * Use is subject to license terms.
 */

/*
 * AVL - generic AVL tree implementation for kernel use
 *
 * A complete description of AVL trees can be found in many CS textbooks.
 *
 * Here is a very brief overview. An AVL tree is a binary search tree that is
 * almost perfectly balanced. By "almost" perfectly balanced, we mean that at
 * any given node, the left and right subtrees are allowed to differ in height
 * by at most 1 level.
 *
 * This relaxation from a perfectly balanced binary tree allows doing
 * insertion and deletion relatively efficiently. Searching the tree is
 * still a fast operation, roughly O(log(N)).
 *
 * The key to insertion and deletion is a set of tree maniuplations called
 * rotations, which bring unbalanced subtrees back into the semi-balanced state.
 *
 * This implementation of AVL trees has the following peculiarities:
 *
 *	- The AVL specific data structures are physically embedded as fields
 *	  in the "using" data structures.  To maintain generality the code
 *	  must constantly translate between "avl_node_t *" and containing
 *	  data structure "void *"s by adding/subracting the avl_offset.
 *
 *	- Since the AVL data is always embedded in other structures, there is
 *	  no locking or memory allocation in the AVL routines. This must be
 *	  provided for by the enclosing data structure's semantics. Typically,
 *	  avl_insert()/_add()/_remove()/avl_insert_here() require some kind of
 *	  exclusive write lock. Other operations require a read lock.
 *
 *	- The implementation uses iteration instead of explicit recursion,
 *	  since it is intended to run on limited size kernel stacks. Since
 *	  there is no recursion stack present to move "up" in the tree,
 *	  there is an explicit "parent" link in the avl_node_t.
 *
 *	- The left/right children pointers of a node are in an array.
 *	  In the code, variables (instead of constants) are used to represent
 *	  left and right indices.  The implementation is written as if it only
 *	  dealt with left handed manipulations.	 By changing the value assigned
 *	  to "left", the code also works for right handed trees.  The
 *	  following variables/terms are frequently used:
 *
 *		int left;	// 0 when dealing with left children,
 *				// 1 for dealing with right children
 *
 *		int left_heavy;	// -1 when left subtree is taller at some node,
 *				// +1 when right subtree is taller
 *
 *		int right;	// will be the opposite of left (0 or 1)
 *		int right_heavy;// will be the opposite of left_heavy (-1 or 1)
 *
 *		int direction;	// 0 for "<" (ie. left child); 1 for ">" (right)
 *
 *	  Though it is a little more confusing to read the code, the approach
 *	  allows using half as much code (and hence cache footprint) for tree
 *	  manipulations and eliminates many conditional branches.
 *
 *	- The avl_index_t is an opaque "cookie" used to find nodes at or
 *	  adjacent to where a new value would be inserted in the tree. The value
 *	  is a modified "avl_node_t *".	 The bottom bit (normally 0 for a
 *	  pointer) is set to indicate if that the new node has a value greater
 *	  than the value of the indicated "avl_node_t *".
 */

//#include <sys/types.h>
#include <stdbool.h>
#include <stdio.h>
#include <assert.h>
#include <stddef.h>
#include "avl.h"

/*
 * Small arrays to translate between balance (or diff) values and child indeces.
 *
 * Code that deals with binary tree data structures will randomly use
 * left and right children when examining a tree.  C "if()" statements
 * which evaluate randomly suffer from very poor hardware branch prediction.
 * In this code we avoid some of the branch mispredictions by using the
 * following translation arrays. They replace random branches with an
 * additional memory reference. Since the translation arrays are both very
 * small the data should remain efficiently in cache.
 */
static const int  avl_child2balance[2]	= {-1, 1};
static const int  avl_balance2child[]	= {0, 0, 1};

/*
 * Search for the node which contains "value".	The algorithm is a
 * simple binary tree search.
 *
 * return value:
 *	NULL: the value is not in the AVL tree
 *		*where (if not NULL)  is set to indicate the insertion point
 *	"void *"  of the found tree node
 */
struct avl_node *
avl_find(avl_tree_t *tree, const struct avl_node *value, avl_index_t *where)
{
	avl_node_t *node;
	avl_node_t *prev = NULL;
	int child = 0;
	int diff;
//	size_t off = tree->avl_offset;

	for (node = tree->avl_root; node != NULL;
	     node = node->avl_child[child]) {

		prev = node;

		if (value->key < node->key)
			diff = -1;
		else if (value->key > node->key)
			diff = 1;
		else
			diff = 0;
//		diff = tree->avl_compar(value, AVL_NODE2DATA(node, off));
		assert(-1 <= diff && diff <= 1);
		if (diff == 0) {
#ifdef DEBUG
			if (where != NULL)
				*where = 0;
#endif
			return node;
		}
		child = avl_balance2child[1 + diff];

	}

	if (where != NULL)
		*where = AVL_MKINDEX(prev, child);

	return (NULL);
}

/*
 * Perform a rotation to restore balance at the subtree given by depth.
 *
 * This routine is used by both insertion and deletion. The return value
 * indicates:
 *	 0 : subtree did not change height
 *	!0 : subtree was reduced in height
 *
 * The code is written as if handling left rotations, right rotations are
 * symmetric and handled by swapping values of variables right/left[_heavy]
 *
 * On input balance is the "new" balance at "node". This value is either
 * -2 or +2.
 */
static int
avl_rotation(avl_tree_t *tree, avl_node_t *node, int balance)
{
	int left = !(balance < 0);	/* when balance = -2, left will be 0 */
	int right = 1 - left;
	int left_heavy = balance >> 1;
	int right_heavy = -left_heavy;
	avl_node_t *parent = AVL_XPARENT(node);
	avl_node_t *child = node->avl_child[left];
	avl_node_t *cright;
	avl_node_t *gchild;
	avl_node_t *gright;
	avl_node_t *gleft;
	int which_child = AVL_XCHILD(node);
	int child_bal = AVL_XBALANCE(child);

	/* BEGIN CSTYLED */
	/*
	 * case 1 : node is overly left heavy, the left child is balanced or
	 * also left heavy. This requires the following rotation.
	 *
	 *		     (node bal:-2)
	 *		      /		  \
	 *		     /		   \
	 *		(child bal:0 or -1)
	 *		/    \
	 *	       /      \
	 *		       cright
	 *
	 * becomes:
	 *
	 *		(child bal:1 or 0)
	 *		/	 \
	 *	       /	  \
	 *			  (node bal:-1 or 0)
	 *			   /	 \
	 *			  /	  \
	 *		       cright
	 *
	 * we detect this situation by noting that child's balance is not
	 * right_heavy.
	 */
	/* END CSTYLED */
	if (child_bal != right_heavy) {

		/*
		 * compute new balance of nodes
		 *
		 * If child used to be left heavy (now balanced) we reduced
		 * the height of this sub-tree -- used in "return...;" below
		 */
		child_bal += right_heavy; /* adjust towards right */

		/*
		 * move "cright" to be node's left child
		 */
		cright = child->avl_child[right];
		node->avl_child[left] = cright;
		if (cright != NULL) {
			AVL_SETPARENT(cright, node);
			AVL_SETCHILD(cright, left);
		}

		/*
		 * move node to be child's right child
		 */
		child->avl_child[right] = node;
		AVL_SETBALANCE(node, -child_bal);
		AVL_SETCHILD(node, right);
		AVL_SETPARENT(node, child);

		/*
		 * update the pointer into this subtree
		 */
		AVL_SETBALANCE(child, child_bal);
		AVL_SETCHILD(child, which_child);
		AVL_SETPARENT(child, parent);
		if (parent != NULL)
			parent->avl_child[which_child] = child;
		else
			tree->avl_root = child;

		return (child_bal == 0);
	}

	/* BEGIN CSTYLED */
	/*
	 * case 2 : When node is left heavy, but child is right heavy we use
	 * a different rotation.
	 *
	 *		     (node b:-2)
	 *		      /	  \
	 *		     /	   \
	 *		    /	    \
	 *	       (child b:+1)
	 *		/     \
	 *	       /       \
	 *		     (gchild b: != 0)
	 *		       /  \
	 *		      /	   \
	 *		   gleft   gright
	 *
	 * becomes:
	 *
	 *		(gchild b:0)
	 *		/	\
	 *	       /	 \
	 *	      /		  \
	 *	  (child b:?)	(node b:?)
	 *	   /  \		 /   \
	 *	  /    \	/     \
	 *	      gleft   gright
	 *
	 * computing the new balances is more complicated. As an example:
	 *	 if gchild was right_heavy, then child is now left heavy
	 *		else it is balanced
	 */
	/* END CSTYLED */
	gchild = child->avl_child[right];
	gleft = gchild->avl_child[left];
	gright = gchild->avl_child[right];

	/*
	 * move gright to left child of node and
	 *
	 * move gleft to right child of node
	 */
	node->avl_child[left] = gright;
	if (gright != NULL) {
		AVL_SETPARENT(gright, node);
		AVL_SETCHILD(gright, left);
	}

	child->avl_child[right] = gleft;
	if (gleft != NULL) {
		AVL_SETPARENT(gleft, child);
		AVL_SETCHILD(gleft, right);
	}

	/*
	 * move child to left child of gchild and
	 *
	 * move node to right child of gchild and
	 *
	 * fixup parent of all this to point to gchild
	 */
	balance = AVL_XBALANCE(gchild);
	gchild->avl_child[left] = child;
	AVL_SETBALANCE(child, (balance == right_heavy ? left_heavy : 0));
	AVL_SETPARENT(child, gchild);
	AVL_SETCHILD(child, left);

	gchild->avl_child[right] = node;
	AVL_SETBALANCE(node, (balance == left_heavy ? right_heavy : 0));
	AVL_SETPARENT(node, gchild);
	AVL_SETCHILD(node, right);

	AVL_SETBALANCE(gchild, 0);
	AVL_SETPARENT(gchild, parent);
	AVL_SETCHILD(gchild, which_child);
	if (parent != NULL)
		parent->avl_child[which_child] = gchild;
	else
		tree->avl_root = gchild;

	return (1);	/* the new tree is always shorter */
}


/*
 * Insert a new node into an AVL tree at the specified (from avl_find()) place.
 *
 * Newly inserted nodes are always leaf nodes in the tree, since avl_find()
 * searches out to the leaf positions.	The avl_index_t indicates the node
 * which will be the parent of the new node.
 *
 * After the node is inserted, a single rotation further up the tree may
 * be necessary to maintain an acceptable AVL balance.
 */
static void
avl_insert(avl_tree_t *tree, struct avl_node *node, avl_index_t where)
{
//	avl_node_t *node;
	avl_node_t *parent = AVL_INDEX2NODE(where);
	int old_balance;
	int new_balance;
	int which_child = AVL_INDEX2CHILD(where);
//	size_t off = tree->avl_offset;

	assert(tree);
//#ifdef _LP64
//	assert(((uintptr_t)new_data & 0x7) == 0);
//#endif

//	node = AVL_DATA2NODE(new_data, off);

	/*
	 * First, add the node to the tree at the indicated position.
	 */
//	++tree->avl_numnodes;

	node->avl_child[0] = NULL;
	node->avl_child[1] = NULL;

	AVL_SETCHILD(node, which_child);
	AVL_SETBALANCE(node, 0);
	AVL_SETPARENT(node, parent);
	if (parent != NULL) {
		assert(parent->avl_child[which_child] == NULL);
		parent->avl_child[which_child] = node;
	} else {
		assert(tree->avl_root == NULL);
		tree->avl_root = node;
	}
	/*
	 * Now, back up the tree modifying the balance of all nodes above the
	 * insertion point. If we get to a highly unbalanced ancestor, we
	 * need to do a rotation.  If we back out of the tree we are done.
	 * If we brought any subtree into perfect balance (0), we are also done.
	 */
	for (;;) {
		node = parent;
		if (node == NULL)
			return;

		/*
		 * Compute the new balance
		 */
		old_balance = AVL_XBALANCE(node);
		new_balance = old_balance + avl_child2balance[which_child];

		/*
		 * If we introduced equal balance, then we are done immediately
		 */
		if (new_balance == 0) {
			AVL_SETBALANCE(node, 0);
			return;
		}

		/*
		 * If both old and new are not zero we went
		 * from -1 to -2 balance, do a rotation.
		 */
		if (old_balance != 0)
			break;

		AVL_SETBALANCE(node, new_balance);
		parent = AVL_XPARENT(node);
		which_child = AVL_XCHILD(node);
	}

	/*
	 * perform a rotation to fix the tree and return
	 */
	(void) avl_rotation(tree, node, new_balance);
}

/*
 * Add a new node to an AVL tree.
 */
void
avl_add(avl_tree_t *tree, struct avl_node *new_node, size_t size)
{
	struct avl_node *node;
	avl_index_t where;

	new_node->key = size;
	/*
	 * This is unfortunate.	 We want to call panic() here, even for
	 * non-DEBUG kernels.  In userland, however, we can't depend on anything
	 * in libc or else the rtld build process gets confused.  So, all we can
	 * do in userland is resort to a normal assert().
	 */
	node = avl_find(tree, new_node, &where);
	if (node != NULL) {
		new_node->next = node->next;
		new_node->prev = node;
		if (node->next != NULL)
			node->next->prev = new_node;
		node->next = new_node;
	} else {
		new_node->next = NULL;
		new_node->prev = NULL;
		avl_insert(tree, new_node, where);
	}
}

/*
 * Delete a node from the AVL tree.  Deletion is similar to insertion, but
 * with 2 complications.
 *
 * First, we may be deleting an interior node. Consider the following subtree:
 *
 *     d	   c		c
 *    / \	  / \	       / \
 *   b	 e	 b   e	      b	  e
 *  / \		/ \	     /
 * a   c       a	    a
 *
 * When we are deleting node (d), we find and bring up an adjacent valued leaf
 * node, say (c), to take the interior node's place. In the code this is
 * handled by temporarily swapping (d) and (c) in the tree and then using
 * common code to delete (d) from the leaf position.
 *
 * Secondly, an interior deletion from a deep tree may require more than one
 * rotation to fix the balance. This is handled by moving up the tree through
 * parents and applying rotations as needed. The return value from
 * avl_rotation() is used to detect when a subtree did not change overall
 * height due to a rotation.
 */
void
avl_remove(avl_tree_t *tree, struct avl_node *delete)
{
//	avl_node_t *delete;
	avl_node_t *parent;
	avl_node_t *node;
	avl_node_t tmp;
	int old_balance;
	int new_balance;
	int left;
	int right;
	int which_child;
//	size_t off = tree->avl_offset;

	assert(tree);

	if (delete->prev != NULL) {
		delete->prev->next = delete->next;
		if (delete->next != NULL)
			delete->next->prev = delete->prev;
		return;
	}
	if (delete->next != NULL) {
		node = delete->next;
		node->avl_child[0] = delete->avl_child[0];
		node->avl_child[1] = delete->avl_child[1];
		node->avl_parent = delete->avl_parent;
		node->avl_child_index = delete->avl_child_index;
		node->avl_balance = delete->avl_balance;
		node->prev = NULL;
		if (node->avl_child[0] != NULL)
			node->avl_child[0]->avl_parent = node;
		if (node->avl_child[1] != NULL)
			node->avl_child[1]->avl_parent = node;
		if (node->avl_parent != NULL)
			node->avl_parent->avl_child[node->avl_child_index] = node;
		else
			tree->avl_root = node;
		return;
	}

//	delete = AVL_DATA2NODE(data, off);

	/*
	 * Deletion is easiest with a node that has at most 1 child.
	 * We swap a node with 2 children with a sequentially valued
	 * neighbor node. That node will have at most 1 child. Note this
	 * has no effect on the ordering of the remaining nodes.
	 *
	 * As an optimization, we choose the greater neighbor if the tree
	 * is right heavy, otherwise the left neighbor. This reduces the
	 * number of rotations needed.
	 */
	if (delete->avl_child[0] != NULL && delete->avl_child[1] != NULL) {

		/*
		 * choose node to swap from whichever side is taller
		 */
		old_balance = AVL_XBALANCE(delete);
		left = avl_balance2child[old_balance + 1];
		right = 1 - left;

		/*
		 * get to the previous value'd node
		 * (down 1 left, as far as possible right)
		 */
		for (node = delete->avl_child[left];
		     node->avl_child[right] != NULL;
		     node = node->avl_child[right])
			;

		/*
		 * create a temp placeholder for 'node'
		 * move 'node' to delete's spot in the tree
		 */
		tmp = *node;

//		*node = *delete;
		node->avl_child[0] = delete->avl_child[0];
		node->avl_child[1] = delete->avl_child[1];
		node->avl_parent = delete->avl_parent;
		node->avl_child_index = delete->avl_child_index;
		node->avl_balance = delete->avl_balance;

		if (node->avl_child[left] == node)
			node->avl_child[left] = &tmp;

		parent = AVL_XPARENT(node);
		if (parent != NULL)
			parent->avl_child[AVL_XCHILD(node)] = node;
		else
			tree->avl_root = node;
		AVL_SETPARENT(node->avl_child[left], node);
		AVL_SETPARENT(node->avl_child[right], node);

		/*
		 * Put tmp where node used to be (just temporary).
		 * It always has a parent and at most 1 child.
		 */
		delete = &tmp;
		parent = AVL_XPARENT(delete);
		parent->avl_child[AVL_XCHILD(delete)] = delete;
		which_child = (delete->avl_child[1] != 0);
		if (delete->avl_child[which_child] != NULL)
			AVL_SETPARENT(delete->avl_child[which_child], delete);
	}


	/*
	 * Here we know "delete" is at least partially a leaf node. It can
	 * be easily removed from the tree.
	 */
//	assert(tree->avl_numnodes > 0);
//	--tree->avl_numnodes;
	parent = AVL_XPARENT(delete);
	which_child = AVL_XCHILD(delete);
	if (delete->avl_child[0] != NULL)
		node = delete->avl_child[0];
	else
		node = delete->avl_child[1];

	/*
	 * Connect parent directly to node (leaving out delete).
	 */
	if (node != NULL) {
		AVL_SETPARENT(node, parent);
		AVL_SETCHILD(node, which_child);
	}
	if (parent == NULL) {
		tree->avl_root = node;
		return;
	}
	parent->avl_child[which_child] = node;


	/*
	 * Since the subtree is now shorter, begin adjusting parent balances
	 * and performing any needed rotations.
	 */
	do {

		/*
		 * Move up the tree and adjust the balance
		 *
		 * Capture the parent and which_child values for the next
		 * iteration before any rotations occur.
		 */
		node = parent;
		old_balance = AVL_XBALANCE(node);
		new_balance = old_balance - avl_child2balance[which_child];
		parent = AVL_XPARENT(node);
		which_child = AVL_XCHILD(node);

		/*
		 * If a node was in perfect balance but isn't anymore then
		 * we can stop, since the height didn't change above this point
		 * due to a deletion.
		 */
		if (old_balance == 0) {
			AVL_SETBALANCE(node, new_balance);
			break;
		}

		/*
		 * If the new balance is zero, we don't need to rotate
		 * else
		 * need a rotation to fix the balance.
		 * If the rotation doesn't change the height
		 * of the sub-tree we have finished adjusting.
		 */
		if (new_balance == 0)
			AVL_SETBALANCE(node, new_balance);
		else if (!avl_rotation(tree, node, new_balance))
			break;
	} while (parent != NULL);
}

/*
 * initialize a new AVL tree
 */
void
avl_create(avl_tree_t *tree)
{
	assert(tree != NULL);
	tree->avl_root = NULL;
//	tree->avl_numnodes = 0;
}

/*
 * Return the number of nodes in an AVL tree.
 */
/*ulong_t
avl_numnodes(avl_tree_t *tree)
{
	assert(tree);
	return (tree->avl_numnodes);
}*/

bool
avl_is_empty(avl_tree_t *tree)
{
	assert(tree != NULL);
	return tree->avl_root == NULL;
}

struct avl_node *
avl_find_best(struct avl_tree *tree, size_t key)
{
	struct avl_node *node, *best_node;

	best_node = NULL;
	for (node = tree->avl_root; node != NULL;) {
		if (node->key == key)
			break;
		if (node->key < key) {
			node = node->avl_child[1];
		} else {
			best_node = node;
			node = node->avl_child[0];
		}
	}
	if (node == NULL)
		node = best_node;
	if (node != NULL && node->next != NULL)
		node = node->next;
	return node;
}

static void
avl_walk_impl(const struct avl_node *node1, void (*func)(const struct avl_node *, bool))
{
    const struct avl_node *node2;

    if (node1->avl_child[0] != NULL) {
        avl_walk_impl(node1->avl_child[0], func);
    }
    func(node1, false);
    for (node2 = node1->next; node2 != NULL; node2 = node2->next) {
        func(node2, true);
    }
    if (node1->avl_child[1] != NULL) {
        avl_walk_impl(node1->avl_child[1], func);
    }
}

void avl_walk(const struct avl_tree *tree, void (*func)(const struct avl_node *, bool)) {
    if (tree->avl_root != NULL) {
        avl_walk_impl(tree->avl_root, func);
    }
}

