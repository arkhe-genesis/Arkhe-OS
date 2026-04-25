#pragma once
#include <cstdint>
#include <cstddef>
#include <pthread.h>

namespace arkhe::core {

typedef struct {
    void* ptr;
    size_t size;
    const char* purpose;      // ex: "zk_witness", "llm_context"
    const char* substrate;    // ex: "FS-100", "FS-98v4"
    uint64_t alloc_ts;
    uint64_t free_ts;
    int freed;
} cathedral_alloc_record_t;

// Arena allocator com tracking para auditoria
typedef struct {
    uint8_t* base;
    size_t capacity;
    size_t offset;
    cathedral_alloc_record_t* records;
    size_t record_count;
    size_t record_capacity;
    pthread_mutex_t lock;
} cathedral_arena_t;

// API com verificação de soberania
extern "C" {
    void* cathedral_calloc_sovereign(cathedral_arena_t* arena,
                                      size_t nmemb, size_t size,
                                      const char* purpose,
                                      const char* substrate);
    void cathedral_free_sovereign(cathedral_arena_t* arena, void* ptr);

    cathedral_arena_t* cathedral_arena_create(size_t capacity);
    void cathedral_arena_destroy(cathedral_arena_t* arena);
}

} // namespace arkhe::core

// Macro para facilitar uso com tracking automático
#ifndef __SUBSTRATE__
#define __SUBSTRATE__ "CORE"
#endif

#define CATHEDRAL_ALLOC(arena, type, count, purpose) \
    (type*)arkhe::core::cathedral_calloc_sovereign(arena, count, sizeof(type), purpose, __SUBSTRATE__)
