#include "arkhe/core/arena.hpp"
#include <cstdlib>
#include <cstring>
#include <ctime>

namespace arkhe::core {

extern "C" {

cathedral_arena_t* cathedral_arena_create(size_t capacity) {
    cathedral_arena_t* arena = (cathedral_arena_t*)malloc(sizeof(cathedral_arena_t));
    if (!arena) return nullptr;

    arena->base = (uint8_t*)malloc(capacity);
    if (!arena->base) {
        free(arena);
        return nullptr;
    }

    arena->capacity = capacity;
    arena->offset = 0;
    arena->record_capacity = 1024; // Default initial capacity for records
    arena->records = (cathedral_alloc_record_t*)malloc(sizeof(cathedral_alloc_record_t) * arena->record_capacity);
    arena->record_count = 0;

    pthread_mutex_init(&arena->lock, nullptr);

    return arena;
}

void cathedral_arena_destroy(cathedral_arena_t* arena) {
    if (!arena) return;
    pthread_mutex_destroy(&arena->lock);
    free(arena->base);
    free(arena->records);
    free(arena);
}

void* cathedral_calloc_sovereign(cathedral_arena_t* arena,
                                  size_t nmemb, size_t size,
                                  const char* purpose,
                                  const char* substrate) {
    if (!arena) return nullptr;

    size_t total_size = nmemb * size;
    pthread_mutex_lock(&arena->lock);

    if (arena->offset + total_size > arena->capacity) {
        pthread_mutex_unlock(&arena->lock);
        return nullptr;
    }

    void* ptr = arena->base + arena->offset;
    memset(ptr, 0, total_size);
    arena->offset += total_size;

    // Tracking
    if (arena->record_count < arena->record_capacity) {
        cathedral_alloc_record_t* rec = &arena->records[arena->record_count++];
        rec->ptr = ptr;
        rec->size = total_size;
        rec->purpose = purpose;
        rec->substrate = substrate;

        struct timespec ts;
        clock_gettime(CLOCK_REALTIME, &ts);
        rec->alloc_ts = (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
        rec->free_ts = 0;
        rec->freed = 0;
    }

    pthread_mutex_unlock(&arena->lock);
    return ptr;
}

void cathedral_free_sovereign(cathedral_arena_t* arena, void* ptr) {
    if (!arena || !ptr) return;

    pthread_mutex_lock(&arena->lock);
    // In a simple arena, we don't actually free the memory until the whole arena is destroyed.
    // We just mark it as freed in our tracking records.
    for (size_t i = 0; i < arena->record_count; ++i) {
        if (arena->records[i].ptr == ptr) {
            arena->records[i].freed = 1;
            struct timespec ts;
            clock_gettime(CLOCK_REALTIME, &ts);
            arena->records[i].free_ts = (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
            break;
        }
    }
    pthread_mutex_unlock(&arena->lock);
}

} // extern "C"

} // namespace arkhe::core
