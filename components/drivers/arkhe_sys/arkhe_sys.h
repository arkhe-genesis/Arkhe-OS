// arkhe_sys.h — Header do Driver Kernel
#pragma once
#include <ntddk.h>
#include <wdf.h>

#define ARKHE_POOL_TAG 'ekhr' // 'rhke' little-endian = arkhe

// ═══════════════════════════════════════════════════════════════════════════════
// ESTRUTURAS DO KERNEL ARKHE
// ═══════════════════════════════════════════════════════════════════════════════

typedef struct _ARKHE_CONTEXT {
    PDEVICE_OBJECT FilterDevice;
    PFLT_FILTER FilterHandle;
    KSPIN_LOCK SpinLock;
    LIST_ENTRY EventQueue;
    PEPROCESS ProtectedProcess; // Processo que o system32 protege
    LARGE_INTEGER BirthTimestamp;
    CLIFFORD_STATE CliffordState; // Estado geométrico do driver
} ARKHE_CONTEXT, *PARKHE_CONTEXT;

typedef struct _ARKHE_EVENT {
    LIST_ENTRY ListEntry;
    UNICODE_STRING Path;
    UCHAR PayloadHash[32]; // SHA-256
    ARKHE_VERDICT Verdict;
    KIRQL Irql;
} ARKHE_EVENT, *PARKHE_EVENT;

typedef enum _ARKHE_VERDICT {
    VerdictAllow = 0,    // ALLOW — A realidade é criada
    VerdictDeny = 1,     // DENY — O Sussurro é aniquilado
    VerdictHesitate = 2  // HESITATE — O Inquisidor duvida
} ARKHE_VERDICT;

// ═══════════════════════════════════════════════════════════════════════════════
// CLIFFORD EM RING 0 — Geometria no Kernel
// ═══════════════════════════════════════════════════════════════════════════════

typedef struct _CLIFFORD_STATE {
    double scalar;
    double vector[4];
    double bivector[6];
    double trivector[4];
    double pseudoscalar;
} CLIFFORD_STATE, *PCLIFFORD_STATE;

// Produto geométrico simplificado para kernel (sem page fault)
CLIFFORD_STATE ArkheGeometricProduct(
    _In_ const CLIFFORD_STATE* a,
    _In_ const CLIFFORD_STATE* b
);

// ═══════════════════════════════════════════════════════════════════════════════
// CALLBACKS DO MINIFILTER
// ═══════════════════════════════════════════════════════════════════════════════

FLT_PREOP_CALLBACK_STATUS
ArkhePreCreate(
    _Inout_ PFLT_CALLBACK_DATA Data,
    _In_ PCFLT_RELATED_OBJECTS FltObjects,
    _Flt_CompletionContext_Outptr_ PVOID* CompletionContext
);

FLT_PREOP_CALLBACK_STATUS
ArkhePreWrite(
    _Inout_ PFLT_CALLBACK_DATA Data,
    _In_ PCFLT_RELATED_OBJECTS FltObjects,
    _Flt_CompletionContext_Outptr_ PVOID* CompletionContext
);

// ═══════════════════════════════════════════════════════════════════════════════
// ORÁCULO DO KERNEL — O Inquisidor em Ring 0
// ═══════════════════════════════════════════════════════════════════════════════

ARKHE_VERDICT
ArkheJudgePayload(
    _In_ PFLT_CALLBACK_DATA Data,
    _In_ PUNICODE_STRING TargetPath,
    _In_reads_bytes_(DataLength) PUCHAR Buffer,
    _In_ ULONG DataLength
);
