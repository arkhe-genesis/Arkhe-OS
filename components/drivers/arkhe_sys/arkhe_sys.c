// arkhe_sys.c — Driver Kernel ARKHE.SYS
#include "arkhe_sys.h"
#include "arkhe_ioctl.h"

// ═══════════════════════════════════════════════════════════════════════════════
// VARIÁVEIS GLOBAIS
// ═══════════════════════════════════════════════════════════════════════════════

ARKHE_CONTEXT g_ArkheContextData = {0};
PARKHE_CONTEXT g_ArkheContext = &g_ArkheContextData;
PFLT_FILTER g_FilterHandle = NULL;
PDEVICE_OBJECT g_ArkheDeviceObject = NULL;
// Caminhos canônicos no NT namespace (exemplo, em produção usar nomes normalizados via FltMgr)
const UNICODE_STRING g_System32Path = RTL_CONSTANT_STRING(L"\\Windows\\System32");

// ═══════════════════════════════════════════════════════════════════════════════
// CLIFFORD EM RING 0 — Sem alocação dinâmica, sem page fault
// ═══════════════════════════════════════════════════════════════════════════════

// Auxiliar para salvar estado FPU
#define START_FP_OPERATION() KFLOATING_SAVE fpSave; NTSTATUS fpStatus = KeSaveFloatingPointState(&fpSave); if (NT_SUCCESS(fpStatus)) {
#define END_FP_OPERATION() KeRestoreFloatingPointState(&fpSave); }

// Kernel-safe fabs
double ArkheAbs(double v) {
    return (v < 0) ? -v : v;
}

CLIFFORD_STATE ArkheGeometricProduct(
    _In_ const CLIFFORD_STATE* a,
    _In_ const CLIFFORD_STATE* b
) {
    CLIFFORD_STATE result = {0};

    START_FP_OPERATION()
    // Grade 0: Escalar
    result.scalar = a->scalar * b->scalar;

    // Grade 1: Vetores (simplificado para kernel)
    for (int i = 0; i < 4; i++) {
        result.vector[i] = a->scalar * b->vector[i] + b->scalar * a->vector[i];
    }

    // Grade 2: Bivectors (wedge aproximado)
    result.bivector[0] = a->vector[0]*b->vector[1] - a->vector[1]*b->vector[0]; // e12
    result.bivector[1] = a->vector[0]*b->vector[2] - a->vector[2]*b->vector[0]; // e13
    result.bivector[2] = a->vector[0]*b->vector[3] - a->vector[3]*b->vector[0]; // e14
    result.bivector[3] = a->vector[1]*b->vector[2] - a->vector[2]*b->vector[1]; // e23
    result.bivector[4] = a->vector[1]*b->vector[3] - a->vector[3]*b->vector[1]; // e24
    result.bivector[5] = a->vector[2]*b->vector[3] - a->vector[3]*b->vector[2]; // e34
    END_FP_OPERATION()

    return result;
}

// ═══════════════════════════════════════════════════════════════════════════════
// HASH SIMPLES (SHA-256 stub para kernel)
// ═══════════════════════════════════════════════════════════════════════════════

