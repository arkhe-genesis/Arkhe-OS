# Substrato 104: A Lente de Fourier — Especificação Formal

## P1: Método de Representação Explícito
- **Operador físico**: Lente como transformada de Fourier via fase quadrática: `U_out(x') ∝ ∫ U_in(x) exp(-i·2π·x·x'/λf) dx`
- **Discretização**: Amostragem espacial `Δx`, banda limitada por `NA = sin(θ_max)`, resolução `δx' ≈ λ/(2·NA)`
- **Representação computacional**: Matriz de propagação `F ∈ ℂ^{N×N}` com elementos `F_{jk} = exp(-i·2π·j·k/N)/√N`
- **Hashing**: SHA256(flatten(F, dtype='complex128')) para reprodutibilidade

## P2: Modelo de Discrepância Quantificado
- **Erro de discretização**: `ε_disc ≈ O((Δx)²)` para amostragem adequada do campo incidente
- **Erro de aproximação paraxial**: `ε_parax ≈ O(θ⁴)` para ângulos pequenos; generalização para alta-NA requer teoria vetorial
- **Critério de convergência**: `max(ε_disc, ε_parax, ε_detector) < 1e-3` para simulações de sensores unificados
- **Falsificabilidade**: Se resposta espectral predita diverge > 3σ de dados experimentais (óptico ou RF), o modelo é numericamente invalidado

## P3: Pipeline de Fases Completo
1. `PHASE_0: WAVE_INIT` → Definir campo incidente `U_in(x,y)` (escalar ou vetorial)
2. `PHASE_1: PHASE_MODULATION` → Aplicar fase quadrática da lente: `U_lens = U_in · exp(-i·k·(x²+y²)/(2f))`
3. `PHASE_2: PROPAGATION` → Propagação para plano focal via transformada de Fourier física ou numérica
4. `PHASE_3: DETECTOR_RESPONSE` → Convolver com função de resposta do detector (pixelização, ruído, eficiência quântica)
5. `PHASE_4: SPECTRAL_EXTRACTION` → Extrair observáveis: posição de pico (ângulo), largura espectral, coerência espacial
6. `PHASE_5: CROSS_BAND_VALIDATION` → Comparar predições para bandas óptica e RF com dados experimentais
7. `PHASE_6: UNIFICATION_METRIC` → Calcular métrica de unificação: similaridade entre respostas óptica/RF normalizadas

## P4: Reprodutibilidade Garantida
- **Seeds**: `np.random.seed(104)`, `torch.manual_seed(104)`
- **Precisão**: `mpmath.mp.dps = 50` para cálculos de fase em alta-NA
- **Grid**: `N_pixels = 1024×1024` (mínimo), `Δx = λ/(4·NA)` para amostragem adequada
- **Ambiente**: Python 3.11, PyTorch 2.1.0, mpmath 1.3.0, custom extensions para propagação vetorial
- **Output**: `results/fourier_lens_v402_run_<timestamp>.h5` com metadados completos

## P5: Convenções Físico-Matemáticas Claras
- **Unidades**: Comprimentos em metros, frequências em Hz, campos em unidades normalizadas
- **Mapeamento de observáveis**:
  - Posição no plano focal `x'` ↔ Ângulo de incidência `θ ≈ x'/f`
  - Largura espectral `Δλ` ↔ Resolução angular `Δθ ≈ λ/(D·cosθ)`
  - Coerência espacial ↔ Grau de polarização/uniformidade de fase
- **Normalização**: Campos normalizados por potência total: `∫|U|² dA = 1`
- **Condições de contorno**: Absorventes (PML) ou periódicas conforme geometria do sensor