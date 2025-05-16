#include <stdio.h>
#include <assert.h>
#include <string.h>
#include <stdint.h>
#include <stddef.h>
#include <limits.h>

#include "allocator.h"
#include "block.h"
#include "config.h"
#include "allocator_impl.h"
#include "kernel.h"

#define ARENA_SIZE (ALLOCATOR_ARENA_PAGES * ALLOCATOR_PAGE_SIZE)
#define BLOCK_SIZE_MAX (ARENA_SIZE - BLOCK_STRUCT_SIZE)

static tree_type block_tree = TREE_INITIALIZER;

static Block* allocate_memory_arena(size_t arena_size) {
    Block *new_block = kernel_memory_allocate(arena_size);
    if (new_block != NULL) {
        arena_init(new_block, arena_size - BLOCK_STRUCT_SIZE);
    }
    return new_block;
}

static Block* allocate_arena_or_block(size_t requested_size) {
    if (requested_size > BLOCK_SIZE_MAX) {
        return allocate_memory_arena(requested_size);
    } else {
        return allocate_memory_arena(ARENA_SIZE);
    }
}

static void add_block_to_tree(Block* block) {
    assert(block_get_flag_busy(block) == false);
    tree_add(&block_tree, block_to_node(block), block_get_size_curr(block));
}

static void remove_block_from_tree(Block* block) {
    assert(block_get_flag_busy(block) == false);
    tree_remove(&block_tree, block_to_node(block));
}

static Block* allocate_large_block_request(size_t requested_size) {
    if (requested_size > SIZE_MAX - (ALIGN - 1)) {
        return NULL;
    }
    size_t arena_size = (ROUND_BYTES(requested_size) / ALLOCATOR_PAGE_SIZE) * ALLOCATOR_PAGE_SIZE + BLOCK_STRUCT_SIZE;
    return allocate_arena_or_block(arena_size);
}

static Block* find_suitable_block(size_t aligned_size) {
    tree_node_type *best_node = tree_find_best(&block_tree, aligned_size);
    Block *suitable_block = NULL;
    if (best_node != NULL) {
        tree_remove(&block_tree, best_node);
        suitable_block = node_to_block(best_node);
    } else {
        suitable_block = allocate_arena_or_block(aligned_size);
    }
    return suitable_block;
}

void* mem_alloc(size_t requested_size) {
    Block *block, *divided_block;

    if (requested_size > BLOCK_SIZE_MAX) {
        block = allocate_large_block_request(requested_size);
        return block ? block_to_payload(block) : NULL;
    }

    if (requested_size < BLOCK_SIZE_MIN) {
        requested_size = BLOCK_SIZE_MIN;
    }
    size_t aligned_size = ROUND_BYTES(requested_size);

    block = find_suitable_block(aligned_size);
    if (block == NULL) {
        return NULL;
    }
    divided_block = block_divide(block, aligned_size);
    if (divided_block != NULL) {
        add_block_to_tree(divided_block);
    }
    return block_to_payload(block);
}

static void show_tree_node(const tree_node_type *node, const bool is_linked) {
    Block* block = node_to_block(node);
    printf("[%20p] %10zu %10zu %s %s %s %s\n",
           (void*)block,
           block_get_size_curr(block),
           block_get_size_prev(block),
           block_get_flag_busy(block) ? "busy" : "free",
           block_get_flag_first(block) ? "first" : "",
           block_get_flag_last(block) ? "last" : "",
           is_linked ? "linked" : "");
}

void mem_show(const char *msg) {
    printf("%s:\n", msg);
    if (tree_is_empty(&block_tree)) {
        printf("Tree is empty\n");
    } else {
        tree_walk(&block_tree, show_tree_node);
    }
}

static void merge_adjacent_free_blocks(Block** block) {
    Block* current_block = *block;
    if (!block_get_flag_last(current_block)) {
        Block* next_block = block_next(current_block);
        if (!block_get_flag_busy(next_block)) {
            remove_block_from_tree(next_block);
            block_combine(current_block, next_block);
        }
    }
    if (!block_get_flag_first(current_block)) {
        Block* prev_block = block_prev(current_block);
        if (!block_get_flag_busy(prev_block)) {
            remove_block_from_tree(prev_block);
            block_combine(prev_block, current_block);
            *block = prev_block;
        }
    }
}

void mem_free(void *ptr) {
    if (ptr == NULL) {
        return;
    }
    Block *block = payload_to_block(ptr);
    block_clr_flag_busy(block);

    if (block_get_size_curr(block) > BLOCK_SIZE_MAX) {
        kernel_memory_free(block, block_get_size_curr(block) + BLOCK_STRUCT_SIZE);
    } else {
        merge_adjacent_free_blocks(&block);
        if (block_get_flag_first(block) && block_get_flag_last(block)) {
            kernel_memory_free(block, ARENA_SIZE);
        } else {
            block_release_unused(block);
            add_block_to_tree(block);
        }
    }
}


static void* shrink_block_to_new_size(Block* block, size_t new_size) {
    if (!block_get_flag_last(block)) {
        Block* right_block = block_divide(block, new_size);
        if (right_block != NULL) {
            Block* next_block = block_next(right_block);
            if (!block_get_flag_busy(next_block)) {
                remove_block_from_tree(next_block);
                block_combine(right_block, next_block);
            }
            add_block_to_tree(right_block);
        }
    }
    return block_to_payload(block);
}

static void* expand_block_to_new_size(Block* block, size_t new_size) {
    if (!block_get_flag_last(block)) {
        Block* right_block = block_next(block);
        if (!block_get_flag_busy(right_block)) {
            size_t total_size = block_get_size_curr(block) + block_get_size_curr(right_block) + BLOCK_STRUCT_SIZE;
            if (total_size >= new_size) {
                remove_block_from_tree(right_block);
                block_combine(block, right_block);
                Block* divided_block = block_divide(block, new_size);
                if (divided_block != NULL) {
                    add_block_to_tree(divided_block);
                }
                return block_to_payload(block);
            }
        }
    }
    return NULL;
}

void* mem_realloc(void* old_ptr, size_t new_size) {
    void *new_ptr;
    Block *old_block;

    if (new_size < BLOCK_SIZE_MIN) {
        new_size = BLOCK_SIZE_MIN;
    }
    new_size = ROUND_BYTES(new_size);

    if (old_ptr == NULL) {
        return mem_alloc(new_size);
    }
    old_block = payload_to_block(old_ptr);
    size_t current_size = block_get_size_curr(old_block);

    if (current_size > BLOCK_SIZE_MAX) {
        if (new_size == current_size) {
            return old_ptr;
        }
        goto move_large_block;
    }
    if (new_size == current_size) {
        return old_ptr;
    }
    if (new_size < current_size) {
        return shrink_block_to_new_size(old_block, new_size);
    }
    if (new_size > current_size) {
        new_ptr = expand_block_to_new_size(old_block, new_size);
        if (new_ptr != NULL) {
            return new_ptr;
        }
    }
move_large_block:
    new_ptr = mem_alloc(new_size);
    if (new_ptr != NULL) {
        memcpy(new_ptr, old_ptr, current_size < new_size ? current_size : new_size);
        mem_free(old_ptr);
    }
    return new_ptr;
}

