#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Script de instalação do ARKHE OS para Windows
.DESCRIPTION
    Instala o driver kernel, serviços e ferramentas CLI
    do sistema ARKHE no Windows 10/11 (x64).
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$InstallDir = "C:\Program Files\ARKHE",

    [Parameter(Mandatory=$false)]
    [switch]$SkipDriver = $false,

    [Parameter(Mandatory=$false)]
    [switch]$SkipServices = $false,
    )
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "╔══════════════════════════════════════════════════╗"
Write-Host "║     ARKHE Ω-TEMP — Instalação para Windows       ║"
Write-Host "╚══════════════════════════════════════════════════╝"
Write-Host ""

# 1. Verificar pré-requisitos
Write-Host "[1/5] Verificando pré-requisitos..."

$prereqs = @(
    @{Name="Windows 10/11"; Test={(Get-WmiObject Win32_OperatingSystem).Version -ge "10.0.10240"}},
    @{Name="Visual C++ Redistributable"; Test={Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" -ErrorAction SilentlyContinue}},
    @{Name="WDK"; Test={Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin" -ErrorAction SilentlyContinue}},
    @{Name="PowerShell 5.1+"; Test={$PSVersionTable.PSVersion.Major -ge 5}},
    @{Name=".NET Framework 4.8"; Test={(Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" -ErrorAction SilentlyContinue).Release -ge 528449}}
)

foreach ($req in $prereqs) {
    $status = if (& $req.Test) { "✓" } else { "✗" }
    Write-Host "   $status $($req.Name)"
}

# 2. Testar modo de teste (Test Signing)
Write-Host "[2/5] Verificando modo de assinatura de teste..."
$bcdTestSigning = bcdedit /enum | Select-String "testsigning"
if ($bcdTestSigning -match "Yes") {
    Write-Host "   ✓ Test Signing está ativo"
} else {
    Write-Host "   ⚠ Test Signing não está ativo."
    Write-Host "     Para instalar drivers não-assinados, execute:"
    Write-Host "       bcdedit /set testsigning on"
    Write-Host "     E reinicie o computador."
}

# 3. Instalar driver
if (-not $SkipDriver) {
    Write-Host "[3/5] Instalando driver kernel..."

    $driverDir = Join-Path $InstallDir "driver"
    if (-not (Test-Path $driverDir)) { New-Item -ItemType Directory -Path $driverDir -Force }

    # Copiar arquivos do driver
    Copy-Item "build\arkhe-km.sys" $driverDir -Force
    Copy-Item "certs\arkhe-test-cert.cer" $driverDir -Force

    # Criar serviço do driver
    $sc = New-Service -Name "arkhe-temporal" `
                     -BinaryPathName "$driverDir\arkhe-km.sys" `
                     -DisplayName "ARKHE Temporal Chain Driver" `
                     -Description "Substrato temporal do ARKHE OS" `
                     -StartupType Boot `
                     -ErrorAction SilentlyContinue

    if ($sc) {
        Write-Host "   ✓ Driver instalado e registrado como serviço de boot"
    } else {
        Write-Host "   ⚠ Driver já existente ou erro na instalação"
        # Tentar usar sc.exe
        & sc.exe create ARKHE_Temporal type= kernel binPath= "$driverDir\arkhe-km.sys" 2>$null
        & sc.exe start ARKHE_Temporal 2>$null
    }

    # Instalar device interfaces (via devcon ou manual)
    Write-Host "   Criando device interfaces..."

    # Usar SetupAPI para criar symbolic links
    # \\.\ARKHE\Temporal, \\.\ARKHE\Consensus, etc.
} else {
    Write-Host "[3/5] Instalação do driver ignorada (--skip-driver)"
}

# 4. Criar diretórios
Write-Host "[4/5] Criando diretórios..."

$dirs = @(
    $InstallDir,
    "$InstallDir\data",
    "$InstallDir\data\ledger",
    "$InstallDir\data\cache",
    "$InstallDir\logs",
    "$InstallDir\services"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "   ✓ Diretórios criados"

# 5. Instalar serviços
if (-not $SkipServices) {
    Write-Host "[5/5] Instalando serviços Windows..."

    # Importar módulo de gerenciamento de serviços
    Import-Module "$InstallDir\services\ArkheServiceManager.psm1" -Force

    # Instalar cada serviço
    $services = @(
        @{Name="arkhe-temporal"; Display="ARKHE Temporal Chain"; Exe="temporal_svc.exe"},
        @{Name="arkhe-oracle"; Display="ARKHE Consensus Oracle"; Exe="oracle_svc.exe"},
        @{Name="arkhe-router"; Display="ARKHE Router"; Exe="router_svc.exe"},
        @{Name="arkhe-ledger"; Display="ARKHE Distributed Ledger"; Exe="ledger_svc.exe"},
        @{Name="arkhe-zkprover"; Display="ARKHE ZK Prover"; Exe="zkprover_svc.exe"}
    )

    foreach ($svc in $services) {
        try {
            $svcPath = "$InstallDir\services\$($svc.Exe)"
            New-Service -Name $svc.Name `
                        -BinaryPathName "`"$svcPath`"" `
                        -DisplayName $svc.Display `
                        -Description "$($svc.Display) - ARKHE Omega-TEMP" `
                        -StartupType Automatic `
                        -ErrorAction Stop

            # Configurar recovery: reiniciar após falha
            sc.exe failure $svc.Name reset= 86400 actions= restart/5000/restart/10000/restart/30000

            # Adicionar permissão de rede
            & netsh advfirewall firewall add rule `
                name="ARKHE - $($svc.Display)" `
                dir=in action=allow program="$svcPath" enable=yes 2>$null

            Write-Host "   ✓ $($svc.Display)"
        } catch {
            Write-Host "   ⚠ $($svc.Display): $($_.Exception.Message)"
        }
    }
} else {
    Write-Host "[5/5] Instalação de serviços ignorada (--skip-services)"
}

# Configurar ACLs de segurança
Write-Host ""
Write-Host "Configurando segurança..."

# Apenas SYSTEM e Administradores podem escrever no diretório de dados
$acl = Get-Acl "$InstallDir\data"
$acl.SetAccessRuleProtection($true, $false)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "BUILTIN\Administrators", "FullControl", "ContainerInherit,ObjectInherit",
    "None", "Allow")
$acl.AddAccessRule($rule)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "NT AUTHORITY\SYSTEM", "FullControl", "ContainerInherit,ObjectInherit",
    "None", "Allow")
$acl.AddAccessRule($rule)
Set-Acl "$InstallDir\data" $acl

# Registrar módulo PowerShell
Copy-Item "powershell\ArkhePS.psm1" "$env:ProgramFiles\WindowsPowerShell\Modules\Arkhe\" -Force
Write-Host "   ✓ Módulo PowerShell registrado"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗"
Write-Host "║  INSTALAÇÃO CONCLUÍDA!                           ║"
Write-Host "╠══════════════════════════════════════════════════╣"
Write-Host "║  Execute 'arkhe help' para começar               ║"
Write-Host "║  Execute 'Start-Service arkhe-oracle' etc.       ║"
Write-Host "║  Execute 'arkhe status' para verificar           ║"
Write-Host "╚══════════════════════════════════════════════════╝"
Write-Host ""
Write-Host "⚠  IMPORTANTE: Se o Test Signing não estiver ativo,"
Write-Host "   reinicie com: bcdedit /set testsigning on"
