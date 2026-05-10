#ifndef CRONOS_SCHEDULER_H
#define CRONOS_SCHEDULER_H

#include "arkhe_hal.h"

typedef enum {
    THREAD_RESONATING,
    THREAD_EXECUTING,
    THREAD_DECOHERENT
} thread_state_t;

typedef struct cronos_thread {
    uint64_t id;
    void* instruction_ptr;
    double natural_freq;
    double lambda_alloc;
    arkhe_phase_t phase;

    // Temporal & Phase Properties
    double lambda_alloc;       // Coherence at the time of thread creation
    arkhe_phase_t phase;       // Current internal phase of the thread
    double natural_freq;       // ω_i (Natural frequency of the task)

    thread_state_t state;
    struct cronos_thread* next;
    struct cronos_thread* prev;
} cronos_thread_t;

void cronos_init(arkhe_node_t* hw_node);
cronos_thread_t* cronos_spawn(void* entry_point, double natural_freq);
cronos_thread_t* cronos_tick(void);

#endif
