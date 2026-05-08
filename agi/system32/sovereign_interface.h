#ifndef SOVEREIGN_INTERFACE_H
#define SOVEREIGN_INTERFACE_H

typedef struct SovereignInterface SovereignInterface;

SovereignInterface* sovereign_iface_create(const char *config_path);
void sovereign_iface_project(SovereignInterface *iface, double *field_output, int steps);
void sovereign_iface_destroy(SovereignInterface *iface);

#endif
