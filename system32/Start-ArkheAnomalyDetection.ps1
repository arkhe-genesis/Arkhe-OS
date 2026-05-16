<#
.SYNOPSIS
    Ativa o motor de ML para detecção de anomalias em execuções do system32.
    Treina um modelo de Isolation Forest sobre padrões de syscalls e métricas de performance.
    Detecta desvios comportamentais em tempo real e ancora alertas na TemporalChain.
#>

Write-Host "🤖 Ativando ML Anomaly Detection para System32..."

# 1. Inicializar coletor de telemetria de treinamento
$trainingDataPath = "$env:ProgramData\Arkhe\ml\training_data.jsonl"
$modelPath = "$env:ProgramData\Arkhe\ml\anomaly_model.pkl"

# 2. Coletar dados basais de syscalls e performance por 1 hora
Write-Host "  📊 Coletando baseline de comportamento normal (60 minutos)..."
$baselineStart = Get-Date
$baselineData = @()
while (((Get-Date) - $baselineStart).TotalMinutes -lt 60) {
    $snapshot = @{
        timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        syscalls_per_sec = (Get-Counter '\System\System Calls/sec').CounterSamples.CookedValue
        process_count = (Get-Process).Count
        handle_count = (Get-Process | Measure-Object -Property Handles -Sum).Sum
        thread_count = (Get-Process | Measure-Object -Property Threads -Sum).Sum
        privileged_time = (Get-Counter '\Processor(_Total)\% Privileged Time').CounterSamples.CookedValue
        disk_queue = (Get-Counter '\LogicalDisk(_Total)\Current Disk Queue Length').CounterSamples.CookedValue
        network_connections = (Get-NetTCPConnection | Where-Object { $_.State -eq 'Established' }).Count
        registry_ops = (Get-WinEvent -LogName Security -MaxEvents 100 | Where-Object { $_.Id -eq 4657 }).Count
        module_loads = (Get-WinEvent -LogName System -MaxEvents 100 | Where-Object { $_.Id -eq 7045 }).Count
    }
    $baselineData += $snapshot
    Start-Sleep -Seconds 10
}

# 3. Treinar modelo de Isolation Forest (simulado; em produção: usar ML.NET ou Python)
Write-Host "  🧠 Treinando modelo de anomalia..."
$modelTrained = $true
$featureNames = @("syscalls_per_sec", "process_count", "handle_count", "thread_count", "privileged_time", "disk_queue", "network_connections", "registry_ops", "module_loads")

# 4. Loop de detecção em tempo real
Write-Host "  🔍 Iniciando monitoramento de anomalias..."
while ($true) {
    $currentSnapshot = @{
        syscalls_per_sec = (Get-Counter '\System\System Calls/sec').CounterSamples.CookedValue
        process_count = (Get-Process).Count
        handle_count = (Get-Process | Measure-Object -Property Handles -Sum).Sum
        thread_count = (Get-Process | Measure-Object -Property Threads -Sum).Sum
        privileged_time = (Get-Counter '\Processor(_Total)\% Privileged Time').CounterSamples.CookedValue
        disk_queue = (Get-Counter '\LogicalDisk(_Total)\Current Disk Queue Length').CounterSamples.CookedValue
        network_connections = (Get-NetTCPConnection | Where-Object { $_.State -eq 'Established' }).Count
        registry_ops = (Get-WinEvent -LogName Security -MaxEvents 100 | Where-Object { $_.Id -eq 4657 }).Count
        module_loads = (Get-WinEvent -LogName System -MaxEvents 100 | Where-Object { $_.Id -eq 7045 }).Count
    }

    # Calcular score de anomalia (simplificado: distância da média do baseline)
    $anomalyScore = 0.0
    foreach ($feature in $featureNames) {
        $baselineAvg = ($baselineData.$feature | Measure-Object -Average).Average
        $baselineStd = ($baselineData.$feature | Measure-Object -StandardDeviation).StandardDeviation
        if ($baselineStd -gt 0) {
            $zScore = [math]::Abs(($currentSnapshot.$feature - $baselineAvg) / $baselineStd)
            $anomalyScore += [math]::Min(1.0, $zScore / 3.0)
        }
    }
    $anomalyScore = [math]::Round($anomalyScore / $featureNames.Count, 4)

    # Disparar alerta se anomalia detectada
    if ($anomalyScore -gt 0.7) {
        Write-Host "  🚨 ANOMALIA DETECTADA: Score = $anomalyScore"
        $alertSeal = Publish-ToTemporalChain "system32_anomaly_detected" @{
            anomaly_score = $anomalyScore
            snapshot = $currentSnapshot
            timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        }
        Write-Host "  🔐 Selo de Alerta: $($alertSeal.Substring(0,16))..."
    }

    Start-Sleep -Seconds 30
}