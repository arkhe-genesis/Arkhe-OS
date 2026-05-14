# ============================================================================
# Install-ArkheWSL.ps1 — Instala o Arkhe OS como distribuição WSL
# ============================================================================
param(
    [string]$Version = "v204.0",
    [string]$InstallPath = "$env:LOCALAPPDATA\ArkheWSL"
)

Write-Host "🪟 Instalando Arkhe OS como distribuição WSL..." -ForegroundColor Cyan

# 1. Baixar rootfs do Arkhe
$rootfsUrl = "https://arkhe.io/wsl/arkhe-wsl-rootfs-$Version.tar.gz"
$rootfsPath = "$env:TEMP\arkhe-wsl-rootfs.tar.gz"

Write-Host "📥 Baixando rootfs..."
Invoke-WebRequest -Uri $rootfsUrl -OutFile $rootfsPath

# 2. Criar diretório de instalação
New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null

# 3. Importar como distribuição WSL
Write-Host "📦 Importando distribuição WSL..."
wsl --import ArkheOS $InstallPath $rootfsPath --version 2

# 4. Configurar integração com Windows
$wslConfig = @"
[wsl2]
kernel=arkhe-wsl-kernel
memory=8GB
processors=4
localhostForwarding=true

[network]
generateResolvConf=true

[interop]
enabled=true
appendWindowsPath=true

[arkhe]
governance=true
mesh-node=true
phi-c-minimum=0.95
anchor-filesystem=true
"@

$wslConfig | Out-File -FilePath "$InstallPath\.wslconfig" -Encoding UTF8

# 5. Iniciar ArkheOS
Write-Host "🚀 Iniciando ArkheOS no WSL..." -ForegroundColor Green
wsl -d ArkheOS -- arkhe-init --first-boot

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗"
Write-Host "║  ✅ Arkhe OS instalado no WSL com sucesso                     ║"
Write-Host "╠══════════════════════════════════════════════════════════════╣"
Write-Host "║  Para acessar: wsl -d ArkheOS                                ║"
Write-Host "║  Shell ASI:    wsl -d ArkheOS -- arkh                        ║"
Write-Host "║  Montar Windows: /mnt/c (sob ArkFS com selos)               ║"
Write-Host "╚══════════════════════════════════════════════════════════════╝"
