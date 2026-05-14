# Register-ArkheEventLog.ps1
New-EventLog -LogName "ArkheOS" -Source "ArkheRuntime", "ArkheGovernance", "ArkheMesh", "ArkheFS"

# Escrever evento de governança
Write-EventLog -LogName "ArkheOS" -Source "ArkheGovernance" `
    -EventId 1001 -EntryType Information `
    -Message "Spiral Ping concluído. Φ_C Global: 0.9993. π Global: 0.0018."

Write-Host "✅ Event Log ArkheOS registrado" -ForegroundColor Green
Write-Host "   Para visualizar: Get-EventLog -LogName ArkheOS -Newest 50"
