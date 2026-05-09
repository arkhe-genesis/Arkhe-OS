import argparse
import numpy as np
import h5py
import os

def simulate_vortex_array_response(vortex_diameter, pitch, wavelength_range, output_path):
    print(f"Simulating vortex array response with diameter {vortex_diameter}, pitch {pitch}")

    # Generate wavelength axis
    lambda_start, lambda_end = wavelength_range
    # Resolution 1nm
    lambda_start_nm = int(lambda_start * 1e9)
    lambda_end_nm = int(lambda_end * 1e9)
    lambda_axis = np.linspace(lambda_start_nm, lambda_end_nm, lambda_end_nm - lambda_start_nm + 1)

    n_oscillators = 768
    phi_sync = 0.58 * np.pi

    # Random phases for 768 oscillators
    np.random.seed(42)
    phi = np.random.uniform(0, 2*np.pi, n_oscillators)

    # αᵢ(λ): coupling coefficients. Let's make a simple model.
    alpha = np.random.uniform(0.01, 0.1, (n_oscillators, len(lambda_axis)))

    # Δφ_opt(λ)
    sin_diff = np.sin(phi - phi_sync)
    delta_phi_opt = np.sum(alpha * sin_diff[:, np.newaxis], axis=0) # shape: (len(lambda_axis),)

    # V(x,y) vorticity function.
    # 10x10 matrix.
    grid_size = 64 # spatial grid
    x = np.linspace(-5e-6, 5e-6, grid_size)
    y = np.linspace(-5e-6, 5e-6, grid_size)
    X, Y = np.meshgrid(x, y)

    # Sum over 10x10 micro-vortices
    V = np.zeros_like(X)
    for i in range(10):
        for j in range(10):
            cx = -4.5e-6 + i * pitch
            cy = -4.5e-6 + j * pitch
            r_ij = np.sqrt((X-cx)**2 + (Y-cy)**2)
            theta_ij = np.arctan2(Y-cy, X-cx)
            # Add vortex phase if within diameter
            mask = r_ij < (vortex_diameter / 2)
            V += mask * theta_ij

    # Calculate S(lambda)
    # S(λ) = |ℱ{ exp[i · Δφ_opt(λ) · V(x,y)] }|²
    S_lambda = np.zeros(len(lambda_axis))

    for k in range(len(lambda_axis)):
        field = np.exp(1j * delta_phi_opt[k] * V)
        # spatial FFT
        F_field = np.fft.fft2(field)
        # Total intensity for this wavelength
        S_lambda[k] = np.sum(np.abs(F_field)**2)

    # Normalize S_lambda to a reasonable range
    S_lambda /= np.max(S_lambda)

    # Ensure output dir exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to HDF5
    with h5py.File(output_path, 'w') as f:
        f.create_dataset('wavelengths', data=lambda_axis)
        f.create_dataset('spectrum', data=S_lambda)
        f.create_dataset('delta_phi_opt', data=delta_phi_opt)
        f.create_dataset('V_matrix', data=V)
        f.create_dataset('phi', data=phi)

    print(f"Simulation saved to {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--vortex-diameter', type=float, default=300e-9)
    parser.add_argument('--pitch', type=float, default=1e-6)
    parser.add_argument('--wavelength-range', type=float, nargs=2, default=[400e-9, 1550e-9])
    parser.add_argument('--output', type=str, default='results/vortex_spectral_model.h5')

    args = parser.parse_args()
    simulate_vortex_array_response(
        args.vortex_diameter,
        args.pitch,
        args.wavelength_range,
        args.output
    )
