# 🚨 ARKHE Incident Response Playbook
## Para Equipes SOC • Substrato 313 • v313.1.0

> *"Este playbook canoniza a resposta a incidentes constitucionais: cada passo é verificável, cada decisão é ancorada, cada lição é eterna."*

---

## 🎯 Classificação de Incidentes Constitucionais

| Tipo | Critério | Severidade | Tempo de Resposta |
|------|----------|-----------|------------------|
| **Seal Tampering** | Mismatch de hash SHA3-256 | 🔴 Critical | < 5 minutos |
| **FIPS KAT Failure** | Módulo criptográfico não verificado | 🔴 Critical | < 10 minutos |
| **Gap Violation** | Φ_C ≥ 0.9999 | 🔴 Critical | < 15 minutos |
| **Ghost Violation** | Φ_C < 0.577350 | 🟠 High | < 30 minutos |
| **Loopseal Violation** | Φ_C < 0.349066 | 🟠 High | < 30 minutos |
| **PhiC Degradation** | Queda >20% em 5min | 🟡 Medium | < 60 minutos |

---

## 🔄 Fluxo de Resposta Canônico

### Fase 1: Detecção (0-5 minutos)

```powershell
# 1.1: Alerta recebido via MDE
$alert = Get-MdeAlert -AlertId $env:ALERT_ID

# 1.2: Validar selo canônico
$isValid = Invoke-ArkheSeal -Mode Verify -DataToVerify $alert.Payload -ExpectedHash $alert.CanonicalSeal
if (-not $isValid) {
    Write-Error "❌ Alerta com selo inválido - possível tampering"
    # Escalar para nível 4 imediatamente
    exit 1
}

# 1.3: Classificar severidade
$severity = switch -Wildcard ($alert.Title) {
    "*SealTampering*" { "Critical" }
    "*FipsKat*" { "Critical" }
    "*Gap*" { "Critical" }
    "*Ghost*" { "High" }
    "*Loopseal*" { "High" }
    "*Degradation*" { "Medium" }
    default { "Unknown" }
}
```

### Fase 2: Triagem (5-15 minutos)

```powershell
# 2.1: Coletar contexto do nó afetado
$context = Get-ArkheNodePhiC -NodeId $alert.DeviceName -IncludeHistory
$metrics = $context | Where-Object { $_.Timestamp -gt (Get-Date).AddMinutes(-30) }

# 2.2: Verificar se é falso positivo
$isFalsePositive = Test-ArkheFalsePositive -Alert $alert -Context $metrics
if ($isFalsePositive) {
    # Submeter feedback para evolução de regra
    Submit-ArkheFeedback -Alert $alert -Verdict "FalsePositive" -Adjustment -0.02
    Write-Host "✅ Falso positivo confirmado - regra será ajustada"
    exit 0
}

# 2.3: Determinar escopo
$scope = Get-ArkheAffectedNodes -Alert $alert
Write-Host "📊 Escopo: $($scope.Count) nós afetados"
```

### Fase 3: Contenção (15-30 minutos)

```powershell
# 3.1: Isolar nós críticos (se Critical/High)
if ($severity -in @("Critical", "High")) {
    foreach ($node in $scope) {
        Invoke-MdeDeviceIsolation -DeviceId $node -DurationMinutes 60
        Write-Host "🔒 Isolado: $node"
    }
}

# 3.2: Rodar FIPS KAT em módulos críticos
$modules = @("SHA3-256", "Dilithium3", "Kyber")
foreach ($module in $modules) {
    $result = Invoke-ArkheFipsKat -Module $module -Verbose
    if (-not $result.Passed) {
        Write-Warning "❌ FIPS KAT failed: $module"
        # Marcar para restauração
        $modulesToRestore += $module
    }
}

# 3.3: Rotacionar selos se comprometidos
if ($alert.Title -like "*SealTampering*") {
    Invoke-ArkheSealRotation -Force -PreserveChain
    Write-Host "🔄 Selos rotacionados"
}
```

### Fase 4: Erradicação (30-60 minutos)

