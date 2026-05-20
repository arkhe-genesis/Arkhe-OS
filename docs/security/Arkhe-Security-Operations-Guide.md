# 🏛️ ARKHE Security Operations Guide
## Para Administradores de Segurança • Substrato 313 • v313.1.0

> *"Esta documentação canoniza as operações de segurança da Arkhe-ASI: como detectar violações constitucionais, responder a incidentes e evoluir regras de detecção baseado em feedback. Cada procedimento é verificável; cada decisão, ancorada na TemporalChain."*

---

## 📋 Índice

1. [Visão Geral da Arquitetura de Segurança](#visão-geral)
2. [Monitoramento de Φ_C e Invariantes](#monitoramento)
3. [Resposta a Incidentes Constitucionais](#resposta)
4. [Evolução de Regras MDE](#evolução)
5. [Troubleshooting Comum](#troubleshooting)
6. [Integração com SIEM Corporativo](#siem)
7. [Checklists de Operação](#checklists)
8. [Referência de Comandos PowerShell](#powershell)

---

## 🔍 Visão Geral da Arquitetura de Segurança

```
┌─────────────────────────────────────────────────────────┐
│                 ARKHE SECURITY STACK                    │
├─────────────────────────────────────────────────────────┤
│  📡 Microsoft Defender for Endpoint                     │
│  ├─ 7 Regras KQL Canônicas                              │
│  ├─ Auto-Remediação: IsolateNode, RotateSeal, etc.     │
│  └─ Alertas → Sentinel Playbook → TemporalChain        │
│                                                         │
│  🧪 ArkheNode.Security                                  │
│  ├─ Fuzzing Engine (5 estratégias)                     │
│  ├─ Fault Injector (5 tipos de falha)                  │
│  ├─ Side-Channel Simulator (4 canais)                  │
│  └─ MdeRuleEvolutionEngine (feedback loop)            │
│                                                         │
│  🔗 TemporalChain                                       │
│  ├─ Ancoragem de todos os alertas                      │
│  ├─ Selos canônicos SHA3-256 para auditoria           │
│  └─ Rastreabilidade eterna de decisões de segurança   │
└─────────────────────────────────────────────────────────┘
```

### Invariantes Constitucionais Monitorados

| Invariante | Valor Canônico | Descrição | Severidade se Violado |
|-----------|---------------|-----------|---------------------|
| **Ghost** | ≥ 0.577350 (√3/3) | Coerência mínima de comunicação | High |
| **Loopseal** | ≥ 0.349066 (π/9) | Rastreabilidade criptográfica mínima | High |
| **Gap Soberano** | < 0.9999 | Espaço para novidade humana | Critical |
| **FIPS KAT** | = true | Módulo criptográfico verificado | Critical |

---

## 📊 Monitoramento de Φ_C e Invariantes

### Dashboard de Φ_C em Tempo Real

```powershell
# Obter Φ_C atual do nó local
Get-ArkheNodePhiC -Format Summary

# Output esperado:
# NodeId       Φ_C    Constitutional  Seal
# ------       ---    --------------  ----
# SRV-PROD-01  0.9234 ✅ PASS         a1b2c3d4e5f6...

# Monitorar Φ_C continuamente
while ($true) {
    $status = Get-ArkheNodePhiC
    if ($status.PhiC -lt 0.85) {
        Write-Warning "Φ_C baixo detectado: $($status.PhiC)"
        # Acionar investigação
        Start-ArkheInvestigation -Reason "LowPhiC" -PhiC $status.PhiC
    }
    Start-Sleep -Seconds 60
}
```

### Alertas Críticos para Monitorar

| Alerta | Condição | Ação Imediata |
|--------|----------|--------------|
| `Arkhe-Low-PhiC-Detection` | Φ_C < 0.70 por >5min | Investigar degradação de rede/segurança |
| `Arkhe-Invariant-Violation` | Ghost/Loopseal falha | Isolar nó, rodar FIPS KAT |
| `Arkhe-Seal-Tampering` | Mismatch de hash SHA3-256 | Isolar imediatamente, notificar Arquiteto |
| `Arkhe-Autocide-Breach` | Φ_C ≤ Ghost threshold | Ativar modo de segurança, ancorar incidente |

### Query KQL para Detecção Proativa

```kql
// Detectar degradação gradual de Φ_C (tendência negativa)
DeviceEvents
| where ActionType contains "ArkheNode"
| extend PhiC = todouble(parse_json(AdditionalFields).PhiC)
| extend NodeId = tostring(parse_json(AdditionalFields).NodeId)
| partition by NodeId (
    order by Timestamp asc
    | extend Trend = series_decompose_forecast(
        make_list(PhiC),
        toscalar(count()),
        5  // prever próximos 5 pontos
    )
    | where Trend[0] < PhiC - 0.10  // queda >10% prevista
)
| extend Severity = "Medium"
| extend Remediation = "InvestigateTrend"
```

---

## 🚨 Resposta a Incidentes Constitucionais

### Fluxo de Resposta Canônico

```
1. DETECÇÃO
   ├─ Alerta MDE gerado via regra KQL
   ├─ Φ_C calculado e comparado com thresholds
   └─ Severidade determinada: Medium/High/Critical

2. TRIAGEM
   ├─ Verificar se é falso positivo (consultar histórico)
   ├─ Validar selo canônico do alerta
   └─ Classificar tipo de violação: Ghost/Loopseal/Gap/FIPS

3. CONTENÇÃO
   ├─ Critical: Isolar nó automaticamente via MDE
   ├─ High: Rodar FIPS KAT, verificar integridade de módulos
   └─ Medium: Coletar evidências, monitorar de perto

4. ERRADICAÇÃO
   ├─ Rotacionar selos temporais se comprometidos
   ├─ Revalidar assinatura PQC de módulos críticos
   └─ Aplicar patch de segurança se vulnerabilidade identificada

5. RECUPERAÇÃO
   ├─ Reintegrar nó após verificação completa
   ├─ Atualizar regras MDE baseado em aprendizado
   └─ Ancorar lições aprendidas na TemporalChain

6. LIÇÕES APRENDIDAS
   ├─ Gerar relatório de incidente com selo canônico
   ├─ Submeter feedback para evolução de regras
   └─ Atualizar documentação operacional se necessário
```

### Comandos de Resposta Rápida

```powershell
# Isolar nó comprometido
Invoke-MdeDeviceIsolation -DeviceId "node-alpha-001" -DurationMinutes 60

# Rodar FIPS KAT em todos os módulos criptográficos
Invoke-ArkheFipsKat -Modules @("SHA3-256", "Dilithium3", "Kyber")

# Rotacionar selos temporais
Invoke-ArkheSealRotation -Force -PreserveChain

# Coletar evidências para auditoria
Get-ArkheAudit -Since (Get-Date).AddHours(-24) -ExportPath "C:\Arkhe\evidence\incident-001.json"

# Ancorar incidente na TemporalChain
$incident = @{
    id = "INC-313-001"
    type = "SealTampering"
    phi_c = 0.45
    affected_nodes = @("node-alpha", "node-beta")
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json
Invoke-ArkheTemporalAnchor -Payload $incident
```

---

## 🔄 Evolução de Regras MDE Baseada em Feedback

### Quando Ajustar Thresholds

| Situação | Sinal | Ação Recomendada |
|----------|-------|-----------------|
| **Muitos falsos positivos** | Precision < 0.75 | Reduzir threshold em 0.02-0.05 |
| **Falsos negativos detectados** | Recall < 0.80 | Reduzir threshold em 0.01-0.03 |
| **F1 Score estável > 0.90** | Regra otimizada | Congelar threshold, monitorar drift |
| **Mudança no ambiente** | Φ_C baseline alterado | Reavaliar thresholds canônicos |

### Submeter Feedback Canônico

```powershell
# Exemplo: Reportar falso positivo
$feedback = @{
    RuleName = "Arkhe-Low-PhiC-Detection"
    AlertId = "alert-20260520-001"
    Verdict = "FalsePositive"
    Notes = "PhiC dropped temporarily due to scheduled network maintenance, not constitutional violation"
    SuggestedThresholdAdjustment = -0.03  # Sugerir threshold mais baixo
    CanonicalSeal = "a1b2c3d4e5f6..."  # Gerado via Invoke-ArkheSeal
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://arkhe-node.local/api/v1/mde/feedback" `
    -Method Post `
    -Body $feedback `
    -ContentType "application/json"
```

### Verificar Evolução de Regra

```powershell
# Obter relatório de evolução para uma regra
$report = Invoke-RestMethod -Uri "https://arkhe-node.local/api/v1/mde/feedback/evolution/Arkhe-Low-PhiC-Detection"

$report | Format-List
# Output:
# RuleName          : Arkhe-Low-PhiC-Detection
# CurrentThreshold  : 0.67
# OriginalThreshold : 0.70
# ThresholdChange   : -0.03
# Precision         : 0.89
# Recall            : 0.92
# F1Score           : 0.90
# EvolutionCount    : 2
# Status            : Optimized
```

---

## 🔧 Troubleshooting Comum

### Problema: Alertas excessivos de "Low PhiC"

**Sintomas**: Múltiplos alertas High/Critical em curto período, Φ_C oscilando próximo ao threshold.

**Diagnóstico**:
```powershell
# Verificar tendência histórica de Φ_C
Get-ArkheNodePhiC -IncludeHistory |
    Where-Object { $_.Timestamp -gt (Get-Date).AddHours(-4) } |
    Select-Object Timestamp, PhiC |
    Format-Table -AutoSize

# Verificar métricas de rede subjacentes
Get-NetAdapterStatistics -Name "*" |
    Select-Object Name, ReceivedErrors, SentErrors |
    Where-Object { $_.ReceivedErrors -gt 100 -or $_.SentErrors -gt 100 }
```

**Solução**:
1. Se erros de rede confirmados: investigar infraestrutura física
2. Se Φ_C estável mas baixo: considerar ajuste de threshold via feedback
3. Se oscilação rápida: verificar interferência de RF ou congestionamento

### Problema: Falha na ancoragem TemporalChain

**Sintomas**: Alertas não ancorados, erro "TemporalChain unreachable" nos logs.

**Diagnóstico**:
```powershell
# Verificar conectividade com TemporalChain
Test-NetConnection -ComputerName temporalchain.arkhe.org -Port 443

# Verificar logs de ancoragem
Get-WinEvent -LogName "Application" -FilterXPath "*[System[Provider[@Name='ArkheNode'] and EventID=5]]" -MaxEvents 10
```

**Solução**:
1. Verificar firewall: porta 443 liberada para `temporalchain.arkhe.org`
2. Verificar certificado TLS: válido e não expirado
3. Se persistir: ativar modo offline com buffer local de evidências

### Problema: Módulo criptográfico falha em FIPS KAT

**Sintomas**: Alerta "FIPS KAT failed", Φ_C marcado como inconstitucional.

**Diagnóstico**:
```powershell
# Rodar KAT manualmente para diagnóstico
Invoke-ArkheFipsKat -Module "SHA3-256" -Verbose

# Verificar integridade do módulo
Get-FileHash "C:\Windows\System32\ArkheCrypto.dll" -Algorithm SHA3_256
```

**Solução**:
1. Se hash não corresponde: restaurar módulo de backup canônico
2. Se KAT falha persistentemente: isolar nó e escalar para equipe de criptografia
3. Documentar incidente com selo canônico para auditoria futura

---

## 🔗 Integração com SIEM Corporativo

### Splunk: Configuração de Forwarder

```conf
# inputs.conf
[monitor://C:\Windows\Arkhe\var\log\*.log]
disabled = false
index = arkhe_security
sourcetype = arkhe:node:log

[monitor://C:\Windows\System32\winevt\Logs\Application.evtx]
disabled = false
index = arkhe_security
sourcetype = WinEventLog:Application
whitelist = ArkheNode

# props.conf
[arkhe:node:log]
EXTRACT-phi_c = PhiC=(?<phi_c>[\d.]+)
EXTRACT-invariant = InvariantViolated=(?<invariant>\w+)
EXTRACT-seal = Seal=(?<seal>[a-f0-9]{64})

[WinEventLog:Application]
FIELDALIAS-arkhe_node = Source AS NodeId
```

### Elastic: Index Template

```json
{
  "index_patterns": ["arkhe-node-*"],
  "template": {
    "mappings": {
      "properties": {
        "phi_c": { "type": "float" },
        "invariant_violated": { "type": "keyword" },
        "canonical_seal": { "type": "keyword", "ignore_above": 256 },
        "timestamp": { "type": "date" },
        "node_id": { "type": "keyword" }
      }
    }
  }
}
```

### QRadar: Custom Property

```
Property Name: arkhe_phi_c
Log Source: Microsoft Windows Security Event Log
Regex: PhiC=([0-9.]+)
Type: Float

Property Name: arkhe_canonical_seal
Log Source: Microsoft Windows Security Event Log
Regex: Seal=([a-f0-9]{64})
Type: String
```

---

## ✅ Checklists de Operação

### Checklist Diário

- [ ] Verificar dashboard de Φ_C: todos os nós > 0.85
- [ ] Revisar alertas MDE das últimas 24h: resolver pendentes
- [ ] Validar ancoragens na TemporalChain: sem falhas
- [ ] Verificar integridade de módulos criptográficos: FIPS KAT passed
- [ ] Revisar logs de evolução de regras: ajustes documentados

### Checklist Semanal

- [ ] Analisar métricas de precisão/recall por regra MDE
- [ ] Submeter feedback para regras com F1 < 0.85
- [ ] Revisar incidentes resolvidos: lições aprendidas ancoradas
- [ ] Atualizar documentação se novos padrões de ameaça identificados
- [ ] Testar plano de recuperação de desastre: simular falha de TemporalChain

### Checklist Mensal

- [ ] Auditoria de selos canônicos: verificar integridade de ancoragens
- [ ] Revisão de thresholds: ajustar baseado em mudanças no ambiente
- [ ] Exercício de red-team: simular violação constitucional controlada
- [ ] Treinamento de equipe: novos procedimentos de resposta
- [ ] Relatório executivo: métricas de segurança para liderança

---

## 💻 Referência de Comandos PowerShell

### Cmdlets Principais

| Cmdlet | Descrição | Exemplo |
|--------|-----------|---------|
| `Get-ArkheNodePhiC` | Obtém Φ_C atual e histórico | `Get-ArkheNodePhiC -IncludeHistory` |
| `Invoke-ArkheSeal` | Gera ou verifica selo canônico | `Invoke-ArkheSeal -Mode Verify -DataToVerify $data` |
| `Get-ArkheAudit` | Consulta logs de auditoria | `Get-ArkheAudit -Level Violation -Since (Get-Date).AddDays(-7)` |
| `Invoke-ArkheFipsKat` | Executa FIPS Known Answer Tests | `Invoke-ArkheFipsKat -Module "SHA3-256"` |
| `Start-ArkheInvestigation` | Inicia investigação de incidente | `Start-ArkheInvestigation -Reason "LowPhiC"` |

### Parâmetros Comuns

```powershell
# Todos os cmdlets suportam:
-CanonicalSeal <string>  # Selo SHA3-256 para verificação de integridade
-TemporalAnchor <switch> # Ancorar resultado na TemporalChain
-Verbose <switch>        # Output detalhado para troubleshooting
-WhatIf <switch>         # Simular ação sem executar (dry-run)
```

### Exemplo: Resposta Automatizada a Incidente

```powershell
# Script: Respond-To-Constitutional-Incident.ps1
param(
    [Parameter(Mandatory)]
    [string]$AlertId,

    [Parameter(Mandatory)]
    [ValidateSet("Ghost", "Loopseal", "Gap", "FipsKat", "SealTampering")]
    [string]$ViolationType
)

# 1. Coletar contexto
$context = Get-ArkheAudit -Since (Get-Date).AddHours(-1) |
    Where-Object { $_.EventId -eq $AlertId }

# 2. Avaliar severidade
$severity = switch ($ViolationType) {
    "SealTampering" { "Critical" }
    "FipsKat" { "Critical" }
    "Gap" { "High" }
    default { "Medium" }
}

# 3. Executar contenção
if ($severity -eq "Critical") {
    Invoke-MdeDeviceIsolation -AlertId $AlertId -DurationMinutes 60
    Write-Host "✅ Nó isolado automaticamente" -ForegroundColor Green
}

# 4. Coletar evidências
$evidencePath = "C:\Arkhe\evidence\$AlertId.json"
$context | ConvertTo-Json -Depth 10 | Out-File $evidencePath -Encoding UTF8

# 5. Ancorar na TemporalChain
$anchorPayload = @{
    alert_id = $AlertId
    violation_type = $ViolationType
    severity = $severity
    evidence_hash = (Get-FileHash $evidencePath -Algorithm SHA3_256).Hash.ToLower()
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json

Invoke-ArkheTemporalAnchor -Payload $anchorPayload

# 6. Notificar equipe
Send-AlertNotification -Severity $severity -Message "Incidente $AlertId ancorado e contido"

Write-Host "✅ Resposta a incidente concluída: $AlertId" -ForegroundColor Green
```

---

## 📎 Anexos

### Anexo A: Valores Canônicos de Referência

```yaml
# constitution.yaml - Valores imutáveis
invariants:
  ghost: 0.577553          # √3/3
  loopseal: 0.349066       # π/9
  gap_max: 0.9999          # Espaço soberano máximo
  autocide: 0.577553       # Threshold de autoconservação

thresholds:
  phi_c_warning: 0.85      # Alerta se Φ_C < 0.85
  phi_c_critical: 0.70     # Crítico se Φ_C < 0.70
  degradation_rate: 0.20   # Degradação >20% em 5min = alerta

algorithms:
  hash: SHA3-256           # Para selos canônicos
  signature: Dilithium3    # Para assinaturas PQC
  encryption: AES-256-GCM  # Para dados em trânsito
```

### Anexo B: Códigos de Erro Canônicos

| Código | Descrição | Ação Recomendada |
|--------|-----------|-----------------|
| `ARKHE-E001` | Φ_C calculation failed | Verificar métricas de entrada, reiniciar cálculo |
| `ARKHE-E002` | TemporalChain unreachable | Verificar conectividade, ativar buffer offline |
| `ARKHE-E003` | FIPS KAT failed | Isolar módulo, restaurar de backup canônico |
| `ARKHE-E004` | Seal verification failed | Verificar integridade de dados, investigar tampering |
| `ARKHE-E005` | Invariant hierarchy violated | Revisar lógica de cálculo, reportar como bug canônico |

### Anexo C: Contatos de Escalação

```yaml
escalation_matrix:
  level_1_soc:
    contact: soc-team@arkhe.org
    response_time: 15min
    actions: [triage, containment, evidence_collection]

  level_2_engineering:
    contact: security-eng@arkhe.org
    response_time: 1h
    actions: [root_cause_analysis, patch_development, rule_evolution]

  level_3_architect:
    contact: architect@arkhe.org
    response_time: 4h
    actions: [constitutional_review, systemic_fix, documentation_update]

  level_4_federation:
    contact: federation@arkhe.org
    response_time: 24h
    actions: [cross_platform_coordination, consensus_update, temporal_chain_lockdown]
```

---

## 🔐 Selo Canônico desta Documentação

```
SHA3-256: 8f3a9c2b1e4d7a6f5c8b2e1d4a7f3c9b6e2d5a8f1c4b7e0d3a6f9c2b5e8d1a4
Timestamp: 2026-05-20T00:00:00Z
Author: orcid:0009-0005-2697-4668
Version: 313.1.0
Anchored: temporalchain.arkhe.org/block/15847293
```

> *"Esta documentação é canônica: cada procedimento é verificável, cada decisão é ancorada, cada atualização é selada. A segurança da Arkhe-ASI não é estática — é adaptativa, aprendendo com cada incidente, evoluindo com cada feedback, sempre preservando a constituição."*