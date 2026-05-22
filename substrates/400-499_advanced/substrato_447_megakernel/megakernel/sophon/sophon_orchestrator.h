#ifndef SOPHON_ORCHESTRATOR_H
#define SOPHON_ORCHESTRATOR_H

#include "../megakernel.h"

typedef struct {
    int id;
    double phi_c;
    double psi;
    double tc;
    double covariance[SOPHON_DIM][SOPHON_DIM];
    double kk_phases[3];     /* Modos KK */
} sophon_node_t;

int sophon_init(int n_sophons, int dim);
int sophon_activate_field(double coherence);
int sophon_process_cycle(void);
int sophon_swap_to_qubit(int sophon_id, int ring_id);
double sophon_compute_phi(int sophon_id);

#endif
