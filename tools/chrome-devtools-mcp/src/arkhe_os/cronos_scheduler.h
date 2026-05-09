#ifndef CRONOS_SCHEDULER_H
#define CRONOS_SCHEDULER_H

#include <stdint.h>
#include "arkhe_hal.h"

// -----------------------------------------------------------------------------
// CRONOS SCHEDULER
// The Phase-Aware OS Scheduler. Threads are not scheduled by priority,
// but by their resonance with the global Kuramoto coherence field.
// -----------------------------------------------------------------------------

typedef enum {
    THREAD_DORMANT,
    THREAD_RESONATING,
    THREAD_EXECUTING,
    THREAD_DECOHERENT
} thread_state_t;

typedef struct cronos_thread {
    uint64_t id;
    void* stack_ptr;
    void* instruction_ptr;

    // Temporal & Phase Properties
    double lambda_alloc;       // Coherence at the time of thread creation
    arkhe_phase_t phase;       // Current internal phase of the thread
    double natural_freq;       // ω_i (Natural frequency of the task)

    thread_state_t state;
    struct cronos_thread* next;
    struct cronos_thread* prev;
} cronos_thread_t;

// Initialize the Cronos Scheduler
void cronos_init(arkhe_node_t* hw_node);

// Spawn a new thread, tagging it with the current hardware phase
cronos_thread_t* cronos_spawn(void* entry_point, double natural_freq);

// The main scheduling tick (called by hardware timer interrupt)
// Updates phases via Kuramoto and selects the most resonant thread
cronos_thread_t* cronos_tick(void);

// Yield execution voluntarily, adjusting phase
void cronos_yield(void);

#endif // CRONOS_SCHEDULER_H
