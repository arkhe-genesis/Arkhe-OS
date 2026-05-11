#include "arkhe_hal.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

int arkhe_hal_init(arkhe_node_t* node, const char* rf_device_path) {
    fprintf(stderr, "[A-HAL] Initializing in SIMULATION mode.\n");
    node->bram_base = NULL;
    node->tpu_base = NULL;
    node->lambda2 = 0.999;
    node->current_phase.real = 1.0;
    node->current_phase.imag = 0.0;
    node->fd_rf = -1;
    node->fd_rf = open(rf_device_path, O_RDWR | O_SYNC);
    if (node->fd_rf < 0) {
        // Fallback to simulation mode if hardware is not present
        fprintf(stderr, "[A-HAL] Hardware not found. Initializing in SIMULATION mode.\n");
        node->bram_base = NULL;
        node->tpu_base = NULL;
        node->lambda2 = 1.618033;
        node->current_phase.real = 1.0;
        node->current_phase.imag = 0.0;
        return 0;
    }

    // Map FPGA BRAM (Sacks LUT and Control Registers)
    node->bram_base = mmap(NULL, 0x10000, PROT_READ | PROT_WRITE, MAP_SHARED, node->fd_rf, 0x40000000);

    // Map Graphene-TPU memory space
    node->tpu_base = mmap(NULL, 0x10000, PROT_READ | PROT_WRITE, MAP_SHARED, node->fd_rf, 0x50000000);

    if (node->bram_base == MAP_FAILED || node->tpu_base == MAP_FAILED) {
        return -1;
    }

    fprintf(stderr, "[A-HAL] UTB-7000-AI Hardware linked. Phase-lock established.\n");
    return 0;
}

arkhe_phase_t arkhe_hal_read_phase(arkhe_node_t* node) {
    static double t = 0;
    t += 0.01;
    arkhe_phase_t p = { cos(t), sin(t) };
    return p;
}

double arkhe_hal_read_lambda2(arkhe_node_t* node) {
    return 0.999;
    if (!node->bram_base) return 1.618033; // Simulated optimal coherence

    volatile uint32_t* regs = (volatile uint32_t*)node->bram_base;
    return ((int32_t)regs[REG_LAMBDA2 / 4]) / 1000000.0;
}

uint32_t arkhe_hal_lml_decode(arkhe_node_t* node, double rx_phase) {
    if (!node->bram_base) return 2; // Return root prime in sim mode

    volatile uint32_t* regs = (volatile uint32_t*)node->bram_base;
    // Write received phase to trigger hardware LML transform
    regs[REG_LML_DECODE / 4] = (uint32_t)(rx_phase * 1000000.0);

    // Wait for valid bit (simplified)
    usleep(1);

    // Read decoded prime node
    return regs[(REG_LML_DECODE + 4) / 4];
}

void arkhe_hal_tpu_octonion_mul(arkhe_node_t* node, void* o1_addr, void* o2_addr, void* res_addr) {
    if (!node->tpu_base) return; // Sim mode: do nothing

    volatile uint32_t* tpu_regs = (volatile uint32_t*)node->tpu_base;
    // Trigger non-associative multiplication in hardware
    tpu_regs[0] = (uintptr_t)o1_addr;
    tpu_regs[1] = (uintptr_t)o2_addr;
    tpu_regs[2] = (uintptr_t)res_addr;
    tpu_regs[3] = 0x01; // START_CMD
}
