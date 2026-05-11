#!/usr/bin/env python3
"""
track1_fluid_mass_dependence.py
Testa se 'tempo de colapso' (convergência da projeção de pressão)
escala com 'massa efetiva' do campo fluido.
"""
import numpy as np
from scipy.optimize import curve_fit
from scipy import stats

# Mocks
def initialize_fluid_superposition(N, coherence_target=0.3):
    return np.random.randn(N, N, 2)

def run_pressure_projection_until_convergence(velocity_field, tolerance=1e-4, max_iterations=1000):
    N = velocity_field.shape[0]
    M = N**2
    a = 150.0
    b = 2.0
    tau = a / np.sqrt(M) + b + np.random.normal(0, 0.2)
    return max(0.1, tau)

def test_fluid_mass_collapse(grid_sizes=[16, 32, 64, 128], n_trials=50):
    """
    Hipótese Orch‑OR fluídica: tempo de convergência da projeção τ ∝ 1/√N
    Hipótese convencional: τ ≈ constante (depende apenas de viscosidade numérica)
    """
    results = []

    for N in grid_sizes:
        collapse_times = []

        for trial in range(n_trials):
            # Inicializar campo fluido com superposição parcial
            velocity_field = initialize_fluid_superposition(N, coherence_target=0.3)

            # Executar loop de projeção até convergência (∇·v < ε)
            t_collapse = run_pressure_projection_until_convergence(
                velocity_field,
                tolerance=1e-4,
                max_iterations=1000
            )

            if t_collapse is not None:
                collapse_times.append(t_collapse)

        if len(collapse_times) >= 10:
            results.append({
                'grid_size': N,
                'effective_mass': N**2,  # 'Massa' ∝ número de graus de liberdade
                'mean_tau': np.mean(collapse_times),
                'std_tau': np.std(collapse_times)
            })

    # Ajustar modelo τ = a/√M + b onde M = N²
    def model(M, a, b):
        return a / np.sqrt(M) + b

    M_vals = np.array([r['effective_mass'] for r in results])
    tau_vals = np.array([r['mean_tau'] for r in results])

    popt, pcov = curve_fit(model, M_vals, tau_vals)
    a_fit, b_fit = popt
    t_stat = a_fit / np.sqrt(pcov[0,0]) if pcov[0,0] > 0 else 0
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=len(results)-2))

    return {
        'fit_parameters': {'a': float(a_fit), 'b': float(b_fit)},
        't_statistic': float(t_stat),
        'p_value_mass_dependence': float(p_value),
        'interpretation': 'evidence for Orch-OR scaling' if p_value < 0.01 else 'no evidence'
    }
