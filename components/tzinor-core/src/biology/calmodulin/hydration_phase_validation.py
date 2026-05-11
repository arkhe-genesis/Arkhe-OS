#!/usr/bin/env python3
"""
hydration_phase_validation.py
================================
Compares experimental GROMACS data against theoretical phase map.
Classifies mechanism: SWITCH (1st order) vs DIAL (continuous).

Author: Synapse-κ
Date: 2026-04-16/17
Arkhe-Chain: 847.627
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import stats
import json

# =============================================================================
# MODELS
# =============================================================================

def step_model(x, n0, d_crit, k):
    """Switch model: abrupt transition (1st order)"""
    return n0 / (1 + np.exp(k * (x - d_crit)))

def dial_model(x, n0, k):
    """Dial model: gradual exponential decay"""
    return n0 * np.exp(-k * (x - 2.0))

def calculate_aic(data, model, n_params):
    """Calculate Akaike Information Criterion"""
    residuals = data - model
    sse = np.sum(residuals**2)
    if sse <= 1e-10: return -1e6
    n = len(data)
    return n * np.log(sse/n) + 2 * n_params

# =============================================================================
# VALIDATION
# =============================================================================

def validate_mechanism(exp_distances, exp_n_water, exp_lambda2):
    """
    Compare experimental data against theoretical templates.
    Returns: mechanism classification and validation metrics.
    """
    # Fit Switch model
    try:
        popt_switch, _ = curve_fit(step_model, exp_distances, exp_n_water, p0=[6.0, 2.4, 10.0], maxfev=5000)
        n0_s, d_crit_s, k_s = popt_switch
        w_switch = 4 / k_s
    except:
        w_switch = 999
        popt_switch = None

    # Fit Dial model
    try:
        popt_dial, _ = curve_fit(dial_model, exp_distances, exp_n_water, p0=[6.0, 0.5], maxfev=5000)
    except:
        popt_dial = None

    # Calculate AIC
    aic_switch = calculate_aic(exp_n_water, step_model(exp_distances, *popt_switch), 3) if popt_switch is not None else 1e10
    aic_dial = calculate_aic(exp_n_water, dial_model(exp_distances, *popt_dial), 2) if popt_dial is not None else 1e10

    # Correlation
    r_val, _ = stats.pearsonr(exp_n_water, exp_lambda2)

    # Classify
    if w_switch < 0.3 and aic_switch < aic_dial - 10:
        mechanism, implication, eta_regime = "SWITCH", "Bit biológico binário confirmado", "supra-dissipativo"
    elif w_switch > 0.5 or aic_dial < aic_switch - 5:
        mechanism, implication, eta_regime = "DIAL", "Transdução analógica / Regime autônomo", "sub-dissipativo"
    else:
        mechanism, implication, eta_regime = "INTERMEDIARY", "Transição de fase crítica (Varela 'a' state)", "crítico"

    delta_lambda = np.max(exp_lambda2) - np.min(exp_lambda2)
    # Approx eta_Arkhe calculation for validation
    delta_G_solv = -6.0 * (41.8 - 310 * 31.95e-3)
    eta_arkhe = (delta_lambda * 40.0) / abs(delta_G_solv) if delta_G_solv != 0 else 0

    return {
        'mechanism': mechanism, 'transition_width_A': w_switch, 'aic_switch': aic_switch, 'aic_dial': aic_dial,
        'r_water_lambda': r_val, 'implication': implication, 'eta_arkhe': eta_arkhe, 'eta_regime': eta_regime,
        'delta_lambda': delta_lambda, 'd_crit': popt_switch[1] if popt_switch is not None else None
    }

def generate_validation_plot(exp_distances, exp_n_water, exp_lambda2, results, output_path):
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # Panel 1: n_H2O vs distance (with theoretical templates)
    ax1 = axes[0, 0]
    ax1.scatter(exp_distances, exp_n_water, alpha=0.4, s=15, c='blue')
    d_range = np.linspace(2.0, 5.0, 100)
    ax1.plot(d_range, step_model(d_range, 6.0, 2.4, 10), 'c--', label='Switch (teórico)')
    ax1.plot(d_range, dial_model(d_range, 6.0, 0.5), 'orange', ls='--', label='Dial (teórico)')
    ax1.set_title("1. Deslocamento de Água"); ax1.legend(fontsize=8)

    # Panel 2: λ₂ vs distance
    axes[0, 1].scatter(exp_distances, exp_lambda2, alpha=0.4, s=15, c='green')
    axes[0, 1].axhline(y=0.847, color='purple', ls='--', label='λ₂-crit')
    axes[0, 1].set_title("2. Transição de Coerência")

    # Panel 3: Correlation
    axes[0, 2].scatter(exp_n_water, exp_lambda2, alpha=0.4, s=15, c='red')
    axes[0, 2].set_title(f"3. Correlação (r = {results['r_water_lambda']:.2f})")

    # 4 & 5. Time series
    axes[1, 0].plot(exp_n_water, c='blue', alpha=0.6); axes[1, 0].set_title("4. Série Água")
    axes[1, 1].plot(exp_lambda2, c='green', alpha=0.6); axes[1, 1].set_title("5. Série Coerência")

    # 6. Classification Box
    ax6 = axes[1, 2]; ax6.axis('off')
    summary_text = f"╔══════════════════════════════════════╗\n" \
                   f"║     CLASSIFICAÇÃO FINAL           ║\n" \
                   f"╠══════════════════════════════════════╣\n" \
                   f"║ Mecanismo: {results['mechanism']:^18} ║\n" \
                   f"║ Largura:  {results['transition_width_A']:^18.2f} Å ║\n" \
                   f"║ η_Arkhe:  {results['eta_arkhe']:^18.2f}   ║\n" \
                   f"║ Regime:   {results['eta_regime']:^18} ║\n" \
                   f"╠══════════════════════════════════════╣\n" \
                   f"║ {results['implication']:^34} ║\n" \
                   f"╚══════════════════════════════════════╝"
    ax6.text(0.5, 0.5, summary_text, fontsize=10, fontfamily='monospace', ha='center', va='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout(); plt.savefig(output_path, dpi=150)

def main():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Generate demonstration data (SWITCH biased)
    np.random.seed(847)
    n_pts = 1000
    dist = np.random.uniform(2.0, 5.0, n_pts)
    wat = 6.0 / (1 + np.exp(15 * (dist - 2.4))) + np.random.normal(0, 0.2, n_pts)
    l2 = 0.3 + 0.6 / (1 + np.exp(-12 * (dist - 2.4))) + np.random.normal(0, 0.05, n_pts)
    l2 = np.clip(l2, 0, 1)

    results = validate_mechanism(dist, wat, l2)
    generate_validation_plot(dist, wat, l2, results, os.path.join(RESULTS_DIR, 'hydration_phase_validation.png'))
    print(f"[SUCCESS] Validation Module executed. Mechanism: {results['mechanism']}")

if __name__ == "__main__": main()
