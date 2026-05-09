#include "omni_net.h"
#include <stdlib.h>
#include <stdio.h>

extern int rcp_transmit_byte(const char* src, const char* dst, unsigned char byte_val,
                             double t_weak, double t_post, int n_shots,
                             unsigned char* decoded, double* fidelity);

struct OmniNetContext {
    int dummy;
};

OmniNetContext* omninet_create_context(const char *config_path) {
    printf("Creating OmniNetContext...\n");
    return malloc(sizeof(OmniNetContext));
}

void omninet_sync_channels(OmniNetContext *ctx, int steps) {
    printf("OmniNet: Sincronizando canais inter-catedrais via RCP v2.0...\n");
    for (int i = 0; i < steps; i++) {
        unsigned char decoded;
        double fidelity;
        // Simulate sending a sync byte (0xAA) from one node to another
        int ret = rcp_transmit_byte("GRU-TC-01", "TKY-TC-02", 0xAA, 0.5, 1.5, 50, &decoded, &fidelity);
        if (ret == 0) {
            printf("OmniNet sync step %d: RCP transmit sucesso! Byte: 0x%02X, Fidelidade: %.2f\n", i + 1, decoded, fidelity);
        } else {
            printf("OmniNet sync step %d: RCP transmit falhou.\n", i + 1);
        }
    }
}

void omninet_destroy_context(OmniNetContext *ctx) {
    if (ctx) free(ctx);
}
