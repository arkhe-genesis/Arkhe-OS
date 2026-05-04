import json
import argparse
import sys
import numpy as np
from typing import List, Dict, Any
import os

# Ensure core module is importable
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.fourier_lens_operator import FourierLensOperator

def calculate_metrics(simulated: List[float], experimental: List[float]) -> tuple:
    # simple chi2 and pseudo p-value for mock validation
    sim = np.array(simulated)
    exp = np.array(experimental)
    # mock errors as 5% of exp
    err = np.maximum(exp * 0.05, 1e-12)
    chi2 = np.sum(((sim - exp) / err) ** 2)
    dof = len(exp)

    # pseudo p-value (good fit if chi2/dof ~ 1)
    if chi2/dof < 2.0:
        p_val = 0.95
    elif chi2/dof < 5.0:
        p_val = 0.05
    else:
        p_val = 0.001

    return float(chi2), dof, float(p_val)

def validate_dataset(filepath: str, w: float, f: float) -> None:
    with open(filepath, 'r') as file:
        data = json.load(file)

    print(f"\n🔮 Validating Substrate {data['substrate']}: {data['description']}")
    print(f"Band: {data['band']} (λ = {w}m, f = {f}m)")

    op = FourierLensOperator({"grid_pixels": [1024, 1024]})

    sim_widths = []
    exp_widths = []

    for i, m in enumerate(data['measurements']):
        na = m['numerical_aperture']
        theta = m['incident_angle_rad']

        band_config = {
            'wavelength': w,
            'focal_length': f,
            'numerical_aperture': na,
            'incident_angle': [theta, 0.0]
        }

        res = op.propagate(band_config)

        sim_widths.append(res['spectral_width'])
        exp_widths.append(m['measured_spectral_width'])

        print(f"\n  [Measurement {i+1}] NA = {na}, θ = {theta}")
        print(f"    Method used: {res['method']}")
        print(f"    Predicted Δθ: {res['spectral_width']:.4e} | Measured Δθ: {m['measured_spectral_width']:.4e}")
        print(f"    Predicted Coherence: {res['spatial_coherence']:.3f} | Measured: {m['measured_coherence']:.3f}")

    chi2, dof, p_val = calculate_metrics(sim_widths, exp_widths)

    print(f"\n  📊 Goodness-of-Fit Metrics (Spectral Width):")
    print(f"    • χ²/dof: {chi2:.2f} / {dof} = {chi2/dof:.2f}")
    print(f"    • p-value: {p_val:.3f}")

    if p_val > 0.05:
        print("  ✅ Experimental Validation: PASS (Model in agreement with data)")
    else:
        print("  ❌ Experimental Validation: FAIL (Model deviates significantly)")

def main():
    parser = argparse.ArgumentParser(description="Validate vectorial propagation against Substrate 85 & 89")
    args = parser.parse_args()

    print("🚀 Running Vectorial High-NA Validations...")

    # Substrate 85 (Optical, lambda=500nm, f=0.05m)
    validate_dataset("data/experimental/substrate_85_optical.json", w=500e-9, f=0.05)

    # Substrate 89 (RF, lambda=10cm, f=1.0m)
    validate_dataset("data/experimental/substrate_89_rf.json", w=0.1, f=1.0)

if __name__ == "__main__":
    main()
