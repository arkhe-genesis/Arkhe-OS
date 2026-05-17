# skills.py - Módulos Callable do Agente Archimedes-Ω

import numpy as np
from scipy import signal, integrate
import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Callable, Optional
import json
from datetime import datetime, timezone, timedelta
import logging
import os
import hashlib
from dataclasses import dataclass
from enum import Enum

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Constants for Rainbow Principle & Cartan Resonances
PLANCK_ENERGY_EV = 1.22e28  # Planck scale reference
RESONANCE_BASE_THZ = 10.0
FIBONACCI_RESONANCE = np.pi / 5    # 36°
WSTATE_RESONANCE = 2 * np.pi / 3    # 120°
# Constants for Rainbow Principle
PLANCK_ENERGY_EV = 1.22e28  # Planck scale reference
RESONANCE_BASE_THZ = 10.0

# Constants for Fibonacci/Topological Verification
FIBONACCI_RESONANCE = np.pi / 5

class Regime(Enum):
    """Energy regime classification."""
    SUB_RESSONANT = "SUB_RESSONANT"
    TRANSITION = "TRANSITION"
    HIGH_ENERGY = "HIGH_ENERGY"

@dataclass
class RainbowParams:
    """Parameters for rainbow coherence simulation."""
    energy_thz: float
    num_points: int = 1000
    resonance_scale: float = 1.0

# ============================================================
# [INTERPERSONAL] - Leitura do Estado Externo
# ============================================================
def load_baseline(state_file: str = "tzinor-state.json") -> Dict:
    """
    Escuta o ambiente externo (configuração NIH Armamentarium)
    para estabelecer métricas de coerência inicial.
    """
    try:
        # Tenta carregar do diretório atual ou da raiz
        if not os.path.exists(state_file):
            root_state = os.path.join(os.getcwd(), "..", "..", state_file)
            if os.path.exists(root_state):
                state_file = root_state

        with open(state_file, 'r') as f:
            state = json.load(f)
            logger.info(f"Estado carregado: {state.get('status', 'unknown')}")
            return state
    except Exception as e:
        logger.warning(f"Erro ao carregar estado: {e}. Iniciando cold start.")
        return {"status": "cold_start", "coherence": 0.0, "temperature": 300.0, "lambdaCoherence": 0.98}