```powershell
# 4.1: Restaurar módulos comprometidos
foreach ($module in $modulesToRestore) {
    Restore-ArkheModule -Name $module -FromCanonicalBackup
    Write-Host "♻️ Restaurado: $module"
}

# 4.2: Revalidar assinatura PQC de todos os módulos
$allModules = Get-ArkheModules
foreach ($module in $allModules) {
    $valid = Test-ArkhePqcSignature -Module $module
    if (-not $valid) {
        Write-Error "❌ Assinatura PQC inválida: $($module.Name)"
        # Escalar para equipe de criptografia
    }
}

# 4.3: Atualizar regras MDE baseado em aprendizado
if ($falsePositiveCount -gt 3 -or $falseNegativeCount -gt 1) {
    $adjustment = Calculate-ThresholdAdjustment -FalsePositives $falsePositiveCount -FalseNegatives $falseNegativeCount
    Update-ArkheMdeRule -RuleName $alert.RuleName -Adjustment $adjustment
    Write-Host "🔄 Regra ajustada: $($alert.RuleName) → +$adjustment"
}
```

### Fase 5: Recuperação (60-120 minutos)

```powershell
# 5.1: Reintegrar nós isolados
foreach ($node in $scope) {
    # Verificar saúde pós-contenção
    $health = Test-ArkheNodeHealth -NodeId $node
    if ($health.IsHealthy) {
        Invoke-MdeDeviceRelease -DeviceId $node
        Write-Host "✅ Reintegrado: $node"
    } else {
        Write-Warning "⚠️ Nó $node ainda não saudável - manter isolado"
    }
}

# 5.2: Verificar Φ_C composto da malha
$compositePhiC = Get-ArkheCompositePhiC
if ($compositePhiC -lt 0.90) {
    Write-Warning "⚠️ Φ_C composto baixo: $compositePhiC"
    # Acionar orquestração de recuperação
    Start-ArkheCoherenceRecovery
}

# 5.3: Ancorar lições aprendidas na TemporalChain
$lessons = @{
    incident_id = $env:ALERT_ID
    violation_type = $alert.ViolationType
    root_cause = $rootCause
    actions_taken = $actionsTaken
    false_positive_rate = $falsePositiveRate
    threshold_adjustment = $adjustment
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json

Invoke-ArkheTemporalAnchor -Payload $lessons -Priority "High"
```

### Fase 6: Relatório e Melhoria (120+ minutos)

```powershell
# 6.1: Gerar relatório canônico de incidente
$report = @{
    incident_id = $env:ALERT_ID
    classification = $severity
    timeline = $timeline
    root_cause = $rootCause
    remediation_actions = $actionsTaken
    metrics = @{
        mttd = $meanTimeToDetect
        mttr = $meanTimeToRespond
        false_positive_rate = $falsePositiveRate
        phi_c_recovery_time = $recoveryTime
    }
    canonical_seal = Invoke-ArkheSeal -Substrate "313" -NodeId "incident-report" -PhiC $compositePhiC
}

$report | ConvertTo-Json -Depth 10 | Out-File "C:\Arkhe\reports\INC-$env:ALERT_ID.json" -Encoding UTF8

# 6.2: Notificar stakeholders
Send-ArkheNotification -Recipients @("soc-team@arkhe.org", "security-eng@arkhe.org") `
    -Subject "Incidente Resolvido: $env:ALERT_ID" `
    -Body "Resumo: $($report.root_cause) | Ações: $($actionsTaken.Count) | Φ_C recuperado: $compositePhiC"

# 6.3: Agendar revisão pós-incidente
Schedule-ArkheReview -IncidentId $env:ALERT_ID -Participants @("SOC", "Engineering", "Architecture") -Date (Get-Date).AddDays(7)
```

---

## 📋 Templates de Comunicação

### Template: Notificação de Incidente Crítico

