"""
rl_profile_adapter.py — Adaptação de Perfis com Aprendizado por Reforço
Usa RL (Q-Learning / PPO) para ajustar automaticamente alpha, beta, gamma e temperatura
com base no feedback do usuário (implícito ou explícito).
"""
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import time

@dataclass
class AttractorParams:
    alpha: float
    beta: float
    gamma: float
    temperature: float

class RlProfileOptimizer:
    """
    Otimizador de perfis usando Aprendizado por Reforço.
    Estado: [taxa_exorcismo, latencia, phi_c_coerencia]
    Ação: Deltas nos parâmetros [d_alpha, d_beta, d_gamma, d_temp]
    Recompensa: Satisfação do usuário (baseada em engajamento, tempo de resposta, ausência de block)
    """
    def __init__(self, profile_id: str, initial_params: AttractorParams):
        self.profile_id = profile_id
        self.current_params = initial_params

        # RL Hyperparameters
        self.learning_rate = 0.05
        self.discount_factor = 0.9
        self.epsilon = 0.2  # Exploration rate

        # Simplified State-Action Value table (Q-table)
        # In reality, this would be a continuous space Policy Network (PPO/SAC)
        # For this implementation, we'll use a simplified continuous update rule (Gradient Bandit)

        # Action space bounds
        self.bounds = {
            'alpha': (0.5, 3.0),
            'beta': (0.1, 1.0),
            'gamma': (0.1, 1.0),
            'temperature': (0.3, 2.0)
        }

        self.history = []

    def _clip(self, val: float, param_name: str) -> float:
        min_v, max_v = self.bounds[param_name]
        return max(min_v, min(val, max_v))

    def choose_action(self) -> Dict[str, float]:
        """
        Seleciona uma ação (ajuste de parâmetros) baseada em exploração/explotação.
        """
        # Epsilon-greedy continuous exploration
        deltas = {}
        if np.random.random() < self.epsilon:
            # Explore: random small adjustments
            deltas['alpha'] = np.random.uniform(-0.2, 0.2)
            deltas['beta'] = np.random.uniform(-0.1, 0.1)
            deltas['gamma'] = np.random.uniform(-0.1, 0.1)
            deltas['temperature'] = np.random.uniform(-0.2, 0.2)
        else:
            # Exploit: move in direction of past high rewards (simplified gradient)
            # If we don't have enough history, just explore slightly
            if len(self.history) < 5:
                deltas = {k: np.random.uniform(-0.05, 0.05) for k in self.bounds.keys()}
            else:
                # Mock gradient ascent based on recent successful actions
                # (Averaging the deltas of the top 20% most rewarding past steps)
                sorted_history = sorted(self.history, key=lambda x: x['reward'], reverse=True)
                top_steps = sorted_history[:max(1, len(sorted_history)//5)]

                for k in self.bounds.keys():
                    avg_delta = np.mean([step['deltas'][k] for step in top_steps])
                    # Add a tiny bit of noise
                    deltas[k] = avg_delta + np.random.uniform(-0.02, 0.02)

        return deltas

    def apply_action(self, deltas: Dict[str, float]) -> AttractorParams:
        """
        Aplica os deltas selecionados para gerar novos parâmetros.
        """
        new_params = AttractorParams(
            alpha=self._clip(self.current_params.alpha + deltas['alpha'], 'alpha'),
            beta=self._clip(self.current_params.beta + deltas['beta'], 'beta'),
            gamma=self._clip(self.current_params.gamma + deltas['gamma'], 'gamma'),
            temperature=self._clip(self.current_params.temperature + deltas['temperature'], 'temperature')
        )
        return new_params

    def update(self, state_metrics: Dict, deltas: Dict[str, float], reward: float):
        """
        Atualiza a política com base no feedback recebido.
        """
        # Record experience
        self.history.append({
            'state': state_metrics,
            'deltas': deltas,
            'reward': reward,
            'timestamp': time.time()
        })

        # Apply the update if it was beneficial
        if reward > 0:
            # Move current params towards the successful action
            self.current_params = self.apply_action({k: v * self.learning_rate for k, v in deltas.items()})

    def calculate_reward(self, user_feedback: float, metrics: Dict) -> float:
        """
        Calcula a recompensa com base no feedback explícito e métricas implícitas.
        """
        # Feedback explícito (1-5 estrelas normalizado para -1 a 1)
        explicit = (user_feedback - 3.0) / 2.0 if user_feedback else 0.0

        # Métricas implícitas
        exorcism_penalty = -0.5 if metrics.get('exorcised', False) else 0.1
        coherence_bonus = metrics.get('phi_c', 0.5) * 0.2
        latency_penalty = -min(0.5, metrics.get('latency_ms', 0) / 1000.0)

        return explicit + exorcism_penalty + coherence_bonus + latency_penalty
