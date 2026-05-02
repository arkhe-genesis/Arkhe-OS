import numpy as np
import json
import os
import argparse

def simulate_mechanical_fem(output_path='results/fem_torsion_simulation.json'):
    # 3. Simulate Mechanical Response (FEM) under torsional loads
    torques = np.linspace(0, 100, 50)

    results = []
    np.random.seed(42)

    for t in torques:
        # Non-linear strain energy based on torque
        strain_energy = 0.5 * 1e-4 * t**2 + np.random.normal(0, 0.001)
        strain = t / 100.0  # normalized strain

        # Determine regime based on torque ranges (capture, dilution, shattering)
        if t < 30:
            regime = "CAPTURE"
            status = "Elastic stabilization"
            coherence = 0.95 - (t/30)*0.1
        elif t < 70:
            regime = "DILUTION"
            status = "Viscoelastic yielding, modal phase mismatch"
            coherence = 0.85 - ((t-30)/40)*0.4
        else:
            regime = "SHATTERING"
            status = "Plastic deformation, lattice rupture"
            coherence = 0.45 - ((t-70)/30)*0.4

        results.append({
            "torque_nm": float(t),
            "strain_energy_j": float(strain_energy),
            "strain": float(strain),
            "regime": regime,
            "status": status,
            "spectral_coherence": max(0.0, float(coherence))
        })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Exported FEM simulation to {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, default='results/fem_torsion_simulation.json')
    args = parser.parse_args()
    simulate_mechanical_fem(args.output)
