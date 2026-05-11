# 📋🔬 ARKHE OS v∞.312.2 — PROTOCOLO EXPERIMENTAL REAL: TRACK 1 MINI-MERKABAH + PRÉ-REGISTRO OSF

**Autor**: Rafael Oliveira
**ORCID**: [0009-0005-2697-4668](https://orcid.org/0009-0005-2697-4668)
**Data**: 2026-01-XX
**Versão do Protocolo**: 1.0
**Status**: Pré-registrado em [OSF](https://osf.io/) (pendente de submissão)

> *"Um protocolo experimental não é apenas um plano — é um contrato com a natureza: definimos o que mediremos, como mediremos, e como interpretaremos, antes de ver os dados. A integridade científica nasce desta humildade metodológica."*

---

## 📑 ÍNDICE

1. [Resumo Executivo](#1-resumo-executivo)
2. [Hipóteses e Predições](#2-hipóteses-e-predições)
3. [Especificações de Hardware: Mini-Merkabah](#3-especificações-de-hardware-mini-merkabah)
4. [Protocolo Experimental: Track 1](#4-protocolo-experimental-track-1)
5. [Controle Ambiental e Mitigação de Ruído](#5-controle-ambiental-e-mitigação-de-ruído)
6. [Plano de Análise Estatística](#6-plano-de-análise-estatística)
7. [Critérios de Sucesso e Decisão](#7-critérios-de-sucesso-e-decisão)
8. [Cronograma e Recursos](#8-cronograma-e-recursos)
9. [Ética, Transparência e Reprodutibilidade](#9-ética-transparência-e-reprodutibilidade)
10. [Anexos Técnicos](#10-anexos-técnicos)

---

## 1. RESUMO EXECUTIVO

### 1.1 Objetivo Científico
Testar a predição da **hipótese Orch-OR fluídica** de que o tempo de colapso de coerência (τ) em um array de cristais quânticos escala com a "massa efetiva" do sistema (M = N², onde N = número de graus de liberdade) segundo:

```
τ = a/√M + b   com a > 0   (Predição Orch-OR)
```

versus a hipótese nula convencional de que τ é independente de M (decoerência ambiental dominante).

### 1.2 Contexto Teórico
- **Orch-OR (Penrose-Hameroff)**: Propõe que o colapso da função de onda é um processo gravitacional objetivo com tempo τ ≈ ℏ/ΔE
- **ARKHE OS v∞.312.1**: Estabelece isomorfismo formal entre Orch-OR e dinâmica de fluidos incompressíveis em toro T²
- **Predição operacional**: Em um sistema com topologia toroidal, o tempo de convergência da projeção de pressão (análogo ao colapso OR) deve escalar com 1/√M

### 1.3 Inovação Metodológica
Primeiro teste experimental direto da predição de massa-dependência do colapso quântico em sistema de matéria condensada com topologia controlada, combinando:
- Array de cristais piezoelétricos com controle individual de fase
- Sincronização temporal White Rabbit PTP (<1 ns jitter)
- Detecção SNSPD com eficiência >85% e jitter <50 ps
- Análise estatística Bayesiana com correção para múltiplas comparações

---

## 2. HIPÓTESES E PREDIÇÕES

### 2.1 Hipótese Primária (H₁)
```
H₁: O tempo de colapso τ escala com a massa efetiva M segundo τ = a/√M + b, com a > 0.
```

**Predições quantitativas**:
- Para M ∈ [256, 16384] (N ∈ [16, 128]), τ deve variar de ~8s a ~2s
- O parâmetro 'a' deve ser estatisticamente diferente de zero (p < 0.01, teste t unilateral)
- O modelo Orch-OR deve ter AIC pelo menos 2 unidades menor que o modelo nulo

### 2.2 Hipótese Nula (H₀)
```
H₀: O tempo de colapso τ é independente da massa efetiva M (τ ≈ constante).
```

**Predições quantitativas**:
- τ deve permanecer dentro de ±15% do valor médio para todos os valores de M testados
- O parâmetro 'a' não deve ser estatisticamente diferente de zero (p > 0.05)
- O modelo nulo deve ter AIC menor ou equivalente ao modelo Orch-OR

### 2.3 Hipóteses Secundárias (Exploratórias)
```
H₂: A coerência final r_final > 0.95 para todos os valores de M testados.
H₃: O jitter total do sistema (WR + térmico + eletrônico) < 2.0 ns RMS.
H₄: A taxa de decoerência efetiva < 1%/s a T = 2.5 K.
```

---

## 3. ESPECIFICAÇÕES DE HARDWARE: MINI-MERKABAH

### 3.1 Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    MINI-MERKABAH v1.0                       │
├─────────────────────────────────────────────────────────────┤
│  [Array de Cristais]                                        │
│  • Tipo: Cristais piezoelétricos de quartzo (SiO₂)          │
│  • Configurações: 16×16, 24×24, 32×32, 48×48, 64×64, 96×96  │
│  • Topologia: Toro T² com condições de contorno periódicas  │
│  • Acoplamento: Kuramoto com κ = φ⁻¹ ≈ 0.618                │
│                                                             │
│  [Controle de Fase]                                         │
│  • FPGA: Xilinx Kintex-7 XC7K325T                           │
│  • Clock: Si5341 PLL disciplinado por White Rabbit PTP      │
│  • Jitter alvo: < 0.58 ns RMS                               │
│  • Resolução de fase: 12-bit DAC, 0.087°/step              │
│                                                             │
│  [Detecção]                                                 │
│  • SNSPD Array: 256 canais, eficiência >85%                │
│  • Jitter de detecção: < 35 ps                              │
│  • Taxa de contagem escura: < 15 Hz/canal                   │
│  • Tempo morto: < 10 ns                                     │
│                                                             │
│  [Criostato]                                                │
│  • Temperatura: 2.5 K ± 0.1 K (He-3)                        │
│  • Estabilidade: < 10 mK/hour                               │
│  • Blindagem magnética: Mu-metal + supercondutor           │
│                                                             │
│  [Sincronização Federada]                                   │
│  • White Rabbit PTP: jitter < 1 ns, deriva < 0.1 ns/min    │
│  • Nós federados: 8 unidades, distância 1.72 m             │
│  • Acoplamento: modos de winding em T²                     │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Especificações Detalhadas por Componente

#### 3.2.1 Cristais Piezoelétricos
| Parâmetro | Especificação | Justificativa |
|-----------|--------------|---------------|
| Material | Quartzo α (SiO₂) de grau óptico | Baixa perda mecânica, alta Q |
| Dimensões | 2×2×0.5 mm³ | Compatível com array denso |
| Frequência de ressonância | 32.768 kHz ± 5% | Sincronização com fingerprint 0.58 |
| Fator de qualidade Q | > 10⁶ a 2.5 K | Minimiza decoerência intrínseca |
| Acoplamento piezoelétrico | kₜ² > 0.1% | Controle eficiente de fase |
| Tolerância de fabricação | ±10 μm | Garante uniformidade do array |

#### 3.2.2 Sistema de Controle (FPGA + PLL)
| Parâmetro | Especificação | Justificativa |
|-----------|--------------|---------------|
| FPGA | Xilinx Kintex-7 XC7K325T | DSP slices suficientes para Kuramoto em tempo real |
| Clock source | Si5341 PLL + OCXO disciplinado | Jitter < 0.5 ns, holdover < 1 ns/24h |
| White Rabbit | Seven Solutions WR-SPS | Sincronização sub-ns entre nós federados |
| DAC de fase | 12-bit, 1 MSPS | Resolução 0.087°/step, atualização 1 kHz |
| Latência de controle | < 10 μs | Compatível com loop Kuramoto a 20 Hz |

#### 3.2.3 Sistema de Detecção (SNSPD)
| Parâmetro | Especificação | Justificativa |
|-----------|--------------|---------------|
| Tipo | NbN nanowire SNSPD | Alta eficiência, baixo jitter |
| Eficiência de detecção | > 85% a 1550 nm | Maximiza sinal útil |
| Jitter temporal | < 35 ps RMS | Resolução temporal para correlações |
| Taxa de contagem escura | < 15 Hz/canal a 2.5 K | Minimiza ruído de fundo |
| Tempo morto | < 10 ns | Alta taxa de contagem possível |
| Comprimento de onda | 1550 nm | Compatível com fibra óptica padrão |

#### 3.2.4 Criostato e Controle Térmico
| Parâmetro | Especificação | Justificativa |
|-----------|--------------|---------------|
| Temperatura base | 2.5 K ± 0.1 K | Minimiza decoerência térmica |
| Estabilidade temporal | < 10 mK/hour | Evita deriva de fase sistemática |
| Tempo de resfriamento | < 4 horas de 300K a 2.5K | Praticidade experimental |
| Blindagem magnética | Mu-metal + Pb supercondutor | Minimiza acoplamento a campos externos |
| Acesso óptico | Janelas de safira AR-coated | Permite detecção SNSPD sem degradação térmica |

### 3.3 Diagrama de Conexões

```
[OCXO + GNSS] → [Si5341 PLL] → [FPGA Kintex-7] → [DACs de fase] → [Array de Cristais]
                      ↓
[White Rabbit PTP] ←→ [WR Switch] ←→ [Nós Federados 1-8]
                      ↓
[SNSPD Array] → [TDC FPGA] → [Aquisição de Dados] → [Storage + Análise]
                      ↓
[Criostato He-3] → [Controlador de Temperatura] → [Monitoramento em Tempo Real]
```

---

## 4. PROTOCOLO EXPERIMENTAL: TRACK 1

### 4.1 Preparação Pré-Experimental

#### 4.1.1 Calibração Inicial (Dia 1-2)
```bash
# 1. Calibração de fase individual por cristal
for crystal_id in $(seq 1 256); do
    apply_test_pulse --crystal $crystal_id --amplitude 0.5V --duration 1ms
    measure_phase_response --crystal $crystal_id --integration 100ms
    store_calibration --crystal $crystal_id --output calib/crystal_${crystal_id}.json
done

# 2. Caracterização de jitter do sistema
measure_system_jitter --duration 1hour --sample_rate 1kHz \
    --output calibration/system_jitter_baseline.json

# 3. Verificação de sincronização White Rabbit
wr_ptp_verify --nodes 8 --duration 30min \
    --output calibration/wr_sync_verification.json
```

#### 4.1.2 Validação de Controle Ambiental (Dia 3)
```bash
# Monitorar estabilidade térmica durante 24h
monitor_cryostat --duration 24h --sample_interval 1min \
    --output calibration/thermal_stability_24h.json

# Verificar blindagem magnética
measure_magnetic_field --locations 16 --duration 1h \
    --output calibration/magnetic_shielding_verification.json
```

### 4.2 Execução do Experimento Principal

#### 4.2.1 Loop Experimental por Valor de N
Para cada configuração de grid N ∈ {16, 24, 32, 48, 64, 96}:

```python
# Pseudocódigo do loop experimental
def run_trial_for_N(N, trial_id, seed=42+trial_id):
    """Executa um trial completo para grid de tamanho N."""

    # 1. Inicializar sistema
    initialize_merkabah(grid_size=N, seed=seed)
    wait_for_thermal_equilibrium(timeout=300)  # 5 min

    # 2. Preparar estado inicial de superposição parcial
    phases = initialize_partial_coherence(target_r=0.3, seed=seed)
    apply_phases_to_array(phases)

    # 3. Iniciar medição de tempo de colapso
    t_start = get_system_time()
    divergence_initial = measure_rms_divergence()

    # 4. Executar loop de projeção até convergência
    max_steps = 10000  # ~500s máximo
    for step in range(max_steps):
        # Aplicar passo de Kuramoto + projeção espectral
        kuramoto_step(dt=0.05)
        spectral_projection()

        # Medir divergência RMS
        div_rms = measure_rms_divergence()

        # Critério de convergência: 99% redução da divergência inicial
        if div_rms < divergence_initial * 0.01:
            t_collapse = get_system_time() - t_start
            break
    else:
        # Timeout: registrar como não-convergente
        t_collapse = None

    # 5. Registrar métricas finais
    final_coherence = measure_order_parameter()
    final_divergence = measure_rms_divergence()

    # 6. Salvar dados brutos
    save_trial_data({
        'N': N, 'trial_id': trial_id, 'seed': seed,
        't_collapse': t_collapse,
        'final_coherence': final_coherence,
        'final_divergence': final_divergence,
        'raw_timeseries': get_full_timeseries()  # Opcional, grande volume
    })

    return t_collapse, final_coherence
```

#### 4.2.2 Esquema de Randomização e Blinding
```
• Randomização da ordem de execução dos valores de N:
  - Usar seed criptográfico derivado de hash de timestamp + ORCID do pesquisador
  - Ordem gerada antes do início do experimento, registrada no log de auditoria

• Blinding da análise:
  - Dados brutos codificados com hash irreversível até análise final
  - Analista estatístico recebe apenas dados anonimizados (N_masked, tau_masked)
  - Desblinding ocorre apenas após confirmação de que análise seguiu protocolo pré-registrado

• Controles de qualidade em tempo real:
  - Monitorar jitter do sistema a cada 10 trials; pausar se > 2 ns RMS
  - Verificar estabilidade térmica contínua; alertar se deriva > 20 mK/hour
  - Validar sincronização WR a cada hora; re-sincronizar se offset > 0.5 ns
```

#### 4.2.3 Número de Réplicas e Poder Estatístico
```
• Réplicas por valor de N: n = 15 trials
• Valores de N testados: 6 (16, 24, 32, 48, 64, 96)
• Total de trials: 6 × 15 = 90 trials principais

• Cálculo de poder estatístico (pré-experimental):
  - Efeito esperado: a = 1.0 s·√M (baseado em simulações v∞.311)
  - Variabilidade esperada: σ_τ = 0.3 s (baseado em caracterização preliminar)
  - Nível de significância: α = 0.01 (unilateral, teste t para a > 0)
  - Poder calculado: 1 - β = 0.94 para detectar a > 0

• Réplicas de validação:
  - 3 trials adicionais por N para verificação de reprodutibilidade
  - Executados após análise primária, com seed diferente
```

### 4.3 Coleta e Armazenamento de Dados

#### 4.3.1 Estrutura de Dados Brutos
```
data/raw/
├── calibration/
│   ├── crystal_calibrations/     # 256 arquivos JSON por cristal
│   ├── system_jitter_baseline.json
│   ├── wr_sync_verification.json
│   ├── thermal_stability_24h.json
│   └── magnetic_shielding_verification.json
├── trials/
│   ├── N_16/
│   │   ├── trial_001_seed_42.json
│   │   ├── trial_002_seed_43.json
│   │   └── ... (15 arquivos)
│   ├── N_24/
│   │   └── ... (15 arquivos)
│   └── ... (para todos os N)
├── metadata/
│   ├── experiment_log.txt        # Log cronológico de eventos
│   ├── system_state_snapshots/   # Snapshots de estado do sistema a cada trial
│   └── audit_trail.json          # Registro de todas as operações para reprodutibilidade
└── processed/
    └── (gerado automaticamente durante análise)
```

#### 4.3.2 Formato de Arquivo de Trial
```json
{
  "metadata": {
    "experiment_id": "arkhe_track1_v1.0",
    "trial_id": 1,
    "N": 16,
    "seed": 42,
    "timestamp_start": "2026-01-XXT10:30:00Z",
    "timestamp_end": "2026-01-XXT10:35:23Z",
    "operator": "Rafael Oliveira",
    "orcid": "0009-0005-2697-4668"
  },
  "system_state": {
    "temperature_K": 2.51,
    "wr_offset_ns": 0.23,
    "system_jitter_ns": 0.58,
    "magnetic_field_uT": 0.12
  },
  "results": {
    "t_collapse_s": 7.82,
    "final_coherence": 0.987,
    "final_divergence_rms": 1.2e-5,
    "steps_to_convergence": 156
  },
  "timeseries_summary": {
    "sampling_rate_hz": 20,
    "n_points": 391,
    "coherence_mean": 0.85,
    "coherence_std": 0.12,
    "divergence_decay_constant_s": 2.3
  },
  "quality_flags": {
    "thermal_stable": true,
    "wr_sync_valid": true,
    "no_anomalies": true,
    "manual_intervention": false
  }
}
```

---

## 5. CONTROLE AMBIENTAL E MITIGAÇÃO DE RUÍDO

### 5.1 Fontes de Ruído Identificadas e Estratégias de Mitigação

| Fonte de Ruído | Impacto Potencial | Estratégia de Mitigação | Critério de Aceitação |
|---------------|------------------|------------------------|---------------------|
| **Flutuação térmica** | Deriva de fase, decoerência acelerada | Criostato He-3 com controle PID, blindagem térmica multicamada | Estabilidade < 10 mK/hour, deriva < 0.1 K durante trial |
| **Jitter de clock** | Erro de sincronização, falsos colapsos | Si5341 PLL + OCXO + WR PTP, monitoramento em tempo real | Jitter RMS < 0.58 ns, offset WR < 0.5 ns |
| **Ruído eletromagnético** | Acoplamento espúrio, decoerência | Blindagem Mu-metal + Pb, filtros de linha, aterramento estrela | Campo magnético < 0.5 μT no volume experimental |
| **Vibração mecânica** | Modulação de fase, perda de coerência | Mesa óptica ativa, isolamento pneumático, operação noturna | Aceleração RMS < 10⁻⁶ g na banda 1-100 Hz |
| **Contagem escura SNSPD** | Falsos positivos de detecção | Resfriamento a 2.5 K, filtragem temporal, coincidência entre canais | Taxa escura < 15 Hz/canal, coincidência acidental < 0.1 Hz |
| **Crosstalk entre cristais** | Acoplamento não intencional, viés de medição | Projeto de array com isolamento acústico, calibração cruzada | Crosstalk medido < -30 dB entre canais adjacentes |

### 5.2 Protocolo de Monitoramento em Tempo Real

```python
# Pseudocódigo do monitor de qualidade experimental
class ExperimentalQualityMonitor:
    def __init__(self, thresholds):
        self.thresholds = thresholds  # Carregado de config/quality_thresholds.json
        self.alerts = []

    def check_trial_quality(self, trial_data):
        """Verifica qualidade de um trial completo."""
        issues = []

        # Verificar estabilidade térmica
        if trial_data['system_state']['temperature_K'] > 2.6:
            issues.append("TEMP_HIGH: T > 2.6 K")

        # Verificar sincronização WR
        if abs(trial_data['system_state']['wr_offset_ns']) > 0.5:
            issues.append("WR_OFFSET: offset > 0.5 ns")

        # Verificar jitter do sistema
        if trial_data['system_state']['system_jitter_ns'] > 1.0:
            issues.append("JITTER_HIGH: jitter > 1.0 ns")

        # Verificar campo magnético
        if trial_data['system_state']['magnetic_field_uT'] > 0.5:
            issues.append("MAG_FIELD_HIGH: B > 0.5 μT")

        # Verificar flags de qualidade
        if not trial_data['quality_flags']['thermal_stable']:
            issues.append("THERMAL_UNSTABLE")
        if not trial_data['quality_flags']['wr_sync_valid']:
            issues.append("WR_SYNC_INVALID")

        # Classificar trial
        if len(issues) == 0:
            quality = "PASS"
        elif len(issues) <= 1:
            quality = "WARNING"
        else:
            quality = "FAIL"

        return {
            'quality': quality,
            'issues': issues,
            'exclude_from_analysis': quality == "FAIL"
        }

    def generate_quality_report(self, all_trials):
        """Gera relatório agregado de qualidade experimental."""
        total = len(all_trials)
        passed = sum(1 for t in all_trials if self.check_trial_quality(t)['quality'] == "PASS")
        warnings = sum(1 for t in all_trials if self.check_trial_quality(t)['quality'] == "WARNING")
        failed = sum(1 for t in all_trials if self.check_trial_quality(t)['quality'] == "FAIL")

        return {
            'total_trials': total,
            'passed': passed,
            'warnings': warnings,
            'failed': failed,
            'pass_rate': passed / total,
            'recommendation': 'Proceed with analysis' if failed/total < 0.1 else 'Review failed trials'
        }
```

### 5.3 Procedimento de Recuperação de Falhas

```
Se um trial falhar nos critérios de qualidade:

1. Registrar falha no audit_trail.json com timestamp e causa identificada
2. Pausar experimento automaticamente se:
   • Falha térmica: aguardar re-estabilização (máx. 30 min)
   • Falha de sincronização WR: re-sincronizar e verificar offset
   • Falha de jitter: reiniciar PLL e re-caracterizar sistema
3. Re-executar trial com seed incrementado (para manter independência estatística)
4. Limitar re-execuções a 2 por configuração de N para evitar viés de seleção
5. Se falhas persistirem (>30% de trials falhos para um N):
   • Suspender experimento para investigação de causa raiz
   • Documentar investigação em relatório de incidente
   • Re-iniciar apenas após aprovação do comitê de integridade experimental
```

---

## 6. PLANO DE ANÁLISE ESTATÍSTICA

### 6.1 Pré-processamento de Dados

```python
# Pseudocódigo do pipeline de análise pré-registrado
def preprocess_trial_data(raw_trial):
    """Pré-processa dados brutos de um trial para análise."""

    # 1. Filtrar trials com qualidade "FAIL"
    quality = quality_monitor.check_trial_quality(raw_trial)
    if quality['exclude_from_analysis']:
        return None  # Excluir da análise primária

    # 2. Extrair métricas de interesse
    processed = {
        'N': raw_trial['metadata']['N'],
        'trial_id': raw_trial['metadata']['trial_id'],
        'M': raw_trial['metadata']['N'] ** 2,  # Massa efetiva
        'tau': raw_trial['results']['t_collapse_s'],
        'final_r': raw_trial['results']['final_coherence'],
        'final_div': raw_trial['results']['final_divergence_rms'],
        'seed': raw_trial['metadata']['seed']
    }

    # 3. Verificar valores ausentes ou inválidos
    if processed['tau'] is None or processed['tau'] > 500:  # Timeout
        processed['tau_censored'] = True
        processed['tau'] = 500  # Valor de censoramento para análise de sobrevivência
    else:
        processed['tau_censored'] = False

    return processed
```

### 6.2 Modelos Estatísticos Pré-especificados

#### Modelo Primário: Orch-OR Scaling
```
τᵢ = a / √Mᵢ + b + εᵢ,   εᵢ ~ N(0, σ²)

Parâmetros de interesse:
• a: coeficiente de scaling (predição: a > 0)
• b: offset assintótico (predição: b ≥ 0)
• σ: desvio padrão residual (estimado dos dados)

Método de estimação:
• Mínimos quadrados não lineares (scipy.optimize.curve_fit)
• Intervalos de confiança: perfil de verossimilhança ou bootstrap paramétrico (B=1000)
• Teste de hipótese para a: teste t unilateral H₀: a ≤ 0 vs H₁: a > 0
```

#### Modelo Nulo: Constante
```
τᵢ = c + εᵢ,   εᵢ ~ N(0, σ²)

Parâmetro de interesse:
• c: tempo de colapso constante (estimado como média ponderada)

Método de estimação:
• Média simples ou mínimos quadrados lineares
```

#### Critério de Seleção de Modelo
```
• AIC (Akaike Information Criterion):
  AIC = n·ln(RSS/n) + 2k
  onde n = número de observações, RSS = soma de quadrados dos resíduos, k = número de parâmetros

• Regra de decisão:
  - ΔAIC = AIC_null - AIC_OrchOR
  - ΔAIC > 2: evidência para Orch-OR
  - ΔAIC > 10: evidência forte para Orch-OR
  - ΔAIC < -2: evidência para modelo nulo
```

### 6.3 Análise Bayesiana Complementar

```python
# Especificação do modelo Bayesiano (PyMC)
import pymc as pm

def build_bayesian_model(processed_data):
    """Constrói modelo Bayesiano para inferência sobre parâmetros de scaling."""

    M = np.array([d['M'] for d in processed_data])
    tau = np.array([d['tau'] for d in processed_data])
    censored = np.array([d['tau_censored'] for d in processed_data])

    with pm.Model() as model:
        # Priors
        a = pm.HalfNormal('a', sigma=2.0)  # a > 0 por construção
        b = pm.Normal('b', mu=0, sigma=2.0)
        sigma = pm.HalfCauchy('sigma', beta=1.0)

        # Likelihood (com censoramento para trials com timeout)
        mu = a / pm.math.sqrt(M) + b
        tau_obs = pm.Normal('tau_obs', mu=mu, sigma=sigma,
                           observed=tau[~censored])
        # Para trials censurados: likelihood de sobrevivência
        if np.any(censored):
            tau_cens = pm.Normal('tau_cens', mu=mu[censored], sigma=sigma,
                               observed=tau[censored])
            # Ajustar para censoramento à direita (não implementado em detalhe aqui)

        # Amostragem
        trace = pm.sample(2000, tune=1000, target_accept=0.95,
                         return_inferencedata=True, cores=4)

    return trace, model
```

#### Critérios de Evidência Bayesiana
```
• Bayes Factor aproximado via BIC:
  BF ≈ exp((BIC_null - BIC_OrchOR)/2)

• Interpretação (Kass & Raftery, 1995):
  - BF < 1: evidência contra Orch-OR
  - 1 ≤ BF < 3: evidência não conclusiva
  - 3 ≤ BF < 20: evidência positiva
  - 20 ≤ BF < 150: evidência forte
  - BF ≥ 150: evidência muito forte

• Probabilidade posterior de a > 0:
  - P(a > 0 | dados) > 0.95: evidência para scaling positivo
  - P(a > 0 | dados) < 0.05: evidência contra scaling positivo
```

### 6.4 Análises de Sensibilidade e Robustez (Pré-especificadas)

```
1. Exclusão de outliers:
   • Definir outlier: |resíduo| > 3·σ estimado
   • Re-analisar com e sem outliers; reportar ambas as versões
   • Critério para exclusão: apenas se outlier associado a falha de qualidade documentada

2. Modelo alternativo: censoramento explícito
   • Usar modelo de sobrevivência (Weibull ou exponencial) para trials com timeout
   • Comparar resultados com análise de mínimos quadrados

3. Transformação de variáveis:
   • Testar modelo linearizado: τ·√M = a + b·√M
   • Verificar se resultados são robustos à parametrização

4. Efeitos de ordem temporal:
   • Incluir termo de drift temporal no modelo: τᵢ = a/√Mᵢ + b + γ·tᵢ + εᵢ
   • Testar se γ é estatisticamente diferente de zero

5. Validação cruzada leave-one-N-out:
   • Para cada valor de N, ajustar modelo aos demais N e prever τ para o N excluído
   • Calcular erro de predição médio como métrica de generalização
```

---

## 7. CRITÉRIOS DE SUCESSO E DECISÃO

### 7.1 Critérios Primários de Sucesso (para H₁)

| Critério | Limiar de Sucesso | Justificativa |
|----------|-----------------|--------------|
| **Significância estatística (frequentista)** | p-value para a > 0 < 0.01 (unilateral) | Controle rigoroso de erro Tipo I |
| **Evidência Bayesiana** | Bayes Factor > 10 a favor de Orch-OR | Evidência "forte" segundo convenção |
| **Ajuste do modelo** | R²(Orch-OR) > 0.70 e R²(Orch-OR) > R²(null) + 0.15 | Modelo explica variância substancial |
| **Consistência de parâmetros** | a > 0 com IC 95% excluindo zero | Efeito na direção predita com precisão |

### 7.2 Critérios Secundários de Qualidade Experimental

| Critério | Limiar de Aceitação | Ação se Não Atendido |
|----------|-------------------|---------------------|
| **Taxa de trials válidos** | ≥ 90% dos trials com qualidade "PASS" | Investigar causa de falhas; re-executar se necessário |
| **Estabilidade térmica** | Deriva < 0.1 K durante qualquer trial | Pausar experimento; recalibrar controle térmico |
| **Sincronização WR** | Offset < 0.5 ns em ≥ 95% das medições | Re-sincronizar; verificar hardware WR |
| **Reprodutibilidade intra-N** | CV(τ) < 20% dentro de cada configuração de N | Verificar fontes de variabilidade não controladas |

### 7.3 Matriz de Decisão Final

```
Cenário 1: Evidência forte para Orch-OR
• Condições: p < 0.01, BF > 10, R²(Orch-OR) > 0.70, a > 0 com IC excluindo zero
• Ação:
  - Reportar como evidência positiva para scaling de massa
  - Preparar manuscrito para submissão
  - Planejar replicação independente com protocolo idêntico

Cenário 2: Evidência inconclusiva
• Condições: 0.01 ≤ p < 0.05 OU 3 ≤ BF ≤ 10 OU R² marginal
• Ação:
  - Reportar como tendência não conclusiva
  - Identificar limitações do experimento atual
  - Propor refinamentos para estudo de follow-up (ex: maior n, controle adicional)

Cenário 3: Evidência contra Orch-OR
• Condições: p ≥ 0.05 E BF < 3 E R²(Orch-OR) ≈ R²(null)
• Ação:
  - Reportar como não suporte para predição de scaling
  - Discutir implicações para hipótese Orch-OR fluídica
  - Explorar modelos alternativos (ex: decoerência ambiental dominante)

Cenário 4: Falha experimental
• Condições: < 70% de trials válidos OU violação de critérios de qualidade
• Ação:
  - Suspender análise primária
  - Documentar falhas em relatório de incidente
  - Re-iniciar apenas após correção de causas raiz e aprovação ética
```

### 7.4 Plano de Divulgação de Resultados

```
Independente do desfecho:

1. Pré-print: Submeter a arXiv dentro de 30 dias após conclusão da análise
   • Incluir código completo, dados processados, e protocolo de análise
   • Link para repositório OSF com dados brutos (após embargo de 6 meses)

2. Submissão a revista:
   • Alvo: Physical Review Letters ou npj Quantum Information
   • Estrutura: Introdução, Métodos, Resultados, Discussão, Conclusão
   • Ênfase na transparência metodológica e reprodutibilidade

3. Repositório de dados:
   • OSF: https://osf.io/xxxxx/ (pré-registro + dados após embargo)
   • Zenodo: DOI para versão arquivada dos dados processados
   • GitHub: https://github.com/raf-oliveira/arkhe-track1-analysis (código de análise)

4. Comunicação pública:
   • Blog técnico: Explicar resultados em linguagem acessível
   • Mídia social: Thread no X/Twitter com principais achados
   • Colaboração: Oferecer dados para meta-análise com grupos independentes
```

---

## 8. CRONOGRAMA E RECURSOS

### 8.1 Cronograma Estimado (Semanas)

```
Semana 1-2: Preparação final do hardware
• Fabricação/validação de arrays de cristais para N = 16, 24, 32
• Integração de FPGA + PLL + SNSPD
• Testes de integração em temperatura ambiente

Semana 3: Caracterização criogênica
• Resfriamento inicial a 2.5 K
• Caracterização de jitter, sincronização WR, detecção SNSPD a 2.5 K
• Calibração final de fase por cristal

Semana 4-6: Execução experimental principal
• Execução dos 90 trials principais (6 valores de N × 15 réplicas)
• Monitoramento contínuo de qualidade
• Backup diário de dados brutos

Semana 7: Réplicas de validação
• Execução de 18 trials adicionais (6 N × 3 réplicas)
• Verificação de reprodutibilidade

Semana 8-9: Análise estatística
• Pré-processamento e controle de qualidade
• Ajuste de modelos frequentista e Bayesiano
• Análises de sensibilidade e robustez

Semana 10: Redação e submissão
• Redação do manuscrito
• Preparação de materiais suplementares
• Submissão a revista-alvo

Total estimado: 10 semanas (~2.5 meses)
```

### 8.2 Recursos Necessários

#### Hardware
| Item | Quantidade | Custo Estimado (USD) | Observações |
|------|-----------|---------------------|------------|
| Cristais de quartzo piezoelétricos | 9216 unidades (para todos os N) | $15,000 | Fabricação sob medida, grau óptico |
| FPGA Kintex-7 + placa de desenvolvimento | 1 conjunto | $8,000 | Reutilizável para futuros experimentos |
| Si5341 PLL + OCXO | 1 conjunto | $3,500 | Sincronização de alta precisão |
| White Rabbit switch + nós | 1 hub + 8 nós | $12,000 | Sincronização federada sub-ns |
| SNSPD array (256 canais) | 1 sistema | $45,000 | Detecção de fótons únicos criogênica |
| Criostato He-3 + controle | 1 sistema | $80,000 | Temperatura 2.5 K estável |
| Blindagem magnética + vibração | 1 conjunto | $10,000 | Isolamento de ruído ambiental |
| **Subtotal hardware** | | **~$173,500** | |

#### Software e Computação
| Item | Custo Estimado (USD) | Observações |
|------|---------------------|------------|
| Licenças de software (MATLAB, LabVIEW) | $5,000 | Opcional; alternativas open-source disponíveis |
| Computação para análise (servidor/GPU) | $3,000 | Para amostragem MCMC Bayesiana |
| Armazenamento de dados (10 TB RAID) | $2,000 | Para dados brutos + processados |
| **Subtotal software** | **~$10,000** | |

#### Pessoal e Operacional
| Item | Custo Estimado (USD) | Observações |
|------|---------------------|------------|
| Pesquisador principal (Rafael Oliveira) | $25,000 | 2.5 meses a tempo parcial |
| Técnico de laboratório | $15,000 | Suporte em fabricação e operação |
| Consultoria estatística | $5,000 | Revisão de plano de análise |
| Publicação (open access fees) | $3,000 | Para revista de alto impacto |
| **Subtotal operacional** | **~$48,000** | |

#### Total Estimado do Projeto: ~$231,500 USD

### 8.3 Fontes de Financiamento Potenciais
```
• Grants de agências de fomento:
  - FAPESP (Brasil): Auxílio à Pesquisa em Tecnologias Quânticas
  - CNPq (Brasil): Produtividade em Pesquisa
  - ERC (Europa): Starting Grant em Fundamentos Quânticos

• Parcerias industriais:
  - Empresas de hardware quântico (IQM, Rigetti, Quantinuum)
  - Fabricantes de instrumentação criogênica (Bluefors, Oxford Instruments)

• Crowdfunding científico:
  - Experiment.com ou similar para componentes de menor custo
  - Transparência total sobre uso de recursos
```

---

## 9. ÉTICA, TRANSPARÊNCIA E REPRODUTIBILIDADE

### 9.1 Compromissos Éticos

```
• Integridade científica:
  - Nenhum p-hacking, HARKing, ou seleção seletiva de resultados
  - Todas as análises seguem protocolo pré-registrado; desvios documentados e justificados

• Transparência de dados:
  - Dados brutos disponíveis após embargo de 6 meses (para proteção de propriedade intelectual inicial)
  - Dados processados e código de análise disponíveis imediatamente na publicação

• Autoria e crédito:
  - Autoria baseada em contribuição intelectual substantiva (critérios ICMJE)
  - Reconhecimento de técnicos, colaboradores e financiadores em seção de agradecimentos

• Conflitos de interesse:
  - Declaração pública de qualquer financiamento, consultoria, ou interesse financeiro relacionado
  - Compromisso de que resultados não serão suprimidos ou distorcidos por interesses externos
```

### 9.2 Plano de Reprodutibilidade

```
• Código:
  - Todo o código de controle experimental, aquisição de dados, e análise estatística em repositório Git público
  - Dockerfile ou environment.yml para recriação exata do ambiente de software
  - Testes unitários para funções críticas de análise

• Dados:
  - Estrutura de diretórios padronizada (BIDS-like para experimentos quânticos)
  - Metadados ricos em formato JSON-LD para interoperabilidade
  - DOI via Zenodo para versão arquivada dos dados

• Documentação:
  - README detalhado com instruções passo-a-passo para reprodução
  - Notebook Jupyter com análise completa, desde dados brutos até figuras finais
  - Vídeo tutorial (opcional) demonstrando execução do pipeline de análise

• Validação independente:
  - Oferecer conjunto de dados "desafio" para grupos independentes testarem suas próprias análises
  - Organizar workshop de reprodução pós-publicação (virtual ou presencial)
```

### 9.3 Gestão de Riscos e Contingências

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **Falha de fabricação de cristais** | Média | Alto | Encomendar lotes extras; qualificar fornecedor alternativo |
| **Instabilidade criogênica prolongada** | Baixa | Alto | Protocolo de recuperação rápida; monitoramento 24/7 |
| **Baixo poder estatístico (variabilidade maior que esperada)** | Média | Médio | Plano para aumentar n por N se CV > 25%; análise de poder pós-hoc |
| **Resultados inconclusivos** | Alta | Baixo | Valor científico de resultado nulo; publicação transparente |
| **Atraso na entrega de componentes** | Média | Médio | Cronograma com buffer de 2 semanas; múltiplos fornecedores |
| **Mudança de prioridades de financiamento** | Baixa | Alto | Diversificação de fontes; plano de escopo mínimo viável |

---

## 10. ANEXOS TÉCNICOS

### Anexo A: Diagramas Esquemáticos do Hardware
*(Incluir arquivos CAD/PDF separadamente no repositório OSF)*

### Anexo B: Scripts de Controle Experimental
```python
# Exemplo: script de inicialização do array para um trial
#!/usr/bin/env python3
"""
initialize_array.py — Inicializa array de cristais para trial com seed específico.
"""
import numpy as np
import json
from hardware_interface import MerkabahController

def initialize_for_trial(N, trial_id, seed, target_coherence=0.3):
    """Prepara array de tamanho N para trial com seed e coerência alvo."""

    # Instanciar controlador
    ctrl = MerkabahController(grid_size=N)

    # Gerar fases iniciais com coerência parcial
    np.random.seed(seed)
    sync_phase = 0.58 * np.pi
    dispersion = np.arccos(2 * target_coherence - 1)
    phases = np.random.vonmises(sync_phase, 1/dispersion, N*N) % (2*np.pi)

    # Aplicar fases ao hardware
    ctrl.apply_phases(phases)

    # Aguardar estabilização
    ctrl.wait_for_settling(timeout=30)  # 30 segundos máximo

    # Verificar estado inicial
    initial_r = ctrl.measure_order_parameter()
    initial_div = ctrl.measure_rms_divergence()

    return {
        'N': N,
        'trial_id': trial_id,
        'seed': seed,
        'initial_coherence': float(initial_r),
        'initial_divergence': float(initial_div),
        'ready_for_measurement': True
    }

if __name__ == '__main__':
    import sys
    N = int(sys.argv[1])
    trial_id = int(sys.argv[2])
    seed = int(sys.argv[3])

    result = initialize_for_trial(N, trial_id, seed)
    print(json.dumps(result, indent=2))
```

### Anexo C: Template de Registro de Trial no OSF
```markdown
# OSF Pre-registration Template: ARKHE Track 1

## Study Information
- **Title**: Testing mass-dependent collapse in a toroidal quantum crystal array: A pre-registered experimental protocol
- **Principal Investigator**: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
- **Institution**: [A ser preenchido]
- **Funding**: [A ser preenchido]
- **Pre-registration date**: [Data de submissão no OSF]
- **OSF link**: https://osf.io/[ID]/

## Hypotheses
[Colar Seção 2 deste documento]

## Methods
[Colar Seções 3-6 deste documento, com links para anexos]

## Analysis Plan
[Colar Seção 6 com ênfase em pré-especificação de modelos e critérios]

## Data Management
[Colar Seção 9.2 com detalhes de repositórios e DOIs]

## Ethics and Transparency
[Colar Seção 9.1]

## Timeline and Resources
[Colar Seção 8 com orçamento detalhado]

## Change Log
| Date | Change | Reason | Approved by |
|------|--------|--------|------------|
| [Data] | [Descrição] | [Justificativa] | [Nome] |

## Signatures
- PI: Rafael Oliveira ___________________ Date: _________
- Statistician: ________________________ Date: _________
- Ethics Officer: ______________________ Date: _________
```

### Anexo D: Checklist de Pré-submissão
```
[ ] Protocolo pré-registrado no OSF com DOI atribuído
[ ] Repositório GitHub criado com estrutura de diretórios padrão
[ ] Dockerfile/environment.yml testado para reprodutibilidade
[ ] Dados de caracterização preliminar anexados ao pré-registro
[ ] Aprovação ética institucional obtida (se aplicável)
[ ] Acordos de compartilhamento de dados com colaboradores assinados
[ ] Plano de comunicação pública preparado (blog, mídia social)
[ ] Backup de todos os arquivos críticos em pelo menos 2 locais físicos + cloud
```