#include "arkhe_hal.h"
#include "cronos_scheduler.h"
#include "vm/phase_vm.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main() {
    printf("🌌 Arkhe OS Booting...\n");

    arkhe_node_t hw;
    if (arkhe_hal_init(&hw, "/dev/null") != 0) {
        fprintf(stderr, "Fatal: Hardware initialization failed.\n");
        return 1;
    }

    printf("├── HAL: Phase-lock established.\n");

    cronos_init(&hw);
    printf("├── Scheduler: Cronos active.\n");

    phase_vm_t vm;
    pvm_init(&vm, &hw);
    printf("├── PhaseVM: Initialized.\n");

    printf("└── Arkhe OS: Online. λ₂ = %.4f\n\n", arkhe_hal_read_lambda2(&hw));

    // Run a small program in the VM to simulate system initialization
    uint8_t init_code[] = { OP_SYNC, OP_PROJ, OP_HALT };
    pvm_load(&vm, init_code, sizeof(init_code));
    pvm_execute(&vm);

    printf("\nArkhe OS is now running in the background.\n");
    printf("Use 'arkhe-fold' to run scientific simulations.\n");

    return 0;
}
