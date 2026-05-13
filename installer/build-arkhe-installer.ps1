param(
    [switch]$SkipBuild,
    [string]$Configuration = "release"
)

$ErrorActionPreference = "Stop"

Write-Host "🏛️ ARKHE OS — Windows Installer Build Pipeline" -ForegroundColor Cyan

# 1. Build Rust workspace
if (-not $SkipBuild) {
    Write-Host "[1/5] Building Rust workspace..."
    cargo build --workspace --release
    if ($LASTEXITCODE -ne 0) { throw "Rust build failed" }
}

# 2. Build Python components (PyInstaller)
Write-Host "[2/5] Building Python components..."
python -m PyInstaller --onefile --name arkhe_omega_temp arkhe_core/run.py
python -m PyInstaller --onefile --name mesh-llm mesh_llm/main.py

# 3. Collect binaries into staging
Write-Host "[3/5] Staging artifacts..."
$stage = "installer\staging"
Remove-Item -Recurse $stage -ErrorAction SilentlyContinue
mkdir $stage\bin, $stage\startup, $stage\dist, $stage\python

copy target\release\arkhe.exe           $stage\bin\
copy target\release\arkhed.exe          $stage\bin\
copy target\release\arkhe-ws.exe        $stage\bin\
copy target\release\arkhe-consciousness.exe $stage\bin\
copy target\release\phase-oracle.exe    $stage\bin\
copy startup\*                          $stage\startup\
copy dist\arkhe_omega_temp.exe          $stage\dist\
copy dist\mesh-llm.exe                  $stage\dist\
copy bridges\x402\x402_pix_bridge.py    $stage\python\

# 4. Build MSI (WiX)
Write-Host "[4/5] Building MSI with WiX..."
if (Get-Command "candle.exe" -ErrorAction SilentlyContinue) {
    cd installer\wix
    candle.exe ARKHE.wxs -ext WixUtilExtension -o ARKHE.wixobj
    light.exe ARKHE.wixobj -ext WixUtilExtension -out ..\staging\ARKHE.msi
    cd ..\..
    Write-Host "   MSI built: installer\staging\ARKHE.msi"
} else {
    Write-Host "   WiX Toolset not found; skipping MSI."
}

# 5. Build EXE (Inno Setup)
Write-Host "[5/5] Building EXE with Inno Setup..."
if (Get-Command "iscc.exe" -ErrorAction SilentlyContinue) {
    cd installer\inno
    iscc.exe ARKHE.iss
    cd ..\..
    Write-Host "   EXE built: installer\output\ARKHE-OS-6.1.0-win64.exe"
} else {
    Write-Host "   Inno Setup not found; skipping EXE."
}

Write-Host "✅ Installer artifacts ready in installer\staging\" -ForegroundColor Green