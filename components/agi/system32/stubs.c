#include "lfir_core.h"
#include "omni_net.h"
#include "temporal_anchor.h"
#include "coherence_field.h"
#include "sovereign_interface.h"
#include <stdlib.h>

double config_get_double(const char *config_path, const char *key, double default_val) { return default_val; }

OmniNetContext* omninet_create_context(const char *config_path) { return NULL; }
void omninet_sync_channels(OmniNetContext *ctx, int steps) {}
void omninet_destroy_context(OmniNetContext *ctx) {}

TemporalAnchor* temporal_anchor_create(const char *config_path) { return NULL; }
void temporal_anchor_stabilize(TemporalAnchor *anchor, double *local_phi_c, double *temporal_state, int steps) {}
void temporal_anchor_destroy(TemporalAnchor *anchor) {}

CoherenceField* coherence_field_create(const char *config_path) { return NULL; }
void coherence_field_propagate(CoherenceField *field, double *temporal_state, double *field_output, double coupling_k, int steps) {}
void coherence_field_destroy(CoherenceField *field) {}

SovereignInterface* sovereign_iface_create(const char *config_path) { return NULL; }
void sovereign_iface_project(SovereignInterface *iface, double *field_output, int steps) {}
void sovereign_iface_destroy(SovereignInterface *iface) {}
