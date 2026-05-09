#include "fractaldb.h"
#include <math.h>
#include <string.h>

#define PHASE_DIVERGENCE_THRESHOLD 0.314 // ~18 degrees

void fdb_init(fractal_db_t* db, arkhe_heap_t* heap) {
    db->heap = heap;

    // Create Genesis Node
    db->genesis_root = (fractal_node_t*)arkhe_malloc(heap, sizeof(fractal_node_t), 1.618);
    db->genesis_root->temporal_id = 0;
    db->genesis_root->phase = 1.618;
    db->genesis_root->data = NULL;
    db->genesis_root->size = 0;
    db->genesis_root->active_branches = 0;

    for(int i=0; i<OCTONION_BRANCHES; i++) {
        db->genesis_root->branches[i] = NULL;
    }

    db->current_head = db->genesis_root;
}

fractal_node_t* fdb_write(fractal_db_t* db, void* data, size_t size, phase_t current_phase) {
    // Allocate new node and copy data using phase-aware allocator
    fractal_node_t* new_node = (fractal_node_t*)arkhe_malloc(db->heap, sizeof(fractal_node_t), current_phase);
    void* new_data = arkhe_malloc(db->heap, size, current_phase);
    memcpy(new_data, data, size);

    new_node->temporal_id = db->current_head->temporal_id + 1;
    new_node->phase = current_phase;
    new_node->data = new_data;
    new_node->size = size;
    new_node->active_branches = 0;
    for(int i=0; i<OCTONION_BRANCHES; i++) new_node->branches[i] = NULL;

    // Calculate phase divergence to decide if we branch or extend
    double divergence = fabs(current_phase - db->current_head->phase);

    if (divergence > PHASE_DIVERGENCE_THRESHOLD && db->current_head->active_branches < OCTONION_BRANCHES) {
        // Fork a new timeline branch (Octonionic divergence)
        db->current_head->branches[db->current_head->active_branches] = new_node;
        db->current_head->active_branches++;
    } else {
        // Extend the primary timeline (Branch 0)
        if (db->current_head->branches[0] == NULL) {
            db->current_head->branches[0] = new_node;
            db->current_head->active_branches = 1;
        } else {
            // If branch 0 is taken, find next available or overwrite oldest branch (simplified)
            db->current_head->branches[0] = new_node;
        }
    }

    db->current_head = new_node;
    return new_node;
}

// Recursive helper for interferometric read
static fractal_node_t* collapse_wavefunction(fractal_node_t* node, phase_t query_phase, double* best_resonance) {
    if (!node) return NULL;

    fractal_node_t* best_node = NULL;
    double resonance = cos(query_phase - node->phase); // Interference pattern

    if (resonance > *best_resonance) {
        *best_resonance = resonance;
        best_node = node;
    }

    // Traverse all active branches (Superposition)
    for (int i = 0; i < node->active_branches; i++) {
        fractal_node_t* candidate = collapse_wavefunction(node->branches[i], query_phase, best_resonance);
        if (candidate) {
            best_node = candidate;
        }
    }

    return best_node;
}

void* fdb_read_resonant(fractal_db_t* db, phase_t query_phase, size_t* out_size) {
    double best_resonance = -1.0;
    fractal_node_t* result = collapse_wavefunction(db->genesis_root, query_phase, &best_resonance);

    if (result) {
        if (out_size) *out_size = result->size;
        return result->data;
    }

    if (out_size) *out_size = 0;
    return NULL;
}
