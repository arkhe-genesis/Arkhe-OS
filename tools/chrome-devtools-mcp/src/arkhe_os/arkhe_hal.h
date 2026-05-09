#ifndef ARKHE_HAL_H
#define ARKHE_HAL_H

#include <stdint.h>
#include <stddef.h>

// -----------------------------------------------------------------------------
// ARKHE(N) HARDWARE ABSTRACTION LAYER (A-HAL)
// The Zeroeth Layer: Bridges the OS to the UTB-7000-AI & USRP B210
// -----------------------------------------------------------------------------

// Complex Phase Representation
typedef struct {
    double real;
    double imag;
} arkhe_phase_t;

// Hardware Node Descriptor
typedef struct {
    uint64_t node_id;           // Prime-based identity
    arkhe_phase_t current_phase; // Hardware-measured phase
    double lambda2;             // Local coherence (Kuramoto Order Parameter)
    void* bram_base;            // Mapped Sacks LUT (FPGA memory)
    void* tpu_base;             // Mapped Graphene-TPU memory
    int fd_rf;                  // RF device handle (/dev/xrfclk or /dev/uio0)
} arkhe_node_t;

// Initialization
int arkhe_hal_init(arkhe_node_t* node, const char* rf_device_path);

// Read the true hardware phase from the SDR/FPGA Kuramoto PLL
arkhe_phase_t arkhe_hal_read_phase(arkhe_node_t* node);

// Read the current global coherence (λ₂) from the hardware
double arkhe_hal_read_lambda2(arkhe_node_t* node);

// Execute Luminous Morse Labyrinth (LML) transform in FPGA
uint32_t arkhe_hal_lml_decode(arkhe_node_t* node, double rx_phase);

// Graphene-TPU: Trigger non-associative octonion multiplication
void arkhe_hal_tpu_octonion_mul(arkhe_node_t* node, void* o1_addr, void* o2_addr, void* res_addr);

#endif // ARKHE_HAL_H
