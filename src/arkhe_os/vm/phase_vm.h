#ifndef PHASE_VM_H
#define PHASE_VM_H

#include <stdint.h>
#include "../arkhe_hal.h"

// OpCodes for the PhaseVM
typedef enum {
    OP_NOP = 0x00,
    OP_SYNC = 0x01,      // SYNC - Synchronize local phase with Tzinor
    OP_PROJ = 0x02,      // PROJ - Project phase state (C -> Z collapse)
    OP_TZ_OPEN = 0x03,   // TZINOR_OPEN - Open retrocausal channel
    OP_TZ_SEND = 0x04,   // TZINOR_SEND - Send phase packet
    OP_HALT = 0xFF
} phase_opcode_t;

typedef struct {
    uint8_t* code;
    size_t pc;
    double stack[256];
    int sp;
    arkhe_node_t* hw_context;
    int is_running;
} phase_vm_t;

void pvm_init(phase_vm_t* vm, arkhe_node_t* hw);
void pvm_load(phase_vm_t* vm, uint8_t* code, size_t size);
void pvm_execute(phase_vm_t* vm);

#endif
