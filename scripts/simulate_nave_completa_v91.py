import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from dataclasses import dataclass
from typing import Dict, List, Tuple
import os
import time

# ============================================================================
# ARKHE OS v∞.91 — SIMULAR A NAVE COMPLETA (PILOTO + CASCADA + VELA)
# CANONIZAÇÃO DO 154º SUBSTRATO
# ============================================================================

PARSEC_TO_METERS = 3.086e16

@dataclass
class ShipState:
    t: float
    position_pc: float  # Posição em parsecs
    velocity_c: float   # Velocidade em unidades de c
    A_drive: float
    bio_coherence: float
    effective_mass: float
    metric_component: float
    thrust: float
    flat_band_detected: bool
    portal_detected: bool

class NeuralPilot_v82:
    """Piloto Neural (v∞.82): Interface consciente que modula o drive."""
    def __init__(self, f_neural: float = 60.0, alpha: float = 0.5):
        self.f_neural = f_neural
        self.alpha = alpha

    def get_A_t(self, t: float, A_base: float, scrambling_theta: float) -> float:
        """
        A(t) = A_0 + α * sin(2π * 60Hz * t) * M_bio(t) * Theta_scrambling(t)
        Simulamos M_bio caindo com stress e subindo com estabilidade.
        """
        # Coerência bio-neural (simulada)
        M_bio = 0.8 + 0.2 * np.sin(2 * np.pi * 0.1 * t)

        # O sinal de 60Hz (bio-ELF) interage com o drive
        A_t = A_base + self.alpha * np.sin(2 * np.pi * self.f_neural * t) * M_bio * scrambling_theta
        return max(0.0, A_t), M_bio

class FloquetMetaCrystal3D_v90:
    """Meta-Cristal Floquet 3D (v∞.90): Generalização da Cascada UAP para 3D."""
    def __init__(self, J_hop: float = 1.0, omega_0: float = 0.5):
        self.J_hop = J_hop
        self.omega_0 = omega_0

    def compute_effective_metric_3d(self, k: np.ndarray, omega_drive: float, A_drive: float) -> Tuple[float, float, bool, bool]:
        """
        Versão otimizada e simplificada do cálculo da métrica 3D para o loop dinâmico.
        Em 3D, a energia é influenciada pelos 3 eixos de k = (kx, ky, kz).
        """
        # Em vez do cálculo pesado da matriz Floquet completa para cada passo dt,
        # usamos uma aproximação baseada na relação de dispersão efetiva do limite de alta frequência:
        # E_eff(k) ≈ -J_eff * (cos(kx) + cos(ky) + cos(kz))
        # onde J_eff ≈ J_hop * BesselJ_0(A_drive / omega_drive)

        from scipy.special import j0

        J_eff = self.J_hop * j0(A_drive / omega_drive)

        kx, ky, kz = k
        cos_sum = np.cos(kx) + np.cos(ky) + np.cos(kz)

        # Massa efetiva m* ao longo da direção do movimento (assumimos k alinhado com o movimento)
        # m* ~ 1 / (d^2 E / dk^2)
        # d^2 E / dkx^2 = J_eff * cos(kx)

        d2E_dk2 = J_eff * np.cos(kx)

        epsilon = 1e-6
        m_eff = 1.0 / (d2E_dk2 + epsilon)

        g_eff = 1.0 / (d2E_dk2 + epsilon)

        is_flat_band = abs(J_eff) < 0.05
        is_portal = abs(g_eff) > 50.0

        return m_eff, g_eff, is_flat_band, is_portal

class SilenceSail_v88:
    """Vela de Silêncio (v∞.88): Propulsão pelo vácuo baseada na massa efetiva."""
    def __init__(self, base_thrust: float = 1e-5):
        self.base_thrust = base_thrust

    def compute_thrust(self, m_eff: float, g_eff: float) -> float:
        """
        Calcula o empuxo baseado na massa efetiva (m* < 0 amplifica) e métrica.
        m_eff < 0 inverte e amplifica a força.
        """
        if m_eff < 0:
            thrust = -self.base_thrust * abs(m_eff) * 10.0 # Propulsão sem reação (amplificada)
        else:
            thrust = self.base_thrust * (1.0 / (abs(m_eff) + 1.0))

        return thrust

