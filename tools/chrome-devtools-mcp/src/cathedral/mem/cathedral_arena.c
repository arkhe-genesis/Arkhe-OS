#include "cathedral_arena.h"
#include <stdlib.h>
cathedral_arena_t* cathedral_arena_create(size_t capacity) {
    cathedral_arena_t* arena = (cathedral_arena_t*)malloc(sizeof(cathedral_arena_t));
    arena->base = malloc(capacity);
    arena->capacity = capacity;
    arena->offset = 0;
    return arena;
}
