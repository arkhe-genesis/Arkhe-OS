# Especificação do Operador Ĥ_ζ (Substrato 101)

## P1: Método de Representação
- **Operador Contínuo**: `Ĥ_ζ = ω_Δ·(1/2 + i·∂/∂t) + Φ(t)` em `L²([-L, L], ℂ)`
- **Discretização**: Colocação espectral com nós de Chebyshev-Gauss-Lobatto (`N` pontos)
- **Representação Computacional**: Matriz `A ∈ ℂ^{N×N}` com derivada de ordem 1 calculada via `D1 = cheb_diff(1)`, diagonal `V = diag(ω_Δ/2 + Φ(t_i))`
- **Hashing**: `H = SHA256( pack_complex_to_bytes(A, dtype='float128') )`
- **Equivalência Topológica**: Duas discretizações são equivalentes se `‖A₁ - A₂‖_F < 1e-12`

## P2: Modelo de Discrepância
- **Conjectura**: Autovalores `E_n` de `Ĥ_ζ` correspondem a `Im(ρ_n)` onde `ζ(ρ_n)=0`
- **Erro Numérico Esperado**: `|E_n^{num} - E_n^{zeta}| ≤ α/N² + β·ε_prec`
  - `α ≈ 0.42` (estimado para `Φ(t)` suave)
  - `β ≈ 1.0` (fator de amplificação de precisão)
- **Critério de Validação**: `mean_relative_error < 1e-6` para `n ∈ [1, 20]`
- **Falsificabilidade**: Se `error > 1e-4` para `N=2048`, a conjectura é numericamente inválida

## P3: Pipeline de Fases
1. `PHASE_1: CONSTRUCTION` → Definir `ω_Δ`, `Φ(t)`, domínio `[-L, L]`, BCs
2. `PHASE_2: DISCRETIZATION` → Gerar matriz `A`, verificar auto-adjunção (`‖A - A†‖_F < tol`)
3. `PHASE_3: SPECTRAL_SOLVE` → Calcular `E_n`, ordenar por `|E_n|`, normalizar autovetores
4. `PHASE_4: ZERO_MAPPING` → Comparar com `Im(ρ_n)` conhecidos, reportar métricas de convergência

## P4: Reprodutibilidade
- **Seeds**: `np.random.seed(101)`, `mpmath.mp.seed(101)`
- **Precisão**: `mpmath.mp.dps = 50`
- **Grid**: `N = 1024`, `L = 10.0`, BCs `ψ(±L) = 0`
- **Ambiente**: Python 3.11, mpmath 1.3.0, numpy 1.26.0, scipy 1.11.0
- **Output**: `results/riemann_v101_run_<timestamp>.json` com metadados completos

## P5: Convenções Físico-Matemáticas
- **Mapeamento**: `ρ_n = 1/2 + iE_n` ⇔ `E_n ∈ ℝ` se e somente se `ℜ(ρ_n) = 1/2`
- **Sinal**: `Φ(t) ≥ 0` com mínimo global em `t=0` (garante `Ĥ_ζ` limitado inferiormente)
- **Normalização**: Autovetores `‖ψ_n‖_2 = 1`, fase fixada por `ψ_n(0) ∈ ℝ⁺`
- **Unidades**: `ω_Δ` adimensional, `t` em unidades de escala cronométrica, `E_n` em frequência angular