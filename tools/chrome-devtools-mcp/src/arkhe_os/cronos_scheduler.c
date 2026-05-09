#include "cronos_scheduler.h"
#include <stdlib.h>
#include <math.h>
#include <stdio.h>

#define K_COUPLING 0.15
#define PHI 1.6180339887

static cronos_thread_t* thread_ring_root = NULL;
static cronos_thread_t* current_thread = NULL;
static arkhe_node_t* hw_context = NULL;
static uint64_t thread_counter = 0;

void cronos_init(arkhe_node_t* hw_node) {
    hw_context = hw_node;
    fprintf(stderr, "[CRONOS] Scheduler initialized. Time is now phase-locked.\n");
}

cronos_thread_t* cronos_spawn(void* entry_point, double natural_freq) {
    cronos_thread_t* t = (cronos_thread_t*)malloc(sizeof(cronos_thread_t)); // In reality, uses arkhe_malloc
    t->id = ++thread_counter;
    t->instruction_ptr = entry_point;
    t->natural_freq = natural_freq;

    // Tag with current hardware coherence
    t->lambda_alloc = arkhe_hal_read_lambda2(hw_context);
    t->phase = arkhe_hal_read_phase(hw_context);
    t->state = THREAD_RESONATING;

    // Insert into the Phase Ring (Circular Doubly-Linked List)
    if (!thread_ring_root) {
        thread_ring_root = t;
        t->next = t;
        t->prev = t;
    } else {
        cronos_thread_t* tail = thread_ring_root->prev;
        tail->next = t;
        t->prev = tail;
        t->next = thread_ring_root;
        thread_ring_root->prev = t;
    }

    return t;
}

// Helper to calculate phase angle from complex phase
static double get_angle(arkhe_phase_t p) {
    return atan2(p.imag, p.real);
}

// Helper to create complex phase from angle
static arkhe_phase_t from_angle(double angle) {
    arkhe_phase_t p = { cos(angle), sin(angle) };
    return p;
}

cronos_thread_t* cronos_tick(void) {
    if (!thread_ring_root) return NULL;

    // 1. Read Global Hardware Phase
    arkhe_phase_t global_phase = arkhe_hal_read_phase(hw_context);
    double global_angle = get_angle(global_phase);
    double current_lambda2 = arkhe_hal_read_lambda2(hw_context);

    cronos_thread_t* t = thread_ring_root;
    cronos_thread_t* best_thread = NULL;
    double best_alignment = -1.0;

    // 2. Kuramoto Phase Update & Resonance Selection
    do {
        if (t->state == THREAD_DECOHERENT) {
            t = t->next;
            continue;
        }

        double t_angle = get_angle(t->phase);

        // Kuramoto coupling: Thread phase is pulled toward global hardware phase
        // dθ_i/dt = ω_i + K * sin(θ_global - θ_i)
        double d_theta = t->natural_freq + K_COUPLING * sin(global_angle - t_angle);
        t_angle += d_theta; // dt is implicit per tick

        t->phase = from_angle(t_angle);

        // Calculate resonance (Cosine similarity between thread phase and global phase)
        double alignment = cos(global_angle - t_angle);

        // Boost alignment if the thread was created during high coherence
        alignment *= (t->lambda_alloc / PHI);

        if (alignment > best_alignment) {
            best_alignment = alignment;
            best_thread = t;
        }

        t = t->next;
    } while (t != thread_ring_root);

    // 3. Context Switch
    if (best_thread && best_thread != current_thread) {
        if (current_thread && current_thread->state == THREAD_EXECUTING) {
            current_thread->state = THREAD_RESONATING;
        }
        best_thread->state = THREAD_EXECUTING;
        current_thread = best_thread;

        // In a real OS, we would trigger the assembly context switch here:
        // switch_context(&current_thread->stack_ptr, &best_thread->stack_ptr);
    }

    return current_thread;
}

void cronos_yield(void) {
    if (current_thread) {
        current_thread->state = THREAD_RESONATING;
        // Artificially shift phase to allow other threads to resonate
        double angle = get_angle(current_thread->phase);
        current_thread->phase = from_angle(angle + M_PI/2.0); // 90-degree shift
    }
    cronos_tick();
}
