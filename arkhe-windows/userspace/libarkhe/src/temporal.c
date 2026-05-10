/*
 * ARKHE Ω-TEMP — Temporal Core (Userspace Library)
 *
 * Fornece a API de alto nível para comunicação com o driver kernel.
 * Usa DeviceIoControl para enviar/receber dados do driver.
 */

#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "arkhe.h"

/* Handle para os devices do driver */
static HANDLE hTemporal = INVALID_HANDLE_VALUE;
static HANDLE hConsensus = INVALID_HANDLE_VALUE;
static HANDLE hMerkle = INVALID_HANDLE_VALUE;

/*
 * Conectar ao driver ARKHE
 * Abre handles para os named pipes do kernel
 */
BOOL ArkheConnect(VOID)
{
    /*
    // Format: \\.\ARKHE\{Temporal,Consensus,Merkle}
    // Nota: No Windows, usamos CreateFile com caminhos de device
    */

    hTemporal = CreateFileW(
        L"\\\\.\\ARKHE\\Temporal",
        GENERIC_READ | GENERIC_WRITE,
        0,
        NULL,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        NULL);

    if (hTemporal == INVALID_HANDLE_VALUE) {
        fprintf(stderr, "ARKHE: Falha ao conectar ao device Temporal (err=%lu)\n",
                GetLastError());
        return FALSE;
    }

    hConsensus = CreateFileW(
        L"\\\\.\\ARKHE\\Consensus",
        GENERIC_READ | GENERIC_WRITE,
        0, NULL, OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL, NULL);

    hMerkle = CreateFileW(
        L"\\\\.\\ARKHE\\Merkle",
        GENERIC_READ | GENERIC_WRITE,
        0, NULL, OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL, NULL);

    return (hTemporal != INVALID_HANDLE_VALUE &&
            hConsensus != INVALID_HANDLE_VALUE &&
            hMerkle != INVALID_HANDLE_VALUE);
}

/*
 * Desconectar do driver
 */
VOID ArkheDisconnect(VOID)
{
    if (hTemporal != INVALID_HANDLE_VALUE) {
        CloseHandle(hTemporal);
        hTemporal = INVALID_HANDLE_VALUE;
    }
    if (hConsensus != INVALID_HANDLE_VALUE) {
        CloseHandle(hConsensus);
        hConsensus = INVALID_HANDLE_VALUE;
    }
    if (hMerkle != INVALID_HANDLE_VALUE) {
        CloseHandle(hMerkle);
        hMerkle = INVALID_HANDLE_VALUE;
    }
}

/*
 * Enviar bloco temporal ao driver para validação e inserção
 */
BOOL ArkheInsertBlock(
    _In_reads_bytes_(BlockSize) PCVOID BlockData,
    _In_ ULONG BlockSize,
    _Out_ PARKEHE_BLOCK_RESULT Result)
{
    DWORD bytesReturned;
    BOOL success;

    success = DeviceIoControl(
        hTemporal,
        IOCTL_ARKHE_TEMPORAL_INSERT_BLOCK,
        (LPVOID)BlockData,
        BlockSize,
        Result,
        sizeof(ARKEHE_BLOCK_RESULT),
        &bytesReturned,
        NULL);

    if (!success) {
        fprintf(stderr, "ARKHE: Falha ao inserir bloco (err=%lu)\n",
                GetLastError());
    }

    return success;
}

/*
 * Obter bloco por índice
 */
BOOL ArkheGetBlock(
    _In_ ULONGLONG Index,
    _Out_writes_bytes_opt_(BufferSize) PVOID Buffer,
    _Inout_ PULONG BufferSize)
{
    ARKHE_BLOCK_QUERY query = {0};
    query.Index = Index;

    DWORD bytesReturned;

    return DeviceIoControl(
        hTemporal,
        IOCTL_ARKHE_TEMPORAL_GET_BLOCK,
        &query, sizeof(query),
        Buffer, *BufferSize,
        &bytesReturned,
        NULL);
}

/*
 * Obter State Root da cadeia
 */
BOOL ArkheGetStateRoot(
    _Out_writes_bytes_(ARKHE_HASH_SIZE) PUCHAR Root)
{
    DWORD bytesReturned;

    return DeviceIoControl(
        hTemporal,
        IOCTL_ARKHE_TEMPORAL_GET_ROOT,
        NULL, 0,
        Root, ARKHE_HASH_SIZE,
        &bytesReturned,
        NULL);
}

/*
 * Avaliar consistência de uma mensagem via Oracle
 */
BOOL ArkheEvaluateConsistency(
    _In_ PCARKHE_MESSAGE Message,
    _Out_ PARKEHE_CONSISTENCY_REPORT Report)
{
    DWORD bytesReturned;

    return DeviceIoControl(
        hConsensus,
        IOCTL_ARKHE_CONSENSUS_EVALUATE,
        (LPVOID)Message, sizeof(ARKHE_MESSAGE),
        Report, sizeof(ARKEHE_CONSISTENCY_REPORT),
        &bytesReturned,
        NULL);
}
