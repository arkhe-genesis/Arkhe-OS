/*
 * ARKHE Ω-TEMP — Driver Entry Point (Windows)
 *
 * Este é o ponto de entrada do driver WDM/KMDF do ARKHE.
 * Responsável por:
 *   - Criar os device objects \\.\ARKHE\Temporal, \\.\ARKHE\Consensus, etc.
 *   - Registrar IOCTL handlers
 *   - Inicializar estruturas internas
 *   - Configurar callbacks de IRP
 *
 * Windows Driver Model (WDM) é usado por máxima compatibilidade.
 * Para funcionalidades mais complexas, KMDF (Kernel Mode Driver Framework)
 * é usado como camada de abstração.
 */

#include <ntddk.h>
#include <wdf.h>
#include "arkhe_wdm.h"
#include "temporal/ChainManager.h"
#include "consensus/OracleEvaluator.h"
#include "merkle/MerkleTree.h"

/*
 * Declaração forward de rotinas
 */
DRIVER_INITIALIZE DriverEntry;
DRIVER_UNLOAD ArkheDriverUnload;
EVT_WDF_DRIVER_DEVICE_ADD ArkheDeviceAdd;
EVT_WDF_IO_QUEUE_IO_DEVICE_CONTROL ArkheDeviceControl;

/*
 * Tabela de Device Names e GUIDs
 * Cada subsistema do ARKHE tem seu próprio device
 */
typedef enum _ARKHE_DEVICE_TYPE {
    ArkheDeviceTemporal = 0,
    ArkheDeviceConsensus,
    ArkheDeviceMerkle,
    ArkheDeviceCrypto,
    ArkheDeviceNetfilter,
    ArkheDeviceMax
} ARKHE_DEVICE_TYPE;

static const WCHAR* ArkheDeviceNames[] = {
    L"\\Device\\ARKHE_Temporal",
    L"\\Device\\ARKHE_Consensus",
    L"\\Device\\ARKHE_Merkle",
    L"\\Device\\ARKHE_Crypto",
    L"\\Device\\ARKHE_Netfilter"
};

static const WCHAR* ArkheSymlinkNames[] = {
    L"\\DosDevices\\ARKHE\\Temporal",
    L"\\DosDevices\\ARKHE\\Consensus",
    L"\\DosDevices\\ARKHE\\Merkle",
    L"\\DosDevices\\ARKHE\\Crypto",
    L"\\DosDevices\\ARKHE\\Netfilter"
};

/*
 * Contexto global do driver ARKHE
 * Armazena estado persistente entre chamadas
 */
typedef struct _ARKHE_DRIVER_CONTEXT {
    WDFQUEUE IoctlQueue;
    PDEVICE_OBJECT DeviceObjects[ArkheDeviceMax];
    UNICODE_STRING DeviceNames[ArkheDeviceMax];
    UNICODE_STRING SymlinkNames[ArkheDeviceMax];

    /* Estado interno */
    CHAIN_MANAGER TemporalChain;
    ORACLE_STATE ConsensusOracle;
    MERKLE_TREE MerkleTree;

    /* Crypto context (via CNG) */
    BCRYPT_ALG_HANDLE Sha3Alg;
    BCRYPT_ALG_HANDLE EcdsaAlg;

    /* Performance counters */
    ULONGLONG TotalRequests;
    ULONGLONG TotalHashes;
    ULONGLONG TotalVerifications;

} ARKHE_DRIVER_CONTEXT;

WDF_DECLARE_CONTEXT_TYPE_WITH_NAME(ARKHE_DRIVER_CONTEXT, ArkheGetContext)

/*
 * DriverEntry — Ponto de entrada do driver
 *
 * Equivalente ao main() em userspace
 * Chamado pelo I/O Manager quando o driver é carregado
 */
