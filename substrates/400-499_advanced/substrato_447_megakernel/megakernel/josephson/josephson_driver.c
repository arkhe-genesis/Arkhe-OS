#include "josephson_driver.h"

josephson_ring_t rings[N_RINGS];
double squid_offset_val;

int josephson_init(int n_rings, double Ic, double T) {
    (void)T;
    for (int i = 0; i < n_rings; i++) {
        rings[i].ring_id = i;
        rings[i].phi = 0.0;
        rings[i].dphi = 0.0;
        rings[i].Ic = Ic;
        rings[i].bias = 0.0;
        rings[i].state = 0;
    }
    squid_offset_val = SQUID_OFFSET;
    return 0;
}

int josephson_calibrate_squids(double offset) {
    squid_offset_val = offset;
    return 0;
}

int josephson_write_bit(int ring_id, int target_state) {
    if (ring_id < 0 || ring_id >= N_RINGS) return -1;

    double target_phi = target_state ? M_PI : 0.0;

    /* Bang-Bang: corrente maxima ate cruzar limiar */
    double limiar = 0.95 * target_phi;
    while (fabs(rings[ring_id].phi) < limiar) {
        rings[ring_id].bias = 3.0 * rings[ring_id].Ic;
        josephson_pid_control(ring_id, target_phi);
        rings[ring_id].phi += (target_phi > rings[ring_id].phi) ? 0.1 : -0.1;
    }
    rings[ring_id].bias = 0.0;

    /* PID fino para anular erro residual */
    while (fabs(rings[ring_id].phi - target_phi) > 0.001) {
        josephson_pid_control(ring_id, target_phi);
        rings[ring_id].phi += (target_phi - rings[ring_id].phi) * 0.5;
    }

    rings[ring_id].state = target_state;
    return 0;
}

int josephson_read_bit(int ring_id, double* squid_voltage) {
    if (ring_id < 0 || ring_id >= N_RINGS) return -1;

    /* SQUID readout com offset Phi_0/4 */
    double flux_total = (rings[ring_id].phi / (2*M_PI) + squid_offset_val) * PHI_0;
    double Ic_mod = 2 * IC_RING * fabs(cos(M_PI * flux_total / PHI_0));
    double discriminant = 1.0 - (Ic_mod/IC_RING)*(Ic_mod/IC_RING);
    *squid_voltage = (discriminant > 0) ? 10e-6 * sqrt(discriminant) : 0.0;
    return rings[ring_id].state;
}

int josephson_process_queue(void) {
    return 0;
}
