# ============================================================================
# ARKHE OS v∞.Ω.∇+++.13.1 — Orbit Residual Simulation with Contortion Modulation
# Purpose: Predict LAGEOS/GRACE-FO range residuals from λ_Δ-modulated torsion
# ============================================================================

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# Constants
GM_EARTH = 3.986004418e14  # m³/s²
R_EARTH = 6378137.0        # m
J2 = 1.08263e-3
LAMBDA_DELTA = 3722 / 2705
TAU0 = 86164.0 / (2 * np.pi)  # Characteristic time ~ 1/ω_orb for MEO

# Contortion coupling (conservative upper bound from current tests)
K_TENSOR = np.diag([0, 1e-15, 1e-15, 1e-15])  # m⁻¹ scale

def earth_gravity(t, state):
    """Standard Newtonian + J2 perturbation."""
    r = state[:3]
    v = state[3:]
    r_norm = np.linalg.norm(r)
    # Newtonian
    a = -GM_EARTH * r / r_norm**3
    # J2 perturbation
    x, y, z = r
    a_x = -GM_EARTH * (1.5 * J2 * R_EARTH**2 * x * (5*z**2 - r_norm**2) / r_norm**7)
    a_y = -GM_EARTH * (1.5 * J2 * R_EARTH**2 * y * (5*z**2 - r_norm**2) / r_norm**7)
    a_z = -GM_EARTH * (1.5 * J2 * R_EARTH**2 * z * (5*z**2 - 3*r_norm**2) / r_norm**7)
    return np.concatenate([v, a + np.array([a_x, a_y, a_z])])

def contortion_acceleration(t, state):
    """λ_Δ-modulated contortion perturbation."""
    r = state[:3]
    v = state[3:]
    r_norm = np.linalg.norm(r)
    tau = t  # Proper time ≈ coordinate time for orbital speeds
    theta = np.sin(LAMBDA_DELTA * tau / TAU0)

    # Projector P^μ_α ≈ I - (v⊗v)/c² (Newtonian limit)
    v_outer = np.outer(v, v) / (299792458**2)
    P = np.eye(3) - v_outer

    # Contortion coupling
    K_u = K_TENSOR[1:, 1:] @ v
    a_K = P @ K_u * theta
    return a_K

def full_dynamics(t, state):
    """Combined GR+J2 + contortion dynamics."""
    return earth_gravity(t, state) + np.concatenate([np.zeros(3), contortion_acceleration(t, state)])

def simulate_orbit(initial_state, t_span, dt):
    """RK4 integration with dense output for residual computation."""
    sol = solve_ivp(full_dynamics, t_span, initial_state, method='RK45',
                    max_step=dt, rtol=1e-12, atol=1e-12, dense_output=True)

    # Reference orbit (no contortion)
    sol_ref = solve_ivp(earth_gravity, t_span, initial_state, method='RK45',
                        max_step=dt, rtol=1e-12, atol=1e-12, dense_output=True)

    # Compute range residuals (LAGEOS/GRACE-FO style)
    t_eval = np.arange(t_span[0], t_span[1], dt)
    r_perturbed = sol.sol(t_eval)[:3]
    r_ref = sol_ref.sol(t_eval)[:3]

    residuals = np.linalg.norm(r_perturbed - r_ref, axis=0)
    return t_eval, residuals, sol, sol_ref

if __name__ == '__main__':
    # Initial conditions: LAGEOS-like orbit (a=12270 km, e=0.004, i=109.84°)
    a = 12270e3
    e = 0.004
    i = 109.84 * np.pi / 180
    v_circ = np.sqrt(GM_EARTH / a)
    initial_pos = np.array([a * (1 - e), 0, a * np.sin(i)])
    initial_vel = np.array([0, v_circ * np.sqrt((1 + e)/(1 - e)) * np.cos(i), 0])
    initial_state = np.concatenate([initial_pos, initial_vel])

    # Run simulation (30 days, 10s step)
    t_eval, residuals, sol_pert, sol_ref = simulate_orbit(
        initial_state, t_span=(0, 30 * 86400), dt=10.0
    )

    # Spectral analysis
    from scipy.signal import welch
    f, psd = welch(residuals, fs=1/10.0, nperseg=8192, detrend='linear')

    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    ax1.plot(t_eval/86400, residuals * 1e3, linewidth=0.8)
    ax1.set_xlabel('Time (days)')
    ax1.set_ylabel('Range Residual (mm)')
    ax1.set_title('Contortion-Modulated Orbit Residuals')
    ax1.grid(True, alpha=0.3)

    ax2.loglog(f, psd, linewidth=1)
    f_res = LAMBDA_DELTA / (2 * np.pi * TAU0)
    ax2.axvline(f_res, color='red', linestyle='--', label=f'λ_Δ resonance @ {f_res:.2e} Hz')
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('PSD (mm²/Hz)')
    ax2.legend()
    ax2.grid(True, alpha=0.3, which='both')
    plt.tight_layout()
    plt.savefig('contortion_orbit_residuals.png', dpi=150)
    print(f"✓ Residual peak predicted at {f_res:.2e} Hz ({f_res*86400:.3f} cycles/day)")
    print(f"✓ Max residual amplitude: {np.max(residuals)*1e3:.3f} mm")
