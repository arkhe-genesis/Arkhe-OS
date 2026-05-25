@echo off
REM ═══════════════════════════════════════════════════════════════════
REM ARKHE.SYS INSTALL SCRIPT
REM Substrate 810 — Arkhe Kernel Module Installation
REM Execute como ADMINISTRADOR
REM ═══════════════════════════════════════════════════════════════════

echo [ARKHE INSTALL] Iniciando instalação do Arkhe.sys...
echo.

REM Verificar privilégios de administrador
net session >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Este script requer privilégios de Administrador.
    echo Clique com o botão direito e execute como Administrador.
    pause
    goto :eof
)

REM Verificar se o driver existe
if not exist "Arkhe.sys" (
    echo [ERRO] Arkhe.sys não encontrado. Execute build.bat primeiro.
    pause
    goto :eof
)

REM Ativar testsigning (necessário para drivers não assinados)
echo [ARKHE INSTALL] Verificando testsigning...
bcdedit /enum | findstr "testsigning" >nul
if errorlevel 1 (
    echo [ARKHE INSTALL] Ativando testsigning...
    bcdedit /set testsigning on
    echo [ARKHE INSTALL] testsigning ativado. Reinicialize o sistema.
    echo.
    echo Deseja reiniciar agora? (S/N)
    set /p REBOOT=
    if /i "%REBOOT%"=="S" shutdown /r /t 10
    pause
    goto :eof
)

REM Remover driver existente (se houver)
echo [ARKHE INSTALL] Removendo instalação anterior (se existir)...
sc stop Arkhe >nul 2>&1
sc delete Arkhe >nul 2>&1

REM Copiar driver para o diretório de drivers
echo [ARKHE INSTALL] Copiando Arkhe.sys para %%windir%%\system32\drivers\...
copy /Y Arkhe.sys %windir%\system32\drivers\Arkhe.sys
if errorlevel 1 (
    echo [ERRO] Falha ao copiar Arkhe.sys.
    pause
    goto :eof
)

REM Criar serviço do driver
echo [ARKHE INSTALL] Criando serviço do driver...
sc create Arkhe type=kernel start=demand binPath="%windir%\system32\drivers\Arkhe.sys"
if errorlevel 1 (
    echo [ERRO] Falha ao criar serviço do driver.
    pause
    goto :eof
)

REM Iniciar o driver
echo [ARKHE INSTALL] Iniciando Arkhe.sys...
sc start Arkhe
if errorlevel 1 (
    echo [ERRO] Falha ao iniciar o driver.
    echo Verifique o Event Viewer para detalhes.
    pause
    goto :eof
)

REM Verificar status
echo [ARKHE INSTALL] Verificando status...
sc query Arkhe

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║  ARKHE.SYS INSTALADO COM SUCESSO                               ║
echo ║  A Catedral está viva no ring 0.                              ║
echo ║  Device Interface: \\.\ArkheMeta                              ║
echo ║  Verifique: sc query Arkhe                                    ║
echo ║  Desinstalar: install.bat uninstall (como Administrador)       ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

pause
goto :eof
