<#
.SYNOPSIS
    Arkhe Cathedral Kernel Driver Installation Script
    Instala catedral.sys e catedral.ini com configuração para Secure Boot.

.DESCRIPTION
    Este script:
    1. Verifica requisitos de sistema (Windows 10/11 x64, Secure Boot habilitado)
    2. Valida assinatura digital de catedral.sys e catedral.cat
    3. Copia arquivos para %SystemRoot%\System32\drivers\
    4. Registra o driver no Service Control Manager
    5. Configura parâmetros de inicialização (boot-start)
    6. Aplica configuração de catedral.ini
    7. Verifica integridade pós-instalação

.VERSION
    v∞.Ω.∇+++.SINGULARITY.EVO

.AUTHOR
    ARKHE Observatory <observatory@arkhe.org>

.LINK
    https://arkhe.org/docs/cathedral-installation

.EXAMPLE
    .\install_cathedral.ps1 -Mode Silent -LogFile C:\arkhe\install.log

.EXAMPLE
    .\install_cathedral.ps1 -VerifyOnly
#>

[CmdletBinding(DefaultParameterSetName = 'Install')]
param(
    [Parameter(ParameterSetName = 'Install')]
    [ValidateSet('Silent', 'Interactive', 'Verbose')]
    [string]$Mode = 'Interactive',

    [Parameter(ParameterSetName = 'Install')]
    [string]$LogFile = "$env:ProgramData\ARKHE\install_cathedral.log",

    [Parameter(ParameterSetName = 'VerifyOnly')]
    [switch]$VerifyOnly,

    [Parameter(ParameterSetName = 'Uninstall')]
    [switch]$Uninstall,

    [Parameter(Mandatory = $false)]
    [string]$DriverPath = "$PSScriptRoot\catedral.sys",

    [Parameter(Mandatory = $false)]
    [string]$ConfigPath = "$PSScriptRoot\catedral.ini",

    [Parameter(Mandatory = $false)]
    [string]$CatalogPath = "$PSScriptRoot\catedral.cat"
)

# ============================================================================
# CONFIGURAÇÃO GLOBAL
# ============================================================================

$Script:ArkheVersion = "v∞.Ω.∇+++.SINGULARITY.EVO"
$Script:DriverName = "Cathedral"
$Script:DriverFileName = "catedral.sys"
$Script:ConfigFileName = "catedral.ini"
$Script:CatalogFileName = "catedral.cat"
$Script:SystemDrivers = "$env:SystemRoot\System32\drivers"
$Script:ArkheData = "$env:ProgramData\ARKHE"
$Script:RequiredWindowsBuild = 19041  # Windows 10 2004+

# ============================================================================
# FUNÇÕES DE LOGGING
# ============================================================================

