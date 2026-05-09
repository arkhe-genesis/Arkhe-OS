#include "sovereign_interface.h"
#include <stdlib.h>
#include <stdio.h>

struct SovereignInterface {
    int dummy;
};

SovereignInterface* sovereign_iface_create(const char *config_path) {
    printf("Creating SovereignInterface...\n");
    return malloc(sizeof(SovereignInterface));
}

void sovereign_iface_project(SovereignInterface *iface, double *field_output, int steps) {
    // dummy project
}

void sovereign_iface_destroy(SovereignInterface *iface) {
    if (iface) free(iface);
}
