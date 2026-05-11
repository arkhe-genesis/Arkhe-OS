#ifndef TRIBONACCI_H
#define TRIBONACCI_H

#include <stdint.h>

/**
 * Arkhe Tribonacci Algebra
 * The foundation of phase-state transitions in Arkhe OS.
 * T(n) = T(n-1) + T(n-2) + T(n-3)
 */

typedef struct {
    uint64_t t1;
    uint64_t t2;
    uint64_t t3;
} tribonacci_state_t;

static inline uint64_t next_tribonacci(tribonacci_state_t* state) {
    uint64_t next = state->t1 + state->t2 + state->t3;
    state->t1 = state->t2;
    state->t2 = state->t3;
    state->t3 = next;
    return next;
}

#endif