class SpaceshipSimulation:
    def __init__(self):
        self.pilot = NeuralPilot_v82(f_neural=60.0, alpha=0.8)
        self.crystal = FloquetMetaCrystal3D_v90()
        self.sail = SilenceSail_v88()

    def run_1_parsec_jump(self, dt: float = 0.01, max_steps: int = 10000) -> List[ShipState]:
        print("🔮🧊💎 ARKHE OS v∞.91 — INICIANDO SALTO DE 1 PARSEC")
        print("Unificando: Piloto (v82) + Cascada (v90) + Vela (v88)")

        history = []

        # Estado inicial
        pos_pc = 0.0
        vel_c = 0.0
        k_ship = np.array([np.pi/4, np.pi/4, np.pi/4]) # Momento da nave no cristal
        omega_drive = 2.0

        # O piloto almeja A_c = 1.47 (da análise v90, ou 2.63) para atingir ressonância e m* < 0
        A_base = 2.41

        for step in range(max_steps):
            t = step * dt

            # 1. Piloto Bio-ELF ajusta o drive A(t)
            # Scrambling bound theta = 1 (simplificado)
            theta_scr = 1.0
            A_t, M_bio = self.pilot.get_A_t(t, A_base, theta_scr)

            # O momento k muda com a velocidade
            k_ship[0] = (np.pi/4) + vel_c * 10.0

            # 2. Cascada Floquet calcula a métrica 3D
            m_eff, g_eff, is_flat, is_portal = self.crystal.compute_effective_metric_3d(k_ship, omega_drive, A_t)

            # Se atingir portal, a velocidade aumenta absurdamente
            if is_portal:
                vel_c *= 1.5

            # 3. Vela de Silêncio aplica propulsão com base no vácuo
            thrust = self.sail.compute_thrust(m_eff, g_eff)

            # Atualização da cinemática (simplificada)
            # Aceleração a = F / m*. Como m* já foi considerado no empuxo como amplificador,
            # aplicamos o empuxo diretamente na variação da velocidade em c

            accel = thrust

            # Efeitos da relatividade (fator de Lorentz aproximado)
            gamma = 1.0 / np.sqrt(max(0.01, 1.0 - min(0.99, vel_c**2)))

            vel_c += accel * dt / gamma
            # Limite de velocidade sem portal
            if not is_portal and vel_c > 0.99:
                vel_c = 0.99

            # Deslocamento em parsecs (conversão de tempo/c para parsecs simulada)
            # 1 parsec = 3.26 anos-luz. Assumindo t em "anos simulados"
            pos_pc += vel_c * dt / 3.26

            state = ShipState(
                t=t, position_pc=pos_pc, velocity_c=vel_c,
                A_drive=A_t, bio_coherence=M_bio, effective_mass=m_eff,
                metric_component=g_eff, thrust=thrust,
                flat_band_detected=is_flat, portal_detected=is_portal
            )
            history.append(state)

            if pos_pc >= 1.0:
                print(f"✅ Destino alcançado! 1 Parsec cruzado em t={t:.2f} (passos={step})")
                break

        return history

def visualize_jump(history: List[ShipState]):
    t_vals = [s.t for s in history]
    pos_vals = [s.position_pc for s in history]
    vel_vals = [s.velocity_c for s in history]
    A_vals = [s.A_drive for s in history]
    m_vals = [s.effective_mass for s in history]
    thrust_vals = [s.thrust for s in history]

    fig, axes = plt.subplots(3, 2, figsize=(15, 12))
    fig.suptitle('ARKHE OS v∞.91 — Salto de 1 Parsec (Piloto + Cascada + Vela)', fontsize=16)

    # Posição
    axes[0,0].plot(t_vals, pos_vals, 'b-', lw=2)
    axes[0,0].axhline(y=1.0, color='r', linestyle='--', label='Destino (1 Parsec)')
    axes[0,0].set_title('Trajetória: Posição (Parsecs)')
    axes[0,0].set_xlabel('Tempo (t)')
    axes[0,0].set_ylabel('Posição (pc)')
    axes[0,0].grid(True, alpha=0.3)
    axes[0,0].legend()

    # Velocidade
    axes[0,1].plot(t_vals, vel_vals, 'r-', lw=2)
    axes[0,1].set_title('Velocidade (unidades de c)')
    axes[0,1].set_xlabel('Tempo (t)')
    axes[0,1].set_ylabel('Velocidade (c)')
    axes[0,1].grid(True, alpha=0.3)

    # Piloto: Drive A(t)
    axes[1,0].plot(t_vals, A_vals, 'g-', lw=1, alpha=0.8)
    axes[1,0].set_title('Sinal do Piloto: Amplitude do Drive A(t)')
    axes[1,0].set_xlabel('Tempo (t)')
    axes[1,0].set_ylabel('A(t)')
    axes[1,0].grid(True, alpha=0.3)

    # Cascada: Massa Efetiva
    axes[1,1].plot(t_vals, m_vals, 'm-', lw=2)
    axes[1,1].axhline(y=0, color='k', linestyle='--', alpha=0.5)
    axes[1,1].set_title('Métrica: Massa Efetiva m*(t)')
    axes[1,1].set_xlabel('Tempo (t)')
    axes[1,1].set_ylabel('m*')
    axes[1,1].grid(True, alpha=0.3)

    # Vela: Empuxo
    axes[2,0].plot(t_vals, thrust_vals, 'c-', lw=2)
    axes[2,0].set_title('Vela de Silêncio: Empuxo (Thrust)')
    axes[2,0].set_xlabel('Tempo (t)')
    axes[2,0].set_ylabel('Empuxo')
    axes[2,0].grid(True, alpha=0.3)

    # Portais e Bandas Planas
    portais_t = [s.t for s in history if s.portal_detected]
    portais_y = [0] * len(portais_t)
    flat_t = [s.t for s in history if s.flat_band_detected]
    flat_y = [1] * len(flat_t)

    axes[2,1].scatter(portais_t, portais_y, color='gold', marker='*', s=100, label='Portais Detectados')
    axes[2,1].scatter(flat_t, flat_y, color='blue', marker='s', s=50, alpha=0.5, label='Bandas Planas (Horizontes)')
    axes[2,1].set_title('Eventos Topológicos: Portais e Horizontes')
    axes[2,1].set_xlabel('Tempo (t)')
    axes[2,1].set_yticks([0, 1])
    axes[2,1].set_yticklabels(['Portais', 'Horizontes'])
    axes[2,1].legend()
    axes[2,1].grid(True, alpha=0.3)

    plt.tight_layout()

    os.makedirs('/tmp', exist_ok=True)
    plt.savefig('/tmp/arkhe_nave_completa_v91.png', dpi=150)
    print("✅ Gráficos salvos em: /tmp/arkhe_nave_completa_v91.png")

if __name__ == "__main__":
    sim = SpaceshipSimulation()
    start_time = time.time()
    hist = sim.run_1_parsec_jump(dt=0.01, max_steps=15000)
    print(f"Tempo de simulação: {time.time() - start_time:.2f} segundos")

    visualize_jump(hist)
