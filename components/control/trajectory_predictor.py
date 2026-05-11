import numpy as np
from scipy.optimize import minimize_scalar
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class CaptureWindow:
    start_time: float
    duration_ms: float
    confidence: float

def solve_intercept_time(pos, vel, L, theta, omega):
    """
    Simplificado: distância radial do payload ao centro = L
    """
    # Aproximação muito simples para tempo de interceptação
    r0 = np.linalg.norm(pos)
    vr = np.dot(pos, vel) / r0 if r0 > 0 else np.linalg.norm(vel)

    # Se está indo para longe, não intercepta
    if vr >= 0:
        return float('inf')

    # Quando r = L?
    # r(t) = r0 + vr * t = L => t = (L - r0) / vr
    t = (L - r0) / vr
    return max(0.0, t)

def compute_jacobian(pos, vel, theta, omega, L):
    """
    Jacobiano simplificado do tempo de interceptação.
    """
    H = np.zeros((1, 6))
    r0 = np.linalg.norm(pos)
    vr = np.dot(pos, vel) / r0 if r0 > 0 else np.linalg.norm(vel)

    if vr == 0:
        return H

    # dt/dr0 = -1/vr
    # dr0/dx = x/r0
    H[0, 0:3] = -pos / (r0 * vr)

    # dt/dvr = -(L-r0)/vr^2
    # dvr/dvx = x/r0
    H[0, 3:6] = -((L - r0) / (vr**2)) * (pos / r0)

    return H

def compute_relative_velocity(payload_state, L, theta, omega_max):
    vel = np.array(payload_state["velocity"])
    # Velocidade tangencial do tether no ponto L com fase theta
    # Assumindo omega = omega_max para matching
    v_tether = np.array([-omega_max * L * np.sin(theta), omega_max * L * np.cos(theta), 0])
    return vel - v_tether

class TrajectoryPredictor:
    """Prevê trajetória do payload e calcula fase ótima de tether para captura."""

    def __init__(self, tether_length_km: float = 22.0, max_tip_velocity_kms: float = 2.5):
        self.L = tether_length_km * 1000  # metros
        self.v_max = max_tip_velocity_kms * 1000  # m/s
        self.omega_max = self.v_max / self.L  # rad/s máximo seguro

    def predict_capture_window(self, payload_state: Dict, tether_state: Dict) -> CaptureWindow:
        """
        Calcula janela de captura com incerteza.

        Returns:
            CaptureWindow com start_time, duration_ms, confidence
        """
        # Extrair estado do payload (posição, velocidade, incerteza)
        pos = np.array(payload_state["position"])
        vel = np.array(payload_state["velocity"])
        cov = np.array(payload_state["covariance"])  # 6x6

        # Extrair estado do tether (fase angular, velocidade angular)
        theta = tether_state["phase_rad"]
        omega = tether_state["angular_velocity"]

        # Calcular tempo até interceptação (solução de equação de movimento relativo)
        # Simplificado: assumir movimento retilíneo uniforme para payload
        # e movimento circular uniforme para ponta do tether
        t_intercept = solve_intercept_time(pos, vel, self.L, theta, omega)

        # Propagar incerteza via linearização (EKF simplificado)
        H = compute_jacobian(pos, vel, theta, omega, self.L)
        P_intercept = H @ cov @ H.T + tether_state["phase_covariance"]

        # Janela de captura: tempo onde probabilidade de interceptação > 95%
        sigma_t = np.sqrt(np.diag(P_intercept)[0]) if P_intercept.ndim > 1 else np.sqrt(P_intercept)  # incerteza em tempo
        duration_ms = 4 * sigma_t * 1000  # 95% confidence interval

        # Garantir mínimo de 200 ms para grappling
        duration_ms = max(duration_ms, 200)

        return CaptureWindow(
            start_time=t_intercept - duration_ms/2000,
            duration_ms=duration_ms,
            confidence=0.95
        )

    def compute_optimal_phase(self, payload_state: Dict, target_window_ms: float = 200) -> float:
        """Calcula fase angular ótima do tether para maximizar janela de captura."""
        # Otimizar theta para alinear velocidade do tether com payload
        # Minimizar diferença de velocidade relativa no ponto de interceptação
        # Usar gradiente descendente com restrição |omega| <= omega_max

        def objective(theta):
            v_rel = compute_relative_velocity(payload_state, self.L, theta, self.omega_max)
            return np.linalg.norm(v_rel)

        theta_opt = minimize_scalar(objective, bounds=(0, 2*np.pi), method='bounded').x
        return theta_opt
