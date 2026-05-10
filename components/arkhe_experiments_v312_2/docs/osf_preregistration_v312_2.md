# OSF Pre-registration Template: ARKHE Track 1

## Study Information
- **Title**: Testing mass-dependent collapse in a toroidal quantum crystal array: A pre-registered experimental protocol
- **Principal Investigator**: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
- **Institution**: [A ser preenchido]
- **Funding**: [A ser preenchido]
- **Pre-registration date**: [Data de submissão no OSF]
- **OSF link**: https://osf.io/[ID]/

## Hypotheses

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

## Methods
*(Consulte a versão completa do protocolo para os detalhes completos)*
- **Hardware**: Mini-Merkabah, Array de cristais de quartzo, FPGA Kintex-7, Si5341 PLL, White Rabbit, SNSPD.
- **Experimental Protocol**: Calibração, monitoramento, execução de N ∈ {16, 24, 32, 48, 64, 96} com 15 réplicas por N. Controle térmico, magnético e de clock.

## Analysis Plan

### Modelos Estatísticos Pré-especificados

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

## Data Management
- OSF: https://osf.io/xxxxx/ (pré-registro + dados após embargo)
- Zenodo: DOI para versão arquivada dos dados processados
- GitHub: https://github.com/raf-oliveira/arkhe-track1-analysis (código de análise)

## Ethics and Transparency
- Integridade científica: Nenhum p-hacking, HARKing. Análises seguem protocolo pré-registrado.
- Transparência de dados: Dados brutos disponíveis após embargo de 6 meses.
- Autoria e crédito: Autoria baseada em contribuição intelectual substantiva.
- Conflitos de interesse: Declaração pública de financiamento.

## Timeline and Resources
- Semana 1-2: Preparação final do hardware
- Semana 3: Caracterização criogênica
- Semana 4-6: Execução experimental principal
- Semana 7: Réplicas de validação
- Semana 8-9: Análise estatística
- Semana 10: Redação e submissão
- **Total Estimado do Projeto**: ~$231,500 USD

## Change Log
| Date | Change | Reason | Approved by |
|------|--------|--------|------------|
| [Data] | [Descrição] | [Justificativa] | [Nome] |

## Signatures
- PI: Rafael Oliveira ___________________ Date: _________
- Statistician: ________________________ Date: _________
- Ethics Officer: ______________________ Date: _________