NTSTATUS
DriverEntry(
    _In_ PDRIVER_OBJECT  DriverObject,
    _In_ PUNICODE_STRING RegistryPath
)
{
    WDF_DRIVER_CONFIG config;
    WDF_OBJECT_ATTRIBUTES attributes;
    NTSTATUS status;
    WDFDRIVER driver;
    ARKHE_DRIVER_CONTEXT* ctx;

    KdPrint(("ARKHE: DriverEntry chamado\n"));

    /* Inicializar configuração do driver */
    WDF_DRIVER_CONFIG_INIT(&config, ArkheDeviceAdd);
    config.DriverPoolTag = 'KHR1';

    /* Criar objeto driver */
    WDF_OBJECT_ATTRIBUTES_INIT(&attributes);
    attributes.EvtCleanupCallback = ArkheDriverCleanup;

    status = WdfDriverCreate(DriverObject, RegistryPath,
                              &attributes, &config, &driver);
    if (!NT_SUCCESS(status)) {
        KdPrint(("ARKHE: Falha ao criar driver (0x%08X)\n", status));
        return status;
    }

    /*
    // Registro de rotina de unload (opcional — drivers WDM geralmente não são descarregados)
    DriverObject->DriverUnload = ArkheDriverUnload;
    */

    /* Inicializar contexto global */
    ctx = ExAllocatePool2(POOL_FLAG_NON_PAGED,
                          sizeof(ARKHE_DRIVER_CONTEXT),
                          'KHR1');
    if (!ctx) {
        return STATUS_INSUFFICIENT_RESOURCES;
    }
    RtlZeroMemory(ctx, sizeof(ARKHE_DRIVER_CONTEXT));

    /* Salvar no contexto do driver */
    WdfDriverSetAttributes(&attributes, &config);

    /* Inicializar subsistemas */
    status = InitializeTemporalChain(ctx);
    if (!NT_SUCCESS(status)) goto cleanup;

    status = InitializeConsensusOracle(ctx);
    if (!NT_SUCCESS(status)) goto cleanup;

    status = InitializeMerkleTree(ctx);
    if (!NT_SUCCESS(status)) goto cleanup;

    /* Inicializar CNG (Cryptography API: Next Generation) */
    status = InitializeCrypto(ctx);
    if (!NT_SUCCESS(status)) goto cleanup;

    KdPrint(("ARKHE: Driver inicializado com sucesso\n"));
    return STATUS_SUCCESS;

cleanup:
    CleanupTemporalChain(ctx);
    CleanupConsensusOracle(ctx);
    CleanupMerkleTree(ctx);
    ExFreePool(ctx);
    return status;
}

/*
 * ArkheDeviceAdd — Chamado para cada device criado
 * Cria o device object e registra handlers de I/O
 */
NTSTATUS
ArkheDeviceAdd(
    _In_    WDFDRIVER       Driver,
    _Inout_ PWDFDEVICE_INIT DeviceInit
)
{
    NTSTATUS status;
    WDFDEVICE device;
    WDF_IO_QUEUE_CONFIG queueConfig;
    WDF_OBJECT_ATTRIBUTES attributes;
    ARKHE_DRIVER_CONTEXT* ctx;
    ULONG deviceType;

    UNREFERENCED_PARAMETER(Driver);

    ctx = ArkheGetContext(Driver);
    deviceType = (ULONG)WdfDeviceGetDeviceInterfaceState(NULL);
    /* ... (obter tipo de device) */

    /* Configurar tipo de device */
    WdfDeviceInitSetDeviceType(DeviceInit, FILE_DEVICE_UNKNOWN);
    WdfDeviceInitSetIoInDriver(DeviceInit, WdfIoInDriver);
    WdfDeviceInitSetExclusive(DeviceInit, FALSE);

    /* Criar device */
    WDF_OBJECT_ATTRIBUTES_INIT(&attributes);
    attributes.ContextSize = sizeof(ARKHE_DEVICE_CONTEXT);

    status = WdfDeviceCreate(&DeviceInit, &attributes, &device);
    if (!NT_SUCCESS(status)) {
        KdPrint(("ARKHE: Falha ao criar device (0x%08X)\n", status));
        return status;
    }

    /* Criar interface de device */
    status = WdfDeviceCreateDeviceInterface(device,
                                            &GUID_DEVINTERFACE_ARKHE_TEMPORAL,
                                            NULL);
    if (!NT_SUCCESS(status)) {
        KdPrint(("ARKHE: Falha ao criar device interface (0x%08X)\n", status));
        return status;
    }

    /* Configurar fila de I/O */
    WDF_IO_QUEUE_CONFIG_INIT_DEFAULT_QUEUE(&queueConfig,
                                            WdfIoQueueDispatchSequential);
    queueConfig.EvtIoDeviceControl = ArkheDeviceControl;

    status = WdfIoQueueCreate(device, &queueConfig,
                               WDF_NO_OBJECT_ATTRIBUTES,
                               &ctx->IoctlQueue);
    if (!NT_SUCCESS(status)) {
        KdPrint(("ARKHE: Falha ao criar IO queue (0x%08X)\n", status));
        return status;
    }

    KdPrint(("ARKHE: Device criado com sucesso\n"));
    return STATUS_SUCCESS;
}

