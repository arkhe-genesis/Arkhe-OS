<# windows/install.ps1 — Enhanced Windows .agi handler #>
param(
    [string]$InstallPath = "C:\Program Files\ARKHE OS",
    [switch]$UserMode = $false,
    [switch]$SkipIcons = $false,
    [switch]$IncludeWSL2 = $true
)
$ErrorActionPreference = "Stop"

function Write-Step { param([string]$m); Write-Host "  [✓] $m" -ForegroundColor Green }
function Write-Warn { param([string]$m); Write-Host "  [⚠] $m" -ForegroundColor Yellow }

# Setup
if (-not (Test-Path $InstallPath)) { New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null }
$BinDir = Join-Path $InstallPath "bin"; $LibDir = Join-Path $InstallPath "lib\arkhe"
New-Item -ItemType Directory -Path $BinDir, $LibDir -Force | Out-Null

# Install core
Write-Step "Installing agictl core..."
Copy-Item -Path "..\common\*.py" -Destination $LibDir -Force

# Create agictl.ps1
$script = @'
param([ValidateSet("open","verify","extract","manifest")][string]$Action,[string]$Path,[string]$Output)
if (-not $Path -or -not (Test-Path $Path)) { Write-Error "Not found: $Path"; exit 1 }
$lib = Split-Path $PSScriptRoot -Parent | Join-Path -ChildPath "lib\arkhe"
$env:PYTHONPATH = "$lib;$env:PYTHONPATH"
switch ($Action) {
  "open" {
      python -c "import sys;sys.path.insert(0,'$lib');from verify import verify_artifact;exit(0 if verify_artifact('$Path')else 1)"
      if ($LASTEXITCODE -eq 0) {
          if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
            $lp = "/mnt/" + $Path[0].ToString().ToLower() + "/" + $Path.Substring(3).Replace("\","/")
            wsl.exe agictl open $lp } else {
          $out = if ($Output) { $Output } else { "$Path`_extracted" }
          python -c "import sys;sys.path.insert(0,'$lib');from extract import extract_artifact;extract_artifact('$Path','$out')"
          Invoke-Item $out }
      } else { exit 1 }
  }
  "verify" { python -c "import sys;sys.path.insert(0,'$lib');from verify import verify_artifact;exit(0 if verify_artifact('$Path')else 1)" }
  "extract" {
      $out = if ($Output) { $Output } else { "$Path`_extracted" }
      python -c "import sys;sys.path.insert(0,'$lib');from extract import extract_artifact;extract_artifact('$Path','$out')"
      Write-Host "✓ $out"
  }
  "manifest" { python -c "import sys;sys.path.insert(0,'$lib');from manifest import view_manifest;view_manifest('$Path')" }
}
'@
$script | Out-File -FilePath "$BinDir\agictl.ps1" -Encoding UTF8

# Create agictl.cmd for double-click
@"
@echo off
setlocal
set "SD=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SD%agictl.ps1" %*
@endlocal
"@ | Out-File -FilePath "$BinDir\agictl.cmd" -Encoding ASCII

# Register extension
Write-Step "Registering .agi extension..."
$reg = @"
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\.agi]
@="ARKHE.agi"

[HKEY_CLASSES_ROOT\ARKHE.agi]
@="ARKHE OS Artifact"

[HKEY_CLASSES_ROOT\ARKHE.agi\shell\open\command]
@="\"$($BinDir.Replace('\','\\'))\\agictl.cmd\" open \"%1\""

[HKEY_CLASSES_ROOT\ARKHE.agi\shell\verify\command]
@="\"$($BinDir.Replace('\','\\'))\\agictl.cmd\" verify \"%1\""

[HKEY_CLASSES_ROOT\ARKHE.agi\shell\extract\command]
@="\"$($BinDir.Replace('\','\\'))\\agictl.cmd\" extract \"%1\" \"\`%1_extracted\`""
"@
$reg | Out-File -FilePath "$InstallPath\arkhe-agi.reg" -Encoding Unicode
Start-Process regedit.exe -ArgumentList "/s `"$InstallPath\arkhe-agi.reg`"" -Wait -WindowStyle Hidden

# Update PATH
if (-not $UserMode -and -not ($env:PATH -like "*$BinDir*")) {
    $newPath = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";$BinDir"
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
} elseif ($UserMode -and -not ($env:PATH -like "*$BinDir*")) {
    $newPath = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";$BinDir"
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
}
Write-Step "PATH updated"

# WSL2 bridge
if ($IncludeWSL2 -and (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    @"
@echo off
wsl.exe -d Ubuntu agictl %*
"@ | Out-File -FilePath "$BinDir\agictl-wsl.bat" -Encoding ASCII
    Write-Step "WSL2 bridge created"
}

Write-Host ""; Write-Step "Windows install complete!"
Write-Host "  • Double-click any .agi file"; Write-Host "  • Test: agictl --help"