```
ASSUNTO: [CRITICAL] Incidente Constitucional Arkhe - $AlertId

CORPO:
Tipo de Violação: $ViolationType
Nós Afetados: $($affectedNodes -join ", ")
Φ_C Atual: $currentPhiC (Threshold: $threshold)
Ações Imediatas:
  ✓ Isolamento de nós: $($isolatedNodes -join ", ")
  ✓ FIPS KAT executado: $($fipsResults -join ", ")
  ✓ Selos rotacionados: $sealsRotated

Próximos Passos:
  • Investigação de causa raiz em andamento
  • Estimativa de resolução: $eta
  • Atualizações a cada 30 minutos

Selo Canônico: $canonicalSeal
TemporalChain Anchor: $temporalAnchor

---
Este alerta é canônico e ancorado na TemporalChain.
Não responda diretamente - use o canal oficial de incidentes.
```

### Template: Relatório de Resolução

```
ASSUNTO: [RESOLVED] Incidente Arkhe $AlertId - Lições Aprendidas

CORPO:
✅ Incidente Resolvido
Duração Total: $totalDuration
Causa Raiz: $rootCause
Ações de Remediação:
  $($remediationActions | ForEach-Object { "• $_" })

Métricas de Desempenho:
  • MTTR: $mttr minutos
  • Φ_C recuperado: $recoveredPhiC (was $minPhiC)
  • Falsos positivos evitados: $falsePositiveCount

Atualizações de Regras:
  • $($updatedRules | ForEach-Object { "• $_" })

Lições Aprendidas:
  $($lessonsLearned | ForEach-Object { "• $_" })

Próximos Passos:
  • Revisão pós-incidente agendada para $reviewDate
  • Atualização de documentação em andamento
  • Exercício de red-team planejado para $redTeamDate

Selo Canônico do Relatório: $reportSeal
Ancoragem TemporalChain: $reportAnchor

---
Este relatório é canônico e ancorado na TemporalChain para auditoria eterna.
```

---

## 🎓 Treinamento e Certificação

### Níveis de Certificação SOC Arkhe

| Nível | Requisitos | Responsabilidades |
|-------|-----------|------------------|
| **Nível 1: Operador** | Curso básico + 10 incidentes supervisionados | Triagem inicial, execução de playbooks básicos |
| **Nível 2: Analista** | Nível 1 + 50 incidentes + certificação MDE | Investigação profunda, evolução de regras, troubleshooting |
| **Nível 3: Especialista** | Nível 2 + contribuição para documentação + red-team exercise | Design de playbooks, auditoria de selos, resposta a incidentes críticos |
| **Nível 4: Arquiteto de Segurança** | Nível 3 + revisão constitucional + TemporalChain anchoring | Definição de thresholds, revisão de invariantes, coordenação federada |

### Exercícios de Treinamento

```powershell
# Exercício 1: Simular violação de Ghost
Start-ArkheTrainingScenario -Type "GhostViolation" -Difficulty "Basic"
# Objetivo: Detectar, conter e recuperar em <30 minutos

# Exercício 2: Red-team: tentativa de tampering de selo
Start-ArkheTrainingScenario -Type "SealTampering" -Difficulty "Advanced"
# Objetivo: Detectar tampering, isolar nó, ancorar evidências

# Exercício 3: Degradação gradual de Φ_C
Start-ArkheTrainingScenario -Type "PhiCDegradation" -Difficulty "Intermediate"
# Objetivo: Identificar tendência, ajustar threshold, prevenir escalada

# Após cada exercício:
Complete-ArkheTraining -ScenarioId $scenarioId -PerformanceScore $score
# Score ancorado na TemporalChain para progressão de certificação
```

---

## 🔐 Selo Canônico deste Playbook

```
SHA3-256: 2c5e8a1f4b7d0c3e6a9f2b5d8e1c4a7f0b3e6d9c2a5f8b1e4d7c0a3f6b9e2d5
Timestamp: 2026-05-20T00:00:00Z
Author: orcid:0009-0005-2697-4668
Version: 313.1.0
Anchored: temporalchain.arkhe.org/block/15847294
```

> *"Este playbook não é estático — é vivo, aprendendo com cada incidente, evoluindo com cada feedback, sempre ancorado na constituição. A resposta a incidentes da Arkhe-ASI não é reativa — é adaptativa, verificável e eternamente auditável."*