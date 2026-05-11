# scripts/analyze_fea_capture_correlation.py
"""
Analyze FEA results to validate CAPTURE regime correspondence
Compare torsional displacement distribution with predicted coupling pattern.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import pearsonr
from core.or_lattice_specs import OR_SPEC

def load_torsion_results(results_path: str = 'fea/results/torsion_results.txt') -> pd.DataFrame:
    """Load torsional rotation results from FEA."""
    data = []
    with open(results_path, 'r') as f:
        # Skip header
        next(f)
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                data.append({
                    'node_id': int(parts[0]),
                    'layer': int(parts[1]),
                    'position': int(parts[2]),
                    'torsion_rad': float(parts[3])
                })
    return pd.DataFrame(data)

def compute_expected_capture_pattern(spec: OR_SPEC) -> np.ndarray:
    """Compute expected torsional pattern for CAPTURE regime."""
    # CAPTURE regime: ferromagnetic alignment with torsional modulation
    # Pattern: φ_expected = λΔ × layer + modular_phase(position)

    pattern = np.zeros((spec.n_layers, spec.crystals_per_ring))

    for layer in range(spec.n_layers):
        for pos in range(spec.crystals_per_ring):
            # Modular phase from F181 arithmetic
            modular_phase = (pow(5, pos, spec.prime_field) / spec.prime_field) * 2 * np.pi
            # Torsional offset
            torsion_offset = spec.lambda_delta * layer
            # Combined expected rotation
            pattern[layer, pos] = (torsion_offset + modular_phase) % (2 * np.pi)

    return pattern

def validate_capture_correlation(fea_results: pd.DataFrame, spec: OR_SPEC) -> dict:
    """Validate that FEA torsion distribution matches CAPTURE prediction."""
    # Reshape FEA results to 2D array
    fea_pattern = np.zeros((spec.n_layers, spec.crystals_per_ring))
    for _, row in fea_results.iterrows():
        if 0 <= row['layer'] < spec.n_layers and 0 <= row['position'] < spec.crystals_per_ring:
            fea_pattern[int(row['layer']), int(row['position'])] = row['torsion_rad']

    # Compute expected pattern
    expected_pattern = compute_expected_capture_pattern(spec)

    # Compute correlation (accounting for 2π periodicity)
    # Use circular correlation for angular data
    def circular_correlation(a, b):
        """Compute correlation for angular data."""
        # Convert to unit vectors
        a_vec = np.stack([np.cos(a), np.sin(a)], axis=-1)
        b_vec = np.stack([np.cos(b), np.sin(b)], axis=-1)
        # Dot product correlation
        dot_products = np.sum(a_vec * b_vec, axis=-1)
        return np.mean(dot_products)

    circ_corr = circular_correlation(fea_pattern.flatten(), expected_pattern.flatten())

    # Also compute linear correlation of unwrapped phases (for magnitude validation)
    linear_corr, p_value = pearsonr(fea_pattern.flatten(), expected_pattern.flatten())

    # Compute RMS error
    rms_error = np.sqrt(np.mean((fea_pattern - expected_pattern)**2))

    return {
        'circular_correlation': float(circ_corr),
        'linear_correlation': float(linear_corr),
        'p_value': float(p_value),
        'rms_error_rad': float(rms_error),
        'rms_error_deg': float(rms_error * 180/np.pi),
        'pattern_match': bool(circ_corr > 0.85)  # Threshold for CAPTURE validation
    }

def plot_torsion_comparison(fea_results: pd.DataFrame, spec: OR_SPEC,
                           output_path: str = 'fea/results/torsion_comparison.png'):
    """Generate visualization of FEA vs expected torsion pattern."""
    fea_pattern = np.zeros((spec.n_layers, spec.crystals_per_ring))
    for _, row in fea_results.iterrows():
        if 0 <= row['layer'] < spec.n_layers and 0 <= row['position'] < spec.crystals_per_ring:
            fea_pattern[int(row['layer']), int(row['position'])] = row['torsion_rad']

    expected_pattern = compute_expected_capture_pattern(spec)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # FEA results
    im1 = axes[0].imshow(fea_pattern, aspect='auto', cmap='viridis',
                        extent=[0, spec.crystals_per_ring, 0, spec.n_layers])
    axes[0].set_title('FEA Torsional Rotation (rad)')
    axes[0].set_xlabel('Crystal Position')
    axes[0].set_ylabel('Layer')
    plt.colorbar(im1, ax=axes[0])

    # Expected CAPTURE pattern
    im2 = axes[1].imshow(expected_pattern, aspect='auto', cmap='viridis',
                        extent=[0, spec.crystals_per_ring, 0, spec.n_layers])
    axes[1].set_title('Expected CAPTURE Pattern (rad)')
    axes[1].set_xlabel('Crystal Position')
    axes[1].set_ylabel('Layer')
    plt.colorbar(im2, ax=axes[1])

    # Difference map
    diff = fea_pattern - expected_pattern
    im3 = axes[2].imshow(diff, aspect='auto', cmap='RdBu_r',
                        extent=[0, spec.crystals_per_ring, 0, spec.n_layers],
                        vmin=-0.5, vmax=0.5)
    axes[2].set_title('Difference (FEA - Expected)')
    axes[2].set_xlabel('Crystal Position')
    axes[2].set_ylabel('Layer')
    plt.colorbar(im3, ax=axes[2])

    plt.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Comparison plot saved: {output_path}")

if __name__ == '__main__':
    results_path = 'fea/results/torsion_results.txt'

    if Path(results_path).exists():
        print("📊 Analyzing FEA torsion results...")
        fea_df = load_torsion_results(results_path)

        validation = validate_capture_correlation(fea_df, OR_SPEC)

        print(f"\n🔍 CAPTURE Regime Validation:")
        print(f"   • Circular correlation: {validation['circular_correlation']:.4f}")
        print(f"   • Linear correlation: {validation['linear_correlation']:.4f} (p={validation['p_value']:.2e})")
        print(f"   • RMS error: {validation['rms_error_deg']:.2f}°")
        print(f"   • Pattern match: {'✅ PASS' if validation['pattern_match'] else '❌ FAIL'}")

        # Generate visualization
        plot_torsion_comparison(fea_df, OR_SPEC)

        if validation['pattern_match']:
            print(f"\n✅ FEA validation PASSED: Torsion distribution matches CAPTURE regime prediction")
        else:
            print(f"\n⚠️  FEA validation NEEDS ATTENTION: Torsion pattern deviates from CAPTURE prediction")
    else:
        print(f"⚠️  FEA results not found: {results_path}")
        print(f"   Run Ansys/Abaqus simulation first")