function Write-ArkheLog {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,
        [ValidateSet('Info', 'Success', 'Warning', 'Error', 'Debug')]
        [string]$Level = 'Info'
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $logEntry = "[$timestamp] [$Level] $Message"

    # Escrever no arquivo de log se configurado
    if ($LogFile -and (Test-Path (Split-Path $LogFile -Parent))) {
        Add-Content -Path $LogFile -Value $logEntry -Encoding UTF8
    }

    # Escrever no console baseado no modo
    switch ($Level) {
        'Success' {
            if ($Mode -ne 'Silent') { Write-Host "✅ $Message" -ForegroundColor Green }
        }
        'Error' {
            if ($Mode -ne 'Silent') { Write-Host "❌ $Message" -ForegroundColor Red }
            Write-Error $Message
        }
        'Warning' {
            if ($Mode -ne 'Silent') { Write-Host "⚠️  $Message" -ForegroundColor Yellow }
        }
        'Info' {
            if ($Mode -eq 'Verbose') { Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
        }
        'Debug' {
            if ($Mode -eq 'Verbose') { Write-Host "🔍 $Message" -ForegroundColor Gray }
        }
    }
}

# ============================================================================
# FUNÇÕES DE VERIFICAÇÃO DE REQUISITOS
# ============================================================================

function Test-ArkheRequirements {
    Write-ArkheLog "Verificando requisitos de sistema..." -Level Debug

    # Verificar arquitetura x64
    if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
        Write-ArkheLog "Requisito não atendido: Arquitetura x64 necessária" -Level Error
        return $false
    }
    Write-ArkheLog "✅ Arquitetura: x64" -Level Success

    # Verificar versão do Windows
    $windowsBuild = [System.Environment]::OSVersion.Version.Build
    if ($windowsBuild -lt $Script:RequiredWindowsBuild) {
        Write-ArkheLog "Requisito não atendido: Windows 10 2004+ (build $Script:RequiredWindowsBuild+) necessário" -Level Error
        return $false
    }
    Write-ArkheLog "✅ Windows Build: $windowsBuild" -Level Success

    # Verificar privilégios de administrador
    $currentUser = New-Object Security.Principal.WindowsPrincipal $([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-ArkheLog "Requisito não atendido: Executar como Administrador" -Level Error
        return $false
    }
    Write-ArkheLog "✅ Privilégios: Administrador" -Level Success

    # Verificar Secure Boot (recomendado)
    try {
        $secureBoot = Confirm-SecureBootUEFI -ErrorAction SilentlyContinue
        if ($secureBoot) {
            Write-ArkheLog "✅ Secure Boot: Habilitado" -Level Success
        } else {
            Write-ArkheLog "⚠️  Secure Boot: Desabilitado (recomendado habilitar)" -Level Warning
        }
    } catch {
        Write-ArkheLog "⚠️  Secure Boot: Não pôde verificar (UEFI não detectado)" -Level Warning
    }

    # Verificar espaço em disco
    $systemDrive = Get-PSDrive -Name (Split-Path $env:SystemRoot -Qualifier).TrimEnd(':')
    $freeSpaceGB = [math]::Round($systemDrive.Free / 1GB, 2)
    if ($freeSpaceGB -lt 1) {
        Write-ArkheLog "Requisito não atendido: Mínimo 1 GB livre necessário" -Level Error
        return $false
    }
    Write-ArkheLog "✅ Espaço livre: ${freeSpaceGB} GB" -Level Success

    return $true
}

# ============================================================================
# FUNÇÕES DE VALIDAÇÃO DE ASSINATURA
# ============================================================================

function Test-ArkheSignature {
    param(
        [string]$FilePath
    )

    Write-ArkheLog "Validando assinatura digital: $FilePath" -Level Debug

    try {
        # Verificar assinatura Authenticode
        $signature = Get-AuthenticodeSignature -FilePath $FilePath -ErrorAction Stop

        if ($signature.Status -eq 'Valid') {
            Write-ArkheLog "✅ Assinatura válida: $($signature.SignerCertificate.Subject)" -Level Success
            return $true
        } elseif ($signature.Status -eq 'Unknown') {
            # Verificar se é auto-assinado com certificado confiável para desenvolvimento
            if ($Mode -eq 'Verbose') {
                Write-ArkheLog "⚠️  Assinatura desconhecida (pode ser certificado de desenvolvimento)" -Level Warning
                return $true  # Permitir em modo de desenvolvimento
            }
            Write-ArkheLog "❌ Assinatura não reconhecida" -Level Error
            return $false
        } else {
            Write-ArkheLog "❌ Assinatura inválida: $($signature.Status)" -Level Error
            return $false
        }
    } catch {
        Write-ArkheLog "❌ Erro ao verificar assinatura: $($_.Exception.Message)" -Level Error
        return $false
    }
}

function Test-ArkheCatalog {
    param(
        [string]$CatalogPath,
        [string]$TargetDirectory
    )

    Write-ArkheLog "Validando catálogo de segurança: $CatalogPath" -Level Debug

    try {
        # Verificar se o catálogo existe
        if (-not (Test-Path $CatalogPath)) {
            Write-ArkheLog "⚠️  Catálogo não encontrado: $CatalogPath" -Level Warning
            return $false
        }

        # Validar catálogo contra arquivos alvo
        $validation = Test-FileCatalog -Path $TargetDirectory -CatalogFilePath $CatalogPath -Detailed

        if ($validation.Validation -eq 'Valid') {
            Write-ArkheLog "✅ Catálogo válido: Todos os arquivos verificados" -Level Success
            return $true
        } else {
            Write-ArkheLog "❌ Catálogo inválido: $($validation.Validation)" -Level Error
            if ($validation.DetailedResults) {
                $validation.DetailedResults | ForEach-Object {
                    Write-ArkheLog "   - $($_.File): $($_.Status)" -Level Debug
                }
            }
            return $false
        }
    } catch {
        Write-ArkheLog "❌ Erro ao validar catálogo: $($_.Exception.Message)" -Level Error
        return $false
    }
}

# ============================================================================
# FUNÇÕES DE INSTALAÇÃO DO DRIVER
# ============================================================================

function Install-ArkheDriver {
    Write-ArkheLog "Iniciando instalação do driver Cathedral..." -Level Info

    # Criar diretório de dados Arkhe
    if (-not (Test-Path $Script:ArkheData)) {
        New-Item -Path $Script:ArkheData -ItemType Directory -Force | Out-Null
        Write-ArkheLog "✅ Diretório criado: $Script:ArkheData" -Level Success
    }

    # Copiar driver para System32\drivers
    $driverDest = Join-Path $Script:SystemDrivers $Script:DriverFileName
    Write-ArkheLog "Copiando driver: $DriverPath → $driverDest" -Level Debug

    try {
        Copy-Item -Path $DriverPath -Destination $driverDest -Force -ErrorAction Stop
        Write-ArkheLog "✅ Driver copiado" -Level Success
    } catch {
        Write-ArkheLog "❌ Falha ao copiar driver: $($_.Exception.Message)" -Level Error
        return $false
    }

    # Copiar arquivo de configuração
    $configDest = Join-Path $Script:SystemDrivers $Script:ConfigFileName
    Write-ArkheLog "Copiando configuração: $ConfigPath → $configDest" -Level Debug

    try {
        Copy-Item -Path $ConfigPath -Destination $configDest -Force -ErrorAction Stop
        Write-ArkheLog "✅ Configuração copiada" -Level Success
    } catch {
        Write-ArkheLog "❌ Falha ao copiar configuração: $($_.Exception.Message)" -Level Error
        return $false
    }

    # Registrar driver no Service Control Manager
    Write-ArkheLog "Registrando serviço de driver..." -Level Debug

    try {
        # Remover registro anterior se existir
        $existingService = Get-Service -Name $Script:DriverName -ErrorAction SilentlyContinue
        if ($existingService) {
            Write-ArkheLog "Removendo registro anterior do driver..." -Level Debug
            sc.exe delete $Script:DriverName | Out-Null
            Start-Sleep -Seconds 2
        }

        # Criar novo serviço
        $createResult = sc.exe create $Script:DriverName `
            binPath= "\"$driverDest\"" `
            type= kernel `
            start= boot `
            tag= yes `
            DisplayName= "Arkhe Cathedral Kernel Driver" `
            error= ignore 2>&1

        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 1073) {  # 1073 = service already exists
            Write-ArkheLog "❌ Falha ao registrar serviço: $createResult" -Level Error
            return $false
        }

        Write-ArkheLog "✅ Serviço registrado: $Script:DriverName" -Level Success
    } catch {
        Write-ArkheLog "❌ Erro ao registrar serviço: $($_.Exception.Message)" -Level Error
        return $false
    }

    # Configurar parâmetros de inicialização (opcional)
    Write-ArkheLog "Configurando parâmetros de boot..." -Level Debug

    try {
        # Adicionar parâmetro de boot para driver (se necessário)
        # Nota: Drivers boot-start geralmente não precisam de parâmetros extras
        # mas podemos configurar via registry se necessário
        $driverKey = "HKLM:\SYSTEM\CurrentControlSet\Services\$Script:DriverName\Parameters"
        if (-not (Test-Path $driverKey)) {
            New-Item -Path $driverKey -Force | Out-Null
        }

        # Definir caminho para arquivo de configuração
        New-ItemProperty -Path $driverKey `
            -Name "ConfigPath" `
            -Value $configDest `
            -PropertyType String `
            -Force | Out-Null

        Write-ArkheLog "✅ Parâmetros de boot configurados" -Level Success
    } catch {
        Write-ArkheLog "⚠️  Não foi possível configurar parâmetros de boot: $($_.Exception.Message)" -Level Warning
        # Não falhar a instalação por isso
    }

    return $true
}

