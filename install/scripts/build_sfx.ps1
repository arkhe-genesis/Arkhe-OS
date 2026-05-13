# Creates a self-extracting archive using 7z
param (
    [string]$SourceFolder = ".\dist",
    [string]$OutputFile = ".\arkhe_sfx.exe"
)

Write-Host "Packaging ARKHE OS into a self-extracting archive: $OutputFile"

# Use 7z to create the SFX. Requires 7z to be installed.
$7z_exe = "C:\Program Files\7-Zip\7z.exe"
if (Test-Path $7z_exe) {
    & $7z_exe a -sfx7z.sfx $OutputFile "$SourceFolder\*"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Successfully created self-extracting archive."
    } else {
        Write-Error "Failed to create archive."
    }
} else {
    Write-Error "7-Zip not found at $7z_exe. Please install 7-Zip."
}
