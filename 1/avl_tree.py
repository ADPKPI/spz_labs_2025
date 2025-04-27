class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left_child = None
        self.right_child = None
        self.parent_node = None
        self.balance_factor = 0
        self.next_duplicate = None
        self.prev_duplicate = None

class BalancedTree:
    def __init__(self):
        self.tree_root = None

    def _locate(self, key):
        node = self.tree_root
        parent = None
        direction = None
        while node:
            parent = node
            if key < node.val:
                direction = 'left'
                node = node.left_child
            elif key > node.val:
                direction = 'right'
                node = node.right_child
            else:
                return node, parent, direction
        return None, parent, direction

    def left_rotate(self, pivot):
        r = pivot.right_child
        pivot.right_child = r.left_child
        if r.left_child:
            r.left_child.parent_node = pivot
        r.parent_node = pivot.parent_node
        if not pivot.parent_node:
            self.tree_root = r
        elif pivot == pivot.parent_node.left_child:
            pivot.parent_node.left_child = r
        else:
            pivot.parent_node.right_child = r
        r.left_child = pivot
        pivot.parent_node = r
        pivot.balance_factor = pivot.balance_factor - 1 - max(r.balance_factor, 0)
        r.balance_factor = r.balance_factor - 1 + min(pivot.balance_factor, 0)

    def right_rotate(self, pivot):
        l = pivot.left_child
        pivot.left_child = l.right_child
        if l.right_child:
            l.right_child.parent_node = pivot
        l.parent_node = pivot.parent_node
        if not pivot.parent_node:
            self.tree_root = l
        elif pivot == pivot.parent_node.left_child:
            pivot.parent_node.left_child = l
        else:
            pivot.parent_node.right_child = l
        l.right_child = pivot
        pivot.parent_node = l
        pivot.balance_factor = pivot.balance_factor + 1 - min(l.balance_factor, 0)
        l.balance_factor = l.balance_factor + 1 + max(pivot.balance_factor, 0)

    def _rebalance(self, node):
        if node.balance_factor == -2:
            if node.left_child.balance_factor <= 0:
                self.right_rotate(node)
            else:
                self.left_rotate(node.left_child)
                self.right_rotate(node)
        elif node.balance_factor == 2:
            if node.right_child.balance_factor >= 0:
                self.left_rotate(node)
            else:
                self.right_rotate(node.right_child)
                self.left_rotate(node)

    def update_balance_insert(self, node):
        parent = node.parent_node
        while parent:
            if node == parent.left_child:
                parent.balance_factor -= 1
            else:
                parent.balance_factor += 1
            if parent.balance_factor == 0:
                break
            if abs(parent.balance_factor) == 2:
                self._rebalance(parent)
                break
            node, parent = parent, parent.parent_node

    def add_node(self, key):
        new_node = TreeNode(key)
        found, parent, direction = self._locate(key)
        if found:
            new_node.next_duplicate = found.next_duplicate
            new_node.prev_duplicate = found
            found.next_duplicate = new_node
            if new_node.next_duplicate:
                new_node.next_duplicate.prev_duplicate = new_node
            return
        new_node.parent_node = parent
        if not parent:
            self.tree_root = new_node
        elif direction == 'left':
            parent.left_child = new_node
        else:
            parent.right_child = new_node
        self.update_balance_insert(new_node)

    def _update_balance_remove(self, node, removed_left):
        while node:
            node.balance_factor += 1 if removed_left else -1
            if abs(node.balance_factor) == 1:
                break
            if abs(node.balance_factor) == 2:
                old_balance = node.balance_factor
                self._rebalance(node)
                if not node.parent_node:
                    node = self.tree_root
                else:
                    node = node.parent_node
                if old_balance != 0:
                    break
            removed_left = node.parent_node and node == node.parent_node.left_child
            node = node.parent_node

    def delete_node(self, key):
        node, _, _ = self._locate(key)
        if not node:
            return
        if node.next_duplicate:
            successor = node.next_duplicate
            successor.prev_duplicate = node.prev_duplicate
            if node.prev_duplicate:
                node.prev_duplicate.next_duplicate = successor
            successor.left_child = node.left_child
            successor.right_child = node.right_child
            successor.parent_node = node.parent_node
            successor.balance_factor = node.balance_factor
            if node.left_child:
                node.left_child.parent_node = successor
            if node.right_child:
                node.right_child.parent_node = successor
            if not node.parent_node:
                self.tree_root = successor
            elif node == node.parent_node.left_child:
                node.parent_node.left_child = successor
            else:
                node.parent_node.right_child = successor
            node = successor
        child = node.left_child or node.right_child
        if child:
            child.parent_node = node.parent_node
        if not node.parent_node:
            self.tree_root = child
        else:
            left_removed = (node == node.parent_node.left_child)
            if left_removed:
                node.parent_node.left_child = child
            else:
                node.parent_node.right_child = child
            self._update_balance_remove(node.parent_node, left_removed)

    def best_match(self, key):
        node = self.tree_root
        candidate = None
        while node:
            if node.val == key:
                candidate = node
                break
            elif node.val < key:
                node = node.right_child
            else:
                candidate = node
                node = node.left_child
        if candidate and candidate.next_duplicate:
            return candidate.next_duplicate
        return candidate

    def iterate(self, action):
        def _walk(node):
            if not node:
                return
            _walk(node.left_child)
            action(node, False)
            dup = node.next_duplicate
            while dup:
                action(dup, True)
                dup = dup.next_duplicate
            _walk(node.right_child)
        _walk(self.tree_root)