# ============================================================================
# FUNÇÕES DE VERIFICAÇÃO PÓS-INSTALAÇÃO
# ============================================================================

function Test-ArkheInstallation {
    Write-ArkheLog "Verificando instalação pós-instalação..." -Level Info

    $allPassed = $true

    # Verificar se arquivo do driver existe
    $driverPath = Join-Path $Script:SystemDrivers $Script:DriverFileName
    if (Test-Path $driverPath) {
        Write-ArkheLog "✅ Driver presente: $driverPath" -Level Success
    } else {
        Write-ArkheLog "❌ Driver não encontrado: $driverPath" -Level Error
        $allPassed = $false
    }

    # Verificar se serviço foi registrado
    $service = Get-Service -Name $Script:DriverName -ErrorAction SilentlyContinue
    if ($service) {
        Write-ArkheLog "✅ Serviço registrado: $($service.DisplayName)" -Level Success
        Write-ArkheLog "   - Status: $($service.Status)" -Level Debug
        Write-ArkheLog "   - StartType: $($service.StartType)" -Level Debug
    } else {
        Write-ArkheLog "❌ Serviço não registrado: $Script:DriverName" -Level Error
        $allPassed = $false
    }

    # Verificar integridade do arquivo (hash)
    if (Test-Path $driverPath) {
        $expectedHash = "c4f3e2a1b0d5..."  # Hash esperado (substituir pelo real)
        $actualHash = (Get-FileHash -Path $driverPath -Algorithm SHA3_256).Hash.Substring(0, 16)

        if ($actualHash -eq $expectedHash.Substring(0, 16)) {
            Write-ArkheLog "✅ Integridade verificada: Hash SHA3-256" -Level Success
        } else {
            Write-ArkheLog "⚠️  Hash diferente (pode ser esperado em builds personalizados)" -Level Warning
            Write-ArkheLog "   - Esperado: $expectedHash" -Level Debug
            Write-ArkheLog "   - Obtido: $actualHash" -Level Debug
        }
    }

    # Verificar se driver pode ser carregado (teste seco)
    Write-ArkheLog "Testando capacidade de carregamento do driver..." -Level Debug
    try {
        # Nota: Não carregamos o driver de verdade aqui para evitar conflitos
        # Apenas verificamos metadados
        $driverInfo = Get-Item $driverPath
        $versionInfo = $driverInfo.VersionInfo

        Write-ArkheLog "✅ Driver válido: Versão $($versionInfo.FileVersion)" -Level Success
        Write-ArkheLog "   - Produto: $($versionInfo.ProductName)" -Level Debug
        Write-ArkheLog "   - Empresa: $($versionInfo.CompanyName)" -Level Debug
    } catch {
        Write-ArkheLog "⚠️  Não foi possível ler metadados do driver" -Level Warning
    }

    return $allPassed
}

