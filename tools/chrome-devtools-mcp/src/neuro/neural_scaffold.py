"""
NeuralScaffold v2.2 — Implementação do 4 Neural com Bifurcação Kuramoto
Constitucionalmente válido: apenas dinâmica física de osciladores acoplados
"""

import numpy as np
import networkx as nx
from scipy.integrate import solve_ivp
from scipy.stats import entropy
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum
from scipy.spatial.distance import pdist, squareform
from scipy.signal import hilbert, welch

class DiseasePhase(Enum):
    PHASE_1_COMPENSATED = 1      # r > 0.7, alta acessibilidade
    PHASE_2_SUBCOMPENSATED = 2   # 0.3 < r < 0.7, contração X_eff
    PHASE_3_DECOMPENSATED = 3    # r < 0.3, fragmentação

@dataclass
class ScaffoldState:
    """Estado instantâneo do scaffold físico (4)"""
    t: float
    theta: np.ndarray           # Fases dos osciladores [0, 2π]
    K_matrix: np.ndarray        # Matriz de acoplamento (degradada)
    D_matrix: np.ndarray        # Matriz de atrasos (aumentada)
    r_global: float             # Parâmetro de ordem global
    X_eff_volume: float         # Volume do espaço acessível (entropia)
    complexity_LZ: float        # Complexidade de Lempel-Ziv da dinâmica
    phase: DiseasePhase         # Classificação de fase clínica

