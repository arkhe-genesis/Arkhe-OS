<#
.SYNOPSIS
    Auditor de privacidade e segurança de dados Arkhe.
    Verifica conformidade com todos os pilares de proteção.
#>

function New-CanonicalSeal {
    param([string]$Data)

    $sha = [System.Security.Cryptography.SHA256]::Create()
    $hash = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Data))
    return [BitConverter]::ToString($hash).Replace('-', '').ToLower()
}

$results = @()

# 1. Verificar HSM
Write-Host "🔐 Verificando HSM..."
$hsm = Get-PnpDevice | Where-Object { $_.FriendlyName -match "Hardware Security Module" }
$results += @{test="HSM Present"; passed=($hsm -ne $null)}

# 2. Verificar PQC
Write-Host "🔷 Verificando PQC..."
$pqc = Get-ChildItem Cert:\LocalMachine\My | Where-Object { $_.SignatureAlgorithm.FriendlyName -match "Dilithium" }
$results += @{test="PQC Certificates"; passed=($pqc -ne $null)}

# 3. Verificar TemporalChain
Write-Host "🔗 Verificando TemporalChain..."
$tc = Invoke-RestMethod -Uri "http://temporal-chain.arkhe:8051/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
$results += @{test="TemporalChain Healthy"; passed=($tc.status -eq "ok")}

# 4. Verificar Differential Privacy
Write-Host "🛡️ Verificando Differential Privacy..."
$dp = Invoke-RestMethod -Uri "http://phi-bus.arkhe:8052/metrics/dp_budget" -TimeoutSec 5 -ErrorAction SilentlyContinue
$results += @{test="DP Budget Available"; passed=($dp.remaining_pct -gt 50)}

# 5. Verificar Guardian PEP
Write-Host "🛡️ Verificando Guardian..."
$guard = Invoke-RestMethod -Uri "http://guardian.arkhe:8050/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
$results += @{test="Guardian Active"; passed=($guard.status -eq "ok")}

# 6. Verificar mTLS
Write-Host "🔒 Verificando mTLS..."
$mtls = Test-NetConnection -ComputerName "qbus-sidecar.arkhe" -Port 50051 -InformationLevel Quiet
$results += @{test="mTLS Port Open"; passed=$mtls}

# Relatório final
$passed = ($results | Where-Object { $_.passed }).Count
$total = $results.Count
$phi_c = [math]::Round($passed / $total, 6)

Write-Host "`n📊 Relatório de Privacidade e Segurança"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
foreach ($r in $results) {
    $icon = if ($r.passed) { "✅" } else { "❌" }
    Write-Host "$icon $($r.test)"
}
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "🌀 Φ_C de Privacidade: $phi_c"
Write-Host "🔐 Selo de Auditoria: $(New-CanonicalSeal -Data ($results | ConvertTo-Json -Compress))"
