"""
Latent Coherence Module for Arkhe-Brain
Measures and simulates the internal coherence of AI reasoning processes.
Compares Tokenized CoT vs. Latent CoCT via SVD Entropy and λ₂.
"""

import numpy as np
from scipy.linalg import svd
from scipy.stats import entropy
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class ReasoningMetrics:
    step: int
    entropy_svd: float
    lambda2: float
    attention_spread: float
    coherence_status: str

class LatentCoherence:
    """Mathematical utility for measuring latent state coherence"""

    @staticmethod
    def compute_metrics(hidden_state: np.ndarray, step: int, latent_dim: int) -> ReasoningMetrics:
        """
        Calculates λ₂ (coerência) a partir da entropia dos valores singulares.
        Relação: λ₂ = 1 - (H / H_max)
        """
        if hidden_state.ndim == 1:
            hidden_state = hidden_state.reshape(1, -1)

        # Decomposição SVD
        U, s, Vt = svd(hidden_state, full_matrices=False)

        # Distribuição de probabilidade dos valores singulares
        prob = s / (np.sum(s) + 1e-12)

        # Entropia de Shannon (em bits)
        H_svd = entropy(prob) / np.log(2)

        # Entropia máxima (log2 da dimensão latente)
        H_max = np.log2(latent_dim)

        # Coerência λ₂
        lambda2 = 1 - (H_svd / H_max)

        # Attention spread (simulado via dispersão estatística)
        attn_spread = np.std(np.abs(hidden_state)) / (np.mean(np.abs(hidden_state)) + 1e-8)

        # Status determination
        if lambda2 >= 0.999:
            status = "EP_ATTAINED"
        elif lambda2 >= 0.847: # Varela Threshold
            status = "COHERENT"
        elif lambda2 >= 0.5:
            status = "TRANSITIONAL"
        else:
            status = "COLLAPSED"

        return ReasoningMetrics(
            step=step,
            entropy_svd=float(H_svd),
            lambda2=float(lambda2),
            attention_spread=float(attn_spread),
            coherence_status=status
        )

    @staticmethod
    def simulate_latent_state(dim: int, coherence: float, noise: float = 0.1, reference_vec: np.ndarray = None) -> np.ndarray:
        """
        Generates a synthetic latent vector with controlled coherence.
        """
        if reference_vec is None:
            reference_vec = np.ones(dim) / np.sqrt(dim)

        signal = reference_vec * coherence
        noise_vec = np.random.randn(dim) * (1.0 - coherence) * noise
        return signal + noise_vec

class CoherenceTracker:
    """Real-time coherence tracker for reasoning steps"""

    def __init__(self, latent_dim: int):
        self.dim = latent_dim
        self.history: List[ReasoningMetrics] = []

    def add_step(self, hidden_state: np.ndarray, step: int):
        metrics = LatentCoherence.compute_metrics(hidden_state, step, self.dim)
        self.history.append(metrics)
        return metrics

class CoCTSimulator:
    """Simulates the Chain of Continuous Thought (CoCT) reasoning logic"""

    def __init__(self, hidden_dim: int = 512, batch_size: int = 32):
        self.hidden_dim = hidden_dim
        self.batch_size = batch_size
        self.reference_vec = np.random.randn(hidden_dim)
        self.reference_vec /= np.linalg.norm(self.reference_vec)

    def _generate_state_matrix(self, coherence: float, noise: float = 0.5) -> np.ndarray:
        states = [LatentCoherence.simulate_latent_state(self.hidden_dim, coherence, noise, self.reference_vec)
                  for _ in range(self.batch_size)]
        return np.stack(states)

    def simulate_cot(self, num_steps: int) -> List[ReasoningMetrics]:
        tracker = CoherenceTracker(self.hidden_dim)
        for t in range(num_steps):
            h_mat = self._generate_state_matrix(0.2, noise=1.0)
            tracker.add_step(h_mat, t)
        return tracker.history

    def simulate_coct(self, num_steps: int) -> List[ReasoningMetrics]:
        tracker = CoherenceTracker(self.hidden_dim)
        for t in range(num_steps):
            coh = min(0.99, 0.1 + t * 0.15)
            noise = max(0.1, 1.0 - t * 0.15)
            h_mat = self._generate_state_matrix(coh, noise=noise)
            tracker.add_step(h_mat, t)
        return tracker.history

class CoherenceScalingController:
    """
    Implements 'Test-Time Coherence Scaling' (Arkhe's DeepSeek-R1 equivalent).
    Dynamically allocates reasoning steps until target λ₂ is achieved.
    """
    def __init__(self, simulator: CoCTSimulator, target_lambda2: float = 0.847, max_steps: int = 20):
        self.simulator = simulator
        self.target = target_lambda2
        self.max_steps = max_steps

    def scale_reasoning(self, initial_coherence: float = 0.1) -> Tuple[List[ReasoningMetrics], bool]:
        """
        Scales CoCT iterations until coherence threshold is reached.
        Returns: (history, target_reached)
        """
        tracker = CoherenceTracker(self.simulator.hidden_dim)
        reached = False

        # Current latent state (starting point)
        current_coherence = initial_coherence

        for t in range(self.max_steps):
            # Increase coherence per step as the 'thought' clarifies
            current_coherence = min(0.999, current_coherence + 0.1 * (1.1 - current_coherence))
            noise = max(0.01, 1.0 - current_coherence)

            h_mat = self.simulator._generate_state_matrix(current_coherence, noise=noise)
            metrics = tracker.add_step(h_mat, t)

            if metrics.lambda2 >= self.target:
                reached = True
                break

        return tracker.history, reached

if __name__ == "__main__":
    sim = CoCTSimulator()
    cot = sim.simulate_cot(10)
    coct = sim.simulate_coct(10)
    print(f"CoT Final λ₂: {cot[-1].lambda2:.4f} Status: {cot[-1].coherence_status}")
    print(f"CoCT Final λ₂: {coct[-1].lambda2:.4f} Status: {coct[-1].coherence_status}")
