# arkhe_os/metrics/floquet_coherence.py
import numpy as np
from arkhe_os.temporal.floquet_driven_qubit import FloquetParameters

def floquet_coherence_metric(
    baseline_coherence: float,
    driving_params: FloquetParameters,
    operation_time: float,
    gamma_0: float = 1.0
) -> dict:
    omega_d = driving_params.omega_d
    omega_R = driving_params.omega_R
    tau = operation_time

    sinc_term = np.sinc(omega_d * tau / np.pi)

    if omega_d > 0:
        gain_factor = np.exp((omega_R / omega_d) * sinc_term)
        effective_gamma = gamma_0 * np.exp(-(omega_R**2)/(omega_d**2))
        floquet_periods = tau / (2*np.pi/omega_d)
    else:
        gain_factor = 1.0
        effective_gamma = gamma_0
        floquet_periods = 0.0

    phi_c_floquet = baseline_coherence * gain_factor

    t2_improvement = gamma_0 / effective_gamma if effective_gamma > 0 else float('inf')

    return {
        "phi_c_baseline": baseline_coherence,
        "phi_c_floquet": phi_c_floquet,
        "gain_factor": gain_factor,
        "sinc_term": sinc_term,
        "effective_decoherence_rate": effective_gamma,
        "t2_improvement_factor": t2_improvement,
        "floquet_periods_in_operation": floquet_periods,
        "stability_regime": _classify_stability_regime(omega_R, omega_d)
    }

def _classify_stability_regime(omega_R: float, omega_d: float) -> str:
    ratio = omega_R / omega_d if omega_d > 0 else 0
    if ratio < 0.1:
        return "weak_driving"
    elif ratio < 1.0:
        return "optimal_driving"
    elif ratio < 10.0:
        return "strong_driving"
    else:
        return "ultra_strong"
