#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/*
 * ARKHE OS — Substrate 316: Omni Core FFI Bridge
 * Invoca o Python runtime omni_core.py via subprocesso.
 * Em produção: usar Python C API para melhor performance.
 */

int omni_init(double phi_seed, double *kappa_out) {
    char cmd[512];
    snprintf(cmd, sizeof(cmd),
        "python3 -c \"from omni_core import OmniCore; "
        "o=OmniCore(); k=o.initialize(%f); print(f'{k:.6f}')\"",
        phi_seed);

    FILE* fp = popen(cmd, "r");
    if (!fp) return -1;

    double k;
    if (fscanf(fp, "%lf", &k) != 1) {
        pclose(fp);
        return -1;
    }
    pclose(fp);

    *kappa_out = k;
    return 0;
}

int omni_cycle(double phi_local, int steps,
               double *phi_projected, double *confidence) {
    char cmd[512];
    snprintf(cmd, sizeof(cmd),
        "python3 -c \"from omni_core import OmniCore; "
        "o=OmniCore(); o.initialize(%f); "
        "r=o.cycle(%f, %d); "
        "print(f\\\"{r['final_phi']}:{r['final_confidence']}\\\")\"",
        phi_local, phi_local, steps);

    FILE* fp = popen(cmd, "r");
    if (!fp) return -1;

    double p, c;
    if (fscanf(fp, "%lf:%lf", &p, &c) != 2) {
        pclose(fp);
        return -1;
    }
    pclose(fp);

    *phi_projected = p;
    *confidence = c;
    return 0;
}

int omni_calibrate(double phi_observed, int data_points,
                   double *kappa_new, int *converged) {
    (void)data_points;
    char cmd[512];
    snprintf(cmd, sizeof(cmd),
        "python3 -c \"from omni_core import OmniCore; "
        "o=OmniCore(); o.initialize(0.5); "
        "o.calibration.calibrate_kappa(%f); "
        "r=o.calibration.get_calibration_report(); "
        "print(f\\\"{r['final_kappa']}:{int(r['converged'])}\\\")\"",
        phi_observed);

    FILE* fp = popen(cmd, "r");
    if (!fp) return -1;

    double k;
    int conv;
    if (fscanf(fp, "%lf:%d", &k, &conv) != 2) {
        pclose(fp);
        return -1;
    }
    pclose(fp);

    *kappa_new = k;
    *converged = conv;
    return 0;
}

int omni_shutdown(void) {
    // No-op para stub - em produção, limpar recursos Python
    return 0;
}
