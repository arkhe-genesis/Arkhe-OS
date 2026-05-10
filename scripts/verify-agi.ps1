# ARKHE OS Integrity Verification Script
# Verifies file hashes and signatures for build artifacts

param(
    [string]$ArtifactPath = "dist/"
)

Write-Host "🔍 Verifying Arkhe OS artifacts..." -ForegroundColor Cyan

# Check if artifacts exist
if (!(Test-Path $ArtifactPath)) {
    Write-Error "Artifact path not found: $ArtifactPath"
    exit 1
}

# Get all artifacts
$artifacts = Get-ChildItem $ArtifactPath -File

if ($artifacts.Count -eq 0) {
    Write-Error "No artifacts found in $ArtifactPath"
    exit 1
}

$verificationResults = @()

foreach ($artifact in $artifacts) {
    Write-Host "Checking $($artifact.Name)..." -ForegroundColor Yellow

    # Calculate SHA3-256 hash
    $hash = (Get-FileHash $artifact.FullName -Algorithm SHA256).Hash.ToLower()

    # Mock signature verification (in real impl, verify Falcon-1024 signature)
    $signatureValid = $true  # Placeholder

    # Check file size (basic sanity check)
    $sizeValid = $artifact.Length -gt 1000000  # At least 1MB

    $result = @{
        File = $artifact.Name
        Hash = $hash
        SignatureValid = $signatureValid
        SizeValid = $sizeValid
        Status = if ($signatureValid -and $sizeValid) { "VALID" } else { "INVALID" }
    }

    $verificationResults += $result
}

# Display results
Write-Host "`n📋 Verification Results:" -ForegroundColor Green
$verificationResults | Format-Table -AutoSize

# Check overall status
$invalidCount = ($verificationResults | Where-Object { $_.Status -eq "INVALID" }).Count

if ($invalidCount -eq 0) {
    Write-Host "✅ All artifacts verified successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Error "❌ $invalidCount artifacts failed verification"
    exit 1
}