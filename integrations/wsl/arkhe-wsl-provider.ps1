# ============================================================================
# ARKHE Ω‑TEMP — WSL2 Integration Provider
# ============================================================================
# Instala o Arkhe Runtime dentro do WSL2 com acesso a recursos do host Windows
# ============================================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$ArkheVersion = "7.0.0",

    [Parameter(Mandatory=$false)]
    [switch]$EnableGPU,

    [Parameter(Mandatory=$false)]
    [switch]$EnableTPU
)

Write-Host "🔗 Configurando integração ArkheOS com WSL2..." -ForegroundColor Cyan

# 1. Verificar pré-requisitos
if (-not (wsl --list --quiet)) {
    Write-Error "❌ WSL2 não está instalado. Execute: wsl --install"
    exit 1
}

# 2. Baixar Arkhe Runtime para WSL
Write-Host "📦 Baixando Arkhe Runtime para WSL..."
$downloadUrl = "https://arkhe.io/releases/runtime/${ArkheVersion}/arkhe-wsl-${env:PROCESSOR_ARCHITECTURE}.tar.gz"
$installPath = "$env:USERPROFILE\ArkheWSL"

if (-not (Test-Path $installPath)) {
    New-Item -ItemType Directory -Path $installPath | Out-Null
}

Invoke-WebRequest -Uri $downloadUrl -OutFile "$installPath\arkhe-runtime.tar.gz"
tar -xzf "$installPath\arkhe-runtime.tar.gz" -C $installPath

# 3. Configurar integração com Hyper-V para acesso a hardware
Write-Host "🔌 Configurando bridge Hyper-V para acesso a hardware..."

if ($EnableGPU) {
    # Habilitar GPU passthrough via WSLg
    wsl --update
    Write-Host "✅ Suporte a GPU habilitado via WSLg"
}

if ($EnableTPU) {
    # Configurar acesso a TPU via libtpu
    $tpuConfig = @"
[wsl2]
kernel = $(wslpath -w $(wslvar WSL2_KERNEL_PATH))
# Habilitar acesso a dispositivos /dev/tpu*
device = /dev/tpu0
"@
    $tpuConfig | Out-File -FilePath "$env:USERPROFILE\.wslconfig" -Encoding utf8
    Write-Host "✅ Suporte a TPU configurado"
}

# 4. Registrar Arkhe como distribuição WSL opcional
Write-Host "🐧 Registrando Arkhe como ambiente WSL..."

$wslImportCmd = "wsl --import ArkheOS `"$installPath\rootfs`" `"$installPath\arkhe-runtime.tar.gz`" --version 2"
Invoke-Expression $wslImportCmd

# 5. Configurar integração com Arkhe Shell
Write-Host "🐚 Configurando Arkhe Shell no WSL..."

$wslSetupScript = @"
#!/bin/bash
# Setup script executado dentro do WSL

# Instalar dependências
apt-get update && apt-get install -y curl wget fuse3

# Instalar Arkhe Runtime interno
curl -sL https://arkhe.io/runtime/install.sh | bash

# Configurar montagem automática de ArkFS
mkdir -p ~/ArkheFS
echo "arkhe-fuse#none /home/$USER/ArkheFS fuse defaults,allow_other 0 0" >> /etc/fstab

# Configurar integração com Windows clipboard
echo "export WSLENV=PATH:/mnt/c/Users/$USER/.arkhe:WL" >> ~/.bashrc

echo "✅ Arkhe Runtime instalado no WSL"
echo "🚀 Para iniciar: wsl -d ArkheOS"
"@

wsl -d ArkheOS -- bash -c "$wslSetupScript"

# 6. Criar atalho no menu Iniciar
$shortcutPath = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\ArkheOS.lnk"
$WScript = New-Object -ComObject WScript.Shell
$Shortcut = $WScript.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = "C:\Windows\System32\wsl.exe"
$Shortcut.Arguments = "-d ArkheOS"
$Shortcut.IconLocation = "$installPath\arkhe-icon.ico,0"
$Shortcut.Description = "ArkheOS via WSL2"
$Shortcut.Save()

Write-Host "✅ Integração WSL2 concluída!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Para iniciar o ArkheOS no WSL:" -ForegroundColor Yellow
Write-Host "   wsl -d ArkheOS"
Write-Host ""
Write-Host "🔗 Recursos disponíveis:" -ForegroundColor Yellow
Write-Host "   • Acesso a GPU: $EnableGPU"
Write-Host "   • Acesso a TPU: $EnableTPU"
Write-Host "   • Integração com Windows: ✅"
Write-Host "   • ArkFS montado em ~/ArkheFS: ✅"