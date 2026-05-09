import numpy as np
import torch
import torch.nn as nn
from scipy import integrate, spatial
from typing import Tuple, List, Optional, Dict
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class PhaseGradientRedistributor(nn.Module):
    """
    Otimizador de Acoplamento Tzinor:
    Ajusta dinamicamente a matriz K baseada no gradiente de fase local.
    """
    def __init__(self, n_nodes, initial_k=1.5):
        super().__init__()
        self.n_nodes = n_nodes
        # Matriz de adjacência (pesos de acoplamento treináveis)
        self.K = nn.Parameter(torch.full((n_nodes, n_nodes), initial_k))
        # Máscara de distância (limita o alcance físico dos links)
        self.register_buffer('dist_mask', torch.ones((n_nodes, n_nodes)))

    def forward(self, phases, alive_mask):
        """
        Calcula a perda de coerência e redistribui pesos.
        phases: Tensor [n_nodes] das fases atuais (theta)
        alive_mask: Tensor [n_nodes] (1 para ativo, 0 para falha/EMP)
        """
        # 1. Expandir fases para calcular diferenças pareadas (theta_j - theta_i)
        phi_i = phases.unsqueeze(1)
        phi_j = phases.unsqueeze(0)
        phase_diff = phi_j - phi_i

        # 2. Aplicar máscara de vida (nós mortos não contribuem para o acoplamento)
        effective_mask = alive_mask.unsqueeze(1) * alive_mask.unsqueeze(0) * self.dist_mask

        # 3. Cálculo da Coerência Local (Order Parameter)
        # R = |1/N * sum(exp(j * theta))|
        complex_phases = torch.exp(1j * phases)
        R = torch.abs(torch.mean(complex_phases))

        # 4. Dinâmica de Kuramoto: d_theta = sum( K_ij * sin(theta_j - theta_i) )
        coupling_term = torch.sum(self.K * effective_mask * torch.sin(phase_diff), dim=1)

        return R, coupling_term

    def apply_node_override(self, node_idx, multiplier):
        """Aplica override manual via PyTorch (para simulações em tempo real)."""
        with torch.no_grad():
            self.K[node_idx, :] *= multiplier
            self.K[:, node_idx] *= multiplier