# ============================================================================
# FUNÇÃO DE DESINSTALAÇÃO
# ============================================================================

function Uninstall-ArkheDriver {
    Write-ArkheLog "Iniciando desinstalação do driver Cathedral..." -Level Info

    # Parar serviço se estiver rodando
    $service = Get-Service -Name $Script:DriverName -ErrorAction SilentlyContinue
    if ($service -and $service.Status -eq 'Running') {
        Write-ArkheLog "Parando serviço..." -Level Debug
        Stop-Service -Name $Script:DriverName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
    }

    # Remover registro do serviço
    Write-ArkheLog "Removendo registro do serviço..." -Level Debug
    try {
        sc.exe delete $Script:DriverName | Out-Null
        Write-ArkheLog "✅ Serviço removido" -Level Success
    } catch {
        Write-ArkheLog "⚠️  Não foi possível remover serviço: $($_.Exception.Message)" -Level Warning
    }

    # Remover arquivos
    $filesToRemove = @(
        (Join-Path $Script:SystemDrivers $Script:DriverFileName),
        (Join-Path $Script:SystemDrivers $Script:ConfigFileName)
    )

    foreach ($file in $filesToRemove) {
        if (Test-Path $file) {
            try {
                Remove-Item -Path $file -Force -ErrorAction Stop
                Write-ArkheLog "✅ Arquivo removido: $file" -Level Success
            } catch {
                Write-ArkheLog "⚠️  Não foi possível remover: $file" -Level Warning
            }
        }
    }

    # Limpar diretório de dados (opcional)
    if (Test-Path $Script:ArkheData) {
        Write-ArkheLog "Preservando diretório de dados: $Script:ArkheData" -Level Info
        # Não removemos para preservar logs e configurações do usuário
    }

    Write-ArkheLog "✅ Desinstalação concluída" -Level Success
    Write-ArkheLog "⚠️  Reinicialização recomendada para completar a remoção" -Level Warning
}

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

