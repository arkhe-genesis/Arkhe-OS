#include "temporal_anchor.h"
#include <stdlib.h>
#include <stdio.h>

struct TemporalAnchor {
    int dummy;
};

TemporalAnchor* temporal_anchor_create(const char *config_path) {
    printf("Creating TemporalAnchor...\n");
    return malloc(sizeof(TemporalAnchor));
}

void temporal_anchor_stabilize(TemporalAnchor *anchor, double *local_phi_c, double *temporal_state, int steps) {
    for (int i = 0; i < steps; i++) {
        temporal_state[i] = local_phi_c[i];
    }
}

void temporal_anchor_destroy(TemporalAnchor *anchor) {
    if (anchor) free(anchor);
}
