#ifndef JOSEPHSON_DRIVER_H
#define JOSEPHSON_DRIVER_H

#include "../megakernel.h"

typedef struct {
    int ring_id;
    double phi;          /* Fase phi (rad) */
    double dphi;         /* Derivada dphi/dt */
    double Ic;           /* Corrente critica */
    double bias;         /* Bias de corrente */
    int state;           /* 0 = |0>, 1 = |1> */
} josephson_ring_t;

extern josephson_ring_t rings[N_RINGS];

int josephson_init(int n_rings, double Ic, double T);
int josephson_calibrate_squids(double offset);
int josephson_write_bit(int ring_id, int target_state);
int josephson_read_bit(int ring_id, double* squid_voltage);
int josephson_process_queue(void);
int josephson_pid_control(int ring_id, double target_phi);

#endif