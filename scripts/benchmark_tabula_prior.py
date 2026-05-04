# scripts/benchmark_tabula_prior.py
"""Benchmark SPSA convergence with vs without Tabula prior."""
import sys
import os
import numpy as np
import time

# Ensure import paths work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'arkhe-v3277')))
from core.spsa_adaptive import AdaptiveSPSA
from core.spsa_tabula_prior import TabulaSPSAPrior

def benchmark_convergence(use_prior: bool = True, n_runs: int = 20):
    """Compare convergence speed with/without Tabula prior."""

    # Synthetic landscape with known optimum
    def synthetic_landscape(theta):
        target = np.array([1.2, 0.004, 0.12, 3.0])
        distance = np.sum((theta - target) ** 2)
        return np.exp(-distance / 0.5)

    param_bounds = [(0.1, 2.0), (0.0001, 0.01), (0.0, 0.3), (2, 5)]

    results = []

    for run in range(n_runs):
        optimizer = AdaptiveSPSA(param_bounds=param_bounds, mode='adaptive')

        # Nuclear features for prior (synthetic but realistic)
        nuclear_features = {
            'BindingEnergy_MeV_per_nucleon': 8.5,
            'logT12': 10.0,
            'Asymmetry': 0.1,
            'Z_over_A': 0.42,
            'Z_magic': 0,
            'N_magic': 1,
            # ... other features matching trained model
        }

        # Load prior (or skip)
        try:
            prior = TabulaSPSAPrior() if use_prior else None
        except Exception as e:
            print(f"Failed to load prior: {e}")
            prior = None

        start = time.time()
        theta = None
        for epoch in range(1, 51):
            theta, score = optimizer.step(
                evaluate_fn=synthetic_landscape,
                epoch=epoch,
                current_theta=theta,
                nuclear_features=nuclear_features if use_prior else None,
                tabula_prior=prior
            )
            if score > 0.95:  # Early stopping at good solution
                break
        elapsed = time.time() - start

        results.append({
            'epochs_to_converge': epoch,
            'final_score': score,
            'time_seconds': elapsed,
            'final_kappa': theta[0] if theta is not None else None
        })

    # Aggregate results
    avg_epochs = np.mean([r['epochs_to_converge'] for r in results])
    avg_time = np.mean([r['time_seconds'] for r in results])

    print(f"{'With' if use_prior else 'Without'} Tabula prior:")
    print(f"   • Avg epochs to converge: {avg_epochs:.1f}")
    print(f"   • Avg time: {avg_time:.2f}s")
    print(f"   • Success rate (score > 0.95): {sum(1 for r in results if r['final_score'] > 0.95) / n_runs:.1%}")

    return results

if __name__ == '__main__':
    print("🔬 Benchmarking Tabula prior for SPSA...")
    print("\n--- Without prior ---")
    results_no_prior = benchmark_convergence(use_prior=False)

    print("\n--- With Tabula prior ---")
    results_with_prior = benchmark_convergence(use_prior=True)

    # Compare
    epochs_no = np.mean([r['epochs_to_converge'] for r in results_no_prior])
    epochs_yes = np.mean([r['epochs_to_converge'] for r in results_with_prior])
    speedup = epochs_no / epochs_yes if epochs_yes > 0 else float('inf')

    print(f"\n🚀 Speedup: {speedup:.2f}× fewer epochs with Tabula prior")
