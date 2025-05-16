#include <assert.h>
#include "block.h"
#include "config.h"
#include "kernel.h"
#include <stdio.h>

static Block* create_block_right(Block* block, size_t size, size_t size_rest) {
    Block* block_r = block_next(block);
    block_init(block_r);
    block_set_size_curr(block_r, size_rest);
    block_set_size_prev(block_r, size);
    block_set_offset(block_r, block_get_offset(block) + size + BLOCK_STRUCT_SIZE);
    return block_r;
}

static void update_flag_last(Block* block, Block* block_r, size_t size_rest) {
    if (block_get_flag_last(block)) {
        block_clr_flag_last(block);
        block_set_flag_last(block_r);
    } else {
        block_set_size_prev(block_next(block_r), size_rest);
    }
}

static int is_division_possible(size_t size_rest) {
    return size_rest >= BLOCK_STRUCT_SIZE + BLOCK_SIZE_MIN;
}

static size_t calculate_rest_size(Block* block, size_t size) {
    return block_get_size_curr(block) - size;
}

Block* block_divide(Block *block, size_t size) {
    block_set_flag_busy(block);
    size_t size_rest = calculate_rest_size(block, size);
    if (!is_division_possible(size_rest)) {
        return NULL;
    }

    size_rest -= BLOCK_STRUCT_SIZE;
    block_set_size_curr(block, size);

    Block* block_r = create_block_right(block, size, size_rest);
    update_flag_last(block, block_r, size_rest);
    return block_r;
}

static size_t calculate_merged_size(Block* block, Block* block_r) {
    return block_get_size_curr(block) + block_get_size_curr(block_r) + BLOCK_STRUCT_SIZE;
}

static void apply_merged_block_changes(Block* block, Block* block_r, size_t merged_size) {
    block_set_size_curr(block, merged_size);
    if (block_get_flag_last(block_r)) {
        block_set_flag_last(block);
    } else {
        block_set_size_prev(block_next(block_r), merged_size);
    }
}

void block_combine(Block *block, Block *block_r) {
    assert(block_get_flag_busy(block_r) == false);
    assert(block_next(block) == block_r);
    size_t merged_size = calculate_merged_size(block, block_r);
    apply_merged_block_changes(block, block_r, merged_size);
}

static int block_has_space(Block* block) {
    size_t size_curr = block_get_size_curr(block);
    return (size_curr - sizeof(tree_node_type)) >= ALLOCATOR_PAGE_SIZE;
}

static size_t calc_offset_start(Block* block, size_t offset) {
    size_t off1 = offset + BLOCK_STRUCT_SIZE + sizeof(tree_node_type);
    off1 = (off1 + ALLOCATOR_PAGE_SIZE - 1) & ~((size_t)ALLOCATOR_PAGE_SIZE - 1);
    return off1;
}

static size_t calc_offset_end(Block* block, size_t offset, size_t size_curr) {
    size_t off2 = offset + size_curr + BLOCK_STRUCT_SIZE;
    off2 &= ~((size_t)ALLOCATOR_PAGE_SIZE - 1);
    return off2;
}

static int is_reset_needed(size_t off1, size_t off2) {
    return off1 != off2;
}

static void reset_unused_memory(Block* block, size_t off1, size_t off2, size_t offset) {
    assert(((off2 - off1) & ((size_t)ALLOCATOR_PAGE_SIZE - 1)) == 0);
    kernel_memory_reset((char*)block + (off1 - offset), off2 - off1);
}

void block_release_unused(Block* block) {
    if (!block_has_space(block)) {
        return;
    }

    size_t offset = block_get_offset(block);
    size_t size_curr = block_get_size_curr(block);
    size_t off1 = calc_offset_start(block, offset);
    size_t off2 = calc_offset_end(block, offset, size_curr);

    if (!is_reset_needed(off1, off2)) {
        return;
    }

    reset_unused_memory(block, off1, off2, offset);
}

