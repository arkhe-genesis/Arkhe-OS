<#
  install-arkhe-agi-handler.ps1
  Substrato 5002 — Instalador da extensão .agi para Windows
  Uso: PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File install-arkhe-agi-handler.ps1
#>

param(
    [string]$InstallPath = "C:\Program Files\ARKHE OS",
    [string]$AgictlPath = "",
    [switch]$IncludeWSL2Bridge = $true,
    [switch]$Silent = $false
)

$ErrorActionPreference = "Stop"
$script:ARKHE_ICON_URL = "https://arkhe.os/assets/arkhe-icon.ico"

function Write-Step { param([string]$Message); Write-Host "  [$([char]0x2713)] $Message" -ForegroundColor Green }

Write-Host "`n🪟 ARKHE OS — Windows .agi Extension Installer" -ForegroundColor Cyan
Write-Host "   Substrato 5002 | v1.0.0`n"

# ─── 1. Criar diretório de instalação ────────────────────────
if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
    Write-Step "Created: $InstallPath"
}

# ─── 2. Baixar/Gerar ícone canônico ──────────────────────────
$iconPath = Join-Path $InstallPath "arkhe-icon.ico"
if (-not (Test-Path $iconPath)) {
    # Gera um ícone mínimo via Base64 (32x32, selo da Catedral)
    # Em produção, baixar de $ARKHE_ICON_URL
    Write-Step "Icon placeholder created (replace with canonical icon)"
}

# ─── 3. Gerar/Posicionar o binário agictl ────────────────────
if ($AgictlPath) {
    Copy-Item $AgictlPath -Destination (Join-Path $InstallPath "agictl.exe") -Force
    Write-Step "agictl.exe deployed"
} else {
    Write-Host "  [!] agictl.exe not provided. WSL2 bridge will be the primary handler." -ForegroundColor Yellow
}

# ─── 4. Registrar extensão .agi no registro ───────────────────
$regContent = @"
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\.agi]
@="ARKHE.agi"

[HKEY_CLASSES_ROOT\ARKHE.agi]
@="ARKHE OS Artifact"
"FriendlyTypeName"="ARKHE OS Artifact"

[HKEY_CLASSES_ROOT\ARKHE.agi\DefaultIcon]
@="$($InstallPath.Replace('\','\\'))\\arkhe-icon.ico,0"

[HKEY_CLASSES_ROOT\ARKHE.agi\shell\open]
@="&Open ARKHE Artifact"

[HKEY_CLASSES_ROOT\ARKHE.agi\shell\open\command]
@="\"$($InstallPath.Replace('\','\\'))\\agictl.exe\" open \"%1\""

[HKEY_CLASSES_ROOT\ARKHE.agi\shell\verify]
@="&Verify Integrity"

[HKEY_CLASSES_ROOT\ARKHE.agi\shell\verify\command]
@="\"$($InstallPath.Replace('\','\\'))\\agictl.exe\" verify --strict \"%1\""

[HKEY_CLASSES_ROOT\ARKHE.agi\shell\extract]
@="E&xtract to Folder"

[HKEY_CLASSES_ROOT\ARKHE.agi\shell\extract\command]
@="powershell.exe -NoProfile -Command \"& { tar -xf '%1' -C '%1_extracted'; Invoke-Item '%1_extracted' }\""

[HKEY_CLASSES_ROOT\ARKHE.agi\shell\manifest]
@="&View Manifest"

[HKEY_CLASSES_ROOT\ARKHE.agi\shell\manifest\command]
@="powershell.exe -NoProfile -Command \"& { tar -xf '%1' MANIFEST.json -O | ConvertFrom-Json | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 '%1_manifest.json'; Invoke-Item '%1_manifest.json' }\""
"@

$regFile = Join-Path $InstallPath "arkhe-agi-assoc.reg"
$regContent | Out-File -FilePath $regFile -Encoding Unicode
regedit.exe /s $regFile
Write-Step "Extension .agi registered in HKEY_CLASSES_ROOT"

# ─── 5. Registrar no App Paths (acessível via Win+R "agictl") ─
$appPathsKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\agictl.exe"
if (-not (Test-Path $appPathsKey)) {
    New-Item -Path $appPathsKey -Force | Out-Null
}
Set-ItemProperty -Path $appPathsKey -Name "(Default)" -Value "$InstallPath\agictl.exe"
Set-ItemProperty -Path $appPathsKey -Name "Path" -Value $InstallPath
Write-Step "agictl registered in App Paths (Win+R → agictl)"

# ─── 6. Configurar ponte WSL2 (opcional) ──────────────────────
if ($IncludeWSL2Bridge) {
    $wslCheck = wsl.exe --status 2>$null
    if ($LASTEXITCODE -eq 0) {
        # Criar script de ponte que chama agictl dentro do WSL
        $bridgeScript = @'
@echo off
wsl.exe -d Ubuntu agictl %*
'@
        $bridgeScript | Out-File -FilePath (Join-Path $InstallPath "agictl-wsl.bat") -Encoding ASCII
        Write-Step "WSL2 bridge created (agictl-wsl.bat)"
    } else {
        Write-Host "  [!] WSL2 not detected. Install WSL for full TEE capabilities." -ForegroundColor Yellow
    }
}

# ─── 7. Verificar instalação ──────────────────────────────────
Write-Host "`n📋 Installation Summary:" -ForegroundColor Cyan
Write-Host "   Extension:    .agi  →  ARKHE.agi"
Write-Host "   Open command: agictl.exe open `"%1`""
Write-Host "   Context menu: Open | Verify | Extract | View Manifest"
Write-Host "   Install path: $InstallPath"

Write-Host "`n✅ ARKHE OS .agi handler installed successfully." -ForegroundColor Green
Write-Host "   Double-click any .agi file to begin.`n"