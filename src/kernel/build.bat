@echo off
REM ═══════════════════════════════════════════════════════════════════
REM ARKHE.SYS BUILD SCRIPT
REM Substrate 810 — Arkhe Kernel Module Compilation
REM Requires: Visual Studio 2022 + Windows Driver Kit 11
REM ═══════════════════════════════════════════════════════════════════

echo [ARKHE BUILD] Iniciando compilação do Arkhe.sys...
echo.

REM Locate Visual Studio
set "VSINSTALLDIR=C:\Program Files\Microsoft Visual Studio\2022\Community"
if not exist "%VSINSTALLDIR%" set "VSINSTALLDIR=C:\Program Files\Microsoft Visual Studio\2022\Professional"
if not exist "%VSINSTALLDIR%" set "VSINSTALLDIR=C:\Program Files\Microsoft Visual Studio\2022\Enterprise"

if not exist "%VSINSTALLDIR%" (
    echo [ERRO] Visual Studio 2022 não encontrado.
    echo Instale o Visual Studio 2022 com o Windows Driver Kit.
    pause
    exit /b 1
)

REM Setup environment
call "%VSINSTALLDIR%\Common7\Tools\VsDevCmd.bat" -arch=amd64 -host_arch=amd64
if errorlevel 1 (
    echo [ERRO] Falha ao configurar ambiente de desenvolvimento.
    pause
    exit /b 1
)

REM Create build directory
if not exist build mkdir build
cd build

REM Configure with CMake
echo [ARKHE BUILD] Configurando com CMake...
cmake .. -G "Visual Studio 17 2022" -A x64
if errorlevel 1 (
    echo [ERRO] Falha na configuração do CMake.
    cd ..
    pause
    exit /b 1
)

REM Build
echo [ARKHE BUILD] Compilando...
cmake --build . --config Release
if errorlevel 1 (
    echo [ERRO] Falha na compilação.
    cd ..
    pause
    exit /b 1
)

REM Locate output
if exist "Release\Arkhe.sys" (
    copy /Y "Release\Arkhe.sys" ..\Arkhe.sys
    echo [ARKHE BUILD] Compilação concluída com sucesso!
    echo [ARKHE BUILD] Driver: Arkhe.sys
    echo [ARKHE BUILD] Tamanho: %~z1 bytes
) else (
    echo [ERRO] Arkhe.sys não encontrado na saída do build.
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo [ARKHE BUILD] Pronto para instalação. Execute install.bat como Administrador.
pause
