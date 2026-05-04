#!/usr/bin/env python3
"""
Grid Sweep for Riemann Operator v∞.101
Tests convergence (O(1/N²) error model) and falsifiability threshold.
"""
import json
import sys
from pathlib import Path
import numpy as np
import warnings
import traceback

from core.riemann_operator_v101 import CONFIG, build_hzeta_matrix, solve_spectrum, riemann_zeros_im, compute_error_model

def run_grid_sweep():
    grid_sizes = [512, 1024, 2048, 4096]

    results = {}

    for N in grid_sizes:
        print(f"Running for N={N}...")
        config = CONFIG.copy()
        config['grid_N'] = N

        try:
            t, A, hash_hex = build_hzeta_matrix(config)

            E_num = solve_spectrum(A, k=config['convergence_criterion_n'])
            E_zeta = riemann_zeros_im(k=config['convergence_criterion_n'])

            error_report = compute_error_model(E_num, E_zeta, config['grid_N'])

            print(f"N={N} -> Mean Relative Error: {error_report['mean_relative_error']:.2e}, Max Error: {error_report['max_relative_error']:.2e}")
            results[N] = error_report
        except Exception as e:
            print(f"Failed for N={N}: {e}")
            traceback.print_exc()
            results[N] = {"error": str(e)}

    # Save results
    out_path = Path("results/riemann_grid_sweep.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved results to {out_path}")

if __name__ == '__main__':
    run_grid_sweep()
