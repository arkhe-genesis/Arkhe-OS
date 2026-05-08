// agictl_win32.cpp — ARKHE OS Runtime Launcher for Windows
// Substrato 5002: Native .agi handler
//
// Build: cl /EHsc /O2 agictl_win32.cpp /link wslapi.lib shell32.lib

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wslapi.h>     // WslLaunch (opcional)
#include <shellapi.h>
#include <shlwapi.h>
#include <stdio.h>
#include <stdlib.h>

#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "shlwapi.lib")

// ─── Constantes ────────────────────────────────────────────────
#define ARKHE_MAGIC "AGI_ARTIFACT_V1"
#define MANIFEST_FILE "MANIFEST.json"
#define SIG_FILE "SEAL.asc"

// ─── Helpers ───────────────────────────────────────────────────
void LogInfo(const char* fmt, ...) {
    char buf[1024];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    MessageBoxA(NULL, buf, "ARKHE OS agictl", MB_OK | MB_ICONINFORMATION);
}

// ─── Verificar integridade do .agi ─────────────────────────────
BOOL VerifyArtifact(const WCHAR* path) {
    // 1. Abrir o arquivo .agi (formato tar)
    // 2. Extrair MANIFEST.json e SHA256SUMS
    // 3. Recalcular hashes e comparar
    // 4. Verificar assinatura Ed25519 no SEAL.asc
    //
    // Esta é uma implementação simplificada.
    LogInfo("Verification placeholder for: %ls", path);
    return TRUE;
}

// ─── Extrair artefato .agi ─────────────────────────────────────
BOOL ExtractArtifact(const WCHAR* path, const WCHAR* outputDir) {
    // Usa tar.exe embutido no Windows 10+ (build 17063+)
    WCHAR cmd[2048];
    swprintf_s(cmd, 2048, L"tar.exe -xf \"%s\" -C \"%s\"", path, outputDir);

    STARTUPINFOW si = { sizeof(si) };
    PROCESS_INFORMATION pi = { 0 };

    if (CreateProcessW(NULL, cmd, NULL, NULL, FALSE,
                       CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {
        WaitForSingleObject(pi.hProcess, 30000);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return TRUE;
    }
    return FALSE;
}

// ─── Abrir com WSL (fallback) ──────────────────────────────────
BOOL OpenInWSL(const WCHAR* path) {
    WCHAR wslCmd[2048];
    // Converte caminho Windows → /mnt/c/...
    WCHAR linuxPath[1024];
    swprintf_s(linuxPath, 1024, L"/mnt/%c/%ls",
               towlower(path[0]), path + 3);
    // Substitui backslashes
    for (WCHAR* p = linuxPath; *p; p++) if (*p == L'\\') *p = L'/';

    swprintf_s(wslCmd, 2048, L"wsl.exe agictl open \"%s\"", linuxPath);

    STARTUPINFOW si = { sizeof(si) };
    PROCESS_INFORMATION pi = { 0 };

    if (CreateProcessW(NULL, wslCmd, NULL, NULL, FALSE,
                       CREATE_NEW_CONSOLE, NULL, NULL, &si, &pi)) {
        WaitForSingleObject(pi.hProcess, INFINITE);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return TRUE;
    }
    return FALSE;
}

// ─── Ponto de entrada ──────────────────────────────────────────
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE, LPSTR, int nCmdShow) {
    int argc;
    LPWSTR* argv = CommandLineToArgvW(GetCommandLineW(), &argc);

    if (argc < 2) {
        LogInfo("Usage: agictl.exe [open|verify|extract] <file.agi>");
        return 1;
    }

    const WCHAR* action = argv[1];
    const WCHAR* path   = (argc >= 3) ? argv[2] : NULL;

    if (wcscmp(action, L"open") == 0 && path) {
        // Tentar abrir nativamente
        if (VerifyArtifact(path)) {
            // Se tiver Docker/WSL, instanciar
            BOOL ok = OpenInWSL(path);
            if (!ok) {
                // Fallback: extrair e mostrar
                WCHAR outDir[MAX_PATH];
                swprintf_s(outDir, MAX_PATH, L"%s_extracted", path);
                ExtractArtifact(path, outDir);
                ShellExecuteW(NULL, L"open", outDir, NULL, NULL, SW_SHOW);
            }
        }
    } else if (wcscmp(action, L"verify") == 0 && path) {
        VerifyArtifact(path);
    } else if (wcscmp(action, L"extract") == 0 && path) {
        WCHAR outDir[MAX_PATH];
        swprintf_s(outDir, MAX_PATH, L"%s_extracted", path);
        ExtractArtifact(path, outDir);
    } else {
        LogInfo("Unknown action: %ls", action);
    }

    LocalFree(argv);
    return 0;
}