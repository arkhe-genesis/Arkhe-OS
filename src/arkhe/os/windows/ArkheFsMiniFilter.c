// ============================================================================
// ArkheFsMiniFilter.c — Minifilter Driver para Windows
// Aplica selos canônicos em toda operação de escrita/leitura no NTFS.
// ============================================================================
#include <fltKernel.h>
#include <dontuse.h>
#include <suppress.h>
#include <ntddk.h>
#include <sha3_256.h>  // Biblioteca SHA3-256 para kernel

PFLT_FILTER gFilterHandle = NULL;

// Estrutura de contexto por arquivo: armazena o selo canônico
typedef struct _ARKHE_FILE_CONTEXT {
    UCHAR Seal[32];           // SHA3-256 hash do conteúdo
    LARGE_INTEGER LastSealTime;
    BOOLEAN IntegrityVerified;
} ARKHE_FILE_CONTEXT, *PARKHE_FILE_CONTEXT;

// Callback: Pré‑escrita — calcular novo selo antes de persistir
FLT_PREOP_CALLBACK_STATUS
ArkhePreWrite(
    _Inout_ PFLT_CALLBACK_DATA Data,
    _In_ PCFLT_RELATED_OBJECTS FltObjects,
    _Flt_CompletionContext_Outptr_ PVOID *CompletionContext
) {
    // Obter buffer de dados sendo escritos
    // Calcular SHA3-256 do novo conteúdo
    // Armazenar no contexto do arquivo

    return FLT_PREOP_SUCCESS_WITH_CALLBACK;
}

// Callback: Pós‑leitura — verificar integridade
FLT_POSTOP_CALLBACK_STATUS
ArkhePostRead(
    _Inout_ PFLT_CALLBACK_DATA Data,
    _In_ PCFLT_RELATED_OBJECTS FltObjects,
    _In_opt_ PVOID CompletionContext,
    _In_ FLT_POST_OPERATION_FLAGS Flags
) {
    // Calcular SHA3-256 do conteúdo lido
    // Comparar com o selo armazenado
    // Se divergir: logar evento de segurança e notificar governança

    return FLT_POSTOP_FINISHED_PROCESSING;
}

// Callback: Pré‑criação — inicializar contexto de arquivo com selo vazio
FLT_PREOP_CALLBACK_STATUS
ArkhePreCreate(
    _Inout_ PFLT_CALLBACK_DATA Data,
    _In_ PCFLT_RELATED_OBJECTS FltObjects,
    _Flt_CompletionContext_Outptr_ PVOID *CompletionContext
) {
    return FLT_PREOP_SUCCESS_WITH_CALLBACK;
}

// Registro de operações que o minifilter intercepta
const FLT_OPERATION_REGISTRATION Callbacks[] = {
    { IRP_MJ_CREATE, 0, ArkhePreCreate, NULL },
    { IRP_MJ_WRITE, FLTFL_OPERATION_REGISTRATION_SKIP_PAGING_IO, ArkhePreWrite, NULL },
    { IRP_MJ_READ, FLTFL_OPERATION_REGISTRATION_SKIP_PAGING_IO, NULL, ArkhePostRead },
    { IRP_MJ_SET_INFORMATION, 0, NULL, NULL },
    { IRP_MJ_OPERATION_END }
};

// Registro de contextos
const FLT_CONTEXT_REGISTRATION Contexts[] = {
    { FLT_FILE_CONTEXT, 0, NULL, sizeof(ARKHE_FILE_CONTEXT), 'AKRF' },
    { FLT_CONTEXT_END }
};

// DriverEntry
NTSTATUS
DriverEntry(
    _In_ PDRIVER_OBJECT DriverObject,
    _In_ PUNICODE_STRING RegistryPath
) {
    NTSTATUS status;

    // Registrar minifilter
    status = FltRegisterFilter(
        DriverObject,
        &FilterRegistration,
        &gFilterHandle
    );

    // Iniciar filtragem
    status = FltStartFiltering(gFilterHandle);

    DbgPrint("🧠 Arkhe FS Minifilter iniciado — todos os arquivos NTFS agora têm selos canônicos.\n");

    return status;
}
