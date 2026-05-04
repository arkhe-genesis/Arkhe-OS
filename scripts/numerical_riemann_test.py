"""
High-precision numerical test of spectral correspondence.
Goal: Compute first 100 eigenvalues of Ĥ_ζ and compare with first 100 Riemann zeros.
"""
import mpmath as mp
import numpy as np
import sys
import os

# Add core path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from core.riemann_operator import RiemannOperator

def riemann_zeros(n: int) -> list:
    """Compute first n non-trivial Riemann zeros via mpmath."""
    return [mp.zetazero(k) for k in range(1, n+1)]

def operator_eigenvalues(n: int, omega_delta: float, lambda_delta: float) -> list:
    """Compute first n eigenvalues of discretized Ĥ_ζ (heuristic)."""
    # Use a dummy gluing potential for exploration
    gluing_potential = lambda t: 0.5 * (1 + np.tanh(t))
    op = RiemannOperator(omega_delta=omega_delta, lambda_delta=lambda_delta, gluing_potential=gluing_potential, n_grid=2000)
    return op.compute_eigenvalues(k=n)

def compare_spectra(N: int = 20):
    """Compare first N Riemann zeros with eigenvalues of Ĥ_ζ."""
    zeros = riemann_zeros(N)
    evals = operator_eigenvalues(N, omega_delta=19.686678, lambda_delta=3722/2705)

    # Compute relative errors
    errors = [abs(float(z.imag) - float(e)) / abs(float(z.imag)) for z, e in zip(zeros, evals)]

    print(f"Mean relative error: {np.mean(errors):.2e}")
    print(f"Max relative error: {np.max(errors):.2e}")

    # Note: Even small errors do not prove correspondence;
    # large errors would falsify the conjecture.
    return errors

if __name__ == '__main__':
    print("Running numerical Riemann test (heuristic exploration)...")
    compare_spectra(N=20)
