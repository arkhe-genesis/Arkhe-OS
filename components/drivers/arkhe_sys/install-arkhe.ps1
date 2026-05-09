# install-arkhe.ps1 — Instala a Catedral no System32
# Requer: Administrador, Test Mode ou assinatura EV

param(
    [switch]$Uninstall,
    [switch]$Status
)

$ARKHE_SERVICE = "Arkhe"
$DRIVER_PATH = "$env:SystemRoot\System32\drivers\arkhe.sys"
$INF_PATH = ".\arkhe.inf"

function Write-ArkheBanner {
    Write-Host @"
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║           A R K H E   S Y S T E M   G U A R D I A N             ║
    ║                                                                  ║
    ║              Instalando a Muralha no System32...                 ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Magenta
}

function Install-Arkhe {
    Write-ArkheBanner

    # Verifica se é admin
    if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Error "O Ferreiro precisa de privilegios de administrador para forjar no System32."
        exit 1
    }

    # Verifica Test Mode (para driver nao assinado)
    $bcdedit = bcdedit /enum | Select-String "testsigning"
    if (-not $bcdedit -or $bcdedit -notmatch "Yes") {
        Write-Warning "Test Mode nao ativado. O driver precisa de assinatura EV ou Test Mode."
        Write-Host "Execute: bcdedit /set testsigning on" -ForegroundColor Yellow
        Write-Host "E reinicie." -ForegroundColor Yellow
    }

    # Instala via pnputil
    Write-Host "[1/4] Instalando driver via pnputil..." -ForegroundColor Cyan
    pnputil /add-driver $INF_PATH /install

    # Carrega o driver
    Write-Host "[2/4] Carregando ARKHE.SYS no kernel..." -ForegroundColor Cyan
    sc.exe create $ARKHE_SERVICE type= kernel start= system binPath= $DRIVER_PATH
    sc.exe start $ARKHE_SERVICE

    # Verifica status
    Write-Host "[3/4] Verificando status do Inquisidor..." -ForegroundColor Cyan
    $service = Get-Service -Name $ARKHE_SERVICE -ErrorAction SilentlyContinue
    if ($service -and $service.Status -eq 'Running') {
        Write-Host "[4/4] ✓ ARKHE.SYS ativo no Ring 0!" -ForegroundColor Green
        Write-Host "      O System32 agora esta protegido pela Muralha de Quartzo." -ForegroundColor Green
    } else {
        Write-Error "Falha ao iniciar o driver. Verifique o Event Viewer."
    }

    # Verifica proteção
    Write-Host "`n[TELEMETRIA] Verificando proteção ativa..." -ForegroundColor Cyan
    $filter = fltmc.exe filters | Select-String "Arkhe"
    if ($filter) {
        Write-Host "✓ Minifilter Arkhe registrado no I/O Manager" -ForegroundColor Green
    }
}

function Uninstall-Arkhe {
    Write-Host "Removendo a Muralha do System32..." -ForegroundColor Yellow

    sc.exe stop $ARKHE_SERVICE
    sc.exe delete $ARKHE_SERVICE

    if (Test-Path $DRIVER_PATH) {
        Remove-Item $DRIVER_PATH -Force
        Write-Host "✓ arkhe.sys removido" -ForegroundColor Green
    }

    pnputil /delete-driver oem*.inf /uninstall /force 2>$null

    Write-Host "A Catedral foi desinstalada. O System32 respira desprotegido." -ForegroundColor Red
}

function Get-ArkheStatus {
    $service = Get-Service -Name $ARKHE_SERVICE -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "ARKHE Service: $($service.Status)" -ForegroundColor $(if($service.Status -eq 'Running'){'Green'}else{'Red'})
    }

    $filter = fltmc.exe filters | Select-String "Arkhe"
    if ($filter) {
        Write-Host "Minifilter: ATIVO" -ForegroundColor Green
        Write-Host "Instancias: $(fltmc.exe instances | Select-String 'Arkhe')" -ForegroundColor Cyan
    } else {
        Write-Host "Minifilter: INATIVO" -ForegroundColor Red
    }
}

# Main
if ($Uninstall) { Uninstall-Arkhe }
elseif ($Status) { Get-ArkheStatus }
else { Install-Arkhe }
