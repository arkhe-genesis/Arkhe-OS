import numpy as np

def simulate_orbit_residuals(t_days, tau_0=1.0, torsion_strength=1e-12):
    """
    Simulates LAGEOS/GRACE-FO orbit residuals modulated by lambda_delta.
    """
    lambda_delta = 3722 / 2705
    # Proper time tau approximated by coordinate time t (for small velocities)
    tau = t_days * 86400  # Convert to seconds

    # Chronometric phase theta_Delta(tau)
    theta_delta = np.sin(lambda_delta * tau / tau_0)

    # Contortion modulation creates a residual periodic acceleration
    # Residual acceleration a_res ~ torsion_strength * theta_delta
    a_res = torsion_strength * theta_delta

    # Residual displacement (double integration of a_res, simplified)
    # Since a_res is periodic, displacement is also periodic
    omega = lambda_delta / tau_0
    displacement_res = - (torsion_strength / omega**2) * np.sin(omega * tau)

    return displacement_res

if __name__ == "__main__":
    t_days = np.linspace(0, 365, 1000)
    residuals = simulate_orbit_residuals(t_days)
    print(f"Max residual over 1 year: {np.max(np.abs(residuals)):.2e} meters")
