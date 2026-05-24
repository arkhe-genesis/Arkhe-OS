#ifndef _ARKHE_GDS_MAP_H
#define _ARKHE_GDS_MAP_H

#include <linux/types.h>

typedef __u32 NTSTATUS;
typedef __u32 ULONG;

#define STATUS_SUCCESS 0x00000000
#define STATUS_CRYPTO_SYSTEM_INVALID 0xC00002F3
#define STATUS_INVALID_PARAMETER 0xC000000D

void ArkheTriggerSfqPulse(ULONG TargetRingId, ULONG LatencyPs);
void ArkheFireOpticalLaserBus(ULONG TargetRingId, ULONG WavelengthNm);
void ArkheFireGlobalOpticalTrigger(void);

#endif /* _ARKHE_GDS_MAP_H */
