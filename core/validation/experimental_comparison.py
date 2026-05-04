#!/usr/bin/env python3
"""
Experimental Validation Framework — Substrate 104
Compares simulated predictions against experimental data from:
  • Substrate 85: PMMA micro-vortex spectrometers (optical band)
  • Substrate 89: Irrotational antennas (RF band, Ku/Ka)

Implements χ²/dof, p-value, and agreement metrics with proper uncertainty propagation.
"""
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from scipy.stats import chi2, norm
import warnings
from dataclasses import dataclass

@dataclass
class ExperimentalDataset:
    """Container for experimental data with uncertainties."""
    substrate_id: str  # '85' or '89'
    band: str  # 'optical' or 'rf'
    wavelength: float
    numerical_aperture: float
    focal_length: float

    # Measured observables with 1σ uncertainties
    peak_position: float
    peak_position_err: float
    spectral_width_fwhm: float
    spectral_width_err: float
    spatial_coherence: float
    coherence_err: float

    # Metadata
    measurement_date: str
    instrument_calibration: str
    notes: str = ""

class ExperimentalValidator:
    """Validates Fourier Lens Operator predictions against experimental data."""

    def __init__(self, simulated_results: Dict, experimental_data: List[ExperimentalDataset]):
        self.simulated = simulated_results
        self.experimental = experimental_data
        self.results = {}

    def compute_chi_squared(self, obs_sim: float, obs_exp: float, err_exp: float) -> float:
        """Compute χ² contribution for single observable."""
        return ((obs_sim - obs_exp) / err_exp)**2

    def validate_single_dataset(self, dataset: ExperimentalDataset,
                               sim_key: str) -> Dict:
        """Validate simulation against single experimental dataset."""
        sim_obs = self.simulated[sim_key]

        # Compute χ² contributions for each observable
        chi2_peak = self.compute_chi_squared(
            sim_obs['peak_position'],
            dataset.peak_position,
            dataset.peak_position_err
        )
        chi2_width = self.compute_chi_squared(
            sim_obs['spectral_width'],
            dataset.spectral_width_fwhm,
            dataset.spectral_width_err
        )
        chi2_coh = self.compute_chi_squared(
            sim_obs['spatial_coherence'],
            dataset.spatial_coherence,
            dataset.coherence_err
        )

        # Total χ² and degrees of freedom
        chi2_total = chi2_peak + chi2_width + chi2_coh
        dof = 3  # Three observables compared

        # p-value: probability of observing χ² this large or larger under null hypothesis
        p_value = 1 - chi2.cdf(chi2_total, dof)

        # Agreement metric: normalized residual for each observable
        residuals = {
            'peak': (sim_obs['peak_position'] - dataset.peak_position) / dataset.peak_position_err,
            'width': (sim_obs['spectral_width'] - dataset.spectral_width_fwhm) / dataset.spectral_width_err,
            'coherence': (sim_obs['spatial_coherence'] - dataset.spatial_coherence) / dataset.coherence_err
        }

        # Overall agreement score: fraction of residuals within ±2σ
        agreement_score = sum(1 for r in residuals.values() if abs(r) <= 2.0) / len(residuals)

        return {
            'substrate_id': dataset.substrate_id,
            'band': dataset.band,
            'chi2_total': chi2_total,
            'dof': dof,
            'reduced_chi2': chi2_total / dof,
            'p_value': p_value,
            'residuals': residuals,
            'agreement_score': agreement_score,
            'status': 'CONSISTENT' if p_value > 0.05 else 'TENSION' if p_value > 0.003 else 'INCONSISTENT'
        }

    def validate_all(self) -> Dict:
        """Run validation against all experimental datasets."""
        results = {}

        for dataset in self.experimental:
            sim_key = f"{dataset.band}_{dataset.substrate_id}"
            if sim_key in self.simulated:
                results[sim_key] = self.validate_single_dataset(dataset, sim_key)
            else:
                warnings.warn(f"No simulation data for key '{sim_key}'")

        # Summary statistics
        if results:
            p_values = [r['p_value'] for r in results.values()]
            agreement_scores = [r['agreement_score'] for r in results.values()]

            results['summary'] = {
                'n_datasets': len(results),
                'mean_p_value': np.mean(p_values),
                'min_p_value': np.min(p_values),
                'mean_agreement_score': np.mean(agreement_scores),
                'all_consistent': all(r['status'] == 'CONSISTENT' for r in results.values())
            }

        self.results = results
        return results
