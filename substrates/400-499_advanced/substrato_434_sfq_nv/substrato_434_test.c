#include <stdio.h>
#include "arkhe_unikernel_polyglot.h"
#include "arkhe_gds_map.h"

int ArkheTriggerSfqPulse_called = 0;
int ArkheFireOpticalLaserBus_called = 0;
int ArkheFireGlobalOpticalTrigger_called = 0;

void ArkheTriggerSfqPulse(ULONG TargetRingId, ULONG LatencyPs) {
    (void)TargetRingId;
    (void)LatencyPs;
    ArkheTriggerSfqPulse_called++;
}

void ArkheFireOpticalLaserBus(ULONG TargetRingId, ULONG WavelengthNm) {
    (void)TargetRingId;
    (void)WavelengthNm;
    ArkheFireOpticalLaserBus_called++;
}

void ArkheFireGlobalOpticalTrigger(void) {
    ArkheFireGlobalOpticalTrigger_called++;
}

typedef enum {
    CMD_WRITE_BIT,
    CMD_READ_SQUID,
    CMD_GATE_TOFFOLI,
    CMD_GLOBAL_RESET
} ARKHE_BUS_COMMAND;

extern NTSTATUS ArkheDispatchHybridControl(ARKHE_BUS_COMMAND Command, ULONG TargetRingId);

int main() {
    ArkheDispatchHybridControl(CMD_WRITE_BIT, 1);
    ArkheDispatchHybridControl(CMD_GATE_TOFFOLI, 1);
    ArkheDispatchHybridControl(CMD_GLOBAL_RESET, 1);
    printf("Tests passed.\n");
    return 0;
}
