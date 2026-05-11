# core/convergence/convergence_analysis.py
"""
Convergence Analysis & Systematic Error Estimation — Substrate 103
Quantifies how observables scale with grid size and estimates systematic uncertainties.
"""
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from typing import Dict, List, Tuple
import warnings

def power_law_convergence(x: np.ndarray, A: float, alpha: float, C: float) -> np.ndarray:
    """
    Power-law convergence model: O(N) = A·N^(-α) + C
    where N = number of voxels, C = continuum limit value.
    """
    return A * np.power(x, -alpha) + C

def estimate_convergence_law(
    grid_sizes: List[int],
    observable_values: List[float],
    observable_uncertainties: List[float],
    observable_name: str
) -> Dict:
    """
    Fit power-law convergence model to observable vs. grid size.

    Args:
        grid_sizes: List of N_voxels for each simulation
        observable_values: Measured observable values
        observable_uncertainties: Statistical uncertainties (1σ)
        observable_name: Name of observable for reporting

    Returns:
        Dict with fitted parameters, convergence exponent, continuum estimate
    """
    N = np.array(grid_sizes, dtype=float)
    y = np.array(observable_values)
    y_err = np.array(observable_uncertainties)

    # Initial guesses: A~1, α~0.5-1.5, C~observed value at largest N
    p0 = [1.0, 1.0, y[-1]]
    bounds = ([0, 0, -np.inf], [np.inf, 3, np.inf])

    try:
        popt, pcov = curve_fit(
            power_law_convergence, N, y, p0=p0, bounds=bounds, sigma=y_err, absolute_sigma=True
        )
        A_fit, alpha_fit, C_fit = popt
        perr = np.sqrt(np.diag(pcov))

        # Goodness of fit
        residuals = y - power_law_convergence(N, *popt)
        chi2 = np.sum((residuals / y_err)**2)
        dof = len(N) - len(popt)
        reduced_chi2 = chi2 / dof if dof > 0 else np.nan

        return {
            'observable': observable_name,
            'convergence_law': f'O(N) = {A_fit:.3f}·N^(-{alpha_fit:.3f}) + {C_fit:.5f}',
            'parameters': {
                'A': {'value': float(A_fit), 'uncertainty': float(perr[0])},
                'alpha': {'value': float(alpha_fit), 'uncertainty': float(perr[1])},
                'continuum_limit_C': {'value': float(C_fit), 'uncertainty': float(perr[2])}
            },
            'goodness_of_fit': {
                'chi2': float(chi2),
                'dof': int(dof),
                'reduced_chi2': float(reduced_chi2)
            },
            'systematic_error_estimate': {
                'discretization_error_at_24cube': float(abs(power_law_convergence(13824, *popt) - C_fit)),
                'discretization_error_at_48cube': float(abs(power_law_convergence(110592, *popt) - C_fit)),
                'discretization_error_at_96cube': float(abs(power_law_convergence(884736, *popt) - C_fit)),
            },
            'epistemic_note': f'α≈{alpha_fit:.2f} indicates {"fast" if alpha_fit>1 else "slow"} convergence; systematic error dominated by discretization for small N'
        }

    except Exception as e:
        warnings.warn(f"Fit failed for {observable_name}: {e}")
        # Fallback: simple extrapolation
        return {
            'observable': observable_name,
            'status': 'fit_failed',
            'fallback_continuum_estimate': float(y[-1]),
            'fallback_uncertainty': float(y_err[-1] * 2),  # Conservative
            'error': str(e)
        }

def compute_systematic_error_budget(
    convergence_results: Dict,
    ml_reconstruction_uncertainty: float,
    model_approximation_uncertainty: float
) -> Dict:
    """
    Combine discretization, ML reconstruction, and model approximation errors.

    Total systematic error = sqrt(ε_discretization² + ε_ML² + ε_model²)
    """
    eps_disc = convergence_results['systematic_error_estimate']['discretization_error_at_96cube']
    eps_ml = ml_reconstruction_uncertainty
    eps_model = model_approximation_uncertainty

    total_systematic = np.sqrt(eps_disc**2 + eps_ml**2 + eps_model**2)

    return {
        'discretization_error_96cube': float(eps_disc),
        'ml_reconstruction_error': float(eps_ml),
        'model_approximation_error': float(eps_model),
        'total_systematic_error': float(total_systematic),
        'dominant_source': max(
            [('discretization', eps_disc), ('ml_reconstruction', eps_ml), ('model_approximation', eps_model)],
            key=lambda x: x[1]
        )[0],
        'recommendation': 'Reduce dominant error source in next iteration' if total_systematic > 0.01 else 'Systematic errors under control'
    }
