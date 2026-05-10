/*
 * ARKHE Ω-TEMP — Windows Service Manager
 *
 * Gerencia a instalação, inicialização e controle dos
 * serviços do ARKHE no Windows.
 */

#include <windows.h>
#include <stdio.h>
#include <tchar.h>
#include "ServiceBase.h"

/*
 * Instalar serviços ARKHE
 */
BOOL InstallArkheServices(VOID)
{
    SC_HANDLE hSCManager = OpenSCManager(
        NULL, NULL, SC_MANAGER_CREATE_SERVICE);

    if (!hSCManager) {
        _tprintf(_T("Falha ao abrir SCManager: %lu\n"),
                 GetLastError());
        return FALSE;
    }

    /* Caminho do executável */
    TCHAR exePath[MAX_PATH];
    GetModuleFileName(NULL, exePath, MAX_PATH);

    /* Instalar cada serviço */
    InstallService(hSCManager,
                   _T("arkhe-oracle"),
                   _T("ARKHE Consensus Oracle"),
                   exePath, _T("--service oracle"));

    InstallService(hSCManager,
                   _T("arkhe-router"),
                   _T("ARKHE Temporal Router"),
                   exePath, _T("--service router"));

    InstallService(hSCManager,
                   _T("arkhe-ledger"),
                   _T("ARKHE Distributed Ledger"),
                   exePath, _T("--service ledger"));

    InstallService(hSCManager,
                   _T("arkhe-zkprover"),
                   _T("ARKHE ZK Proof Engine"),
                   exePath, _T("--service zkprover"));

    CloseServiceHandle(hSCManager);
    return TRUE;
}

/*
 * Iniciar serviços ARKHE
 */
BOOL StartArkheServices(VOID)
{
    SC_HANDLE hSCManager = OpenSCManager(
        NULL, NULL, SC_MANAGER_CONNECT);

    if (!hSCManager) return FALSE;

    const TCHAR* services[] = {
        _T("arkhe-temporal"),
        _T("arkhe-oracle"),
        _T("arkhe-router"),
        _T("arkhe-ledger"),
        _T("arkhe-zkprover"),
        NULL
    };

    for (int i = 0; services[i]; i++) {
        SC_HANDLE hService = OpenService(
            hSCManager, services[i], SERVICE_START);

        if (hService) {
            if (!StartService(hService, 0, NULL)) {
                _tprintf(_T("Falha ao iniciar %s: %lu\n"),
                         services[i], GetLastError());
            } else {
                _tprintf(_T("✓ Serviço %s iniciado\n"),
                         services[i]);
            }
            CloseServiceHandle(hService);
        }
    }

    CloseServiceHandle(hSCManager);
    return TRUE;
}

/*
 * Verificar status dos serviços
 */
VOID CheckServiceStatus(VOID)
{
    SC_HANDLE hSCManager = OpenSCManager(
        NULL, NULL, SC_MANAGER_ENUMERATE_SERVICE);

    if (!hSCManager) return;

    DWORD bytesNeeded, servicesReturned;
    EnumServicesStatus(
        hSCManager,
        SERVICE_WIN32,
        SERVICE_STATE_ALL,
        NULL, 0,
        &bytesNeeded,
        &servicesReturned,
        NULL);

    LPENUM_SERVICE_STATUS services =
        (LPENUM_SERVICE_STATUS)malloc(bytesNeeded);

    if (services && EnumServicesStatus(
        hSCManager, SERVICE_WIN32,
        SERVICE_STATE_ALL,
        services, bytesNeeded,
        &bytesNeeded, &servicesReturned, NULL)) {

        _tprintf(_T("\n=== ARKHE Services Status ===\n"));
        for (DWORD i = 0; i < servicesReturned; i++) {
            LPENUM_SERVICE_STATUS svc = &services[i];
            const TCHAR* status;

            switch (svc->ServiceStatus.dwCurrentState) {
                case SERVICE_RUNNING:
                    status = _T("RUNNING");
                    break;
                case SERVICE_STOPPED:
                    status = _T("STOPPED");
                    break;
                case SERVICE_START_PENDING:
                    status = _T("STARTING...");
                    break;
                default:
                    status = _T("UNKNOWN");
            }

            _tprintf(_T("  %-25s %s\n"),
                     svc->lpServiceName, status);
        }
    }

    free(services);
    CloseServiceHandle(hSCManager);
}
