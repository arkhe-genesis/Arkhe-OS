#!/usr/bin/env python3
"""
statistical_analysis.py - Pipeline de análise estatística para Track 1 (Orch-OR fluidic scaling)
"""

import numpy as np
import warnings
from quality_monitor import ExperimentalQualityMonitor

def preprocess_trial_data(raw_trial, quality_monitor):
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

def perform_frequentist_analysis(processed_data):
    """Executa modelo primário e nulo usando frequentist stats."""
    from scipy.optimize import curve_fit

    valid_data = [d for d in processed_data if not d['tau_censored']]
    M_vals = np.array([d['M'] for d in valid_data])
    tau_vals = np.array([d['tau'] for d in valid_data])

    if len(M_vals) < 5:
        return {"error": "Insufficient valid data points"}

    # Model 1: Orch-OR Scaling (tau = a/sqrt(M) + b)
    def orch_or_model(M, a, b):
        return a / np.sqrt(M) + b

    # Set boundaries: a > 0, b >= 0
    bounds = ([0.0, 0.0], [np.inf, np.inf])

    try:
        # Initial guess based on simulations
        p0 = [1.0, 0.5]

        # We need to make sure our M_vals have enough variance or the curve fit might fail
        # and we need to make sure values aren't exactly 0 or inf
        weights = np.ones_like(tau_vals)
        # Using minimum non-zero threshold for error/variance as memory suggests
        # to prevent divide by zero in curve fitting weights (if we used them)
        weights = np.maximum(weights, 1e-6)

        popt, pcov = curve_fit(orch_or_model, M_vals, tau_vals, p0=p0, bounds=bounds)
        a_opt, b_opt = popt
        a_err, b_err = np.sqrt(np.diag(pcov))

        # Calculate RSS and AIC for Orch-OR
        residuals_orch = tau_vals - orch_or_model(M_vals, a_opt, b_opt)
        rss_orch = np.sum(residuals_orch**2)
        n = len(M_vals)
        k_orch = 2
        aic_orch = n * np.log(rss_orch / n) + 2 * k_orch

    except Exception as e:
        warnings.warn(f"Orch-OR curve fit failed: {e}")
        a_opt, b_opt, a_err, b_err = 0, 0, 0, 0
        aic_orch = np.inf

    # Model 2: Null Model (tau = c)
    c_opt = np.mean(tau_vals)
    residuals_null = tau_vals - c_opt
    rss_null = np.sum(residuals_null**2)
    k_null = 1
    aic_null = n * np.log(rss_null / n) + 2 * k_null

    delta_aic = aic_null - aic_orch

    # Simplified P-value calculation for 'a' (using normal approx)
    from scipy.stats import norm
    if a_err > 0:
        z_score = a_opt / a_err
        p_value = 1.0 - norm.cdf(z_score) # 1-sided
    else:
        p_value = 1.0

    return {
        "n_samples": n,
        "orch_or": {
            "a": float(a_opt),
            "a_std_err": float(a_err),
            "b": float(b_opt),
            "aic": float(aic_orch)
        },
        "null_model": {
            "c": float(c_opt),
            "aic": float(aic_null)
        },
        "comparison": {
            "delta_aic": float(delta_aic),
            "evidence_for_orch_or": bool(delta_aic > 2),
            "strong_evidence_for_orch_or": bool(delta_aic > 10),
            "p_value_a_gt_0": float(p_value)
        }
    }

if __name__ == "__main__":
    import json

    # Generate some mock data simulating the Orch-OR prediction
    np.random.seed(42)
    N_values = [16, 24, 32, 48, 64, 96]
    mock_raw_data = []

    # a = 120, b = 0.5
    for N in N_values:
        M = N**2
        for t_id in range(15):
            true_tau = 120.0 / np.sqrt(M) + 0.5
            obs_tau = true_tau + np.random.normal(0, 0.2)

            mock_raw_data.append({
                "metadata": { "trial_id": t_id, "N": N, "seed": 42+t_id },
                "system_state": {
                    "temperature_K": 2.51,
                    "wr_offset_ns": 0.23,
                    "system_jitter_ns": 0.58,
                    "magnetic_field_uT": 0.12
                },
                "results": {
                    "t_collapse_s": obs_tau,
                    "final_coherence": 0.98,
                    "final_divergence_rms": 1e-5
                },
                "quality_flags": {
                    "thermal_stable": True, "wr_sync_valid": True
                }
            })

    monitor = ExperimentalQualityMonitor()
    processed_data = []
    for raw in mock_raw_data:
        p = preprocess_trial_data(raw, monitor)
        if p: processed_data.append(p)

    print(f"Processed {len(processed_data)} valid trials.")
    results = perform_frequentist_analysis(processed_data)
    print("Frequentist Analysis Results:")
    print(json.dumps(results, indent=2))
