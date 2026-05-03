import numpy as np

def compute_negative_dwell_time(E_d_baseline, E_d_tau, tau_entry, tau_exit):
    """
    Computes effective dwell time based on Uniphics principle.
    t_flow = k / E_d
    """
    # Simulate an energy density dip
    # For a photon spin-wave structure reducing local E_d
    def E_d_dip(tau):
        return E_d_baseline - (E_d_baseline - E_d_tau) * np.exp(-((tau - (tau_entry+tau_exit)/2)**2) / (0.1)**2)

    # Delta tau_effective = int (1 - E_d_baseline / E_d(tau)) dtau
    tau_vals = np.linspace(tau_entry, tau_exit, 1000)
    dtau = tau_vals[1] - tau_vals[0]

    integrand = 1 - (E_d_baseline / E_d_dip(tau_vals))
    delta_tau_eff = np.sum(integrand) * dtau

    return delta_tau_eff

if __name__ == "__main__":
    baseline = 1.0
    dip = 0.5  # E_d drops to 50%

    dwell_time = compute_negative_dwell_time(baseline, dip, 0, 1)
    print(f"Effective Dwell Time Change: {dwell_time:.4f}")
    if dwell_time < 0:
         print("Negative dwell time confirmed (Uniphics principle).")
