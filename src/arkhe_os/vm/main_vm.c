#include "phase_vm.h"
#include <stdio.h>
#include <stdlib.h>

int main() {
    arkhe_node_t hw;
    arkhe_hal_init(&hw, "/dev/null");

    phase_vm_t vm;
    pvm_init(&vm, &hw);

    // Sample bytecode: SYNC, PROJ, TZ_OPEN, TZ_SEND, HALT
    uint8_t program[] = {
        OP_SYNC,
        OP_PROJ,
        OP_TZ_OPEN,
        OP_TZ_SEND,
        OP_HALT
    };

    printf("🜏 Starting Arkhe PhaseVM...\n");
    pvm_load(&vm, program, sizeof(program));
    pvm_execute(&vm);

    printf("🜏 PhaseVM execution complete.\n");

    return 0;
}
