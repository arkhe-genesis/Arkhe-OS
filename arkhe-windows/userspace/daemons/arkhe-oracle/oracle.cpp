/*
 * ARKHE Ω-TEMP — Oracle Daemon (Windows Service)
 *
 * Este serviço Windows executa continuamente:
 *   - Recebe mensagens temporais via named pipe
 *   - Avalia consistência via ConsensusEngine
 *   - Envia resultados de volta
 *   - Mantém estado do consensus
 *
 * Funciona como um "filho" do driver kernel, mas com
 * lógica complexa demais para rodar no kernel.
 */

#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../libarkhe/include/arkhe_consensus.h"

#define SERVICE_NAME L"arkhe-oracle"
#define PIPE_NAME L"\\\\.\\pipe\\arkhe-oracle"

static SERVICE_STATUS_HANDLE g_ServiceStatusHandle;
static SERVICE_STATUS g_ServiceStatus;
static HANDLE g_StopEvent = NULL;

/*
 * Forward declarations
 */
VOID WINAPI ServiceMain(DWORD argc, LPTSTR* argv);
VOID WINAPI ServiceCtrlHandler(DWORD ctrlCode);
DWORD WINAPI WorkerThread(LPVOID param);
VOID RunOracleLoop(VOID);

/*
 * Entry point do serviço
 */
VOID WINAPI ServiceMain(DWORD argc, LPTSTR* argv)
{
    UNREFERENCED_PARAMETER(argc);
    UNREFERENCED_PARAMETER(argv);

    g_ServiceStatusHandle = RegisterServiceCtrlHandlerW(
        SERVICE_NAME, ServiceCtrlHandler);

    if (!g_ServiceStatusHandle) return;

    g_ServiceStatus.dwServiceType = SERVICE_WIN32_OWN_PROCESS;
    g_ServiceStatus.dwCurrentState = SERVICE_START_PENDING;
    g_ServiceStatus.dwControlsAccepted =
        SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN;
    g_ServiceStatus.dwWin32ExitCode = NO_ERROR;
    g_ServiceStatus.dwServiceSpecificExitCode = 0;
    g_ServiceStatus.dwCheckPoint = 0;
    g_ServiceStatus.dwWaitHint = 3000;

    SetServiceStatus(g_ServiceStatusHandle, &g_ServiceStatus);

    /* Criar evento de parada */
    g_StopEvent = CreateEventW(NULL, TRUE, FALSE, NULL);

    /* Criar thread de trabalho */
    HANDLE hThread = CreateThread(NULL, 0, WorkerThread, NULL, 0, NULL);

    g_ServiceStatus.dwCurrentState = SERVICE_RUNNING;
    g_ServiceStatus.dwCheckPoint = 0;
    g_ServiceStatus.dwWaitHint = 0;
    SetServiceStatus(g_ServiceStatusHandle, &g_ServiceStatus);

    /* Aguardar thread terminar */
    WaitForSingleObject(hThread, INFINITE);
    CloseHandle(hThread);

    g_ServiceStatus.dwCurrentState = SERVICE_STOPPED;
    SetServiceStatus(g_ServiceStatusHandle, &g_ServiceStatus);
}

/*
 * Handler de controle do serviço
 */
VOID WINAPI ServiceCtrlHandler(DWORD ctrlCode)
{
    switch (ctrlCode) {
        case SERVICE_CONTROL_STOP:
        case SERVICE_CONTROL_SHUTDOWN:
            g_ServiceStatus.dwCurrentState = SERVICE_STOP_PENDING;
            g_ServiceStatus.dwCheckPoint = 1;
            g_ServiceStatus.dwWaitHint = 5000;
            SetServiceStatus(g_ServiceStatusHandle, &g_ServiceStatus);

            SetEvent(g_StopEvent);
            break;

        default:
            break;
    }
}

/*
 * Thread principal de trabalho
 */
DWORD WINAPI WorkerThread(LPVOID param)
{
    UNREFERENCED_PARAMETER(param);

    KdPrint(("ARKHE: Oracle Service iniciado\n"));

    /* Inicializar engine de consenso */
    if (!InitializeConsensusEngine()) {
        KdPrint(("ARKHE: Falha ao inicializar ConsensusEngine\n"));
        return 1;
    }

    /* Criar named pipe para comunicação */
    RunOracleLoop();

    /* Cleanup */
    CleanupConsensusEngine();
    CloseHandle(g_StopEvent);

    return 0;
}

/*
 * Loop principal do Oracle
 * Escuta mensagens via named pipe e responde avaliações
 */
VOID RunOracleLoop(VOID)
{
    HANDLE hPipe = INVALID_HANDLE_VALUE;

    while (WaitForSingleObject(g_StopEvent, 0) != WAIT_OBJECT_0) {
        /* Criar/recolocar named pipe */
        hPipe = CreateNamedPipeW(
            PIPE_NAME,
            PIPE_ACCESS_DUPLEX,
            PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE |
            PIPE_WAIT,
            PIPE_UNLIMITED_INSTANCES,
            4096, 4096, 0, NULL);

        if (hPipe == INVALID_HANDLE_VALUE) {
            Sleep(1000);
            continue;
        }

        /* Aguardar conexão */
        if (!ConnectNamedPipe(hPipe, NULL)) {
            CloseHandle(hPipe);
            continue;
        }

        /* Processar mensagens */
        BYTE buffer[65536];
        DWORD bytesRead;

        while (ReadFile(hPipe, buffer, sizeof(buffer),
                        &bytesRead, NULL) && bytesRead > 0) {

            /* Processar mensagem recebida */
            ProcessOracleRequest(buffer, bytesRead, hPipe);
        }

        DisconnectNamedPipe(hPipe);
        CloseHandle(hPipe);
    }
}

/*
 * Processar requisição do Oracle
 */
VOID ProcessOracleRequest(
    _In_reads_bytes_(Length) PBYTE Request,
    _In_ DWORD Length,
    _In_ HANDLE ReplyPipe)
{
    ARKEHE_CONSISTENCY_REPORT report;

    if (Length < sizeof(ARKEHE_CONSENSUS_REQUEST)) {
        report.Score = HEYTING_MIN;
        report.Pruned = TRUE;
        DWORD bytesWritten;
        WriteFile(ReplyPipe, &report, sizeof(report), &bytesWritten, NULL);
        return;
    }

    /* Parse da requisição */
    PARKEHE_CONSENSUS_REQUEST req =
        (PARKEHE_CONSENSUS_REQUEST)Request;

    switch (req->Type) {
        case ARKHE_CONSENSUS_EVALUATE: {
            /* Avaliar mensagem temporal */
            ARKEHE_MESSAGE msg;
            ParseMessageFromRequest(req, &msg);

            EvaluateMessage(&msg, &report);
            break;
        }

        case ARKHE_CONSENSUS_VALIDATE_BLOCK: {
            /* Validar bloco inteiro */
            ValidateBlock(req->Data, req->DataLength, &report);
            break;
        }

        case ARKHE_CONSENSUS_HEARTBEAT: {
            /* Health check */
            report.Score = HEYTING_ONE;
            report.Pruned = FALSE;
            break;
        }

        default:
            report.Score = HEYTING_MIN;
            report.Pruned = TRUE;
    }

    /* Enviar resposta */
    DWORD bytesWritten;
    WriteFile(ReplyPipe, &report, sizeof(report),
              &bytesWritten, NULL);
}