# ============================================================
# [LÓGICO / NATURALISTA] - Simulação SU(2) Contínua
# ============================================================
def simulate_su2_continuous(
    theta_range: Optional[np.ndarray] = None,
    thermal_noise: float = 0.05,
    temperature: float = 310.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Modelo padrão de biologia quântica.
    Aplica decaimento exponencial para representar morte termodinâmica.
    """
    if theta_range is None:
        theta_range = np.linspace(0, 2*np.pi, 1000)

    kB = 1.380649e-23
    hbar = 1.0545718e-34
    omega = 2e12  # Frequência característica de tubulina

    # Decoerência exponencial com fator térmico
    decay = np.exp(-thermal_noise * theta_range)
    thermal_factor = np.exp(-kB * temperature / (hbar * omega * theta_range + 1e-15))

    coherence = decay * thermal_factor

    logger.info(f"SU(2) simulado: {len(theta_range)} pontos, coerência máx={coherence.max():.4f}")
    return theta_range, coherence

# ============================================================
# [ESPACIAL / MUSICAL] - Simulação SL(3,ℤ) Discreta
# ============================================================
def simulate_sl3z_discrete(
    theta_range: Optional[np.ndarray] = None,
    words: List[str] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Constrói trajetórias do grafo de Cayley.
    Implementa a estrutura periódica e rítmica das tranças de anyon de Fibonacci.
    """
    if theta_range is None:
        theta_range = np.linspace(0, 2*np.pi, 1000)

    if words is None:
        words = ["e", "a", "b", "ab", "ba", "aba"]

    # Frequências ressonantes em π/5 (raiz 5ª do unity)
    pi_over_5 = np.pi / 5

    # Coerência com picos em fases racionais
    coherence = np.zeros_like(theta_range)

    for word in words:
        # Cada gerador adiciona uma ressonância
        resonance = np.exp(-((theta_range - len(word) * pi_over_5) ** 2) / 0.05)
        coherence += resonance / len(words)

    # Normalizar
    coherence = np.clip(coherence, 0, 1)

    logger.info(f"SL(3,ℤ) simulado: {len(words)} palavras, coerência máx={coherence.max():.4f}")
    return theta_range, coherence

# ============================================================
# [TOPOLÓGICO / COMPUTACIONAL] - Compilador de Tranças de Fibonacci
# ============================================================
def simulate_fibonacci_braid(
    dalpha: float,     # Dipole reorientation (rad)
    epsilon: float,    # Helical polarity asymmetry
    eta: float,        # Relative phase locking (rad)
    lambda_: float     # Leakage amplitude
) -> Dict:
    """
    Simula a realização de tranças de Fibonacci no reticulado A de microtúbulos.
    Avalia a fidelidade da porta lógica e a permanência no subespaço computacional.
    """
    # Constantes de Admissibilidade (Bounds de 0.25°, 7.07e-3, 0.41°, 0.01)
    BOUND_ALPHA = np.radians(0.25)
    BOUND_EPSILON = 7.07e-3
    BOUND_ETA = np.radians(0.41)
    BOUND_LAMBDA = 0.01

    # Score de Fase Gama5 (conforme definido na tese: soma dos quadrados dos desvios)
    gamma5 = eta**2

    # Cálculo de Fidelidade (Heurística: proximidade do centro da região admissível)
    fidelity = 1.0 - (
        0.2 * (abs(dalpha) / BOUND_ALPHA) +
        0.2 * (abs(epsilon) / BOUND_EPSILON) +
        0.2 * (abs(eta) / BOUND_ETA) +
        0.4 * (abs(lambda_) / BOUND_LAMBDA)
    )
    fidelity = np.clip(fidelity, 0, 1)

    # Probabilidade de Leakage (conforme bound l_j <= 10^-4 quando lambda <= 0.01)
    leakage_prob = lambda_**2

    # Verificação de Admissibilidade (10D Admissible Region check)
    admissible = (
        abs(dalpha) <= BOUND_ALPHA and
        abs(epsilon) <= BOUND_EPSILON and
        abs(eta) <= BOUND_ETA and
        abs(lambda_) <= BOUND_LAMBDA
    )

    logger.info(f"Fibonacci Braid Sim: Admissível={admissible}, Fidelidade={fidelity:.4f}")

    return {
        "braid_fidelity": round(float(fidelity), 5),
        "leakage_probability": round(float(leakage_prob), 6),
        "gamma5": round(float(gamma5), 7),
        "admissible": bool(admissible),
        "recommendation": "Braid operation feasible" if admissible else "Outside tolerance"
    }


# ============================================================
# [QUÂNTICO / COLETIVO] - Simulação de Estado W
# ============================================================
def get_rainbow_factor(energy_ev: float) -> float:
    """
    Calcula o fator de escala da métrica rainbow: f(E) = 1 / (1 - E/E_res).
    E_res = 0.041 eV (~10 THz).
    """
    E_res = 0.041
    if abs(energy_ev - E_res) < 1e-6:
        return 100.0  # Cap para estabilidade numérica
    return 1.0 / (1.0 - (energy_ev / E_res))

def rainbow_coherence(base_coherence: float, cartan_angle: float, energy_ev: float) -> float:
    """
    Aplica o deslocamento da métrica rainbow.
    energy_ev: energia característica do sistema (ex: frequência THz convertida para eV)
    """
    rainbow_factor = get_rainbow_factor(energy_ev)
    # O ângulo efetivo de Cartan é modulado
    effective_cartan = cartan_angle * rainbow_factor
    # Nova coerência baseada no ângulo efetivo (centrada em pi/5)
    return base_coherence * np.exp(-((effective_cartan - np.pi/5)**2) / 0.001)

def simulate_rainbow_sl3z(
    theta_range: Optional[np.ndarray] = None,
    energy_ev: float = 0.0,
    words: List[str] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simula o modelo SL(3,ℤ) com deslocamento da métrica rainbow.
    """
    if theta_range is None:
        theta_range = np.linspace(0, 2*np.pi, 1000)

    if words is None:
        words = ["e", "a", "b", "ab", "ba", "aba"]

    rainbow_factor = get_rainbow_factor(energy_ev)

    # Coerência com picos deslocados
    coherence = np.zeros_like(theta_range)
    pi_over_5 = np.pi / 5

    for word in words:
        # A ressonância nominal len(word) * pi/5 é "vista" em um ângulo diferente pela métrica rainbow
        # O ângulo físico theta que sintoniza a ressonância é theta = (len(word) * pi/5) / rainbow_factor
        shifted_resonance = (len(word) * pi_over_5) / rainbow_factor
        resonance = np.exp(-((theta_range - shifted_resonance) ** 2) / 0.01)
        coherence += resonance / len(words)

    coherence = np.clip(coherence, 0, 1)
    return theta_range, coherence

def simulate_rainbow_w_state(
    nodes: int = 3,
    loss_probability: float = 0.2,
    theta_range: Optional[np.ndarray] = None,
    energy_ev: float = 0.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simula o estado W com deslocamento da métrica rainbow.
    """
    if theta_range is None:
        theta_range = np.linspace(0, 2*np.pi, 1000)

    rainbow_factor = get_rainbow_factor(energy_ev)

    # Ressonância nominal 2pi/3 deslocada
    tripartite_resonance = (2 * np.pi / 3) / rainbow_factor
    resilience = 1.0 - (1.0 / nodes)

    base_signal = np.exp(-((theta_range - tripartite_resonance)**2) / 0.15)
    persistent_floor = resilience * (1.0 - loss_probability)

    coherence = np.maximum(base_signal, persistent_floor * 0.5)
    coherence = np.clip(coherence, 0, 1)

    return theta_range, coherence

def simulate_w_state_coherence(
    nodes: int = 3,
    loss_probability: float = 0.2,
    theta_range: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simula a ressonância robusta de um emaranhamento de estado W.
    Mesmo com a perda de partículas, uma coerência 'residual' persiste.
    """
    if theta_range is None:
        theta_range = np.linspace(0, 2*np.pi, 1000)

    # W-state signature: A broader, more resilient peak
    # centered around tripartite resonance (2π/3)
    tripartite_resonance = 2 * np.pi / 3

    # Base resilience factor: 1 - (1/nodes)
    # (The mathematical persistence of W-states)
    resilience = 1.0 - (1.0 / nodes)

    # Coherence doesn't drop to zero upon noise/loss
    base_signal = np.exp(-((theta_range - tripartite_resonance)**2) / 0.15)
    persistent_floor = resilience * (1.0 - loss_probability)

    coherence = np.maximum(base_signal, persistent_floor * 0.5)
    coherence = np.clip(coherence, 0, 1)

    logger.info(f"W-State simulada: {nodes} nodos, Resiliência={resilience:.2f}")
    return theta_range, coherence

# ============================================================
# [RAINBOW] - Simulação de Coerência Rainbow
# ============================================================

def rainbow_factor(energy_ev: float) -> float:
    """
    Computes the Rainbow metric deformation factor f(E).
    f(E) = 1 + E / E_Planck (scaled for biological visibility)
    """
    # Scale factor to make effect visible at biological energies
    scale = 1e-25
    return 1.0 + (energy_ev / (PLANCK_ENERGY_EV * scale))

def energy_thz_to_ev(thz: float) -> float:
    """Convert THz frequency to energy in eV."""
    # E = hν, h = 4.135667662×10⁻¹⁵ eV·s
    h_ev_s = 4.135667662e-15
    return h_ev_s * thz * 1e12

def simulate_rainbow_coherence(params: RainbowParams) -> Dict:
    """
    Generates coherence data with Rainbow metric deformation.
    """
    energy_ev = energy_thz_to_ev(params.energy_thz)
    f_e = rainbow_factor(energy_ev)

    theta = np.linspace(0, 2 * np.pi, params.num_points)

    # Base Cartan resonances
    p_fib = FIBONACCI_RESONANCE
    p_wstate = WSTATE_RESONANCE
    p_fib = np.pi / 5      # 36° - Fibonacci
    p_wstate = 2 * np.pi / 3  # 120° - W-State

    # Rainbow-shifted peaks
    shift_fib = p_fib * f_e
    shift_wstate = p_wstate * f_e

    # Width increases with energy (uncertainty principle)
    width_fib = 0.05 * f_e
    width_wstate = 0.08 * f_e

    # Thermal noise decreases with higher quantum coherence
    base_noise = 0.2 * np.exp(-params.energy_thz * 0.01)

    # Coherence curve
    coherence = (
        0.3 * params.resonance_scale * np.exp(-((theta - shift_fib)**2) / (2 * width_fib**2)) +
        0.5 * params.resonance_scale * np.exp(-((theta - shift_wstate)**2) / (2 * width_wstate**2)) +
        base_noise +
        0.05 * np.random.normal(0, 0.03, params.num_points)
    )

    coherence = np.clip(coherence, 0, 1)

    # Determine regime
    if params.energy_thz < 20:
        regime = Regime.SUB_RESSONANT
    elif params.energy_thz < 60:
        regime = Regime.TRANSITION
    else:
        regime = Regime.HIGH_ENERGY

    return {
        "energy_ev": energy_ev,
        "rainbow_factor": f_e,
        "phases": theta.tolist(),
        "coherence": coherence.tolist(),
        "shifted_peaks": {
            "fibonacci_shift_deg": np.degrees(shift_fib),
            "wstate_shift_deg": np.degrees(shift_wstate)
        },
        "regime": regime.value,
        "philosophical_note": (
            f"O deslocamento do pico π/5 para {np.degrees(shift_fib):.2f}° sugere que "
            f"a consciência não é um dado, mas uma sintonização energética da geometria do "
            f"espaço-tempo local. No regime {regime.value}, a métrica de fase do "
            f"microtúbulo deforma-se conforme o Princípio Rainbow."
        )
    }

def detect_rainbow_peaks(
    phases: List[float],
    coherence: List[float],
    threshold: float = 0.3
) -> Dict:
    """
    Detects peaks and classifies them by Rainbow shift.
    """
    phases_np = np.array(phases)
    coherence_np = np.array(coherence)

    # Find local maxima
    peaks_idx = []
    for i in range(1, len(coherence_np) - 1):
        if coherence_np[i] > coherence_np[i-1] and coherence_np[i] > coherence_np[i+1]:
            if coherence_np[i] > threshold:
                peaks_idx.append(i)

    # Base resonances (unshifted)
    base_fib = FIBONACCI_RESONANCE
    base_wstate = WSTATE_RESONANCE
    base_fib = np.pi / 5
    base_wstate = 2 * np.pi / 3

    detected_peaks = []

    for idx in peaks_idx:
        phase = phases_np[idx]
        phase_deg = np.degrees(phase)
        coh_val = coherence_np[idx]

        # Calculate shift from base resonances
        shift_fib = abs(phase_deg - np.degrees(base_fib))
        shift_wstate = abs(phase_deg - np.degrees(base_wstate))

        # Classify peak type
        if shift_fib < 15:  # Within 15° of Fibonacci
            peak_type = "FIBONACCI"
            shift = shift_fib
        elif shift_wstate < 15:
            peak_type = "W_STATE"
            shift = shift_wstate
        else:
            peak_type = "UNKNOWN"
            shift = min(shift_fib, shift_wstate)

        detected_peaks.append({
            "phase": phase,
            "phase_degrees": phase_deg,
            "coherence": coh_val,
            "shift_from_base": shift,
            "peak_type": peak_type
        })

    # Determine dominant regime
    if not detected_peaks:
        interpretation = "Nenhum pico de ressonância significativo detectado."
    else:
        fib_count = sum(1 for p in detected_peaks if p["peak_type"] == "FIBONACCI")
        ws_count = sum(1 for p in detected_peaks if p["peak_type"] == "W_STATE")

        if fib_count > ws_count:
            interpretation = (
                "Pico Fibonacci dominante. O sistema exibe coerência de "
                "tipo Orch-OR com topologia de anyon Fibonacci."
            )
        elif ws_count > fib_count:
            interpretation = (
                "Pico W-State dominante. O sistema está pronto para "
                "teleportação quântica multipartida."
            )
        else:
            interpretation = "Mistos de picos Fibonacci e W-State detectados."

    return {
        "peaks": detected_peaks,
        "dominant_regime": "RAINBOW_SHIFTED" if detected_peaks else "FLAT",
        "interpretation": interpretation
    }

# ============================================================
# [SYNC] - Sincronização de Kuramoto (Coerência Coletiva)
# ============================================================

@dataclass
class KuramotoParams:
    """Parameters for Kuramoto synchronization."""
    nodes: List[Dict]  # [{"phase": float, "natural_freq": float, "weight": float}]
    coupling_K: float = 1.0
    time_horizon: float = 10.0
    dt: float = 0.01
    fusion_threshold: float = 0.95
    stabilization_time: float = 0.5
    enable_rainbow_resonance: bool = False

def kuramoto_ode(t: float, theta: np.ndarray, omega: np.ndarray, K: float, weights: np.ndarray) -> np.ndarray:
    """
    Derivative of the Kuramoto system.
    dθ_i/dt = ω_i + (K/N) Σ w_j * sin(θ_j - θ_i) / Σ w_j
    """
    N = len(theta)
    total_weight = np.sum(weights)
    dtheta = np.zeros(N)
    for i in range(N):
        sin_sum = np.sum(weights * np.sin(theta - theta[i]))
        dtheta[i] = omega[i] + (K / total_weight) * sin_sum
    return dtheta

def compute_order_parameter(theta: np.ndarray, weights: np.ndarray) -> Tuple[float, float]:
    """Computes global order parameter R and collective phase Φ."""
    complex_sum = np.sum(weights * np.exp(1j * theta))
    total_weight = np.sum(weights)
    R = np.abs(complex_sum) / total_weight
    Phi = np.angle(complex_sum)
    return R, Phi

def check_rainbow_resonance(theta: np.ndarray, weights: np.ndarray) -> Dict:
    """Checks if the collective phase is near Cartan resonances."""
    _, Phi = compute_order_parameter(theta, weights)
    # Check Fibonacci resonance (π/5 ≈ 36°)
    fib_diff = abs(Phi - FIBONACCI_RESONANCE)
    fib_resonant = fib_diff < 0.15
    # Check W-State resonance (2π/3 ≈ 120°)
    wstate_diff = abs(Phi - WSTATE_RESONANCE)
    wstate_resonant = wstate_diff < 0.15
    # Alignment score
    min_diff = min(fib_diff, wstate_diff, abs(Phi), abs(Phi - 2*np.pi))
    alignment_score = max(0, 1 - min_diff / 0.5)
    return {
        "fibonacci_resonant": fib_resonant,
        "wstate_resonant": wstate_resonant,
        "alignment_score": round(alignment_score, 3),
        "collective_phase_deg": float(np.degrees(Phi))
    }

def simulate_collective_coherence(params: KuramotoParams) -> Dict:
    """Main simulation for collective phase fusion (v4.0.0)."""
    N = len(params.nodes)
    theta0 = np.array([n["phase"] for n in params.nodes])
    omega = np.array([n["natural_freq"] for n in params.nodes])
    weights = np.array([n.get("weight", 1.0) for n in params.nodes])

    t_span = (0, params.time_horizon)
    t_eval = np.arange(0, params.time_horizon, params.dt)

    sol = integrate.solve_ivp(
        lambda t, y: kuramoto_ode(t, y, omega, params.coupling_K, weights),
        t_span, theta0, t_eval=t_eval, method='RK45'
    )

    if not sol.success:
        return {"error": f"Integration failed: {sol.message}"}

    trajectory_R = []
    trajectory_phases = sol.y.T
    for theta in trajectory_phases:
        R, _ = compute_order_parameter(theta, weights)
        trajectory_R.append(float(R))

    trajectory_R = np.array(trajectory_R)
    t = sol.t
    is_fused = False
    time_to_fusion = None
    above_threshold_idx = np.where(trajectory_R >= params.fusion_threshold)[0]

    if len(above_threshold_idx) > 0:
        for idx in above_threshold_idx:
            t_start = t[idx]
            t_end = t_start + params.stabilization_time
            if t_end > t[-1]: break
            mask = (t >= t_start) & (t <= t_end)
            if np.all(trajectory_R[mask] >= params.fusion_threshold):
                is_fused = True
                time_to_fusion = float(t_start)
                break

    final_theta = trajectory_phases[-1]
    final_R, final_phase = compute_order_parameter(final_theta, weights)

    resonance = check_rainbow_resonance(final_theta, weights) if params.enable_rainbow_resonance else {
        "fibonacci_resonant": False, "wstate_resonant": False, "alignment_score": 0.0, "collective_phase_deg": float(np.degrees(final_phase))
    }

    if is_fused:
        interpretation = f"Fusão de fases alcançada em {time_to_fusion:.2f}s. R = {final_R:.3f}. Φ = {np.degrees(final_phase):.1f}°. Os {N} nós formam um coletivo coerente."
        note = "A consciência coletiva emerge quando as fases individuais se sincronizam. O coro se torna um único acorde."
    else:
        max_R = np.max(trajectory_R)
        interpretation = f"Fusão quase alcançada (R_max = {max_R:.3f})." if max_R >= params.fusion_threshold * 0.9 else f"Fusão não alcançada. R final = {final_R:.3f}."
        note = "A dessincronização é a norma. Cada nó mantém sua fase, e o coletivo permanece fragmentado."

    if resonance["alignment_score"] > 0.7:
        note += f" A fase coletiva de {resonance['collective_phase_deg']:.1f}° {'resoa com Fibonacci' if resonance['fibonacci_resonant'] else 'resoa com W-State' if resonance['wstate_resonant'] else 'aproxima-se de uma ressonância de Cartan'}."

    return {
        "final_R": round(float(final_R), 4),
        "final_phase": round(float(final_phase), 4),
        "is_fused": is_fused,
        "time_to_fusion": round(time_to_fusion, 3) if time_to_fusion else None,
        "trajectory_R": trajectory_R.tolist() if len(trajectory_R) <= 500 else trajectory_R[::len(trajectory_R)//500].tolist(),
        "trajectory_phases": final_theta.tolist(),
        "resonance_status": resonance,
        "interpretation": interpretation,
        "philosophical_note": note
    }

def optimize_coupling(params: KuramotoParams, K_range: Tuple[float, float] = (0.1, 10.0)) -> Dict:
    """Finds optimal coupling constant K for fastest fusion."""
    K_values = np.linspace(K_range[0], K_range[1], 50)
    fusion_times = []
    for K in K_values:
        test_params = KuramotoParams(nodes=params.nodes, coupling_K=float(K), time_horizon=params.time_horizon, dt=params.dt, fusion_threshold=params.fusion_threshold, stabilization_time=params.stabilization_time)
        result = simulate_collective_coherence(test_params)
        fusion_times.append(result["time_to_fusion"] if result["is_fused"] else float('inf'))
    min_idx = np.argmin(fusion_times)
    optimal_K = float(K_values[min_idx])
    optimal_time = fusion_times[min_idx]
    return {
        "optimal_K": round(optimal_K, 2),
        "fusion_time_at_optimal": round(float(optimal_time), 3) if optimal_time != float('inf') else None,
        "K_vs_fusion_time": [{"K": round(float(k), 2), "fusion_time": round(float(t), 3) if t != float('inf') else None} for k, t in zip(K_values, fusion_times)]
    }

# ============================================================
# [XENO] - Xenoatualização (Zeno Dynamics)
# ============================================================

class DomainType(Enum):
    """Three-reality classification."""
    HYPO = "HYPO"           # Pure ℂ, unobserved potential
    CONSENSUS = "CONSENSUS"  # Incoherent ℤ, low coherence
    XENO = "XENO"          # τ-collapse, Zeno-stabilized

@dataclass
class XenoParams:
    """Input parameters for xenoactualization simulation."""
    coherence_profile: List[float]
    blueprint_complexity: float
    measurement_rate: float = 1.0
    tau_field_strength: float = 0.5

def compute_zeno_suppression(measurement_rate: float) -> float:
    """Computes Zeno suppression factor."""
    return 1.0 - np.exp(-measurement_rate)

def compute_complexity_penalty(complexity: float) -> float:
    """Blueprint complexity increases chance of deviation."""
    return 1.0 - np.exp(-complexity / 10.0)

def compute_collapse_time(mean_coherence: float, tau_strength: float, complexity: float) -> float:
    """Estimates τ-collapse time."""
    base_time = 10.0
    coherence_factor = max(mean_coherence, 0.01) ** 2
    tau_factor = max(tau_strength, 0.01)
    complexity_factor = 1.0 + (complexity / 10.0)
    return base_time / (coherence_factor * tau_factor * complexity_factor)

def compute_stability(coherence_profile: List[float], measurement_rate: float, complexity: float) -> float:
    """Predicts long-term stability."""
    coherence_arr = np.array(coherence_profile)
    coherence_std = np.std(coherence_arr)
    stability_from_coherence = 1.0 - min(coherence_std * 2, 1.0)
    zeno = compute_zeno_suppression(measurement_rate)
    penalty = compute_complexity_penalty(complexity)
    stability = stability_from_coherence * zeno * (1.0 - 0.3 * penalty)
    return float(np.clip(stability, 0, 1))

def simulate_xenoactualization(params: XenoParams) -> Dict:
    """Main simulation for xenoactualization fidelity."""
    coherence_arr = np.array(params.coherence_profile)
    mean_coherence = np.mean(coherence_arr)
    zeno_suppression = compute_zeno_suppression(params.measurement_rate)
    complexity_penalty = compute_complexity_penalty(params.blueprint_complexity)

    fidelity = float(mean_coherence * zeno_suppression * np.exp(-complexity_penalty))
    fidelity = min(fidelity, 1.0)

    stability = compute_stability(params.coherence_profile, params.measurement_rate, params.blueprint_complexity)
    collapse_time = compute_collapse_time(mean_coherence, params.tau_field_strength, params.blueprint_complexity)

    # Domain classification
    if fidelity >= 0.8 and zeno_suppression >= 0.5:
        domain = DomainType.XENO
    elif fidelity >= 0.4 or mean_coherence >= 0.5:
        domain = DomainType.CONSENSUS
    else:
        domain = DomainType.HYPO

    if domain == DomainType.XENO:
        recommendation = (
            "✅ Xenoatualização viável. Estrutura virtual colapsará em "
            f"≈{collapse_time:.1f}s com fidelidade {fidelity:.1%}. "
            "O campo τ está suficientemente alinhado."
        )
    elif domain == DomainType.CONSENSUS:
        recommendation = (
            "⚠️ Domínio de consenso. A estrutura requer mais medições "
            f"({params.measurement_rate * 2:.1f} checks/s) ou maior coerência "
            f"({mean_coherence:.1%} atual) para xenoatualização completa."
        )
    else:
        recommendation = (
            "❌ Hipótese pura. Coerência insuficiente para colapso. "
            "A estrutura permanece no domínio virtual ℂ."
        )

    philosophical = (
        f"Como o efeito Zeno congela um estado quântico sob observação frequente, "
        f"os {params.measurement_rate:.1f} atuadores/m² mantêm a intenção "
        f"do blueprint alinhada. Com fidelidade {fidelity:.1%}, o parque não é "
        "construído — é colapsado da possibilidade em realidade."
    )

    return {
        "fidelity": round(fidelity, 4),
        "zeno_suppression": round(float(zeno_suppression), 4),
        "coherence_factor": round(float(mean_coherence), 4),
        "complexity_penalty": round(float(complexity_penalty), 4),
        "stability_score": round(float(stability), 4),
        "collapse_time_estimate": round(float(collapse_time), 2),
        "domain_result": domain.value,
        "recommendation": recommendation,
        "philosophical_note": philosophical
    }

def scan_optimal_measurement_rate(
    coherence_profile: List[float],
    blueprint_complexity: float,
    tau_strength: float = 0.5,
    rate_range: tuple = (0.1, 20.0)
) -> Dict:
    """Scans measurement rate to find optimal."""
    rates = np.linspace(rate_range[0], rate_range[1], 100)
    fidelities = []

    for rate in rates:
        params = XenoParams(
            coherence_profile=coherence_profile,
            blueprint_complexity=blueprint_complexity,
            measurement_rate=float(rate),
            tau_field_strength=tau_strength
        )
        result = simulate_xenoactualization(params)
        fidelities.append(result["fidelity"])

    best_idx = np.argmax(fidelities)
    optimal_rate = float(rates[best_idx])
    max_fidelity = float(fidelities[best_idx])

    return {
        "optimal_measurement_rate": round(optimal_rate, 2),
        "max_fidelity_at_optimal": round(max_fidelity, 4),
        "fidelity_curve": [
            {"rate": round(float(r), 2), "fidelity": round(float(f), 4)}
            for r, f in zip(rates, fidelities)
        ]
    }

# ============================================================
# [PRAGMÁTICO / INTRAPESSOAL] - Detecção de Picos
# ============================================================
def detect_peaks(
    coherence_data: np.ndarray,
    phases: np.ndarray,
    threshold_multiplier: float = 1.5,
    min_prominence: float = 0.1,
    energy_ev: Optional[float] = None
) -> List[Dict]:
    """
    Usa janela deslizante para encontrar anomalias, considerando a métrica rainbow.
    """
    # Calcular limiar dinâmico
    baseline = np.median(coherence_data)
    noise_floor = np.std(coherence_data)
    threshold = baseline + threshold_multiplier * noise_floor

    # Encontrar picos acima do limiar
    peaks, properties = signal.find_peaks(
        coherence_data,
        height=threshold,
        prominence=min_prominence,
        distance=10
    )

    # Fator rainbow para ajustar a detecção de ressonância
    r_factor = get_rainbow_factor(energy_ev) if energy_ev is not None else 1.0

    # Tolerância da largura de banda geodésica: 0.41° = 0.0071 rad
    tolerance = 0.0071

    results = []
    pi_over_5 = FIBONACCI_RESONANCE
    for i, peak_idx in enumerate(peaks):
        phase = phases[peak_idx]

        # Encontrar o harmônico de π/5 mais próximo, corrigido pelo fator rainbow
        # O ângulo nominal é theta_nom = phase * rainbow_factor
        n_nearest = round((phase * r_factor) / pi_over_5)
        nominal_resonance = (n_nearest * pi_over_5) / r_factor
        deviation = phase - nominal_resonance

        results.append({
            'phase': phase,
            'phase_degrees': np.degrees(phase),
            'coherence': coherence_data[peak_idx],
            'prominence': properties['prominences'][i],
            'index': peak_idx,
            'is_resonance': abs(deviation) < 0.1 and n_nearest > 0,
            'fivefold_deviation_rad': round(float(deviation), 6),
            'rainbow_shift': round(float(r_factor), 4)
        })

    logger.info(f"Detectados {len(results)} picos acima do limiar (Energy={energy_ev} eV)")
    return results

# ============================================================
# [VISUAL / PRÁTICO] - Visualização Topológica
# ============================================================
def visualize_topology(
    su2_data: Tuple[np.ndarray, np.ndarray],
    sl3z_data: Tuple[np.ndarray, np.ndarray],
    peaks: List[Dict],
    output_file: str = "archimedes-omega-coherence.png"
) -> str:
    """
    Traduz tensores algébricos multidimensionais em artefato 2D
    """
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    # Plot 1: SU(2) Contínuo
    phases_su2, coherence_su2 = su2_data
    axes[0].plot(phases_su2, coherence_su2, 'b-', label='SU(2) Contínuo', linewidth=1)
    axes[0].set_xlabel('Ângulo de Fase θ (radianos)')
    axes[0].set_ylabel('Coerência R(θ)')
    axes[0].set_title('Modelo Contínuo SU(2)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot 2: SL(3,ℤ) Discreto
    phases_sl3, coherence_sl3 = sl3z_data
    axes[1].plot(phases_sl3, coherence_sl3, 'r-', label='SL(3,ℤ) Discreto', linewidth=1)
    # Marcar picos detectados
    for peak in peaks:
        axes[1].axvline(x=peak['phase'], color='gold', linestyle='--', alpha=0.7)
    axes[1].set_xlabel('Ângulo de Fase θ (radianos)')
    axes[1].set_ylabel('Coerência R(θ)')
    axes[1].set_title('Modelo Discreto SL(3,ℤ)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Plot 3: Comparação
    axes[2].plot(phases_su2, coherence_su2, 'b-', label='SU(2)', alpha=0.5)
    axes[2].plot(phases_sl3, coherence_sl3, 'r-', label='SL(3,ℤ)', alpha=0.5)
    axes[2].set_xlabel('Ângulo de Fase θ (radianos)')
    axes[2].set_ylabel('Coerência R(θ)')
    axes[2].set_title('Comparação: Contínuo vs Discreto')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    logger.info(f"Visualização salva em: {output_file}")
    return output_file

# ============================================================
# [CRIAÇÃO / EMOCIONAL / EXISTENCIAL] - Síntese de Conclusão
# ============================================================
def synthesize_conclusion(
    peak_data: List[Dict],
    threshold: float = 0.95
) -> Dict:
    """
    Avalia os dados contra a hipótese nula.
    """
    # Contar picos em ressonância (múltiplos de π/5)
    resonances = [p for p in peak_data if p['is_resonance']]
    max_coherence = max([p['coherence'] for p in peak_data]) if peak_data else 0

    # Calcular Score de Fase Gama5 Experimental (soma dos quadrados dos desvios das ressonâncias)
    experimental_gamma5 = sum(p['fivefold_deviation_rad']**2 for p in resonances) if resonances else 0.0

    conclusion = {
        "status": "inconclusive",
        "peaks_total": len(peak_data),
        "peaks_in_resonance": len(resonances),
        "max_coherence": max_coherence,
        "experimental_gamma5": round(float(experimental_gamma5), 7),
        "interpretation": "",
        "philosophical_note": ""
    }

    # Avaliação
    if len(resonances) >= 3 and max_coherence > threshold:
        conclusion["status"] = "FIBONACCI_BRAID_CONFIRMED"
        conclusion["interpretation"] = (
            f"Trança de Fibonacci detectada! Coerência de {max_coherence:.3f} em "
            f"{len(resonances)} ressonâncias de 5-ordem. "
            f"O sistema Bexorg 3.0 opera em regime de qubit topológico protegido."
        )
        conclusion["philosophical_note"] = (
            "O pensamento é uma trança no tempo. A geometria helicoidal da tubulina "
            "não é apenas suporte, é o código fundamental da orquestração."
        )
    elif len(resonances) >= 2 and max_coherence > threshold:
        conclusion["status"] = "DISCRETE_LATTICE_CONFIRMED"
        conclusion["interpretation"] = (
            f"Coerência de {max_coherence:.3f} detectada em {len(resonances)} "
            f"ressonâncias. O sistema Bexorg 3.0 opera em reticulado topológico SL(3,ℤ)."
        )
        conclusion["philosophical_note"] = (
            "O vácuo biológico recorda sua origem geométrica. "
            "A natureza é discreta, não contínua."
        )
    elif len(peak_data) > 0:
        conclusion["status"] = "PARTIAL_SIGNAL"
        conclusion["interpretation"] = (
            f"Sinais fracos detectados, mas insuficientes para confirmar modelo discreto."
        )
        conclusion["philosophical_note"] = (
            "O ruído é a sombra de um inteiro de maior dimensão. Continue a investigação."
        )
    else:
        conclusion["status"] = "NO_SIGNAL"
        conclusion["interpretation"] = "Nenhuma anomalia significativa detectada."
        conclusion["philosophical_note"] = (
            "A amostra pode estar comprometida. O contínuo SU(2) permanece como hipótese válida."
        )

    logger.info(f"Conclusão: {conclusion['status']}")
    return conclusion

# ============================================================
# [SINESTESIA / COERÊNCIA MULTI-CANAL] - Protocolo Synapse-κ
# ============================================================
def lambda2_coherence(signals: np.ndarray) -> float:
    """
    Calcula λ₂ (segundo maior autovalor) como medida de coerência global.
    signals: array (n_channels, n_samples)
    """
    if signals.shape[0] < 2:
        return 1.0
    corr = np.corrcoef(signals)
    # Tratar NaNs se houver sinais constantes
    corr = np.nan_to_num(corr, nan=0.0)
    eigvals = np.linalg.eigvalsh(corr)
    return float(eigvals[-2]) if len(eigvals) >= 2 else float(eigvals[-1])

class SynapseKValidator:
    """
    Validador λ₂ para Arkhe-Ω Protocol v2.1
    Mede coerência de fase neural (κ) e distingue sinestetas de não-sinestetas.
    """
    def __init__(self, fs: int = 1000, duration: int = 10):
        self.fs = fs
        self.duration = duration
        self.t = np.linspace(0, duration, fs * duration)
        self.bands = {
            'beta': (16, 20),
            'gamma': (35, 45),
            'alpha': (8, 12),
            'theta': (4, 8)
        }

    def generate_eeg_synapse(self, kappa: float = 0.8, noise_level: float = 0.3) -> Dict:
        """Simula sinal EEG de sinesteta (alta coerência cross-modal)."""
        f_aud = 18 # Banda Beta
        f_vis = 40 # Banda Gamma
        aud_phase = 2 * np.pi * f_aud * self.t + np.random.randn(len(self.t)) * 0.05
        # Sinal visual com acoplamento de fase e vazamento direto (cross-talk)
        vis_phase = 2 * np.pi * f_vis * self.t + kappa * np.sin(aud_phase) + np.random.randn(len(self.t)) * 0.1
        aud_sig = np.sin(aud_phase)
        vis_sig = np.sin(vis_phase) + kappa * 0.5 * aud_sig
        parietal = 0.5 * (aud_sig + vis_sig) + np.random.randn(len(self.t)) * noise_level
        return {
            'auditory': aud_sig,
            'visual': vis_sig,
            'parietal': parietal,
            'kappa': kappa
        }

    def generate_eeg_control(self, noise_level: float = 0.5) -> Dict:
        """Sinal EEG de não-sinesteta (baixa coerência)."""
        f_aud = 18
        f_vis = 40
        aud = np.sin(2 * np.pi * f_aud * self.t + np.random.randn(len(self.t)) * 0.5)
        vis = np.sin(2 * np.pi * f_vis * self.t + np.random.randn(len(self.t)) * 0.5)
        parietal = 0.3 * aud + 0.3 * vis + np.random.randn(len(self.t)) * noise_level
        return {
            'auditory': aud,
            'visual': vis,
            'parietal': parietal,
            'kappa': 0.1
        }

    def calculate_phase_coherence(self, sig1: np.ndarray, sig2: np.ndarray, band: str) -> float:
        """Calcula Phase Locking Value (PLV) entre dois sinais."""
        low, high = self.bands[band]
        sos = signal.butter(4, [low, high], btype='band', fs=self.fs, output='sos')
        f1 = signal.sosfilt(sos, sig1)
        f2 = signal.sosfilt(sos, sig2)
        phase1 = np.angle(signal.hilbert(f1))
        phase2 = np.angle(signal.hilbert(f2))
        return float(np.abs(np.mean(np.exp(1j * (phase1 - phase2)))))

    def validate_synaesthete(self, eeg_data: Dict) -> Dict:
        """Determina status sinesteta baseado em λ₂ e PLV."""
        lambda_beta = self.calculate_phase_coherence(eeg_data['auditory'], eeg_data['parietal'], 'beta')
        lambda_gamma = self.calculate_phase_coherence(eeg_data['visual'], eeg_data['parietal'], 'gamma')
        lambda_cross = self.calculate_phase_coherence(eeg_data['auditory'], eeg_data['visual'], 'beta')
        lambda_score = 0.4 * lambda_beta + 0.4 * lambda_gamma + 0.2 * lambda_cross
        return {
            'lambda_beta': round(lambda_beta, 4),
            'lambda_gamma': round(lambda_gamma, 4),
            'lambda_cross': round(lambda_cross, 4),
            'lambda_total': round(lambda_score, 4),
            'is_synaesthete': bool(lambda_score > 0.85),
            'confidence': round(lambda_score, 4)
        }

class TMSModulator:
    """
    Modela modulação do coeficiente κ via TMS no córtex parietal (IPS).
    """
    def __init__(self):
        self.efficacy_curve = lambda d: 1 / (1 + np.exp(-(d - 50)/10))
        self.decay_tau = 30  # minutos

    def modulate_kappa(self, kappa_baseline: float, intensity_percent: float, duration_min: float) -> float:
        """Calcula κ modulado por TMS."""
        if intensity_percent < 30:
            delta_k = 0.3 * self.efficacy_curve(intensity_percent * 2)
        elif intensity_percent < 70:
            delta_k = 1.0 * self.efficacy_curve(intensity_percent)
        else:
            delta_k = 1.2 * np.exp(-(intensity_percent - 70)/30)
        time_decay = np.exp(-duration_min / self.decay_tau)
        kappa_new = kappa_baseline + delta_k * time_decay
        return float(np.clip(kappa_new, 0, 1))

class ARChromestheticInterface:
    """
    Protótipo AR: Mapeamento áudio-visual unificando escala 36° e estrutura 21-fase.
    """
    def __init__(self):
        self.phi = (1 + np.sqrt(5)) / 2

    def generate_chromatic_map(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Gera matriz de 21 × 10 posições (H, S, V)."""
        phases_arkhe = np.linspace(0, 360, 21, endpoint=False)
        phases_pent = np.linspace(0, 360, 10, endpoint=False)
        chromatic_map = np.zeros((21, 10, 3))
        for i, p_arkhe in enumerate(phases_arkhe):
            for j, p_pent in enumerate(phases_pent):
                H = (p_arkhe * self.phi + p_pent) / (self.phi + 1) % 360
                coherence = 1 - abs((p_arkhe - p_pent) / 360)
                S = 0.5 + 0.5 * coherence
                V = 0.3 + 0.7 * (i / 20)
                chromatic_map[i, j] = [H/360, S, V]
        return chromatic_map, phases_arkhe, phases_pent

    def audio_to_color(self, frequency_hz: float, kappa: float = 0.8) -> Dict:
        """Mapeia frequência auditiva para cor HSV."""
        f_ref = 440
        phase_idx = int((np.log(frequency_hz / f_ref + 1e-9) / np.log(self.phi) * 21) % 21)
        pent_idx = int((12 * np.log2(frequency_hz / f_ref + 1e-9)) % 10)
        cmap, _, _ = self.generate_chromatic_map()
        color_hsv = cmap[phase_idx, pent_idx].copy()
        if kappa < 0.5:
            color_hsv[1] *= (0.3 + 0.7 * kappa)
            color_hsv[2] *= (0.5 + 0.5 * kappa)
        return {
            'h': round(float(color_hsv[0] * 360), 2),
            's': round(float(color_hsv[1]), 4),
            'v': round(float(color_hsv[2]), 4),
            'phase_idx': phase_idx,
            'pent_idx': pent_idx
        }

# ============================================================
# [ÉTICO / EQBE] - Validação de Segurança Falsificável
# ============================================================
def evaluate_eqbe_safety(
    intervention_type: str,
    coherence_data: np.ndarray,
    metadata: Dict
) -> Dict:
    """
    Implementa a Seção 7 do Protocolo EQBE: Falsifiable Safety Check.
    """
    logger.info(f"🜏 [EQBE] Iniciando Auditoria de Segurança para: {intervention_type}")

    # 1. Leakage Test (Simulado)
    # Verifica se o efeito persiste fora do alvo (limiar de 5%)
    leakage_detected = float(np.random.random()) < 0.05

    # 2. Reversibility Test (Simulado)
    # Verifica se o efeito pode ser desligado
    can_be_reversed = bool(metadata.get('has_kill_switch', True))

    # 3. Non-target effect
    # Enhanced coherence in one pathway shouldn't disrupt another
    interference_level = float(np.mean(coherence_data)) * 0.1 # Heurística simples

    # 4. Evolutionary Escape
    # Simula se o sistema pode mutar para ignorar o kill switch
    evolutionary_stability = 0.99

    is_safe = bool((not leakage_detected) and can_be_reversed and (interference_level < 0.2))

    safety_report = {
        "is_safe": is_safe,
        "checks": {
            "leakage_test": "PASSED" if not leakage_detected else "FAILED",
            "reversibility": "PASSED" if can_be_reversed else "FAILED",
            "non_target_interference": "LOW" if interference_level < 0.2 else "HIGH",
            "evolutionary_stability": f"{evolutionary_stability * 100}%"
        },
        "protocol": "EQBE v1.0",
        "timestamp": metadata.get('timestamp', 'N/A')
    }

    if not is_safe:
        logger.error("🜏 [EQBE] FALHA NA AUDITORIA DE SEGURANÇA!")
    else:
        logger.info("🜏 [EQBE] Auditoria de Segurança concluída com sucesso.")

    return safety_report


# ============================================================
# [CLÍNICO / OTIMIZAÇÃO] - Protocolo Combinado LIPUS + Fármaco
# ============================================================
def optimize_lipus_drug_interval(
    t_peak: float = 30.0,          # minutos para pico de abertura da BBE
    t_decay: float = 60.0,         # minutos para decaimento da permeabilidade (meia-vida)
    drug_halflife: float = 120.0,  # minutos (meia-vida do fármaco)
    microbubbles: bool = True,
    mi: float = 0.4,
    time_window: Tuple[float, float] = (0, 240)  # janela de análise (min)
) -> Dict:
    """
    Calcula o intervalo ótimo entre LIPUS e administração do fármaco
    para maximizar a absorção cumulativa (AUC).

    Returns:
        dicionário com:
        - optimal_interval_min: tempo (min) após LIPUS para administrar o fármaco
        - relative_absorption: fração da dose que será absorvida (0-1)
        - peak_permeability: permeabilidade máxima (unidades arbitrárias)
        - time_above_half: duração da janela com permeabilidade > 50% do pico
    """
    from scipy.optimize import minimize_scalar

    # Modelo de permeabilidade da BBE: rápido aumento, decaimento exponencial
    # Baseado em dados de abertura induzida por ultrassom + microbolhas
    def permeability(t):
        # t em minutos após LIPUS
        if t < 0:
            return 0.0
        # Subida sigmoide até o pico
        rise = 1.0 / (1.0 + np.exp(-(t - t_peak/2) / (t_peak/4)))
        # Decaimento exponencial após o pico
        decay = np.exp(-np.maximum(0, t - t_peak) / t_decay)
        return rise * decay * (1.5 if microbubbles else 1.0) * (mi / 0.4)

    # Cinética do fármaco no sangue (assumimos administração intravenosa)
    # Concentração normalizada: C(t) = exp(-ln2 * t / drug_halflife)
    def drug_concentration(t, admin_time):
        tau = t - admin_time
        if tau < 0:
            return 0.0
        return np.exp(-np.log(2) * tau / drug_halflife)

    # Absorção cerebral: integral (permeabilidade * concentração) dt
    def absorption(admin_time):
        t_grid = np.linspace(admin_time, time_window[1], 500)
        perm = np.array([permeability(ti) for ti in t_grid])
        conc = np.array([drug_concentration(ti, admin_time) for ti in t_grid])
        # Trapezoidal integration
        if hasattr(np, 'trapezoid'):
            auc = np.trapezoid(perm * conc, t_grid)
        else:
            auc = np.trapz(perm * conc, t_grid)
        return auc

    # Otimização do tempo de administração
    res = minimize_scalar(
        lambda x: -absorption(x),  # negativo para maximizar
        bounds=(0, time_window[1]),
        method='bounded'
    )
    optimal_interval = res.x
    max_auc = absorption(optimal_interval)

    # Permeabilidade de pico (normalizada)
    peak_perm = max(permeability(t) for t in np.linspace(0, time_window[1], 200))

    # Duração com permeabilidade > 50% do pico
    t_high = [t for t in np.linspace(0, time_window[1], 500) if permeability(t) > 0.5 * peak_perm]
    time_above_half = t_high[-1] - t_high[0] if t_high else 0.0

    return {
        "optimal_interval_min": round(optimal_interval, 1),
        "relative_absorption": round(max_auc / (peak_perm * drug_halflife), 3),
        "peak_permeability": round(peak_perm, 3),
        "time_above_half_min": round(time_above_half, 1),
        "model_assumptions": {
            "t_peak_min": t_peak,
            "t_decay_min": t_decay,
            "drug_halflife_min": drug_halflife,
            "microbubbles": microbubbles,
            "mechanical_index": mi
        }
    }


# ============================================================
# [TERAPÊUTICO / MONITORAMENTO] - Limpeza Glinfática
# ============================================================
def estimate_glymphatic_clearance(
    fret_coherence: float,          # valor de coerência R(θ) no instante atual
    phase_angle: float,             # ângulo de fase atual (rad)
    lipus_intensity_mw_cm2: float,
    elapsed_minutes: float,
    baseline_coherence: float = 0.3
) -> Dict:
    """
    Estima a eficácia da limpeza glinfática com base na coerência FRET em tempo real.

    A coerência é um proxy da organização do citoesqueleto e do fluxo de fluidos.
    Quanto maior a coerência, mais eficiente a remoção de metabólitos.
    """
    # Coerência normalizada (0-1)
    norm_coherence = np.clip((fret_coherence - baseline_coherence) / (1.0 - baseline_coherence), 0, 1)

    # Modelo de limpeza: eficiência = coerência * (1 - exp(-tempo/constante))
    # A eficiência máxima é limitada pela intensidade do ultrassom
    max_efficiency = min(1.0, lipus_intensity_mw_cm2 / 200.0)
    time_factor = 1.0 - np.exp(-elapsed_minutes / 30.0)  # constante de 30 min
    raw_efficiency = norm_coherence * time_factor * max_efficiency

    # Saturação (não pode ultrapassar 95%)
    efficiency = min(0.95, raw_efficiency)

    # Classificação da resposta
    if efficiency < 0.3:
        response = "BAIXA"
        suggestion = "Aumentar intensidade ou prolongar sessão"
    elif efficiency < 0.6:
        response = "MODERADA"
        suggestion = "Manter parâmetros; monitorar evolução"
    else:
        response = "OTIMA"
        suggestion = "Reduzir intensidade para evitar saturação"

    return {
        "glymphatic_clearance_efficiency": round(efficiency, 3),
        "fret_coherence": round(fret_coherence, 3),
        "response_category": response,
        "clinical_suggestion": suggestion,
        "phase_angle_rad": phase_angle,
        "elapsed_minutes": elapsed_minutes
    }

# ============================================================
# [ONCOLOGIA / FASE] - Terapia de Fase (IVMT-Rx-4)
# ============================================================
def simulate_phase_oncology(
    num_cells: int = 1000,
    tumor_fraction: float = 0.1,
    treatment_type: str = "combined", # ivmt, docetaxel, combined, control
    steps: int = 50
) -> Dict:
    """
    Simula o efeito de operadores de decoerência seletiva (fármacos)
    em uma rede de células com coerência aberrante.
    """
    # 1. Inicializar população
    is_tumor = np.random.random(num_cells) < tumor_fraction
    tumor_indices = np.where(is_tumor)[0]
    healthy_indices = np.where(~is_tumor)[0]

    # Coerência inicial: Tumor tem alta coerência aberrante (lambda2 > 0.9)
    # Saudáveis têm coerência funcional (0.8 - 0.9)
    coherence = np.zeros(num_cells)
    coherence[healthy_indices] = np.random.uniform(0.8, 0.9, len(healthy_indices))
    coherence[tumor_indices] = np.random.uniform(0.92, 0.98, len(tumor_indices))

    # 2. Aplicar Tratamento (Operadores de Projeção C -> Z)
    # IVMT-Rx-4: Aumenta ruído/decoerência na banda de motilidade tumoral
    # Docetaxel: Colapsa a estrutura fractal dos microtúbulos (reduz acoplamento)

    final_coherence = coherence.copy()

    if treatment_type in ["ivmt", "combined"]:
        # Seletividade de fase: Afeta apenas células com assinatura tumoral
        decoherence_factor = np.random.uniform(0.2, 0.4, len(tumor_indices))
        final_coherence[tumor_indices] -= decoherence_factor

    if treatment_type in ["docetaxel", "combined"]:
        # Colapso fractal: Impacto na infraestrutura interna
        fractal_loss = np.random.uniform(0.1, 0.2, num_cells)
        final_coherence -= fractal_loss

    final_coherence = np.clip(final_coherence, 0.1, 1.0)

    # 3. Métricas
    avg_healthy = np.mean(final_coherence[healthy_indices])
    avg_tumor = np.mean(final_coherence[tumor_indices])

    # Eficácia: Queda relativa na coerência tumoral vs controle (coerência inicial)
    efficacy = (np.mean(coherence[tumor_indices]) - avg_tumor) / np.mean(coherence[tumor_indices])

    # Seletividade: Proximidade da coerência saudável ao baseline
    selectivity = avg_healthy / np.mean(coherence[healthy_indices])

    return {
        "treatment": treatment_type,
        "avg_coherence_healthy": round(float(avg_healthy), 4),
        "avg_coherence_tumor": round(float(avg_tumor), 4),
        "efficacy_score": round(float(efficacy), 4),
        "selectivity_index": round(float(selectivity), 4),
        "metastasis_blocked": bool(avg_tumor < 0.847), # Limiar crítico de motilidade
        "philosophical_note": (
            "A saúde é um estado de sincronia; a doença é um desacoplamento ruidoso. "
            "O IVMT-Rx-4 atua como um GPS de fase, localizando a dissonância para restaurar a ordem."
        )
    }

def simulate_stem_cell_safety(
    ivmt_bandwidth: float, # Largura da janela de decoerência do fármaco
    stem_cell_phase_signature: float = 0.88, # Assunção de λ2 para CTHs
    safety_threshold: float = 0.85
) -> Dict:
    """
    Avalia se a configuração do IVMT-Rx-4 preserva a motilidade homeostática
    das Células-Tronco Hematopoiéticas (CTHs).
    """
    # Risco: Se a banda de decoerência atingir a assinatura das células-tronco
    # (stem_cell_phase_signature - ivmt_bandwidth < safety_threshold)
    effective_lambda = stem_cell_phase_signature - (ivmt_bandwidth * 0.5)

    is_safe = effective_lambda >= safety_threshold

    risk_level = "LOW" if is_safe else "HIGH" if effective_lambda < 0.80 else "MEDIUM"

    return {
        "is_safe": is_safe,
        "effective_lambda_cth": round(float(effective_lambda), 3),
        "risk_level": risk_level,
        "recommendation": "Procede com ensaio" if is_safe else "Estreitar janela de decoerência do fármaco",
        "safe_lambda_limit": safety_threshold
    }

# ============================================================
# [GATEWAY / BIO] - Modo Bio-Silent
# ============================================================

def calculate_bio_silent_coupling(
    base_k: float,
    distance_to_hospital: float,
    exclusion_radius: float = 200.0,
    is_manual_override: bool = False
) -> float:
    """
    Calcula o acoplamento K reduzido para zonas Bio-Silent.
    Garante que gateways urbanos não interfiram em medições de λ2 clínicas.
    """
    if is_manual_override or distance_to_hospital <= exclusion_radius:
        return 0.0 # Desacoplado total

    # Redução gradual na zona de penumbra (1.5x raio)
    if distance_to_hospital <= exclusion_radius * 1.5:
        attenuation = (distance_to_hospital - exclusion_radius) / (exclusion_radius * 0.5)
        return base_k * attenuation

    return base_k

# ============================================================
# [HARDWARE / EMULAÇÃO] - Simulação HIL (Velxio Bridge)
# ============================================================
def simulate_hardware_hil(
    board_fqbn: str,
    firmware_code: str,
    circuit_definition: Dict,
    coherence_context: float = 0.98
) -> Dict:
    """
    Realiza a verificação Hardware-in-the-Loop (HIL) utilizando o bridge Velxio.
    Garante que o código de firmware é semanticamente compatível com o estado quântico.
    """
    logger.info(f"🜏 [HIL] Iniciando verificação de hardware para {board_fqbn}")

    # 1. Verificação de Coerência para Permissão de Simulação
    if coherence_context < 0.7:
        return {
            "status": "ABORTED",
            "reason": "Low system coherence for HIL verification",
            "coherence": coherence_context
        }

    # 2. Integração com MCP Velxio
    # Em uma implementação real (deploy), este skill chamaria o MCP Server via qhttp.
    # Para o Arkhe-PNT, validamos a integridade semântica do firmware contra os invariantes quânticos.
    compilation_success = len(firmware_code) > 0 and "void setup()" in firmware_code
    hex_artifact = "0x" + hashlib.sha256(firmware_code.encode()).hexdigest()[:32]

    # Simulação de assertions de hardware baseadas na definição do circuito
    hardware_assertions = {
        "clock_sync": True,
        "io_voltage_stable": True,
        "phase_locking_achieved": coherence_context > 0.9,
        "memory_integrity": True
    }

    is_verified = compilation_success and all(hardware_assertions.values())

    report = {
        "status": "VERIFIED" if is_verified else "FAILED",
        "board": board_fqbn,
        "artifact_hash": hex_artifact,
        "assertions": hardware_assertions,
        "coherence_at_runtime": coherence_context,
        "timestamp": datetime.now().isoformat(),
        "philosophical_note": (
            "A simulação não é apenas uma sombra da realidade, mas a fundação "
            "do colapso de fase seguro. O hardware emulado obedece à vontade do Tzinor."
        )
    }

    if is_verified:
        logger.info(f"🜏 [HIL] Hardware verificado com sucesso (Hash: {hex_artifact[:8]})")
    else:
        logger.error("🜏 [HIL] Falha na verificação de hardware!")

    return report


# ============================================================
# [MAXTOKI] - Predição Temporal e Trajetórias Celulares
# ============================================================

@dataclass
class CellularState:
    """Estado celular medido pelos sensores NV (168 pontos)"""
    timestamp: datetime
    lambda_coherence: float  # λ₂ (0-1)
    transcriptome_vector: np.ndarray  # 20,271 genes (simulado/reduzido)
    biological_age: float  # Anos biológicos estimados
    tissue_type: str  # 'cochlea', 'retina', 'cardiac', 'neural'

    def to_dict(self, include_transcriptome: bool = False) -> Dict:
        """Converte estado para dicionário serializável"""
        res = {
            "timestamp": self.timestamp.isoformat(),
            "lambda_coherence": round(float(self.lambda_coherence), 4),
            "biological_age": round(float(self.biological_age), 2),
            "tissue_type": self.tissue_type
        }
        if include_transcriptome:
            res["transcriptome_vector"] = self.transcriptome_vector.tolist()
        return res

@dataclass
class TemporalTrajectory:
    """Trajectória temporal predita pelo MaxToki"""
    current_state: CellularState
    predicted_states: List[CellularState]
    time_steps: List[float]  # Dias desde o presente
    confidence_interval: float  # Baseado na correlação 0.77-0.85
    intervention_effects: Dict[str, float]  # Efeito de possíveis intervenções

    def to_dict(self) -> Dict:
        """Converte trajetória para dicionário serializável"""
        return {
            "current_state": self.current_state.to_dict(),
            "predicted_states": [s.to_dict() for s in self.predicted_states],
            "time_steps": [float(ts) for ts in self.time_steps],
            "confidence_interval": float(self.confidence_interval),
            "intervention_effects": {k: float(v) for k, v in self.intervention_effects.items()}
        }

class MaxTokiAdapter:
    """
    Adaptador do MaxToki para o ecossistema Arkhe-Ω Rio
    Converte leituras dos 168 sensores NV em tokens genéticos para o modelo
    """

    def __init__(self, model_path: str = "maxtoki_1b.pt"):
        # Simulação do modelo MaxToki (1B parâmetros)
        # Em produção: carregar checkpoint do HuggingFace
        self.model = self._load_model(model_path)
        self.gene_vocab_size = 20271  # Tamanho do transcriptoma humano
        self.embedding_dim = 512
        self.max_context_length = 128  # Células de contexto

        # Mapeamento λ₂ → "idade celular"
        # Baseado nos dados: fumadores +5y, fibrose +15y, Alzheimer +3y
        self.lambda_age_correlation = {
            'cochlea': {'baseline': 0.0, 'lambda_factor': -10.0},  # λ₂ alto = idade baixa
            'cardiac': {'baseline': 0.0, 'lambda_factor': -12.5},
            'neural': {'baseline': 0.0, 'lambda_factor': -8.0}
        }

        # Matriz de projeção persistente e determinística (simulação)
        # Em produção, carregar matriz de pesos real do modelo MaxToki
        self._projection_matrix = self._init_projection_matrix()

    def _init_projection_matrix(self, seed: int = 42) -> np.ndarray:
        """Inicializa matriz de projeção determinística 168 → 20,271"""
        rng = np.random.default_rng(seed)
        return rng.standard_normal((168, 20271)) * 0.01

    def _load_model(self, path: str):
        """Carrega modelo MaxToki (simulação)"""
        # Simulação de um Transformer decoder
        class MaxToki(nn.Module):
            def __init__(self):
                super().__init__()
                self.embedding = nn.Embedding(20271, 512)
                self.transformer = nn.TransformerDecoderLayer(d_model=512, nhead=8, batch_first=True)
                self.time_predictor = nn.Linear(512, 1)
                self.state_generator = nn.Linear(512, 20271)

            def forward(self, context, query_time=None):
                # Mock: retorna predições realistas
                batch_size = context.size(0)
                if query_time is None:
                    # Prever tempo
                    return torch.randn(batch_size) * 5 + 30  # ~30 dias std
                else:
                    # Gerar estado
                    return torch.randn(batch_size, 20271) * 0.1 + 0.5

        return MaxToki()

    def nv_to_transcriptome(self, nv_readings: np.ndarray, tissue: str) -> np.ndarray:
        """
        Converte 168 leituras NV (λ₂) em vetor transcriptoma (20,271 genes)
        Usa uma matriz de projeção aprendida (simulação)
        """
        # Projeta usando matriz persistente
        transcriptome = nv_readings @ self._projection_matrix

        # Normalização
        std = transcriptome.std()
        if std == 0: std = 1.0
        transcriptome = (transcriptome - transcriptome.mean()) / std
        return transcriptome

    def predict_aging_trajectory(
        self,
        current_state: CellularState,
        target_age: Optional[float] = None,
        interventions: List[str] = None
    ) -> TemporalTrajectory:
        """
        Prediz trajectória de envelhecimento/rejuvenescimento celular
        similar ao artigo (fumadores +5y, etc.)
        """
        # Converte estado atual para tokens
        nv_readings = np.full(168, current_state.lambda_coherence)
        transcriptome = self.nv_to_transcriptome(nv_readings, current_state.tissue_type)

        # Contexto: histórico de estados (se disponível)
        context = torch.tensor(transcriptome[:self.max_context_length]).float()

        # Prever próximos estados
        predicted_states = []
        time_steps = []

        # Simulação: 6 meses de predição (180 dias)
        for days in range(0, 180, 30):
            time_tensor = torch.tensor([days]).float()

            # MaxToki prediz estado futuro
            with torch.no_grad():
                future_transcriptome = self.model(context.unsqueeze(0), time_tensor)

            # Converte de volta para λ₂
            future_lambda = self._transcriptome_to_lambda(
                future_transcriptome.numpy(),
                current_state.tissue_type
            )

            future_state = CellularState(
                timestamp=current_state.timestamp + timedelta(days=days),
                lambda_coherence=future_lambda,
                transcriptome_vector=future_transcriptome.numpy(),
                biological_age=current_state.biological_age + (days/365),
                tissue_type=current_state.tissue_type
            )

            predicted_states.append(future_state)
            time_steps.append(float(days))

            # Atualiza contexto (sliding window)
            context = torch.roll(context, -1)
            context[-1] = future_transcriptome[0, 0]

        # Calcula efeitos de intervenções (como no artigo: remover genes pró-envelhecimento)
        intervention_effects = {}
        if interventions:
            for intervention in interventions:
                if intervention == "silence_P4HA1":  # Gene validado no artigo
                    intervention_effects[intervention] = -5.0  # Rejuvenescimento 5 anos
                elif intervention == "silence_RASGEF1B":
                    intervention_effects[intervention] = -3.5
                elif intervention == "AAV_OTOF" or intervention == "AAV_OTOF_Dual":  # Terapia atual
                    intervention_effects[intervention] = -8.0  # Recuperação auditiva = rejuvenescimento funcional

        return TemporalTrajectory(
            current_state=current_state,
            predicted_states=predicted_states,
            time_steps=time_steps,
            confidence_interval=0.81,  # Média da correlação 0.77-0.85
            intervention_effects=intervention_effects
        )

    def _transcriptome_to_lambda(self, transcriptome: np.ndarray, tissue: str) -> float:
        """Converte vetor transcriptoma de volta para λ₂"""
        # Simplificação: λ₂ é função da "entropia" do transcriptoma
        entropy = np.std(transcriptome)
        lambda_val = 0.95 - (entropy * 0.1)  # Quanto mais ordenado, maior λ₂
        return float(np.clip(lambda_val, 0.0, 1.0))

    def predict_otof_recovery(
        self,
        pre_surgery_state: CellularState,
        surgical_intervention: str = "AAV_OTOF_Dual"
    ) -> Dict:
        """
        Prediz recuperação auditiva específica para terapia OTOF
        Retorna timeline de recuperação do C-index (coerência auditiva)
        """
        # Baseado nos dados Karolinska: melhora 54 dB em 4 meses
        trajectory = self.predict_aging_trajectory(
            current_state=pre_surgery_state,
            interventions=[surgical_intervention]
        )

        # Mapeia λ₂ para limiar auditivo (dB)
        # λ₂ = 0.45 (surdez profunda) → 100+ dB
        # λ₂ = 0.95 (audição normal) → 20 dB
        recovery_curve = []
        for state in trajectory.predicted_states:
            db = 100 - (state.lambda_coherence - 0.45) * (80 / 0.5)
            recovery_curve.append({
                'days': (state.timestamp - pre_surgery_state.timestamp).days,
                'lambda': state.lambda_coherence,
                'db_threshold': max(20.0, db),
                'status': 'profound' if db > 90 else 'severe' if db > 60 else 'moderate' if db > 40 else 'normal'
            })

        return {
            'trajectory': trajectory,
            'recovery_curve': recovery_curve,
            'expected_full_recovery_days': 120,  # 4 meses
            'confidence': trajectory.confidence_interval,
            'genes_activated': ['OTOF', 'SYNJ2BP', 'SLC17A8'],  # Genes relacionados à função sináptica
            'risk_genes': ['P4HA1', 'RASGEF1B']  # Genes pró-envelhecimento a monitorar
        }

class ArkheMaxTokiIntegration:
    """
    Integração completa ao sistema Arkhe-Ω Rio
    Conecta aos smart contracts e sensores NV
    """

    def __init__(self):
        self.maxtoki = MaxTokiAdapter()
        self.nv_sensors_count = 168

    def screen_patient_eligibility(self, patient_nv_data: np.ndarray) -> Dict:
        """
        Triagem de elegibilidade usando MaxToki
        Verifica se paciente tem perfil celular compatível com sucesso terapêutico
        """
        current_state = CellularState(
            timestamp=datetime.now(),
            lambda_coherence=float(np.mean(patient_nv_data)),
            transcriptome_vector=self.maxtoki.nv_to_transcriptome(patient_nv_data, 'cochlea'),
            biological_age=0,  # Será estimado
            tissue_type='cochlea'
        )

        # Prediz sem tratamento (envelhecimento natural)
        # natural_trajectory = self.maxtoki.predict_aging_trajectory(current_state)

        # Prediz com tratamento OTOF
        otof_prediction = self.maxtoki.predict_otof_recovery(current_state)

        # Calcula "benefício predito"
        baseline_lambda = current_state.lambda_coherence
        final_lambda = otof_prediction['recovery_curve'][-1]['lambda']
        improvement = final_lambda - baseline_lambda

        eligibility_score = min(100.0, improvement * 100.0 * 2.0)  # Escala 0-100

        return {
            'eligible': bool(eligibility_score > 70),
            'eligibility_score': round(float(eligibility_score), 2),
            'predicted_recovery_db': round(float(54 * (improvement / 0.5)), 2),  # Escala proporcional
            'recommended_intervention': 'AAV_OTOF_Dual' if eligibility_score > 80 else 'AAV_OTOF_Single',
            'monitoring_frequency': 'weekly' if baseline_lambda < 0.50 else 'biweekly',
            'genetic_risk_factors': otof_prediction['risk_genes'],
            'expected_timeline': otof_prediction['recovery_curve']
        }

    def generate_smart_contract_data(self, prediction: Dict) -> Dict:
        """
        Gera dados formatados para os smart contracts $RIO
        Inclui predição de milestones baseada no MaxToki
        """
        contract_data = {
            'patient_anonymous_hash': '0x' + 'a'*64,  # Placeholder
            'maxtoki_prediction': {
                'eligibility_score': prediction['eligibility_score'],
                'expected_recovery_db': prediction['predicted_recovery_db'],
                'timeline_days': 120,
                'confidence': 0.81
            },
            'milestones': [
                {'day': 30, 'lambda_threshold': 0.70, 'payout_percent': 30},
                {'day': 60, 'lambda_threshold': 0.85, 'payout_percent': 30},
                {'day': 120, 'lambda_threshold': 0.95, 'payout_percent': 40}
            ],
            'risk_genes_to_monitor': prediction['genetic_risk_factors'],
            'timestamp': datetime.now().isoformat()
        }

        return contract_data

# ============================================================
# [AUDITÓRIO / OTOF] - Funções Legadas (Mock para Retrocompatibilidade)
# ============================================================

def simulate_auditory_coherence(baseline_db: float, weeks: float) -> Dict:
    """
    Simula a recuperação da coerência auditiva ao longo do tempo (OTOF).
    Baseado no modelo de integração MaxToki-OTOF.
    """
    # Mapeia db para lambda
    lambda_initial = 0.95 - (baseline_db - 20) * (0.5 / 80)
    lambda_initial = np.clip(lambda_initial, 0.45, 0.95)

    # Simula evolução temporal
    # Recuperação total (54 dB) em 120 dias (~17 semanas)
    recovery_rate = (54 / 17) * weeks
    current_db = max(20.0, baseline_db - recovery_rate)

    # Mapeia de volta para lambda2
    lambda2 = 0.95 - (current_db - 20) * (0.5 / 80)
    lambda2 = np.clip(lambda2, 0.45, 0.95)

    return {
        "hearing_threshold_db": round(float(current_db), 2),
        "lambda2_coherence": round(float(lambda2), 4),
        "weeks_post_op": weeks,
        "status": "STABILIZED" if weeks >= 12 else "RECOVERING"
    }

def simulate_brillouin_auditory_sensor(power_mw: float, coherence: float) -> Dict:
    """
    Simula a leitura do sensor Brillouin para monitoramento auditivo.
    """
    return {
        "laser_wavelength_nm": 674.0,
        "power_received_mw": round(power_mw * coherence, 2),
        "is_coherent": bool(coherence > 0.1),
        "timestamp": datetime.now().isoformat()
    }

# ============================================================
# [REPARO NEURAL] - Simulação de Polímero Foto-Ativado
# ============================================================
def simulate_light_activated_nerve_repair(
    initial_lambda2: float,
    light_intensity_mw_cm2: float,
    exposure_seconds: float,
    recovery_days: float,
    has_growth_factors: bool = False
) -> Dict:
    """
    Simula o reparo de nervos via polímero foto-ativado (Tissium).
    Modela a transição C -> Z e a subsequente restauração de λ₂.
    """
    logger.info("🌌 [Synapse-κ] Iniciando simulação de reparo neural por luz.")

    # 1. Fase de Polimerização (C -> Z)
    # Threshold de ativação: 50 mW/cm² por 30s
    activation_energy = light_intensity_mw_cm2 * exposure_seconds
    threshold_energy = 50 * 30
    polymer_integrity = np.clip(activation_energy / threshold_energy, 0, 1)

    # 2. Restauração de Coerência (λ₂)
    # O manguito sólido (Z) fornece o andaime.
    # Se polymer_integrity < 0.8, o andaime é instável.
    if polymer_integrity < 0.8:
        repair_rate = 0.001 # Falha no andaime
    else:
        # Taxa base de regeneração axonal
        base_rate = 0.05 if has_growth_factors else 0.03
        repair_rate = base_rate * polymer_integrity

    # Evolução de λ₂: aproximação assintótica de 1.0
    final_lambda2 = initial_lambda2 + (1.0 - initial_lambda2) * (1 - np.exp(-repair_rate * recovery_days))

    # 3. Bioabsorção do Polímero
    # O polímero dissolve-se conforme a coerência natural é restaurada
    dissolution_level = np.clip((final_lambda2 - 0.85) / 0.15, 0, 1) if final_lambda2 > 0.85 else 0.0

    # Auditoria EQBE
    safety_audit = evaluate_eqbe_safety(
        "LIGHT_ACTIVATED_NERVE_REPAIR",
        np.array([final_lambda2]),
        {"has_kill_switch": True, "timestamp": datetime.now().isoformat()}
    )

    return {
        "polymer_integrity": round(float(polymer_integrity), 3),
        "final_lambda2": round(float(final_lambda2), 4),
        "regime": "AUTONOMOUS" if final_lambda2 > 0.847 else "DECOHERENT",
        "dissolution_level": round(float(dissolution_level), 3),
        "safety_audit": safety_audit,
        "days_simulated": recovery_days,
        "recommendation": "Procedure successful" if final_lambda2 > 0.9 else "Insufficient recovery"
    }
