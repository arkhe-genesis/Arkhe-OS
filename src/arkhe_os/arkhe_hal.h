#ifndef ARKHE_HAL_H
#define ARKHE_HAL_H

#include <stdint.h>
#include <stddef.h>

// Complex Phase Representation
typedef struct {
    double real;
    double imag;
} arkhe_phase_t;

// Hardware Node Descriptor
typedef struct {
    uint64_t node_id;
    arkhe_phase_t current_phase;
    double lambda2;
    void* bram_base;
    void* tpu_base;
    int fd_rf;
} arkhe_node_t;

int arkhe_hal_init(arkhe_node_t* node, const char* rf_device_path);
arkhe_phase_t arkhe_hal_read_phase(arkhe_node_t* node);
double arkhe_hal_read_lambda2(arkhe_node_t* node);

#endif
