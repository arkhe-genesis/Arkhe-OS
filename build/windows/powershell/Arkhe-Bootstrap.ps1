<# ARKHE OS Bootstrap Installer #>
param([switch]$Uninstall)

$ARKHE_HOME = "$env:ProgramFiles\ARKHE OS"
$package = Join-Path $PSScriptRoot "arkhe-package.zip"

function Install-ARKHE {
    Write-Host "Installing ARKHE OS v6.1.0..." -ForegroundColor Cyan
    Expand-Archive -Path $package -DestinationPath $ARKHE_HOME -Force

    # Register services
    & "$ARKHE_HOME\bin\arkhed.exe" --install
    & "$ARKHE_HOME\bin\arkhe-ws.exe" --install

    # Add to PATH
    $envPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($envPath -notlike "*$ARKHE_HOME\bin*") {
        [Environment]::SetEnvironmentVariable("Path", "$envPath;$ARKHE_HOME\bin", "Machine")
    }
    Write-Host "ARKHE OS installed successfully." -ForegroundColor Green
}

function Uninstall-ARKHE {
    Write-Host "Removing ARKHE OS..." -ForegroundColor Yellow
    & "$ARKHE_HOME\bin\arkhed.exe" --uninstall
    Remove-Item -Recurse -Force $ARKHE_HOME
    Write-Host "Uninstalled." -ForegroundColor Green
}

if ($Uninstall) { Uninstall-ARKHE } else { Install-ARKHE }