#!/usr/bin/env python3
"""
track1_gtzk_wrapper_optimized.py
Versão otimizada do wrapper Track 1 com constraints reduzidas.
"""
import numpy as np
from scipy.optimize import curve_fit
from scipy import stats
import json

def track1_gtzk_instruction_optimized(grid_sizes, tau_measurements, model_type='orch_or'):
    """
    Versão otimizada: reduz constraints via:
    1. Pré-computação pública de M_vals
    2. Agregação de checks via random linear combination
    3. Uso de restricted-set para resíduos (batch-friendly)
    """
    # 1. Pré-computar M_vals publicamente (remove constraints de computação)
    M_vals = np.array([N**2 for N in grid_sizes])  # Público, pré-computado

    # 2. Extrair estatísticas mínimas necessárias (reduz witness size)
    tau_means = np.array([t['mean_tau'] for t in tau_measurements])
    tau_stds = np.array([t['std_tau'] for t in tau_measurements])
    n_trials = np.array([t['n_trials'] for t in tau_measurements])

    # 3. Fit Orch-OR (mesmo algoritmo, mas com constraints otimizadas)
    def orch_or_model(M, a, b):
        return a / np.sqrt(M) + b

    try:
        popt, pcov = curve_fit(orch_or_model, M_vals, tau_means,
                              sigma=tau_stds, absolute_sigma=True, maxfev=10000)
        a_fit, b_fit = popt

        # Calcular R² com fórmula otimizada (evita loops)
        ss_res = np.sum(((tau_means - orch_or_model(M_vals, *popt)) / tau_stds)**2)
        ss_tot = np.sum(((tau_means - np.mean(tau_means)) / tau_stds)**2)
        r2 = max(0, 1 - ss_res / ss_tot)

        # AIC/BIC com fórmula vetorial (remove loops)
        n = len(M_vals)
        aic = n * np.log(ss_res / n) + 4  # 2 params × 2
        bic = n * np.log(ss_res / n) + 2 * np.log(n)
        bayes_factor = np.exp((bic - aic) / 2)  # Aproximação

        # t-test simplificado
        se_a = np.sqrt(pcov[0, 0])
        t_stat = a_fit / se_a if se_a > 0 else 0
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-2))

    except:
        a_fit, b_fit, r2, aic, bayes_factor, p_value = 0, 0, 0, 0, 1, 1

    # 4. Constraints otimizadas (agregadas via random linear combination)
    # Em vez de 5 constraints separadas, usar 1 constraint agregada:
    # γ₁·(r²_calc - r²) + γ₂·(BF_calc - BF) + ... = 0
    constraints = [
        "aggregated_check: Σ γᵢ·(computedᵢ - publicᵢ) = 0  # via Schwartz-Zippel"
    ]

    # 5. Outputs públicos (minimizados)
    public_outputs = {
        'a_fit': float(a_fit),
        'r2': float(r2),
        'bayes_factor': float(bayes_factor),
        'p_value': float(p_value),
        'interpretation': 'evidence for Orch-OR' if a_fit > 0 and p_value < 0.01 else 'no evidence'
    }

    # 6. Witness privado (minimizado: apenas resíduos agregados)
    private_witness = {
        'aggregated_residual': float(np.mean((tau_means - orch_or_model(M_vals, a_fit, b_fit)) / tau_stds)),
        'checksum': hash(json.dumps(public_outputs, sort_keys=True)) % (2**32)
    }

    from track1_gtzk_wrapper import GTZKInstruction
    instruction = GTZKInstruction(
        name='track1_mass_scaling_opt',
        public_inputs={'grid_sizes': grid_sizes, 'n_points': len(grid_sizes)},
        private_witness=private_witness,
        constraints=constraints
    )

    return instruction, public_outputs