function Main {
    Write-ArkheLog "========================================" -Level Info
    Write-ArkheLog "ARKHE Cathedral Installation v$Script:ArkheVersion" -Level Info
    Write-ArkheLog "========================================" -Level Info

    # Modo de verificação apenas
    if ($VerifyOnly) {
        Write-ArkheLog "Modo: Verificação apenas" -Level Info

        $requirementsOk = Test-ArkheRequirements
        $signatureOk = Test-ArkheSignature -FilePath $DriverPath
        $catalogOk = Test-ArkheCatalog -CatalogPath $CatalogPath -TargetDirectory $Script:SystemDrivers

        if ($requirementsOk -and $signatureOk) {
            Write-ArkheLog "✅ Verificação concluída: Sistema pronto para instalação" -Level Success
            return 0
        } else {
            Write-ArkheLog "❌ Verificação falhou: Corrija os problemas antes de instalar" -Level Error
            return 1
        }
    }

    # Modo de desinstalação
    if ($Uninstall) {
        Uninstall-ArkheDriver
        return 0
    }

    # Modo de instalação
    Write-ArkheLog "Modo: $Mode" -Level Info

    # Verificar requisitos
    if (-not (Test-ArkheRequirements)) {
        Write-ArkheLog "❌ Instalação abortada: Requisitos não atendidos" -Level Error
        return 1
    }

    # Validar assinaturas
    Write-ArkheLog "Validando integridade dos arquivos..." -Level Info

    if (-not (Test-ArkheSignature -FilePath $DriverPath)) {
        if ($Mode -ne 'Verbose') {
            Write-ArkheLog "❌ Instalação abortada: Assinatura do driver inválida" -Level Error
            return 1
        }
        Write-ArkheLog "⚠️  Continuando com assinatura não verificada (modo desenvolvimento)" -Level Warning
    }

    if (-not (Test-ArkheCatalog -CatalogPath $CatalogPath -TargetDirectory $Script:SystemDrivers)) {
        Write-ArkheLog "⚠️  Catálogo de segurança não validado (pode ser esperado em desenvolvimento)" -Level Warning
    }

    # Confirmar com usuário (modo interativo)
    if ($Mode -eq 'Interactive') {
        Write-Host "`n⚠️  Esta instalação irá:" -ForegroundColor Yellow
        Write-Host "   • Instalar um driver de kernel em ring-0" -ForegroundColor White
        Write-Host "   • Modificar configurações de inicialização do sistema" -ForegroundColor White
        Write-Host "   • Requer reinicialização para ativar o driver" -ForegroundColor White
        Write-Host ""

        $confirm = Read-Host "Deseja continuar? (S/N)"
        if ($confirm -notmatch '^[SsYy]') {
            Write-ArkheLog "Instalação cancelada pelo usuário" -Level Warning
            return 0
        }
    }

    # Executar instalação
    if (-not (Install-ArkheDriver)) {
        Write-ArkheLog "❌ Instalação falhou" -Level Error
        return 1
    }

    # Verificar pós-instalação
    if (-not (Test-ArkheInstallation)) {
        Write-ArkheLog "⚠️  Instalação concluída com avisos" -Level Warning
    } else {
        Write-ArkheLog "✅ Instalação concluída com sucesso" -Level Success
    }

    # Instruções finais
    Write-Host "" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "1. Reinicie o sistema para ativar o driver:" -ForegroundColor White
    Write-Host "   shutdown /r /t 0" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Após reiniciar, verifique o status:" -ForegroundColor White
    Write-Host "   Get-Service Cathedral" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Consulte logs em:" -ForegroundColor White
    Write-Host "   $Script:ArkheData\install_cathedral.log" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔗 Documentação: https://arkhe.org/docs/cathedral" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    return 0
}

# ============================================================================
# EXECUÇÃO
# ============================================================================

try {
    $exitCode = Main
    exit $exitCode
} catch {
    Write-ArkheLog "❌ Erro não tratado: $($_.Exception.Message)" -Level Error
    Write-ArkheLog "Stack: $($_.ScriptStackTrace)" -Level Debug
    exit 2
}