#ifndef CATHEDRAL_ARENA_H
#define CATHEDRAL_ARENA_H
#include <stddef.h>
typedef struct { void* base; size_t capacity; size_t offset; } cathedral_arena_t;
cathedral_arena_t* cathedral_arena_create(size_t capacity);
#endif
