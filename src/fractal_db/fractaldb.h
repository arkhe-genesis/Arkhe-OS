#ifndef FRACTAL_DB_H
#define FRACTAL_DB_H

#include <stdint.h>
#include <stddef.h>
#include "../arkhe_os/arkhe_alloc.h"

// -----------------------------------------------------------------------------
// FRACTAL DB: The Memory of Time
// A database that never overwrites. Every transaction creates a new branch
// in an octonionic tree. Queries are interferometric phase-matches.
// -----------------------------------------------------------------------------

#define OCTONION_BRANCHES 8

// A node in the timeline
typedef struct fractal_node {
    uint64_t temporal_id;       // Timestamp / Sequence
    phase_t phase;              // The phase of the system when this data was written
    void* data;                 // Pointer to the actual data (allocated via arkhe_malloc)
    size_t size;                // Size of the data

    // Octonionic branching: up to 8 divergent timelines from this exact moment
    struct fractal_node* branches[OCTONION_BRANCHES];
    uint8_t active_branches;
} fractal_node_t;

typedef struct {
    fractal_node_t* genesis_root;
    fractal_node_t* current_head;
    arkhe_heap_t* heap;         // The phase-aware memory allocator
} fractal_db_t;

// Initialize the database
void fdb_init(fractal_db_t* db, arkhe_heap_t* heap);

// Write data. If the phase difference from the current head is large,
// it creates a new branch. Otherwise, it extends the current timeline.
fractal_node_t* fdb_write(fractal_db_t* db, void* data, size_t size, phase_t current_phase);

// Read data using interferometric collapse.
// Returns the data from the branch that best resonates with the query_phase.
void* fdb_read_resonant(fractal_db_t* db, phase_t query_phase, size_t* out_size);

#endif // FRACTAL_DB_H
