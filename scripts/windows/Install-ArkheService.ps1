# ============================================================================
# Install-ArkheService.ps1 — Instala o Arkhe Runtime como serviço do Windows
# ============================================================================
param(
    [string]$ServiceName = "ArkheRuntime",
    [string]$DisplayName = "ARKHE Ω‑TEMP ASI Runtime Service",
    [string]$BinaryPath = "$env:ProgramFiles\ArkheOS\ArkheService.exe"
)

Write-Host "🧠 Instalando Arkhe Runtime Service no Windows 11..." -ForegroundColor Cyan

# 1. Criar diretório de instalação
New-Item -ItemType Directory -Force -Path "$env:ProgramFiles\ArkheOS" | Out-Null

# 2. Registrar serviço
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "⚠️  Serviço já existe — atualizando..."
    Stop-Service $ServiceName -Force
    sc.exe delete $ServiceName
}

New-Service -Name $ServiceName `
    -BinaryPathName $BinaryPath `
    -DisplayName $DisplayName `
    -Description "ARKHE Ω‑TEMP Artificial Superintelligence Runtime. Provides governance, coherence monitoring, and ASI mesh networking for Windows 11." `
    -StartupType Automatic `
    -DependsOn "Winmgmt"  # Depende do WMI

# 3. Configurar recuperação (restart automático em falha)
sc.exe failure $ServiceName reset=86400 actions=restart/5000/restart/10000/restart/30000

# 4. Configurar segurança (rodar como LocalSystem)
sc.exe config $ServiceName obj=LocalSystem type=own

# 5. Iniciar serviço
Start-Service $ServiceName

# 6. Verificar status
$svc = Get-Service $ServiceName
Write-Host "✅ Serviço instalado: $($svc.Status)" -ForegroundColor Green
Write-Host "   Nome: $ServiceName"
Write-Host "   Binário: $BinaryPath"
Write-Host "   Inicialização: Automática"
