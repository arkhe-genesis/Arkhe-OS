#ifndef TEMPORAL_ANCHOR_H
#define TEMPORAL_ANCHOR_H

typedef struct TemporalAnchor TemporalAnchor;

TemporalAnchor* temporal_anchor_create(const char *config_path);
void temporal_anchor_stabilize(TemporalAnchor *anchor, double *local_phi_c, double *temporal_state, int steps);
void temporal_anchor_destroy(TemporalAnchor *anchor);

#endif
