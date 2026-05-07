import numpy as np
from arkhe_os.temporal.floquet_driven_qubit import FloquetParameters

def floquet_coherence_metric(
    baseline_coherence: float,
    driving_params: FloquetParameters,
    operation_time: float,
    gamma_0: float = 1.0
) -> dict:
    """
    Calcula Φ_C^Floquet = Φ_C^(0) · exp[(Ω_R/ω_d) · sinc(ω_d τ)]

    Retorna dicionário com métricas detalhadas para auditoria.
    """
    omega_d = driving_params.omega_d
    omega_R = driving_params.omega_R
    tau = operation_time

    # Fator de ganho de Floquet
    sinc_term = np.sinc(omega_d * tau / np.pi)  # np.sinc usa π normalizado
    gain_factor = np.exp((omega_R / omega_d) * sinc_term)

    # Coerência efetiva
    phi_c_floquet = baseline_coherence * gain_factor

    # Métricas auxiliares
    effective_gamma = gamma_0 * np.exp(-(omega_R**2)/(omega_d**2))
    t2_improvement = gamma_0 / effective_gamma if effective_gamma > 0 else float('inf')

    return {
        "phi_c_baseline": baseline_coherence,
        "phi_c_floquet": phi_c_floquet,
        "gain_factor": gain_factor,
        "sinc_term": sinc_term,
        "effective_decoherence_rate": effective_gamma,
        "t2_improvement_factor": t2_improvement,
        "floquet_periods_in_operation": tau / (2*np.pi/omega_d),
        "stability_regime": _classify_stability_regime(omega_R, omega_d)
    }

def _classify_stability_regime(omega_R: float, omega_d: float) -> str:
    """Classifica o regime de estabilidade baseado na razão Ω_R/ω_d."""
    ratio = omega_R / omega_d if omega_d > 0 else 0
    if ratio < 0.1:
        return "weak_driving"      # Pouco ganho, regime perturbativo
    elif ratio < 1.0:
        return "optimal_driving"   # Ganho significativo, regime ideal
    elif ratio < 10.0:
        return "strong_driving"    # Ganho máximo, cuidado com aquecimento
    else:
        return "ultra_strong"      # Regime não-perturbativo, efeitos exóticos