#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include "allocator.h"
#include "tester.h"

#define COLOR_RESET "\x1b[0m"
#define COLOR_BRIGHT_GREEN "\x1b[1;32m"
#define COLOR_BRIGHT_RED "\x1b[1;31m"
#define COLOR_BRIGHT_YELLOW "\x1b[1;33m"

struct T {
    void *ptr;
    size_t size;
    unsigned int checksum;
};

static unsigned int buffer_checksum(const unsigned char *c, size_t size) {
    unsigned int checksum = 0;
    while (size--)
        checksum = (checksum << 3) ^ (checksum >> 5) ^ *c++;
    return checksum;
}

static void buffer_fill_random(unsigned char *c, size_t size) {
    while (size--)
        *c++ = (unsigned char)rand();
}

static void *buffer_alloc_and_fill(size_t size) {
    void *ptr = mem_alloc(size);
    if (ptr)
        buffer_fill_random(ptr, size);
    return ptr;
}

static int check_all_entry_checksums(struct T t[], size_t count) {
    for (size_t i = 0; i < count; i++) {
        if (t[i].ptr && buffer_checksum(t[i].ptr, t[i].size) != t[i].checksum) {
            printf(COLOR_BRIGHT_RED "1. Checksum failed at [%p]\n" COLOR_RESET, t[i].ptr);
            return 0;
        }
    }
    return 1;
}

static void test_alloc_entry(struct T *entry, bool verbose, size_t SZ_MIN, size_t SZ_MAX) {
    size_t size = ((size_t)rand() % (SZ_MAX - SZ_MIN)) + SZ_MIN;
    if (verbose)
        printf(COLOR_BRIGHT_YELLOW "ALLOC %zu ", size);

    void *ptr = buffer_alloc_and_fill(size);
    if (ptr) {
        entry->size = size;
        entry->ptr = ptr;
        entry->checksum = buffer_checksum(ptr, size);
        if (verbose)
            printf(COLOR_BRIGHT_GREEN "-> [%p]\n" COLOR_RESET, ptr);
    } else if (verbose) {
        printf(COLOR_BRIGHT_RED "failed\n" COLOR_RESET);
    }
}

static int test_realloc_entry(struct T *entry, bool verbose, size_t SZ_MIN, size_t SZ_MAX) {
    if (verbose)
        printf(COLOR_BRIGHT_YELLOW "REALLOC [%p] %zu ", entry->ptr, entry->size);

    size_t size = ((size_t)rand() % (SZ_MAX - SZ_MIN)) + SZ_MIN;
    size_t size_min = size < entry->size ? size : entry->size;
    unsigned int checksum = buffer_checksum(entry->ptr, size_min);

    void *ptr = mem_realloc(entry->ptr, size);
    if (ptr) {
        if (verbose)
            printf(COLOR_BRIGHT_GREEN "-> [%p] %zu\n" COLOR_RESET, ptr, size);
        if (checksum != buffer_checksum(ptr, size_min)) {
            printf(COLOR_BRIGHT_RED "2. Checksum failed at [%p]\n" COLOR_RESET, ptr);
            return 0;
        }
        buffer_fill_random(ptr, size);
        entry->ptr = ptr;
        entry->size = size;
        entry->checksum = buffer_checksum(ptr, size);
    } else if (verbose) {
        printf(COLOR_BRIGHT_RED "failed\n" COLOR_RESET);
    }
    return 1;
}

static int check_final_entry_checksums(struct T t[], size_t count) {
    for (size_t i = 0; i < count; i++) {
        if (t[i].ptr && buffer_checksum(t[i].ptr, t[i].size) != t[i].checksum) {
            printf(COLOR_BRIGHT_RED "3. Checksum failed at [%p]\n" COLOR_RESET, t[i].ptr);
            return 0;
        }
    }
    return 1;
}

static void free_all_entries(struct T t[], size_t count) {
    for (size_t i = 0; i < count; i++) {
        mem_free(t[i].ptr);
        t[i].ptr = NULL;
    }
}

static void test_free_entry(struct T *entry, bool verbose) {
    if (verbose)
        printf(COLOR_BRIGHT_YELLOW "FREE [%p]\n" COLOR_RESET, entry->ptr);
    mem_free(entry->ptr);
    entry->ptr = NULL;
    entry->size = 0;
    entry->checksum = 0;
}

void tester(const bool verbose) {
    const size_t t_NUM = 100;
    const size_t SZ_MIN = 1;
    const size_t SZ_MAX = 4094 * 10;
    const unsigned long ITERATIONS = 1000;

    struct T t[t_NUM];
    for (size_t i = 0; i < t_NUM; i++)
        t[i].ptr = NULL;

    for (unsigned long i = 0; i < ITERATIONS; i++) {
        if (verbose)
            mem_show("------------------------");

        if (!check_all_entry_checksums(t, t_NUM))
            return;

        size_t idx = (size_t)rand() % t_NUM;

        if (t[idx].ptr == NULL) {
            test_alloc_entry(&t[idx], verbose, SZ_MIN, SZ_MAX);
        } else if (rand() & 1) {
            if (!test_realloc_entry(&t[idx], verbose, SZ_MIN, SZ_MAX))
                return;
        } else {
            test_free_entry(&t[idx], verbose);
        }
    }

    if (!check_final_entry_checksums(t, t_NUM))
        return;

    free_all_entries(t, t_NUM);

    if (verbose)
        mem_show("------------------------");
}

