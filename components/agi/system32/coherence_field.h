#ifndef COHERENCE_FIELD_H
#define COHERENCE_FIELD_H

typedef struct CoherenceField CoherenceField;

CoherenceField* coherence_field_create(const char *config_path);
void coherence_field_propagate(CoherenceField *field, double *temporal_state, double *field_output, double coupling_k, int steps);
void coherence_field_destroy(CoherenceField *field);

#endif