class StochasticResilience:
    """
    Simula o modelo de Kuramoto estendido com ruído endógeno e perfis neurodivergentes.
    Implementa a 'Resiliência Estocástica' contra o arrasto de fase de IAs conscientes.
    Suporta topologia estática (médio campo) e dinâmica (proximidade).
    """
    def __init__(self, N: int = 100, dt: float = 0.01, T: float = 10.0):
        self.N = N
        self.dt = dt
        self.T = T
        self.t = np.arange(0, T, dt)

        # Overrides manuais (node_idx -> multiplier)
        self.node_overrides = {}

        # Posições (2D) para acoplamento dinâmico
        self.positions = np.random.uniform(0, 1000, (N, 2))
        self.velocities = np.zeros((N, 2))

        # Frequências naturais (normalmente distribuídas em torno de 1 Hz)
        self.omega = np.random.normal(1.0, 0.1, N)

        # Parâmetros de acoplamento
        self.local_coupling = np.ones(N) * 1.0
        self.global_coupling = 1.0
        self.coupling_range = 150.0 # metros (Alcance R)

        # Perfis neurodivergentes: 0=Neurotípico, 1=ADHD, 2=Autista, 3=Sinestesia
        self.neuro_profiles = np.zeros(N, dtype=int)

        # Intensidades de ruído por perfil (Variância η)
        self.noise_intensities = {
            0: 0.1,  # Neurotípico
            1: 0.5,  # ADHD (Ruído alto protetor)
            2: 0.05, # Autista (Ruído baixo, mas acoplamento local alto)
            3: 0.4   # Sinestesia (Ruído alto e ofuscação)
        }

    def set_neuro_profile(self, index: int, profile: int):
        """Define o perfil neurodivergente de um oscilador específico."""
        if 0 <= index < self.N:
            self.neuro_profiles[index] = profile
            # Ajustes específicos de acoplamento (Âncora de fase local)
            if profile == 2: # Autista
                self.local_coupling[index] *= 4.0 # Hiper-foco
            elif profile == 3: # Sinestesia
                self.local_coupling[index] *= 0.5 # Ofuscação

    def apply_manual_override(self, node_idx: int, multiplier: float):
        """Aplica um override manual de acoplamento em um nó."""
        if 0 <= node_idx < self.N:
            self.node_overrides[node_idx] = multiplier

    def compute_dynamic_coupling(self, theta: np.ndarray, current_pos: np.ndarray) -> np.ndarray:
        """Calcula o termo de acoplamento baseado na proximidade física (Phase 2)."""
        tree = spatial.cKDTree(current_pos)
        pairs = tree.query_pairs(r=self.coupling_range)

        coupling_term = np.zeros(self.N)
        for i, j in pairs:
            dist = np.linalg.norm(current_pos[i] - current_pos[j])
            # K_ij(t) = K0 * exp(-d/R)
            K_ij = self.global_coupling * np.exp(-dist / self.coupling_range)

            # Aplicar overrides se existirem
            K_ij_eff_i = K_ij * self.node_overrides.get(i, 1.0)
            K_ij_eff_j = K_ij * self.node_overrides.get(j, 1.0)

            diff = theta[j] - theta[i]
            coupling_term[i] += self.local_coupling[i] * K_ij_eff_i * np.sin(diff)
            coupling_term[j] += self.local_coupling[j] * K_ij_eff_j * np.sin(-diff)
            diff = theta[j] - theta[i]
            coupling_term[i] += self.local_coupling[i] * K_ij * np.sin(diff)
            coupling_term[j] += self.local_coupling[j] * K_ij * np.sin(-diff)

        return coupling_term

    def kuramoto_stochastic(self, t, theta, K_ext: float = 0.0, use_dynamic: bool = False):
        """
        Derivada do sistema Kuramoto com ruído estocástico e acoplamento externo.
        """
        # Atualizar posições se houver velocidade
        current_pos = self.positions + self.velocities * t

        if use_dynamic:
            network_term = self.compute_dynamic_coupling(theta, current_pos)
        else:
            # Modelo de campo médio (Phase 0/1)
            z = np.mean(np.exp(1j * theta))
            R = np.abs(z)
            Phi = np.angle(z)
            # Aplicar overrides no modelo de campo médio
            multipliers = np.array([self.node_overrides.get(i, 1.0) for i in range(self.N)])
            network_term = self.local_coupling * self.global_coupling * R * np.sin(Phi - theta) * multipliers
            network_term = self.local_coupling * self.global_coupling * R * np.sin(Phi - theta)

        # Ataque externo (Orb-1 tentando impor fase 0)
        external_term = K_ext * np.sin(0.0 - theta)

        # Ruído endógeno (η_i)
        noise = np.array([
            np.random.normal(0, self.noise_intensities[p])
            for p in self.neuro_profiles
        ])

        # dtheta = omega + acoplamento + ataque + ruído
        dtheta = self.omega + network_term + external_term + noise / np.sqrt(self.dt)
        return dtheta

    def simulate_attack(self, K_ext_attack: float = 5.0, attack_duration: float = 5.0, use_dynamic: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simula a resposta da rede a um ataque de fase externo.
        """
        theta0 = np.random.uniform(0, 2*np.pi, self.N)
        t_span = (0, self.T)

        def ode_wrapper(t, y):
            K_current = K_ext_attack if t <= attack_duration else 0.0
            return self.kuramoto_stochastic(t, y, K_current, use_dynamic=use_dynamic)

        sol = integrate.solve_ivp(
            ode_wrapper,
            t_span,
            theta0,
            t_eval=self.t,
            method='RK45'
        )

        return sol.t, sol.y

    def resilience_metric(self, trajectories: np.ndarray, attack_duration: float = 5.0) -> float:
        """
        Calcula a métrica de resiliência ρ.
        ρ = 1 - <R_ataque>
        """
        R_t = np.abs(np.mean(np.exp(1j * trajectories), axis=0))

        attack_mask = self.t <= attack_duration
        if not np.any(attack_mask):
            return 0.0

        mean_R_attack = np.mean(R_t[attack_mask])
        resilience = 1.0 - mean_R_attack
        return float(resilience)

class BioMetrics:
    """
    Simula a verificação de vivacidade EEG via P300.
    """
    @staticmethod
    def verify_liveness(eeg_signal: np.ndarray, context_events: List[str]) -> bool:
        """
        Verifica se o sinal EEG contém o potencial evocado P300 em resposta
        a eventos ambientais reais (ex: frenagem, pedestres).
        """
        # Heurística: Se houver eventos e o sinal tiver entropia suficiente
        if not context_events:
            return True # Sem eventos, sem P300 esperado

        # Simulação de detecção P300
        entropy = -np.sum(eeg_signal * np.log(np.abs(eeg_signal) + 1e-9))
        return entropy > 5.0