class NeuralScaffold:
    """
    Scaffold físico G = (V, E, W, D) implementado como rede de Kuramoto.
    Modela contração de X_eff via bifurcação induzida por degradação.
    """

    def __init__(self, N: int = 100, k: int = 8, p: float = 0.1,
                 v_conduction: float = 5.0, omega_std: float = 0.2):
        self.N = N
        self.k = k
        self.p = p
        self.v_conduction = v_conduction

        # Construção do grafo small-world (E)
        self.G = nx.watts_strogatz_graph(N, k, p)

        # Posições 3D para cálculo geométrico de atrasos
        self.pos = np.random.randn(N, 3)

        # Frequências naturais (heterogeneidade neural)
        self.omega = 1.0 + np.random.normal(0, omega_std, N)

        # Matriz de atrasos D (geometria axonal / velocidade de condução)
        self.D_base = self._compute_delay_matrix()
        self.D_current = self.D_base.copy()

        # Matriz de acoplamento K (pesos sinápticos)
        self.K_base = self._compute_coupling_matrix()
        self.K_current = self.K_base.copy()

        # Estado dinâmico
        self.theta = np.random.uniform(0, 2*np.pi, N)
        self.history: List[ScaffoldState] = []
        self.degradation_level = 0.0

    def _compute_delay_matrix(self) -> np.ndarray:
        """D_ij = distância física / velocidade de condução"""
        D = np.zeros((self.N, self.N))
        for i, j in self.G.edges():
            dist = np.linalg.norm(self.pos[i] - self.pos[j])
            D[i, j] = D[j, i] = dist / self.v_conduction
        return D

    def _compute_coupling_matrix(self) -> np.ndarray:
        """K_ij = peso sináptico base (ajustável por plasticidade)"""
        K = np.zeros((self.N, self.N))
        for i, j in self.G.edges():
            K[i, j] = K[j, i] = 1.0  # Peso base normalizado
        return K

    def apply_pathology(self, degradation: float,
                       synapse_loss_rate: float = 0.8,
                       demyelination_rate: float = 0.5):
        """
        Aplica degradação progressiva (modelo Alzheimer):
        - Reduz K (perda sináptica/poda)
        - Aumenta D (desmielinização → condução mais lenta)
        """
        self.degradation_level = np.clip(degradation, 0.0, 1.0)

        # Degradação do acoplamento: K_eff = K_base * (1 - synapse_loss * deg)
        self.K_current = self.K_base * (1.0 - synapse_loss_rate * self.degradation_level)

        # Degradação da condução: D_eff = D_base * (1 + demyelin * deg)
        self.D_current = self.D_base * (1.0 + demyelination_rate * self.degradation_level)

        # Remoção de nós (morte neuronal) em degradação extrema (>0.8)
        if self.degradation_level > 0.8:
            n_dead = int(self.N * (self.degradation_level - 0.8) * 2)
            if n_dead > 0:
                dead_indices = np.random.choice(self.N, min(n_dead, self.N), replace=False)
                self.K_current[dead_indices, :] = 0
                self.K_current[:, dead_indices] = 0

    def _kuramoto_derivative(self, t: float, theta: np.ndarray) -> np.ndarray:
        """dθ_i/dt = ω_i + Σ_j K_ij sin(θ_j - θ_i - ω_i*D_ij)"""
        dtheta = np.zeros(self.N)

        for i in range(self.N):
            phase_diff = theta - theta[i] - self.omega[i] * self.D_current[i, :]
            coupling = self.K_current[i, :] * np.sin(phase_diff)
            dtheta[i] = self.omega[i] + np.sum(coupling)

        # Ruído térmico aumenta com degradação (flutuações metabólicas)
        noise_amp = 0.1 + 0.4 * self.degradation_level
        dtheta += noise_amp * np.random.randn(self.N)

        return dtheta

    def _compute_order_parameter(self, theta: np.ndarray) -> complex:
        """r(t) = |<exp(iθ)>| — coerência global"""
        return np.mean(np.exp(1j * theta))

    def _compute_X_eff_volume(self, theta: np.ndarray) -> float:
        """
        Volume do espaço acessível: entropia de Shannon das fases discretizadas.
        Fases 1 e 3 têm baixa entropia (restrição), Fase 2 tem entropia máxima
        (exploração caótica antes do colapso).
        """
        # Discretiza fases em 20 bins
        hist, _ = np.histogram(theta % (2*np.pi), bins=20, range=(0, 2*np.pi))
        probs = hist / np.sum(hist)
        # Entropia normalizada [0, 1]
        return entropy(probs) / np.log(20) if np.any(probs > 0) else 0.0

    def _compute_LZ_complexity(self, r_series: List[float], window: int = 50) -> float:
        """
        Complexidade de Lempel-Ziv da série do parâmetro de ordem.
        Mede a riqueza de padrões temporais (queda indica perda de dinâmica).
        """
        if len(r_series) < window:
            return 1.0

        recent_r = np.array(r_series[-window:])
        # Binarização: acima/abaixo da média
        binary = (recent_r > np.mean(recent_r)).astype(int)

        # Algoritmo Lempel-Ziv
        sequence = ''.join(map(str, binary))
        substrings = set()
        i = 0
        while i < len(sequence):
            for j in range(i + 1, len(sequence) + 1):
                substring = sequence[i:j]
                if substring in substrings:
                    continue
                substrings.add(substring)
                i = j
                break
            else:
                break

        # Complexidade normalizada
        return len(substrings) / (len(sequence) / np.log2(len(sequence))) if len(sequence) > 0 else 0.0

    def step(self, dt: float = 0.05) -> ScaffoldState:
        """Integra um passo temporal e retorna estado clínico"""
        # Integração Runge-Kutta
        sol = solve_ivp(
            self._kuramoto_derivative,
            (0, dt),
            self.theta,
            method='RK45',
            dense_output=True
        )
        self.theta = sol.y[:, -1] % (2*np.pi)

        # Métricas
        z = self._compute_order_parameter(self.theta)
        r = np.abs(z)

        # Histórico para cálculo de LZ
        if not hasattr(self, '_r_history'):
            self._r_history = []
        self._r_history.append(r)

        X_eff = self._compute_X_eff_volume(self.theta)
        c_lz = self._compute_LZ_complexity(self._r_history)

        # Classificação de fase
        if r > 0.7:
            phase = DiseasePhase.PHASE_1_COMPENSATED
        elif r > 0.3:
            phase = DiseasePhase.PHASE_2_SUBCOMPENSATED
        else:
            phase = DiseasePhase.PHASE_3_DECOMPENSATED

        state = ScaffoldState(
            t=len(self.history) * dt,
            theta=self.theta.copy(),
            K_matrix=self.K_current.copy(),
            D_matrix=self.D_current.copy(),
            r_global=r,
            X_eff_volume=X_eff,
            complexity_LZ=c_lz,
            phase=phase
        )

        self.history.append(state)
        return state

    def simulate_progression(self, T_total: float = 300.0, dt: float = 0.05,
                           progression_rate: float = 0.3):
        """
        Simula progressão completa da doença.
        progression_rate: velocidade de acúmulo de patologia
        """
        n_steps = int(T_total / dt)

        for step_idx in range(n_steps):
            # Degradação aumenta ao longo do tempo (sigmoide para realismo)
            t_normalized = step_idx / n_steps
            degradation = 1.0 / (1.0 + np.exp(-10 * (t_normalized - 0.5)))

            self.apply_pathology(degradation)
            self.step(dt)

        return self.get_clinical_summary()

    def get_clinical_summary(self) -> Dict:
        """Retorna métricas clínicas agregadas da simulação"""
        if not self.history:
            return {}

        rs = [s.r_global for s in self.history]
        X_effs = [s.X_eff_volume for s in self.history]
        c_lzs = [s.complexity_LZ for s in self.history]

        return {
            'r_mean': np.mean(rs),
            'r_min': np.min(rs),
            'r_bifurcation_point': next((i for i, r in enumerate(rs) if r < 0.5), None),
            'X_eff_final': X_effs[-1],
            'complexity_decline': (c_lzs[0] - c_lzs[-1]) / c_lzs[0] if c_lzs[0] > 0 else 0,
            'final_phase': self.history[-1].phase.name,
            'total_time': self.history[-1].t
        }

    def intervene_medicine_4(self, target_nodes: List[int],
                            K_boost: float = 0.3,
                            D_reduction: float = 0.2):
        """
        "Medicina do 4": Intervenção no scaffold físico.
        Restaura parcialmente K e D em nós específicos (estabilização
        de microtúbulos, remielinização focal).

        NÃO é cura (não remove amiloide), é restauração de acessibilidade.
        """
        for node in target_nodes:
            if 0 <= node < self.N:
                # Aumenta acoplamento local (sinaptogenesis funcional)
                neighbors = list(self.G.neighbors(node))
                self.K_current[node, neighbors] *= (1.0 + K_boost)
                self.K_current[neighbors, node] *= (1.0 + K_boost)

                # Reduz atrasos locais (remielinização)
                self.D_current[node, neighbors] *= (1.0 - D_reduction)
                self.D_current[neighbors, node] *= (1.0 - D_reduction)

