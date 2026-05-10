#!/usr/bin/env python3
"""
track1_mass_dependence/analyze_mass_scaling.py
Analisa se tempo de sincronização τ escala com 1/√N (Orch‑OR) ou é constante (convencional).
"""
import numpy as np
from scipy.optimize import curve_fit
from scipy import stats
import json
from typing import List, Dict
import math
import sys
import os

def test_mass_dependence(n_values: List[int] = [16, 64, 256, 768],
                         n_trials: int = 100,
                         threshold: float = 0.95) -> Dict:
    """
    Testa predição de massa-dependência do tempo de colapso.

    Hipótese Orch‑OR: τ = a/√N + b (colapso gravitacional)
    Hipótese convencional: τ ≈ constante (decoerência ambiental)
    """
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from simulate_crystal_array import CrystalArraySimulator, CrystalArraySpec

    results = []

    for N in n_values:
        sync_times = []

        for trial in range(n_trials):
            spec = CrystalArraySpec(n_crystals=N)
            sim = CrystalArraySimulator(spec)
            result = sim.run_until_synchronization(threshold=threshold)

            if result['sync_time_s'] is not None:
                sync_times.append(result['sync_time_s'])

        if len(sync_times) >= 10:  # Mínimo para estatística
            results.append({
                'N': N,
                'mean_tau': float(np.mean(sync_times)),
                'std_tau': float(np.std(sync_times)),
                'n_success': len(sync_times),
                'n_trials': n_trials
            })

    if len(results) < 2:
        return {'error': 'Insufficient data for fitting'}

    # Ajustar modelo τ = a/√N + b
    def model(N, a, b):
        return a / np.sqrt(N) + b

    N_vals = np.array([r['N'] for r in results])
    tau_vals = np.array([r['mean_tau'] for r in results])
    tau_errs = np.array([max(r['std_tau'] / np.sqrt(r['n_success']), 1e-6) for r in results])

    try:
        popt, pcov = curve_fit(model, N_vals, tau_vals, sigma=tau_errs, absolute_sigma=True)
        a_fit, b_fit = popt
        a_err, b_err = np.sqrt(np.diag(pcov))

        # Teste t para parâmetro 'a' (deve ser ≠ 0 para Orch‑OR)
        t_stat_a = a_fit / a_err if a_err > 0 else 0
        p_value_a = 2 * (1 - stats.t.cdf(abs(t_stat_a), df=len(N_vals) - 2))

        # Bayes factor aproximado (BIC difference)
        # Modelo 1: τ = a/√N + b (2 parâmetros)
        # Modelo 0: τ = b (1 parâmetro, a=0)
        rss_full = np.sum(((tau_vals - model(N_vals, *popt)) / tau_errs) ** 2)
        rss_null = np.sum(((tau_vals - b_fit) / tau_errs) ** 2)
        n_data = len(N_vals)
        bic_full = n_data * np.log(rss_full / n_data) + 2 * 2
        bic_null = n_data * np.log(rss_null / n_data) + 2 * 1

        try:
            bayes_factor_approx = np.exp((bic_null - bic_full) / 2)
            if math.isnan(bayes_factor_approx) or math.isinf(bayes_factor_approx):
                bayes_factor_approx = 1.0
        except Exception:
            bayes_factor_approx = 1.0

        return {
            'fit_results': {
                'a': float(a_fit), 'a_err': float(a_err),
                'b': float(b_fit), 'b_err': float(b_err)
            },
            'frequentist_test': {
                't_stat_a': float(t_stat_a),
                'p_value_mass_dependence': float(p_value_a)
            },
            'bayesian_evidence': {
                'bayes_factor_approx': float(bayes_factor_approx),
                'interpretation': ('strong' if bayes_factor_approx > 100 else
                                  'moderate' if bayes_factor_approx > 10 else
                                  'weak' if bayes_factor_approx > 3 else 'none')
            },
            'raw_data': results
        }

    except Exception as e:
        return {'error': f'Fitting failed: {str(e)}', 'raw_data': results}
