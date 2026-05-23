#Requires -RunAsAdministrator
[CmdletBinding()]
param()

Write-Host "ARKHE OS v∞.Ω.∇+++ — Native C#/.NET MSI Builder" -ForegroundColor Cyan

# Define absolute paths (to be executed on a Windows runner or Wine-mono environment)
$SourceDir = $PSScriptRoot
$BuildDir = Join-Path $SourceDir "build"
$TargetExe = Join-Path $BuildDir "ArkheService.exe"
$TargetWxs = Join-Path $SourceDir "ArkheInstaller.wxs"
$TargetWixobj = Join-Path $BuildDir "ArkheInstaller.wixobj"
$TargetMsi = Join-Path $BuildDir "ArkheInstaller.msi"

if (-not (Test-Path $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir | Out-Null
}

# 1. Compile the C# Service
Write-Host "Compiling C# Service..." -ForegroundColor Yellow
# Requires .NET SDK (csc.exe) in PATH. Using classic Framework csc for simplicity.
$cscPath = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path $cscPath)) {
    Write-Warning "csc.exe not found at standard path. Skipping native compile in this stub."
} else {
    & $cscPath /target:exe /out:$TargetExe (Join-Path $SourceDir "ArkheService.cs")
    if ($LASTEXITCODE -ne 0) { throw "C# Compilation Failed" }
}

# 2. Compile and Link the MSI via WiX Toolset
Write-Host "Building MSI via WiX Toolset..." -ForegroundColor Yellow
$wixCandle = "C:\Program Files (x86)\WiX Toolset v3.11\bin\candle.exe"
$wixLight = "C:\Program Files (x86)\WiX Toolset v3.11\bin\light.exe"

if (-not (Test-Path $wixCandle)) {
    Write-Warning "WiX Toolset not found. Skipping MSI build."
} else {
    & $wixCandle $TargetWxs -out $TargetWixobj
    if ($LASTEXITCODE -ne 0) { throw "WiX Candle Failed" }

    & $wixLight $TargetWixobj -out $TargetMsi
    if ($LASTEXITCODE -ne 0) { throw "WiX Light Failed" }
}

Write-Host "Native C# Build Process Complete." -ForegroundColor Green