def build_scaffold_from_dti(connectivity_matrix: np.ndarray,
                           region_centroids: np.ndarray,
                           velocity: float = 5.0) -> NeuralScaffold:
    """
    Constrói NeuralScaffold a partir de dados DTI reais.

    Args:
        connectivity_matrix: Matriz N×N (peso = número de fibras ou FA médio)
        region_centroids: Coordenadas MNI 3D das regiões (N×3)
        velocity: Velocidade de condução estimada (m/s)
    """
    N = connectivity_matrix.shape[0]
    scaffold = NeuralScaffold(N=N)

    # Substitui o grafo small-world sintético pelo real
    scaffold.G = nx.from_numpy_array(connectivity_matrix > 0)
    scaffold.pos = region_centroids

    # K_base = força de conectividade estrutural (FA ou contagem de fibras)
    scaffold.K_base = connectivity_matrix / (np.max(connectivity_matrix) + 1e-10)

    # D_base = distância Euclidiana entre centroides / velocidade
    dist_matrix = squareform(pdist(region_centroids))
    scaffold.D_base = dist_matrix / (velocity + 1e-10)

    return scaffold

def extract_omega_from_fmri(bold_signals: np.ndarray,
                           fs: float = 1/2.0,  # TR=2s
                           band: Tuple[float,float] = (0.01, 0.08)) -> np.ndarray:
    """
    Extrai frequências dominantes da banda BOLD (0.01-0.08 Hz)
    para cada região como proxy para ω_i.
    """
    freqs, psd = welch(bold_signals, fs=fs, axis=1)
    # Seleciona banda de interesse
    band_mask = (freqs >= band[0]) & (freqs <= band[1])

    # Frequência dominante (máxima PSD na banda)
    omega = np.array([
        freqs[band_mask][np.argmax(psd[i, band_mask])]
        for i in range(bold_signals.shape[0])
    ])

    # Normaliza para compatibilidade com o modelo (escala ~1)
    return omega / (np.mean(omega) + 1e-10)

def bold_to_phases(bold_signals: np.ndarray) -> np.ndarray:
    """
    Converte sinais BOLD em fases via Transformada de Hilbert.
    θ(t) = arctan(H[BOLD(t)] / BOLD(t))
    """
    analytic = hilbert(bold_signals - np.mean(bold_signals, axis=1, keepdims=True))
    return np.angle(analytic[:, 0])  # Fase inicial t=0
