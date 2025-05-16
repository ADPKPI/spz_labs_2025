#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "kernel.h"

#define DEBUG_KERNEL_RESET

static _Noreturn void error_alloc_fail(void) {
#define msg "kernel_memory_allocate() failed\n"
    write(STDERR_FILENO, msg, sizeof(msg) - 1);
#undef msg
    exit(EXIT_FAILURE);
}

static _Noreturn void error_free_fail(void) {
#define msg "kernel_memory_free() failed\n"
    write(STDERR_FILENO, msg, sizeof(msg) - 1);
#undef msg
    exit(EXIT_FAILURE);
}

static _Noreturn void error_reset_fail(void) {
#define msg "kernel_memory_reset() failed\n"
    write(STDERR_FILENO, msg, sizeof(msg) - 1);
#undef msg
    exit(EXIT_FAILURE);
}

// =====================
// 1. Unix/Linux реалізація
// =====================

#if !(defined(_WIN32) || defined(_WIN64))

#include <sys/mman.h>
#include <errno.h>

#if defined(MAP_ANONYMOUS)
# define MMAP_FLAG_ANON MAP_ANONYMOUS
#elif defined(MAP_ANON)
# define MMAP_FLAG_ANON MAP_ANON
#else
# error "ErrAn"
#endif

static void* mmap_allocate(size_t size) {
    return mmap(NULL, size, PROT_READ | PROT_WRITE, MMAP_FLAG_ANON | MAP_PRIVATE, -1, 0);
}

static void* mmap_process_result(void* ptr) {
    if (ptr == MAP_FAILED) {
        if (errno == ENOMEM)
            return NULL;
        error_alloc_fail();
    }
    return ptr;
}

static void mmap_deallocate(void* ptr, size_t size) {
    if (munmap(ptr, size) < 0)
        error_free_fail();
}

static void memset_debug_reset(void* ptr, size_t size) {
#ifdef DEBUG_KERNEL_RESET
    memset(ptr, 0x7e, size);
#endif
}

static void mmap_reset_advise(void* ptr, size_t size) {
    if (madvise(ptr, size, MADV_DONTNEED) < 0)
        error_reset_fail();
}

void* kernel_memory_allocate(size_t size) {
    void* ptr = mmap_allocate(size);
    return mmap_process_result(ptr);
}

void kernel_memory_free(void* ptr, size_t size) {
    mmap_deallocate(ptr, size);
}

void kernel_memory_reset(void* ptr, size_t size) {
    memset_debug_reset(ptr, size);
    mmap_reset_advise(ptr, size);
}

// =====================
// 2. Windows реалізація
// =====================

#else

static void* virtual_alloc_memory(size_t size) {
    return VirtualAlloc(NULL, size, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
}

void* kernel_memory_allocate(size_t size) {
    void* ptr = virtual_alloc_memory(size);
    return ptr;
}

static void virtual_free_memory(void* ptr, size_t size) {
    (void)size;
    if (VirtualFree(ptr, 0, MEM_RELEASE) == 0)
        error_free_fail();
}

void kernel_memory_free(void* ptr, size_t size) {
    virtual_free_memory(ptr, size);
}

static void virtual_reset_memory(void* ptr, size_t size) {
#ifdef DEBUG_KERNEL_RESET
    memset(ptr, 0x7e, size);
#endif
    if (VirtualAlloc(ptr, size, MEM_RESET, PAGE_READWRITE) == NULL)
        error_reset_fail();
}

void kernel_memory_reset(void* ptr, size_t size) {
    virtual_reset_memory(ptr, size);
}

#endif

