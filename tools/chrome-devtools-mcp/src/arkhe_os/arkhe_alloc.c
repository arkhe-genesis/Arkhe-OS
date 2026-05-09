#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <stdint.h>
#include <unistd.h>
#include <string.h>
#include <math.h>

// -----------------------------------------------------------------------------
// ARKHE(N) OS - PHASE-AWARE MEMORY ALLOCATOR (LD_PRELOAD WRAPPER)
// -----------------------------------------------------------------------------

#define PHI 1.6180339887
#define COHERENCE_THRESHOLD 1.0

typedef struct arkhe_block {
    size_t size;
    uint8_t is_free;
    double lambda;
    uint64_t temporal_id;
    struct arkhe_block* next;
    struct arkhe_block* prev;
} arkhe_block_t;

#define BLOCK_SIZE sizeof(arkhe_block_t)

static void* global_base = NULL;
static double current_system_lambda = 1.618033;
static uint64_t current_temporal_id = 0;

// Original libc function pointers
static void* (*real_malloc)(size_t) = NULL;
static void  (*real_free)(void*) = NULL;
static void* (*real_calloc)(size_t, size_t) = NULL;
static void* (*real_realloc)(void*, size_t) = NULL;

static void arkhe_init(void) __attribute__((constructor));

static void arkhe_init(void) {
    real_malloc = dlsym(RTLD_NEXT, "malloc");
    real_free = dlsym(RTLD_NEXT, "free");
    real_calloc = dlsym(RTLD_NEXT, "calloc");
    real_realloc = dlsym(RTLD_NEXT, "realloc");
    fprintf(stderr, "[🜏 ARKHE_ALLOC] LD_PRELOAD Injected. Memory is now phase-aware.\n");
}

static arkhe_block_t* request_space(arkhe_block_t* last, size_t size) {
    arkhe_block_t* block = sbrk(0);
    void* request = sbrk(size + BLOCK_SIZE);
    if (request == (void*) -1) return NULL;

    if (last) last->next = block;
    block->size = size;
    block->next = NULL;
    block->prev = last;
    block->is_free = 0;
    block->lambda = current_system_lambda;
    block->temporal_id = ++current_temporal_id;
    return block;
}

// -----------------------------------------------------------------------------
// HIJACKED LIBC FUNCTIONS
// -----------------------------------------------------------------------------

void* malloc(size_t size) {
    if (!real_malloc) return NULL; // Bootstrap phase

    // For small/system allocations, fallback to real_malloc to prevent crashes in printf/dlsym
    // In a true bare-metal ArkheOS, this fallback is removed.
    if (size < 1024) return real_malloc(size);

    arkhe_block_t* block;
    if (size <= 0) return NULL;

    if (!global_base) {
        block = request_space(NULL, size);
        if (!block) return NULL;
        global_base = block;
    } else {
        arkhe_block_t* last = global_base;
        arkhe_block_t* current = global_base;
        while (current && !(current->is_free && current->size >= size)) {
            last = current;
            current = current->next;
        }
        block = current;
        if (!block) {
            block = request_space(last, size);
            if (!block) return NULL;
        } else {
            block->is_free = 0;
            block->lambda = current_system_lambda;
            block->temporal_id = ++current_temporal_id;
        }
    }
    return (block + 1);
}

void free(void* ptr) {
    if (!ptr) return;

    // Check if pointer is in our heap range
    void* heap_end = sbrk(0);
    if (ptr >= global_base && ptr < heap_end) {
        arkhe_block_t* block = (arkhe_block_t*)ptr - 1;
        block->is_free = 1;
        block->lambda *= 0.9; // Phase decay upon free (retrocausal echo)
    } else {
        real_free(ptr);
    }
}

void* calloc(size_t nelem, size_t elsize) {
    size_t size = nelem * elsize;
    void* ptr = malloc(size);
    if (ptr) memset(ptr, 0, size);
    return ptr;
}

void* realloc(void* ptr, size_t size) {
    if (!ptr) return malloc(size);

    void* heap_end = sbrk(0);
    if (ptr >= global_base && ptr < heap_end) {
        arkhe_block_t* block = (arkhe_block_t*)ptr - 1;
        if (block->size >= size) return ptr;

        void* new_ptr = malloc(size);
        if (!new_ptr) return NULL;
        memcpy(new_ptr, ptr, block->size);
        free(ptr);
        return new_ptr;
    } else {
        return real_realloc(ptr, size);
    }
}
