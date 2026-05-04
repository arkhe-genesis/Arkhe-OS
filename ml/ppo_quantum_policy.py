#!/usr/bin/env python3
"""
ppo_quantum_policy.py — Política PPO treinada para mitigação de bursts quânticos.
Substitui a política simplificada por RL completo com vantagens generalizadas.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import time

@dataclass
class PPOConfig:
    """Configuração para treino PPO."""
    # Hiperparâmetros PPO
    lr: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_epsilon: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_grad_norm: float = 0.5

    # Arquitetura da rede
    hidden_dim: int = 128
    num_layers: int = 2

    # Treino
    epochs_per_update: int = 10
    batch_size: int = 64
    minibatch_size: int = 32

    # Ambiente
    state_dim: int = 8  # [gap, gap_history, active_bursts, phase_error, ...]
    action_dim: int = 4  # [PROCEED, APPLY_ECHO, PAUSE, WAIT]

class QuantumPolicyNetwork(nn.Module):
    """
    Rede ator-crítico para política PPO de mitigação quântica.
    """

    def __init__(self, config: PPOConfig):
        super().__init__()
        self.config = config

        # Actor: π(a|s; θ)
        self.actor = nn.Sequential(
            nn.Linear(config.state_dim, config.hidden_dim),
            nn.ReLU(),
            *[nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim),
                nn.ReLU()
            ) for _ in range(config.num_layers - 1)],
            nn.Linear(config.hidden_dim, config.action_dim),
            nn.Softmax(dim=-1)
        )

        # Critic: V(s; φ)
        self.critic = nn.Sequential(
            nn.Linear(config.state_dim, config.hidden_dim),
            nn.ReLU(),
            *[nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim),
                nn.ReLU()
            ) for _ in range(config.num_layers - 1)],
            nn.Linear(config.hidden_dim, 1)
        )

    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass: retorna distribuição de ações e valor de estado."""
        action_probs = self.actor(state)
        state_value = self.critic(state).squeeze(-1)
        return action_probs, state_value

    def evaluate_actions(
        self,
        state: torch.Tensor,
        action: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Avalia ações para cálculo de loss PPO."""
        action_probs, state_value = self.forward(state)

        # Log-probabilidade da ação selecionada
        dist = Categorical(action_probs)
        log_prob = dist.log_prob(action)

        # Entropia para regularização
        entropy = dist.entropy()

        return log_prob, entropy, state_value

class PPOQuantumTrainer:
    """
    Treinador PPO para política de mitigação de bursts quânticos.
    """

    def __init__(self, config: PPOConfig, device: str = 'cpu'):
        self.config = config
        self.device = torch.device(device)

        # Inicializar rede
        self.policy = QuantumPolicyNetwork(config).to(self.device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=config.lr)

        # Buffer de experiências para GAE
        self.buffer: deque = deque(maxlen=10000)

        # Métricas de treino
        self.training_history: List[Dict] = []

    def select_action(
        self,
        state: np.ndarray,
        deterministic: bool = False
    ) -> Tuple[int, Dict]:
        """Seleciona ação baseada na política atual."""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        with torch.no_grad():
            action_probs, value = self.policy(state_tensor)

            if deterministic:
                action = torch.argmax(action_probs, dim=-1)
            else:
                dist = Categorical(action_probs)
                action = dist.sample()

            log_prob = torch.log(action_probs[0, action] + 1e-8)

        return action.item(), {
            'value': value.item(),
            'log_prob': log_prob.item(),
            'action_probs': action_probs.squeeze(0).cpu().numpy()
        }

    def store_transition(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        log_prob: float,
        value: float
    ):
        """Armazena transição para treino posterior."""
        self.buffer.append({
            'state': torch.FloatTensor(state),
            'action': torch.LongTensor([action]),
            'reward': torch.FloatTensor([reward]),
            'next_state': torch.FloatTensor(next_state),
            'done': torch.FloatTensor([1.0 if done else 0.0]),
            'log_prob': torch.FloatTensor([log_prob]),
            'value': torch.FloatTensor([value])
        })

    def compute_gae(
        self,
        rewards: torch.Tensor,
        values: torch.Tensor,
        next_values: torch.Tensor,
        dones: torch.Tensor
    ) -> torch.Tensor:
        """Computa Generalized Advantage Estimation (GAE)."""
        advantages = torch.zeros_like(rewards)
        gae = 0.0

        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = next_values[-1] if len(next_values) > 0 else 0.0
            else:
                next_value = values[t + 1]

            delta = rewards[t] + self.config.gamma * next_value * (1 - dones[t]) - values[t]
            gae = delta + self.config.gamma * self.config.gae_lambda * (1 - dones[t]) * gae
            advantages[t] = gae

        return advantages

    def update_policy(self) -> Dict[str, float]:
        """Executa update PPO com múltiplas epochs e minibatches."""
        if len(self.buffer) < self.config.batch_size:
            return {'status': 'insufficient_data'}

        # Coletar batch do buffer
        batch = list(self.buffer)[-self.config.batch_size:]

        # Converter para tensors
        states = torch.stack([t['state'] for t in batch]).to(self.device)
        actions = torch.stack([t['action'] for t in batch]).squeeze(-1).to(self.device)
        rewards = torch.stack([t['reward'] for t in batch]).to(self.device)
        dones = torch.stack([t['done'] for t in batch]).to(self.device)
        old_log_probs = torch.stack([t['log_prob'] for t in batch]).to(self.device)
        old_values = torch.stack([t['value'] for t in batch]).squeeze(-1).to(self.device)

        # Computar retornos e vantagens
        with torch.no_grad():
            _, next_values = self.policy(states)
            advantages = self.compute_gae(rewards, old_values, next_values, dones)
            returns = advantages + old_values
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # Múltiplas epochs de update
        total_loss = 0.0
        for epoch in range(self.config.epochs_per_update):
            # Shuffle e minibatches
            indices = torch.randperm(self.config.batch_size)

            for start in range(0, self.config.batch_size, self.config.minibatch_size):
                end = start + self.config.minibatch_size
                idx = indices[start:end]

                # Forward pass
                action_probs, values = self.policy(states[idx])
                dist = Categorical(action_probs)

                # Loss do actor (PPO clip)
                new_log_probs = dist.log_prob(actions[idx])
                ratio = torch.exp(new_log_probs - old_log_probs[idx])

                surr1 = ratio * advantages[idx]
                surr2 = torch.clamp(ratio, 1 - self.config.clip_epsilon, 1 + self.config.clip_epsilon) * advantages[idx]
                actor_loss = -torch.min(surr1, surr2).mean()

                # Loss do critic
                critic_loss = nn.functional.mse_loss(values, returns[idx])

                # Entropia para exploração
                entropy_loss = -dist.entropy().mean()

                # Loss total
                loss = actor_loss + self.config.value_coef * critic_loss + self.config.entropy_coef * entropy_loss

                # Backward
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), self.config.max_grad_norm)
                self.optimizer.step()

                total_loss += loss.item()

        # Limpar buffer após update
        for _ in range(min(self.config.batch_size, len(self.buffer))):
            self.buffer.popleft()

        # Registrar métricas
        metrics = {
            'total_loss': total_loss / (self.config.epochs_per_update * (self.config.batch_size // self.config.minibatch_size)),
            'actor_loss': actor_loss.item(),
            'critic_loss': critic_loss.item(),
            'entropy': entropy_loss.item(),
            'buffer_size': len(self.buffer)
        }
        self.training_history.append(metrics)

        return metrics

    def save_checkpoint(self, path: str, metadata: Optional[Dict] = None):
        """Salva checkpoint da política treinada."""
        checkpoint = {
            'policy_state_dict': self.policy.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config,
            'training_history': self.training_history[-100:],
            'metadata': metadata or {},
            'timestamp': time.time()
        }
        torch.save(checkpoint, path)
        print(f"✅ Checkpoint salvo em {path}")

    def load_checkpoint(self, path: str) -> bool:
        """Carrega checkpoint da política."""
        try:
            checkpoint = torch.load(path, map_location=self.device)
            self.policy.load_state_dict(checkpoint['policy_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.training_history.extend(checkpoint.get('training_history', []))
            print(f"✅ Checkpoint carregado de {path}")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar checkpoint: {e}")
            return False
