# build-sfx.ps1
# Creates a Self-Extracting Archive for ARKHE OS Full Stack

$ErrorActionPreference = 'Stop'

$Version = "6.1.0"
$ArchiveName = "ArkheOS-Full-$Version-Windows-x64-SFX.exe"
$OutputArchive = ".\$ArchiveName"
$TempDir = ".\ArkheOS_TempSFX"

Write-Host "Creating temporary directory..."
If (Test-Path $TempDir) { Remove-Item $TempDir -Recurse -Force }
New-Item -ItemType Directory -Path $TempDir | Out-Null

Write-Host "Copying ARKHE OS components..."
# Define source directories based on repository structure
$Sources = @(
    "..\..\target\release\arkhed.exe",
    "..\..\target\release\arkhe-ws.exe",
    "..\..\target\release\arkhe-consciousness.exe",
    "..\..\target\release\phase-oracle.exe",
    "..\..\cmd\arkhe\arkhe.exe",
    "..\..\dist\python",
    "..\..\dist\corvo-os",
    "..\..\README.md",
    "..\..\LICENSE"
)

foreach ($Source in $Sources) {
    if (Test-Path $Source) {
        Copy-Item -Path $Source -Destination $TempDir -Recurse -Force
    } else {
        Write-Warning "Source path not found, skipping: $Source"
    }
}

# Create extraction stub
$InstallScriptPath = Join-Path $TempDir "install.bat"
$InstallScriptContent = @"
@echo off
echo Installing ARKHE OS v$Version...
set TARGET_DIR=%PROGRAMFILES%\ARKHE\OS
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
xcopy /E /Y /C /I * "%TARGET_DIR%"
echo Updating PATH...
setx PATH "%PATH%;%TARGET_DIR%" /M
echo Installation complete.
pause
"@

Set-Content -Path $InstallScriptPath -Value $InstallScriptContent

Write-Host "Creating SFX using 7-Zip (Requires 7z.exe in PATH)..."
# We require 7-Zip for an actual SFX, falling back to a regular zip if not present
if (Get-Command 7z -ErrorAction SilentlyContinue) {
    # 7z a -sfx7z.sfx $OutputArchive $TempDir\*
    Start-Process -FilePath "7z" -ArgumentList "a","-sfx7z.sfx",$OutputArchive,"$TempDir\*" -Wait -NoNewWindow
    Write-Host "SFX archive created at $OutputArchive"
} else {
    Write-Warning "7z not found in PATH. Creating standard ZIP archive instead."
    $ZipPath = ".\ArkheOS-Full-$Version-Windows-x64.zip"
    Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipPath -Force
    Write-Host "ZIP archive created at $ZipPath"
}

Write-Host "Cleaning up temporary files..."
Remove-Item $TempDir -Recurse -Force
Write-Host "Build finished successfully."
