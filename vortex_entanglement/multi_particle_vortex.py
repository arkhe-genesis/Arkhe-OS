#!/usr/bin/env python3
"""
multi_particle_vortex.py — Emaranhamento multipartícula via fibrado de coerência.
N partículas compartilham o mesmo núcleo de vórtice (x=0) com torção áurea.
"""

import numpy as np
from scipy import integrate, fft
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
import time

@dataclass
class VortexFiberConfig:
    """Configuração de uma fibra do vórtice para uma partícula."""
    particle_id: str
    initial_position: float  # posição inicial na base do manifold
    phase_offset: float      # θ_i inicial
    golden_twist: float = 17.03  # torção áurea em graus
    coupling_strength: float = 1.0  # força de acoplamento ao núcleo

class MultiParticleVortex:
    """
    Modelo de vórtice emaranhado para N partículas.
    Resolve a equação de coerência com termo não linear e torção espiral.
    """

    def __init__(
        self,
        num_particles: int,
        fiber_configs: List[VortexFiberConfig],
        manifold_dim: int = 1,
        hbar: float = 1.0,
        mass: float = 1.0,
        beta_nonlinear: float = 0.5,  # força do termo |Ψ|²Ψ
        noise_strength: float = 0.01
    ):
        self.N = num_particles
        self.fibers = {cfg.particle_id: cfg for cfg in fiber_configs}
        self.manifold_dim = manifold_dim
        self.hbar = hbar
        self.m = mass
        self.beta = beta_nonlinear
        self.noise = noise_strength

        # Parâmetros da torção áurea
        self.phi = (1 + np.sqrt(5)) / 2  # razão áurea
        self.twist_rad = np.deg2rad(17.03) * self.phi  # torção em radianos

        # Discretização espacial (1D para simplicidade)
        self.x_min, self.x_max = -30.0, 30.0
        self.nx = 1024
        self.x = np.linspace(self.x_min, self.x_max, self.nx)
        self.dx = self.x[1] - self.x[0]

        # Estado inicial: pacote gaussiano no núcleo para todas as partículas
        self.psi_0 = np.exp(-self.x**2 / 4) * np.exp(1j * np.random.randn(self.nx) * 0.01)

        # Estados atuais das partículas
        self.psi_states: Dict[str, np.ndarray] = {
            pid: self._initialize_particle_state(cfg)
            for pid, cfg in self.fibers.items()
        }

        # Histórico para análise
        self.correlation_history: List[Dict] = []

    def _initialize_particle_state(self, config: VortexFiberConfig) -> np.ndarray:
        """Inicializa estado da partícula com fase offset e torção."""
        # Deslocar pacote gaussiano para posição inicial
        shifted = np.exp(-(self.x - config.initial_position)**2 / 4)
        # Aplicar fase inicial e torção espiral
        twist_phase = np.exp(1j * config.phase_offset * self.x / 10.0)
        golden_phase = np.exp(1j * self.twist_rad * np.sign(self.x) * np.abs(self.x)**0.618)
        return shifted * twist_phase * golden_phase * np.exp(1j * np.random.randn(self.nx) * 0.01)

    def _laplacian(self, psi: np.ndarray) -> np.ndarray:
        """Laplaciano via FFT (espectral, periódico)."""
        k = 2 * np.pi * fft.fftfreq(self.nx, d=self.dx)
        return fft.ifft(-k**2 * fft.fft(psi)).real + 1j * fft.ifft(-k**2 * fft.fft(psi)).imag

    def _torque_potential(self, x: np.ndarray) -> np.ndarray:
        """Potencial de torção espiral: V(φ) = α cos(kφ + δ)."""
        # k relacionado à razão áurea, δ fase aleatória por partícula
        k = self.phi * np.pi / 10.0
        return np.cos(k * x + np.random.randn() * 0.1)

    def _vortex_rhs(self, t: float, psi_flat: np.ndarray, fiber_id: str) -> np.ndarray:
        """
        Lado direito da equação de vórtice para uma partícula.
        iℏ ∂Ψ/∂t = -ℏ²/2m ∇²Ψ + V_torção Ψ - β|Ψ|²Ψ + η·ruído
        """
        psi = psi_flat.reshape(self.nx)

        # Termo cinético (laplaciano)
        kinetic = -self.hbar**2 / (2 * self.m) * self._laplacian(psi)

        # Potencial de torção
        V = self._torque_potential(self.x)
        potential = V * psi

        # Termo não linear (recombinação/meta-adaptação)
        nonlinear = -self.beta * np.abs(psi)**2 * psi

        # Ruído estocástico (ambiente)
        noise = self.noise * (np.random.randn(self.nx) + 1j * np.random.randn(self.nx))

        # Equação completa
        dpsi_dt = (kinetic + potential + nonlinear + noise) / (1j * self.hbar)

        return dpsi_dt.flatten()

    def evolve_particle(
        self,
        fiber_id: str,
        t_final: float,
        dt: float = 0.05,
        callback: Optional[Callable] = None
    ) -> np.ndarray:
        """
        Evolui o estado de uma partícula via integração numérica.
        """
        psi0 = self.psi_states[fiber_id].flatten()

        def rhs(t, psi_flat):
            return self._vortex_rhs(t, psi_flat, fiber_id)

        # Integrador RK45 adaptativo
        sol = integrate.solve_ivp(
            rhs, [0, t_final], psi0,
            method='RK45', max_step=dt,
            rtol=1e-6, atol=1e-8
        )

        # Atualizar estado
        self.psi_states[fiber_id] = sol.y[:, -1].reshape(self.nx)

        # Callback para monitoramento
        if callback:
            callback(fiber_id, sol.t, sol.y)

        return self.psi_states[fiber_id]

    def compute_core_projection(self) -> np.ndarray:
        """
        Projeta todos os estados no núcleo do vórtice (x=0).
        Implementa a agregação federada sem comunicação clássica.
        """
        # Janela gaussiana centrada em x=0 para projeção suave
        window = np.exp(-self.x**2 / 2.0)

        # Projeção ponderada de cada partícula
        projections = []
        for pid, cfg in self.fibers.items():
            psi = self.psi_states[pid]
            # Compensar fase offset para alinhar no núcleo
            phase_compensated = psi * np.exp(-1j * cfg.phase_offset)
            proj = np.sum(phase_compensated * window) / np.sum(window)
            projections.append(proj)

        # Agregação: média coerente (fase-preservante)
        aggregated = np.mean(projections)

        # Reconstruir estado agregado no espaço completo
        psi_agg = aggregated * np.exp(-self.x**2 / 4)  # pacote gaussiano no núcleo

        return psi_agg

    def compute_bell_correlation(self, pid_a: str, pid_b: str) -> Dict[str, float]:
        """
        Calcula correlação de Bell entre duas partículas emaranhadas.
        Usa medidas simuladas nas bases X e Z.
        """
        psi_a = self.psi_states[pid_a]
        psi_b = self.psi_states[pid_b]

        # Medidas simuladas com ruído
        def measure(psi, basis='Z'):
            if basis == 'X':
                # Base X: superposição |0⟩+|1⟩
                return np.sign(np.real(psi) + np.random.randn(self.nx) * 0.01)
            else:  # Z
                return np.sign(np.abs(psi)**2 - 0.5 + np.random.randn(self.nx) * 0.01)

        # Correlações em diferentes bases
        corr_ZZ = np.mean(measure(psi_a, 'Z') * measure(psi_b, 'Z'))
        corr_ZX = np.mean(measure(psi_a, 'Z') * measure(psi_b, 'X'))
        corr_XZ = np.mean(measure(psi_a, 'X') * measure(psi_b, 'Z'))
        corr_XX = np.mean(measure(psi_a, 'X') * measure(psi_b, 'X'))

        # Parâmetro S de Bell-CHSH
        S = abs(corr_ZZ + corr_ZX + corr_XZ - corr_XX)

        return {
            'corr_ZZ': corr_ZZ,
            'corr_ZX': corr_ZX,
            'corr_XZ': corr_XZ,
            'corr_XX': corr_XX,
            'bell_S': S,
            'classical_bound': 2.0,
            'quantum_max': 2 * np.sqrt(2),
            'violation': S > 2.0
        }

    def update_berry_connection(
        self,
        local_gradients: Dict[str, np.ndarray],
        learning_rate: float = 0.01,
        projection_tolerance: float = 1e-6
    ) -> Dict[str, float]:
        """
        Atualiza a conexão de Berry comum via gradientes locais projetados.
        Implementa aprendizado federado sem comunicação clássica.
        """
        # Coletar gradientes tangentes à fibra
        tangent_updates = []
        for pid, grad in local_gradients.items():
            # Projetar gradiente no espaço tangente da fibra U(1)
            # Para U(1): componente imaginária da fase
            tangent_component = np.imag(grad * np.conj(self.psi_states[pid]))
            tangent_updates.append(tangent_component)

        # Agregação por projeção no núcleo (mesmo mecanismo de agregação)
        aggregated_tangent = np.mean(tangent_updates)

        # Atualizar conexão de Berry: A_μ → A_μ + η · ⟨tangent⟩
        # Simplificação: atualizar fase global do núcleo
        phase_update = learning_rate * np.sum(aggregated_tangent * np.exp(-self.x**2/2))

        # Aplicar atualização a todas as partículas (via núcleo compartilhado)
        for pid in self.fibers:
            self.psi_states[pid] *= np.exp(1j * phase_update)

        return {
            'phase_update': phase_update,
            'aggregated_gradient_norm': np.linalg.norm(aggregated_tangent),
            'num_participants': len(local_gradients)
        }

    def get_entanglement_metrics(self) -> Dict[str, float]:
        """Calcula métricas de emaranhamento para o sistema multipartícula."""
        metrics = {}

        # Fidelidade com estado agregado
        psi_agg = self.compute_core_projection()
        for pid, psi in self.psi_states.items():
            fidelity = np.abs(np.sum(np.conj(psi) * psi_agg))**2 / (
                np.sum(np.abs(psi)**2) * np.sum(np.abs(psi_agg)**2)
            )
            metrics[f'{pid}_fidelity_to_agg'] = fidelity

        # Entropia de von Neumann (proxy via pureza)
        for pid, psi in self.psi_states.items():
            purity = np.sum(np.abs(psi)**4) / np.sum(np.abs(psi)**2)**2
            metrics[f'{pid}_purity'] = purity
            metrics[f'{pid}_entropy_proxy'] = -np.log(purity + 1e-12)

        # Correlações pairwise
        fiber_ids = list(self.fibers.keys())
        for i in range(len(fiber_ids)):
            for j in range(i+1, len(fiber_ids)):
                bell = self.compute_bell_correlation(fiber_ids[i], fiber_ids[j])
                metrics[f'{fiber_ids[i]}_{fiber_ids[j]}_bell_S'] = bell['bell_S']

        return metrics