# ==================================================
# SCRIPT: Benchmark.ps1
# DESCRIÇÃO: Executa o benchmark das primitivas COBIT
# ==================================================

$ModulePath = Join-Path $PSScriptRoot ".." "src" "Cathedral.Governance.Cobit.Calculus.psm1"
Write-Host "Importando módulo: $ModulePath" -ForegroundColor Gray
Import-Module $ModulePath

Write-Host "Iniciando Invoke-CobitCalculusBenchmark..." -ForegroundColor Indigo
$Results = Invoke-CobitCalculusBenchmark -Iterations 10 -QuantumMode

Write-Host "`nResultados do Benchmark:" -ForegroundColor Green
$Results.GetEnumerator() | ForEach-Object {
    $Name = $_.Name
    $Mean = $_.Value.Mean
    $StdDev = $_.Value.StdDev
    Write-Host "[$Name] Média: $Mean Ticks | Desvio Padrão: $StdDev"
}

Write-Host "`nExecutando teste de sanidade isolado..." -ForegroundColor Yellow
Test-CobitSanity -UpTo 15
