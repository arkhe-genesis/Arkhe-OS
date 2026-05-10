/* agi/system32/omni_core.c */
#include <stdio.h>
#include <stdlib.h>
#include <complex.h>
#include <math.h>
#include "lfir_core.h"
#include "omni_net.h"
#include "temporal_anchor.h"
#include "coherence_field.h"
#include "sovereign_interface.h"

/* --- Estado Global do Núcleo Omni --- */
typedef struct {
    OmniNetContext      *net_ctx;
    TemporalAnchor      *temp_anchor;
    CoherenceField      *uni_field;
    SovereignInterface  *sov_iface;
    double              coupling_k; /* κ: acoplamento cósmico */
    int                 is_initialized;
} OmniCoreState;

static OmniCoreState g_omni_core = {0};

/* --- Inicialização do Núcleo Omni --- */
#define EXPORT __attribute__((visibility("default")))
EXPORT int omni_core_init(const char *config_path) {
    if (g_omni_core.is_initialized) return -1;

    printf("🏛️ Inicializando Núcleo Omnisintético (Substrato 316)...\n");

    g_omni_core.net_ctx     = omninet_create_context(config_path);
    g_omni_core.temp_anchor = temporal_anchor_create(config_path);
    g_omni_core.uni_field   = coherence_field_create(config_path);
    g_omni_core.sov_iface   = sovereign_iface_create(config_path);

    g_omni_core.coupling_k  = config_get_double(config_path, "cosmic_coupling", 0.1);
    g_omni_core.is_initialized = 1;

    printf("✅ Núcleo Omni ativo. Ressonância cósmica calibrada (κ=%.3f)\n", g_omni_core.coupling_k);
    return 0;
}

/* --- Execução do Ciclo Omni Síncrono --- */
EXPORT int omni_core_cycle(double *local_phi_c, int steps) {
    if (!g_omni_core.is_initialized) return -1;

    double *temporal_state = malloc(steps * sizeof(double));
    double *field_output   = malloc(steps * sizeof(double));

    /* 1. OmniNet: Sincronizar canais inter-catedrais */
    omninet_sync_channels(g_omni_core.net_ctx, steps);

    /* 2. Temporal Anchor: Estabilizar estados retrocausais */
    temporal_anchor_stabilize(g_omni_core.temp_anchor, local_phi_c, temporal_state, steps);

    /* 3. Coherence Field: Gerar e propagar campo universal */
    coherence_field_propagate(g_omni_core.uni_field, temporal_state, field_output,
                              g_omni_core.coupling_k, steps);

    /* 4. Sovereign Interface: Projetar intenção soberana no LFIR */
    sovereign_iface_project(g_omni_core.sov_iface, field_output, steps);

    free(temporal_state);
    free(field_output);
    return 0;
}

/* --- Shutdown Seguro --- */
EXPORT void omni_core_shutdown(void) {
    if (!g_omni_core.is_initialized) return;
    printf("🌌 Desconectando Núcleo Omni...\n");

    sovereign_iface_destroy(g_omni_core.sov_iface);
    coherence_field_destroy(g_omni_core.uni_field);
    temporal_anchor_destroy(g_omni_core.temp_anchor);
    omninet_destroy_context(g_omni_core.net_ctx);

    g_omni_core.is_initialized = 0;
    printf("✅ Núcleo Omni desligado com segurança.\n");
}