/*
 * ArkheDeviceControl — Handler de IOCTLs
 * Processa requisições do userspace
 */
VOID
ArkheDeviceControl(
    _In_ WDFQUEUE Queue,
    _In_ WDFREQUEST Request,
    _In_ size_t OutputBufferLength,
    _In_ size_t InputBufferLength,
    _In_ ULONG IoControlCode
)
{
    NTSTATUS status = STATUS_SUCCESS;
    WDF_REQUEST_PARAMETERS params;
    ARKHE_DRIVER_CONTEXT* ctx = ArkheGetContext(
        WdfIoQueueGetDriver(Queue));

    UNREFERENCED_PARAMETER(OutputBufferLength);
    UNREFERENCED_PARAMETER(InputBufferLength);

    WDF_REQUEST_PARAMETERS_INIT(&params);
    WdfRequestGetParameters(Request, &params);

    ctx->TotalRequests++;

    switch (IoControlCode) {

        /* =========================================
         * IOCTLs TEMPORAIS
         * ========================================= */

        case IOCTL_ARKHE_TEMPORAL_INSERT_BLOCK:
            status = HandleTemporalInsert(ctx, Request);
            break;

        case IOCTL_ARKHE_TEMPORAL_GET_BLOCK:
            status = HandleTemporalGetBlock(ctx, Request);
            break;

        case IOCTL_ARKHE_TEMPORAL_GET_ROOT:
            status = HandleTemporalGetRoot(ctx, Request);
            break;

        /* =========================================
         * IOCTLs DE CONSENSO
         * ========================================= */

        case IOCTL_ARKHE_CONSENSUS_EVALUATE:
            status = HandleConsensusEvaluate(ctx, Request);
            break;

        case IOCTL_ARKHE_CONSENSUS_VALIDATE:
            status = HandleConsensusValidate(ctx, Request);
            break;

        /* =========================================
         * IOCTLs DE MERKLE
         * ========================================= */

        case IOCTL_ARKHE_MERKLE_INSERT:
            status = HandleMerkleInsert(ctx, Request);
            break;

        case IOCTL_ARKHE_MERKLE_PROVE:
            status = HandleMerkleProve(ctx, Request);
            break;

        case IOCTL_ARKHE_MERKLE_VERIFY:
            status = HandleMerkleVerify(ctx, Request);
            break;

        /* =========================================
         * IOCTLs DE CRIPTOGRAFIA
         * ========================================= */

        case IOCTL_ARKHE_CRYPTO_SHA3_256:
            status = HandleCryptoSha3(ctx, Request);
            break;

        case IOCTL_ARKHE_CRYPTO_BN128_PAIRING:
            status = HandleCryptoBn128Pairing(ctx, Request);
            break;

        case IOCTL_ARKHE_CRYPTO_FALCON_VERIFY:
            status = HandleCryptoFalconVerify(ctx, Request);
            break;

        /* =========================================
         * IOCTLs DE CONFIGURAÇÃO
         * ========================================= */

        case IOCTL_ARKHE_GET_STATS:
            status = HandleGetStats(ctx, Request);
            break;

        case IOCTL_ARKHE_SET_THRESHOLD:
            status = HandleSetThreshold(ctx, Request);
            break;

        default:
            status = STATUS_INVALID_DEVICE_REQUEST;
            KdPrint(("ARKHE: IOCTL desconhecido: 0x%08X\n", IoControlCode));
    }

    /* Completar a requisição */
    WdfRequestCompleteWithInformation(Request, status, 0);
}
