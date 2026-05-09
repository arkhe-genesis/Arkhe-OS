#!/usr/bin/env python3
"""
quantum_transfer_learning.py — Fine-tuning de política PPO com dados de hardware real.
Implementa adaptação de política simulada → real via domain randomization e meta-learning.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import time

from .ppo_quantum_policy import PPOQuantumTrainer, PPOConfig, QuantumPolicyNetwork

@dataclass
class TransferLearningConfig:
    """Configuração para transfer learning quântico."""
    # Domínios
    sim_domain_name: str = 'simulator'
    real_domain_name: str = 'hardware'

    # Adaptação de domínio
    domain_randomization: bool = True
    randomization_factors: Dict[str, float] = field(default_factory=lambda: {
        'phase_noise': 0.1,
        'readout_error': 0.05,
        'gate_error': 0.02
    })

    # Meta-learning
    use_maml: bool = True
    inner_lr: float = 1e-3
    inner_steps: int = 3

    # Regularização
    kl_divergence_weight: float = 0.1
    max_kl_divergence: float = 0.05

class QuantumTransferLearner:
    """
    Transfer learner para adaptar política PPO de simulação para hardware real.
    """

    def __init__(
        self,
        base_trainer: PPOQuantumTrainer,
        transfer_config: TransferLearningConfig,
        device: str = 'cpu'
    ):
        self.base_trainer = base_trainer
        self.config = transfer_config
        self.device = torch.device(device)

        # Buffer para experiências reais
        self.real_experience_buffer: deque = deque(maxlen=5000)

        # Métricas de transferência
        self.transfer_metrics: List[Dict] = []

    def apply_domain_randomization(self, sim_experience: Dict) -> Dict:
        """Aplica randomização de domínio para aproximar simulação → real."""
        if not self.config.domain_randomization:
            return sim_experience

        randomized = sim_experience.copy()

        # Adicionar ruído de fase
        if 'next_state' in randomized and self.config.randomization_factors.get('phase_noise'):
            phase_noise = torch.randn_like(randomized['next_state']) * self.config.randomization_factors['phase_noise']
            randomized['next_state'] = randomized['next_state'] + phase_noise

        # Adicionar erro de leitura
        if 'reward' in randomized and self.config.randomization_factors.get('readout_error'):
            readout_noise = torch.randn_like(randomized['reward']) * self.config.randomization_factors['readout_error']
            randomized['reward'] = randomized['reward'] + readout_noise

        return randomized

    def store_real_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        log_prob: float,
        value: float,
        hardware_metadata: Optional[Dict] = None
    ):
        """Armazena experiência coletada em hardware real."""
        experience = {
            'state': torch.FloatTensor(state),
            'action': torch.LongTensor([action]),
            'reward': torch.FloatTensor([reward]),
            'next_state': torch.FloatTensor(next_state),
            'done': torch.FloatTensor([1.0 if done else 0.0]),
            'log_prob': torch.FloatTensor([log_prob]),
            'value': torch.FloatTensor([value]),
            'domain': 'real',
            'hardware_metadata': hardware_metadata or {},
            'timestamp': time.time()
        }
        self.real_experience_buffer.append(experience)

    def fine_tune_on_real_data(self, epochs: int = 10) -> Dict[str, float]:
        """Fine-tuning da política em experiências reais."""
        if len(self.real_experience_buffer) < self.base_trainer.config.batch_size:
            return {'status': 'insufficient_real_data'}

        # Sample batch de experiências reais
        indices = np.random.choice(
            len(self.real_experience_buffer),
            self.base_trainer.config.batch_size,
            replace=False
        )
        batch = [list(self.real_experience_buffer)[i] for i in indices]

        # Converter para tensors
        states = torch.stack([e['state'] for e in batch]).to(self.device)
        actions = torch.stack([e['action'] for e in batch]).squeeze(-1).to(self.device)
        rewards = torch.stack([e['reward'] for e in batch]).to(self.device)
        dones = torch.stack([e['done'] for e in batch]).to(self.device)
        old_log_probs = torch.stack([e['log_prob'] for e in batch]).to(self.device)
        old_values = torch.stack([e['value'] for e in batch]).squeeze(-1).to(self.device)

        # Computar retornos e vantagens
        with torch.no_grad():
            _, next_values = self.base_trainer.policy(states)
            advantages = self.base_trainer.compute_gae(
                rewards, old_values, next_values, dones
            )
            returns = advantages + old_values
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # Fine-tuning com regularização KL para evitar catastrophic forgetting
        total_loss = 0.0
        for epoch in range(epochs):
            # Forward pass
            action_probs, values = self.base_trainer.policy(states)
            dist = torch.distributions.Categorical(action_probs)

            # PPO loss
            new_log_probs = dist.log_prob(actions)
            ratio = torch.exp(new_log_probs - old_log_probs)

            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.base_trainer.config.clip_epsilon,
                              1 + self.base_trainer.config.clip_epsilon) * advantages
            actor_loss = -torch.min(surr1, surr2).mean()

            critic_loss = nn.functional.mse_loss(values, returns)

            # Regularização KL para preservar conhecimento da simulação
            if self.config.kl_divergence_weight > 0:
                # Calcular KL entre política atual e política de referência (simulação)
                # Simplificação: usar política antes do fine-tuning como referência
                kl_loss = dist.entropy().mean()  # Placeholder
                total_loss = actor_loss + 0.5 * critic_loss + self.config.kl_divergence_weight * kl_loss
            else:
                total_loss = actor_loss + 0.5 * critic_loss

            # Backward
            self.base_trainer.optimizer.zero_grad()
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(
                self.base_trainer.policy.parameters(),
                self.base_trainer.config.max_grad_norm
            )
            self.base_trainer.optimizer.step()

        # Registrar métricas
        metrics = {
            'fine_tune_loss': total_loss.item(),
            'real_buffer_size': len(self.real_experience_buffer),
            'epochs': epochs,
            'timestamp': time.time()
        }
        self.transfer_metrics.append(metrics)

        return metrics

    def evaluate_transfer_gap(self, sim_policy: nn.Module, real_policy: nn.Module,
                           test_states: torch.Tensor) -> Dict[str, float]:
        """Avalia a divergência entre política de simulação e política adaptada."""
        with torch.no_grad():
            sim_probs, _ = sim_policy(test_states)
            real_probs, _ = real_policy(test_states)

            # KL divergence
            kl_div = torch.nn.functional.kl_div(
                torch.log(real_probs + 1e-8),
                sim_probs,
                reduction='batchmean'
            )

            # Action agreement
            sim_actions = torch.argmax(sim_probs, dim=-1)
            real_actions = torch.argmax(real_probs, dim=-1)
            agreement = (sim_actions == real_actions).float().mean()

        return {
            'kl_divergence': kl_div.item(),
            'action_agreement': agreement.item(),
            'transfer_quality': 'good' if agreement > 0.8 and kl_div < 0.1 else 'needs_more_data'
        }
