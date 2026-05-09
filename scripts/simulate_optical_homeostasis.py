import argparse
import numpy as np
import os
import json

def phase_to_spectrum(phi, kappa):
    """Simplified physical model for testing convergence."""
    # This acts as a stand-in for the real spectral model
    lambda_axis = np.linspace(400, 1550, 1151)

    # Example logic: phase distribution affects spectrum shape
    phi_sync = 0.58 * np.pi
    sync_measure = np.mean(np.cos(phi - phi_sync))

    # Create a spectrum whose shape depends on synchronization
    spectrum = np.exp(-0.5 * ((lambda_axis - 800 - 100*sync_measure) / 200)**2)
    return spectrum

def simulate_optical_homeostatic_loop(kappa_initial, gamma_prop, gamma_int, dt, max_steps, output_path):
    print(f"Simulating optical homeostatic loop with kappa0={kappa_initial}, gamma_p={gamma_prop}, gamma_i={gamma_int}")

    # 768 oscillators
    n_oscillators = 768
    np.random.seed(42)
    phi = np.random.uniform(0, 2*np.pi, n_oscillators)

    # Create target spectrum (corresponding to high synchronization)
    target_phi = np.full(n_oscillators, 0.58 * np.pi)
    target_spectrum = phase_to_spectrum(target_phi, 1.0)

    kappa = kappa_initial
    integral_error = 0.0

    history = {'kappa': [], 'error': [], 'convergence_step': -1}

    for step in range(max_steps):
        # [1] Current spectrum
        S_current = phase_to_spectrum(phi, kappa)

        # [2] Spectral error
        error = np.trapezoid((S_current - target_spectrum)**2, dx=1.0)

        # [3] Update kappa via PI control
        integral_error += error * dt
        kappa_new = kappa + gamma_prop * error + gamma_int * integral_error
        kappa = np.clip(kappa_new, 0.1, 2.0)

        # [4] Update phases via Kuramoto
        # To avoid N^2 in numpy for 768, use mean field
        mean_field_x = np.mean(np.cos(phi))
        mean_field_y = np.mean(np.sin(phi))
        R = np.sqrt(mean_field_x**2 + mean_field_y**2)
        Psi = np.arctan2(mean_field_y, mean_field_x)

        # dphi = kappa * R * sin(Psi - phi) + noise
        dphi = kappa * R * np.sin(Psi - phi) + np.random.normal(0, 0.01, n_oscillators)
        phi = (phi + dphi * dt) % (2*np.pi)

        # [5] Record history (subsample to save memory/disk space if max_steps is large)
        if step % 100 == 0 or step == max_steps - 1:
            history['kappa'].append(float(kappa))
            history['error'].append(float(error))

        # [6] Convergence criterion
        if error < 1e-4 and step > 100:
            print(f"✓ Converged in {step} steps: error={error:.2e}, kappa={kappa:.3f}")
            history['convergence_step'] = step
            break

    # Ensure output dir exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(history, f, indent=2)

    print(f"Convergence history saved to {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--initial-kappa', type=float, default=0.75)
    parser.add_argument('--gamma-prop', type=float, default=1e-3)
    parser.add_argument('--gamma-int', type=float, default=1e-6)
    parser.add_argument('--dt', type=float, default=1e-6) # Can be artificially scaled up for simulation speed if needed
    parser.add_argument('--max-steps', type=int, default=10000)
    parser.add_argument('--output', type=str, default='results/homeostasis_convergence.json')

    args = parser.parse_args()

    # We might want to use a larger dt for simulation purposes to see convergence in 10k steps,
    # or just run it. If dt is 1e-6, it might not converge in 10k steps. Let's let the user override it.

    simulate_optical_homeostatic_loop(
        args.initial_kappa,
        args.gamma_prop,
        args.gamma_int,
        args.dt,
        args.max_steps,
        args.output
    )