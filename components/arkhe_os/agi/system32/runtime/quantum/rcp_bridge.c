#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// Invoca o Python via subprocesso e captura o resultado.
// Em produção, usar Python C API ou embutir o interpretador.
int rcp_transmit_byte(const char* src, const char* dst, unsigned char byte_val,
                      double t_weak, double t_post, int n_shots,
                      unsigned char* decoded, double* fidelity) {
    char cmd[512];
    snprintf(cmd, sizeof(cmd),
        "python3 -c \"from rcp_v2_engine import RetrocausalChannel8Bit; "
        "ch=RetrocausalChannel8Bit(); "
        "d,f=ch.transmit_byte(%d, n_shots=%d, t_weak=%f, t_post=%f); "
        "print(f'{d}:{f:.4f}')\"",
        byte_val, n_shots, t_weak, t_post);
    FILE* fp = popen(cmd, "r");
    if (!fp) return -1;
    int d;
    double f;
    fscanf(fp, "%d:%lf", &d, &f);
    pclose(fp);
    *decoded = (unsigned char)d;
    *fidelity = f;
    return 0;
}

int rcp_send_message(const char* src, const char* dst, const char* message,
                     double t_weak, double t_post, int n_shots,
                     char* result_buf, int buf_len) {
    // … implementação similar, byte a byte
    return 0;
}
