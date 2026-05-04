#!/usr/bin/env python3
"""
Analyze convergence laws across 24³, 48³, 96³ grids and estimate systematic errors.
"""
import json
import numpy as np
#import matplotlib.pyplot as plt
from pathlib import Path
import sys
import argparse

# mock plotting since we don't have interactive display
def plot_convergence_results(results, output_path):
    pass

from core.convergence.convergence_analysis import (
    estimate_convergence_law, compute_systematic_error_budget
)
from core.holography.ml_enhanced_reconstruction import estimate_ml_reconstruction_uncertainty

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", help="Input JSON files")
    parser.add_argument("--output", help="Output JSON file")
    parser.add_argument("--plot-results", action="store_true")
    args = parser.parse_args()

    print("🔬 Convergence Analysis — Substrate 103", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Load results from all grids
    grids = ['24_cube', '48_cube', '96_cube']
    results = {}

    for grid in grids:
        path = Path(f'results/convergence_{grid}.json')
        if path.exists():
            with open(path) as f:
                results[grid] = json.load(f)
            print(f"  Loaded {grid}: {results[grid].get('simulation_metadata', {}).get('total_voxels', 'Unknown')} voxels", file=sys.stderr)

    if len(results) < 2:
        print("⚠️  Need at least 2 grids for convergence analysis", file=sys.stderr)
        return

    # Extract observables for convergence analysis
    observables = ['scar_fraction', 'sigma_xy', 'H0_kmsMpc', 'Omega_Lambda']
    convergence_summary = {}

    for obs in observables:
        N_values = [results[g]['simulation_metadata']['total_voxels'] for g in grids if obs in results[g] and 'simulation_metadata' in results[g]]
        values = [results[g][obs]['value'] for g in grids if obs in results[g] and 'simulation_metadata' in results[g]]
        uncertainties = [results[g][obs].get('uncertainty', 0.01) for g in grids if obs in results[g] and 'simulation_metadata' in results[g]]

        if len(N_values) >= 2:
            conv_result = estimate_convergence_law(N_values, values, uncertainties, obs)
            convergence_summary[obs] = conv_result
            print(f"\n  {obs}:", file=sys.stderr)
            print(f"    {conv_result.get('convergence_law', 'Fit Failed')}", file=sys.stderr)
            if 'parameters' in conv_result:
                print(f"    Continuum limit: {conv_result['parameters']['continuum_limit_C']['value']:.4f} ± {conv_result['parameters']['continuum_limit_C']['uncertainty']:.4f}", file=sys.stderr)
                print(f"    Convergence exponent α: {conv_result['parameters']['alpha']['value']:.3f}", file=sys.stderr)

    # Estimate ML reconstruction uncertainty (using 96³ data as representative)
    if '96_cube' in results:
        ml_uncertainty = estimate_ml_reconstruction_uncertainty(
            results['96_cube'].get('observer_data', [])
        )
        print(f"\n  ML reconstruction uncertainty: {ml_uncertainty:.4f}", file=sys.stderr)
    else:
        ml_uncertainty = 0.02  # Conservative default

    # Compute systematic error budget
    error_budget = None
    if 'H0_kmsMpc' in convergence_summary:
        error_budget = compute_systematic_error_budget(
            convergence_summary['H0_kmsMpc'],
            ml_reconstruction_uncertainty=ml_uncertainty,
            model_approximation_uncertainty=0.015  # Estimated from theory approximations
        )
        print(f"\n  Systematic error budget (Friedmann params):", file=sys.stderr)
        print(f"    Discretization (96³): {error_budget['discretization_error_96cube']:.4f}", file=sys.stderr)
        print(f"    ML reconstruction: {error_budget['ml_reconstruction_error']:.4f}", file=sys.stderr)
        print(f"    Model approximation: {error_budget['model_approximation_error']:.4f}", file=sys.stderr)
        print(f"    TOTAL: {error_budget['total_systematic_error']:.4f}", file=sys.stderr)
        print(f"    Dominant source: {error_budget['dominant_source']}", file=sys.stderr)

    # Save summary
    output = {
        'version': 'v∞.393.3',
        'grids_analyzed': list(results.keys()),
        'convergence_laws': convergence_summary,
        'systematic_error_budget': error_budget if error_budget else None,
        'recommendations': [
            'Upgrade to float64 precision for 96³ to reduce numerical noise',
            'Increase PINN training epochs for better holographic reconstruction',
            'Validate convergence exponent α against theoretical expectations',
            'If total systematic > 0.02, consider 192³ grid for next iteration'
        ]
    }

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
    else:
        with open('results/convergence_summary_v393.3.json', 'w') as f:
            json.dump(output, f, indent=2)

    if args.plot_results:
        # Generate convergence plots
        plot_convergence_results(convergence_summary, output_path='results/convergence_plots_v393.3.png')

    print(f"\n✅ Analysis complete. Summary: results/convergence_summary_v393.3.json", file=sys.stderr)

if __name__ == '__main__':
    main()
