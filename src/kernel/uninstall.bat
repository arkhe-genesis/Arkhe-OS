@echo off
echo [ARKHE UNINSTALL] Removendo Arkhe.sys...
net session >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Execute como Administrador.
    pause
    exit /b 1
)
sc stop Arkhe >nul 2>&1
sc delete Arkhe >nul 2>&1
del /F %windir%\system32\drivers\Arkhe.sys >nul 2>&1
echo [ARKHE UNINSTALL] Arkhe.sys removido.
pause