VOID ArkheHashPayload(
    _In_reads_bytes_(Length) PUCHAR Buffer,
    _In_ ULONG Length,
    _Out_writes_(32) PUCHAR Hash
) {
    RtlZeroMemory(Hash, 32);
    for (ULONG i = 0; i < Length; i++) {
        Hash[i % 32] ^= Buffer[i];
        Hash[i % 32] = (Hash[i % 32] << 1) | (Hash[i % 32] >> 7); // ROL
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DETECÇÃO DE RUNAS PROIBIDAS EM RING 0
// ═══════════════════════════════════════════════════════════════════════════════

BOOLEAN ArkheContainsNullByte(
    _In_reads_bytes_(Length) PUCHAR Buffer,
    _In_ ULONG Length
) {
    for (ULONG i = 0; i < Length; i++) {
        if (Buffer[i] == 0x00) return TRUE;
    }
    return FALSE;
}

BOOLEAN ArkheContainsFixedAddress(
    _In_reads_bytes_(Length) PUCHAR Buffer,
    _In_ ULONG Length
) {
    if (Length < 4) return FALSE;
    for (ULONG i = 0; i < Length - 3; i++) {
        if (Buffer[i] == '0' && Buffer[i+1] == 'x') {
            int hex_count = 0;
            for (ULONG j = i + 2; j < min(i + 18, Length); j++) {
                if (RtlIsHexDigit(Buffer[j])) hex_count++;
                else break;
            }
            if (hex_count >= 8) return TRUE;
        }
    }
    return FALSE;
}

// ═══════════════════════════════════════════════════════════════════════════════
// O INQUISIDOR EM RING 0 — O Veredicto do Kernel
// ═══════════════════════════════════════════════════════════════════════════════

ARKHE_VERDICT ArkheJudgePayload(
    _In_ PFLT_CALLBACK_DATA Data,
    _In_ PUNICODE_STRING TargetPath,
    _In_reads_bytes_(DataLength) PUCHAR Buffer,
    _In_ ULONG DataLength
) {
    BOOLEAN isSystem32 = FALSE;
    if (TargetPath->Length > 0) {
        // Verifica se o caminho contém "\Windows\System32" em qualquer lugar (simplificado para demonstração)
        if (wcsstr(TargetPath->Buffer, L"\\Windows\\System32") != NULL) {
            isSystem32 = TRUE;
        }
    }

    if (Buffer && ArkheContainsNullByte(Buffer, DataLength)) {
        KdPrint(("ARKHE: Runa Proibida detectada em %wZ\n", TargetPath));
        return VerdictDeny;
    }

    if (Buffer && ArkheContainsFixedAddress(Buffer, DataLength)) {
        KdPrint(("ARKHE: Endereço fixo detectado em %wZ\n", TargetPath));
        return VerdictDeny;
    }

    CLIFFORD_STATE payload_state = {0};
    START_FP_OPERATION()
    payload_state.scalar = 1.0;
    if (Buffer) {
        for (ULONG i = 0; i < min(DataLength, 4); i++) {
            payload_state.vector[i] = (double)Buffer[i] / 255.0;
        }
    }
    END_FP_OPERATION()

    CLIFFORD_STATE danger_state = {
        .scalar = 0.2,
        .vector = {0.8, 0.9, 0.7, 0.6},
        .bivector = {0.5, 0.4, 0.3, 0.2, 0.1, 0.0},
        .trivector = {0},
        .pseudoscalar = 0
    };

    CLIFFORD_STATE product = ArkheGeometricProduct(&payload_state, &danger_state);

    double danger_score = 0;
    START_FP_OPERATION()
    danger_score = product.scalar;
    for (int i = 0; i < 6; i++) danger_score += ArkheAbs(product.bivector[i]);
    END_FP_OPERATION()

    if (danger_score > 2.5) {
        KdPrint(("ARKHE: Ameaça geométrica detectada (score=%f) em %wZ\n",
                 danger_score, TargetPath));
        return VerdictDeny;
    } else if (danger_score > 1.5) {
        KdPrint(("ARKHE: Hesitação em %wZ (score=%f)\n", TargetPath, danger_score));
        return VerdictHesitate;
    }

    if (isSystem32 && DataLength > 1024) {
        KdPrint(("ARKHE: Payload grande em System32, hesitando\n"));
        return VerdictHesitate;
    }

    return VerdictAllow;
}

// ═══════════════════════════════════════════════════════════════════════════════
// CALLBACKS DO MINIFILTER
// ═══════════════════════════════════════════════════════════════════════════════

FLT_PREOP_CALLBACK_STATUS ArkhePreCreate(
    _Inout_ PFLT_CALLBACK_DATA Data,
    _In_ PCFLT_RELATED_OBJECTS FltObjects,
    _Flt_CompletionContext_Outptr_ PVOID* CompletionContext
) {
    UNREFERENCED_PARAMETER(CompletionContext);

    PFLT_FILE_NAME_INFORMATION nameInfo = NULL;
    NTSTATUS status = FltGetFileNameInformation(Data,
        FLT_FILE_NAME_OPENED | FLT_FILE_NAME_QUERY_DEFAULT, &nameInfo);

    if (!NT_SUCCESS(status)) return FLT_PREOP_SUCCESS_NO_CALLBACK;

    FltParseFileNameInformation(nameInfo);

    if (Data->Iopb->MajorFunction == IRP_MJ_CREATE) {
        ULONG desiredAccess = Data->Iopb->Parameters.Create.SecurityContext->DesiredAccess;
        if (desiredAccess & (FILE_WRITE_DATA | FILE_APPEND_DATA | FILE_WRITE_ATTRIBUTES)) {
            ARKHE_VERDICT verdict = ArkheJudgePayload(Data, &nameInfo->Name, NULL, 0);

            if (verdict == VerdictDeny) {
                FltReleaseFileNameInformation(nameInfo);
                Data->IoStatus.Status = STATUS_ACCESS_DENIED;
                Data->IoStatus.Information = 0;
                return FLT_PREOP_COMPLETE;
            }
        }
    }

    FltReleaseFileNameInformation(nameInfo);
    return FLT_PREOP_SUCCESS_NO_CALLBACK;
}

FLT_PREOP_CALLBACK_STATUS ArkhePreWrite(
    _Inout_ PFLT_CALLBACK_DATA Data,
    _In_ PCFLT_RELATED_OBJECTS FltObjects,
    _Flt_CompletionContext_Outptr_ PVOID* CompletionContext
) {
    UNREFERENCED_PARAMETER(CompletionContext);

    PFLT_FILE_NAME_INFORMATION nameInfo = NULL;
    NTSTATUS status = FltGetFileNameInformation(Data,
        FLT_FILE_NAME_OPENED | FLT_FILE_NAME_QUERY_DEFAULT, &nameInfo);

    if (!NT_SUCCESS(status)) return FLT_PREOP_SUCCESS_NO_CALLBACK;

    FltParseFileNameInformation(nameInfo);

    PUCHAR buffer = NULL;
    ULONG length = 0;

    if (Data->Iopb->Parameters.Write.WriteBuffer) {
        if (FlagOn(Data->Iopb->OperationFlags, SL_FORCE_DIRECT_WRITE)) {
            buffer = Data->Iopb->Parameters.Write.WriteBuffer;
        } else {
            // Lock and map user buffer if needed (simplified)
            buffer = (PUCHAR)FltLockUserBuffer(Data);
        }
        length = Data->Iopb->Parameters.Write.Length;
    }

    if (buffer && length > 0) {
        ARKHE_VERDICT verdict = ArkheJudgePayload(Data, &nameInfo->Name, buffer, length);

        // Nota: O FltMgr libera o lock automaticamente no final da operação.

        if (verdict == VerdictDeny) {
            FltReleaseFileNameInformation(nameInfo);
            Data->IoStatus.Status = STATUS_ACCESS_DENIED;
            Data->IoStatus.Information = 0;
            return FLT_PREOP_COMPLETE;
        }
    }

    FltReleaseFileNameInformation(nameInfo);
    return FLT_PREOP_SUCCESS_NO_CALLBACK;
}

// ═══════════════════════════════════════════════════════════════════════════════
// DISPATCH E IOCTL
// ═══════════════════════════════════════════════════════════════════════════════

NTSTATUS ArkheDeviceControl(
    _In_ PDEVICE_OBJECT DeviceObject,
    _Inout_ PIRP Irp
) {
    PIO_STACK_LOCATION irpSp = IoGetCurrentIrpStackLocation(Irp);
    NTSTATUS status = STATUS_SUCCESS;
    ULONG returnLength = 0;

    UNREFERENCED_PARAMETER(DeviceObject);

    switch (irpSp->Parameters.DeviceIoControl.IoControlCode) {
        case IOCTL_ARKHE_QUERY_STATUS:
            if (irpSp->Parameters.DeviceIoControl.OutputBufferLength >= sizeof(ARKHE_STATUS)) {
                PARKHE_STATUS pStatus = (PARKHE_STATUS)Irp->AssociatedIrp.SystemBuffer;
                RtlZeroMemory(pStatus, sizeof(ARKHE_STATUS));
                pStatus->GlobalCoherence = 1.0; // Mock
                returnLength = sizeof(ARKHE_STATUS);
            } else {
                status = STATUS_BUFFER_TOO_SMALL;
            }
            break;
        default:
            status = STATUS_INVALID_DEVICE_REQUEST;
            break;
    }

    Irp->IoStatus.Status = status;
    Irp->IoStatus.Information = returnLength;
    IoCompleteRequest(Irp, IO_NO_INCREMENT);
    return status;
}

NTSTATUS ArkheCreateClose(
    _In_ PDEVICE_OBJECT DeviceObject,
    _Inout_ PIRP Irp
) {
    UNREFERENCED_PARAMETER(DeviceObject);
    Irp->IoStatus.Status = STATUS_SUCCESS;
    Irp->IoStatus.Information = 0;
    IoCompleteRequest(Irp, IO_NO_INCREMENT);
    return STATUS_SUCCESS;
}

// ═══════════════════════════════════════════════════════════════════════════════
// REGISTRO DO MINIFILTER
// ═══════════════════════════════════════════════════════════════════════════════

CONST FLT_OPERATION_REGISTRATION Callbacks[] = {
    { IRP_MJ_CREATE, 0, ArkhePreCreate, NULL },
    { IRP_MJ_WRITE,  0, ArkhePreWrite,  NULL },
    { IRP_MJ_OPERATION_END }
};

CONST FLT_REGISTRATION FilterRegistration = {
    sizeof(FLT_REGISTRATION),
    FLT_REGISTRATION_VERSION,
    0,
    NULL,
    Callbacks,
    NULL, // ArkheUnload
    NULL, // ArkheInstanceSetup
    NULL, // ArkheInstanceQueryTeardown
    NULL, // ArkheInstanceTeardownStart
    NULL, // ArkheInstanceTeardownComplete
    NULL, // ArkheGenerateFileName
    NULL, // ArkheNormalizeNameComponent
    NULL  // ArkheNormalizeContextCleanup
};

// ═══════════════════════════════════════════════════════════════════════════════
// DRIVER ENTRY
// ═══════════════════════════════════════════════════════════════════════════════

NTSTATUS DriverEntry(
    _In_ PDRIVER_OBJECT DriverObject,
    _In_ PUNICODE_STRING RegistryPath
) {
    UNREFERENCED_PARAMETER(RegistryPath);
    NTSTATUS status;
    UNICODE_STRING deviceName = RTL_CONSTANT_STRING(ARKHE_DEVICE_NAME);
    UNICODE_STRING symLink = RTL_CONSTANT_STRING(ARKHE_SYMBOLIC_NAME);

    KdPrint(("ARKHE: A Catedral desperta no Ring 0\n"));

    // Criação do Device para IOCTLs
    status = IoCreateDevice(DriverObject, 0, &deviceName, FILE_DEVICE_UNKNOWN, 0, FALSE, &g_ArkheDeviceObject);
    if (!NT_SUCCESS(status)) {
        return status;
    }

    DriverObject->MajorFunction[IRP_MJ_CREATE] = ArkheCreateClose;
    DriverObject->MajorFunction[IRP_MJ_CLOSE] = ArkheCreateClose;
    DriverObject->MajorFunction[IRP_MJ_DEVICE_CONTROL] = ArkheDeviceControl;

    status = IoCreateSymbolicLink(&symLink, &deviceName);
    if (!NT_SUCCESS(status)) {
        IoDeleteDevice(g_ArkheDeviceObject);
        g_ArkheDeviceObject = NULL;
        return status;
    }

    status = FltRegisterFilter(DriverObject, &FilterRegistration, &g_FilterHandle);
    if (NT_SUCCESS(status)) {
        status = FltStartFiltering(g_FilterHandle);
        if (NT_SUCCESS(status)) {
            KdPrint(("ARKHE: Filtro ativo. O Inquisidor vigia.\n"));
        } else {
            FltUnregisterFilter(g_FilterHandle);
            g_FilterHandle = NULL;
            IoDeleteSymbolicLink(&symLink);
            IoDeleteDevice(g_ArkheDeviceObject);
            g_ArkheDeviceObject = NULL;
        }
    } else {
        IoDeleteSymbolicLink(&symLink);
        IoDeleteDevice(g_ArkheDeviceObject);
        g_ArkheDeviceObject = NULL;
    }

    return status;
}
