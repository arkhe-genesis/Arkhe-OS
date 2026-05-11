#!/usr/bin/env python3
"""
angular_coherence_zdna.py — Test Prediction B: A predicts σ₁/₂ for B→Z transition
"""
import numpy as np
from Bio import SeqIO
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import pandas as pd

PHI = (1 + np.sqrt(5)) / 2
HELICAL_REPEAT = 10.5  # bp/turn for B‑DNA
TWIST_PER_BP = 360 / HELICAL_REPEAT  # degrees

def compute_angular_coherence(sequence, reference_phase=0):
    """
    Compute angular coherence A for a DNA sequence.
    Uses cumulative twist projection onto 34.3° periodicity.
    """
    # For simplicity, assume canonical twist; in practice, use MD‑derived twist angles
    N = len(sequence)
    cumulative_twist = np.arange(N) * TWIST_PER_BP

    # Phase projection: how well does twist align with φ‑scaled periodicity?
    # The 17° phase relationship implies a secondary periodicity of 360/17 ≈ 21.18 bp
    phi_period = 360 / 17  # ~21.18 bp

    phases = np.exp(1j * 2 * np.pi * cumulative_twist / phi_period)
    A = np.abs(np.mean(phases))

    return A

def generate_sequence_library(n_sequences=100, length=200, coherence_range=(0.3, 0.95)):
    """
    Generate synthetic DNA sequences with controlled angular coherence.
    Uses a simple Markov model to tune phase alignment.
    """
    sequences = []
    for _ in range(n_sequences):
        target_A = np.random.uniform(*coherence_range)
        seq = []
        # Start with random base
        bases = ['A', 'C', 'G', 'T']
        seq.append(np.random.choice(bases))

        # Build sequence with bias toward maintaining phase coherence
        for i in range(1, length):
            # Desired phase at position i
            desired_phase = (i * TWIST_PER_BP) % 360

            # Choose next base to maintain coherence (simplified model)
            # In reality, use dinucleotide twist propensities from MD
            if np.random.random() < target_A:
                # Favor bases that maintain phase (e.g., alternating purine‑pyrimidine)
                if seq[-1] in ['A', 'G']:  # purine
                    seq.append(np.random.choice(['C', 'T']))  # pyrimidine
                else:
                    seq.append(np.random.choice(['A', 'G']))
            else:
                seq.append(np.random.choice(bases))

        sequences.append(''.join(seq))

    return sequences

def fit_zdna_transition_model(supercoiling_densities, z_fractions):
    """
    Fit the two‑state B↔Z transition model to extract σ₁/₂.
    Model: f_Z(σ) = 1 / (1 + exp[-(σ - σ₁/₂) / w])
    """
    def sigmoid(sigma, sigma_half, width):
        return 1 / (1 + np.exp(-(sigma - sigma_half) / width))

    popt, pcov = curve_fit(sigmoid, supercoiling_densities, z_fractions,
                          p0=[-0.05, 0.01], bounds=([-0.2, 0.001], [0, 0.1]))
    return popt[0], np.sqrt(pcov[0,0])  # σ₁/₂ and its error

def test_angular_coherence_prediction(sequences, experimental_sigma_half_fn):
    """
    Main test: correlate computed A with measured σ₁/₂.
    experimental_sigma_half_fn: function that takes sequence and returns (σ₁/₂, error)
    """
    results = []
    for seq in sequences:
        A = compute_angular_coherence(seq)
        sigma_half, sigma_err = experimental_sigma_half_fn(seq)
        results.append({'sequence': seq[:50]+'...', 'A': A, 'sigma_half': sigma_half, 'sigma_err': sigma_err})

    df = pd.DataFrame(results)

    # Linear regression: σ₁/₂ = σ₀ - γ·(A - A_c)
    from scipy.stats import linregress
    mask = df['A'] > 0.5  # Focus on high‑coherence regime
    if mask.sum() < 10:
        return None

    slope, intercept, r_value, p_value, std_err = linregress(df.loc[mask, 'A'], df.loc[mask, 'sigma_half'])

    return {
        'n_sequences': len(df),
        'slope_gamma': -slope,  # γ = -slope
        'intercept_sigma0': intercept + slope * 0.7,  # σ₀ at A_c = 0.7
        'r_squared': r_value**2,
        'p_value': p_value,
        'std_err_slope': std_err,
        'data': df
    }

# Example usage (with simulated experimental data):
if __name__ == '__main__':
    # Generate sequences with known A
    sequences = generate_sequence_library(n_sequences=50, length=200)

    # Simulate experimental σ₁/₂ measurements with noise
    def mock_experiment(seq):
        A = compute_angular_coherence(seq)
        # True model: σ₁/₂ = -0.06 - 0.03·(A - 0.7)
        true_sigma = -0.06 - 0.03 * (A - 0.7)
        # Add measurement noise
        noise = np.random.normal(0, 0.005)
        return true_sigma + noise, 0.005

    result = test_angular_coherence_prediction(sequences, mock_experiment)

    if result:
        print(f"✅ Angular Coherence Test:")
        print(f"   Sequences tested: {result['n_sequences']}")
        print(f"   γ (slope): {result['slope_gamma']:.4f} ± {result['std_err_slope']:.4f}")
        print(f"   R²: {result['r_squared']:.3f}")
        print(f"   p‑value: {result['p_value']:.4f}")

        # Plot
        import matplotlib.pyplot as plt
        df = result['data']
        plt.figure(figsize=(8,6))
        plt.errorbar(df['A'], df['sigma_half'], yerr=df['sigma_err'],
                    fmt='o', alpha=0.6, label='Data')
        x_fit = np.linspace(0.5, 0.95, 100)
        y_fit = result['intercept_sigma0'] - result['slope_gamma'] * (x_fit - 0.7)
        plt.plot(x_fit, y_fit, 'r-', label=f'Fit: R²={result["r_squared"]:.2f}')
        plt.xlabel('Angular Coherence A')
        plt.ylabel('B→Z Transition Midpoint σ₁/₂')
        plt.title('Prediction B: A predicts σ₁/₂')
        plt.legend()
        plt.grid(alpha=0.3)
        plt.savefig('angular_coherence_zdna_test.png', dpi=300)
        print(f"   📊 Plot saved: angular_coherence_zdna_test.png")
