# tests/test_skyrmion_robustness.py
import argparse
import numpy as np
from core.topology.skyrmion_programmer import SkyrmionProgrammer, SkyrmionProgram, SkyrmionType
from core.topology.skyrmion_invariant import compute_skyrmion_charge

def test_robustness(noise_strength):
    print(f"Testing skyrmion robustness with noise strength: {noise_strength}")
    programmer = SkyrmionProgrammer(lattice_spacing=1.0, simulation_size=(128, 128))

    program = SkyrmionProgram(
        target_charge=1,
        skyrmion_type=SkyrmionType.NEEL,
        core_radius=10.0,
        boundary_condition="fixed",
        control_fields={"E_z": 1e6}
    )

    # Generate clean texture
    n_field_clean = programmer.generate_texture(program)

    # Add noise
    noise = np.random.randn(*n_field_clean.shape) * noise_strength
    n_field_noisy = n_field_clean + noise

    # Re-normalize noisy field
    norm = np.linalg.norm(n_field_noisy, axis=-1, keepdims=True)
    n_field_noisy /= (norm + 1e-10)

    # Denoise before computing charge
    from core.topology.denoising import compute_robust_charge

    # Compute charge with denoising
    Q_noisy = compute_robust_charge(n_field_noisy, dx=programmer.dx, denoise_sigma=1.0)

    print(f"Original Q: 1.0")
    print(f"Noisy Q computed: {Q_noisy:.3f}")

    # Check if Q is preserved within tolerance
    if abs(abs(Q_noisy) - 1.0) < 0.2:
        print("✅ Q preserved within tolerance despite noise.")
    else:
        print("❌ Q outside tolerance.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test skyrmion robustness to noise.")
    parser.add_argument("--noise-strength", type=float, default=0.2, help="Strength of Gaussian noise to add to the field.")
    args = parser.parse_args()
    test_robustness(args.noise_strength)
