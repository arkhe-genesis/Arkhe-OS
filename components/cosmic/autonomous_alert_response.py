#!/usr/bin/env python3
"""
autonomous_alert_response.py — Política de RL para resposta autônoma a alertas de consciência cósmica.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque
import time

class AlertAction(Enum):
    """Ações possíveis em resposta a alertas cósmicos."""
    LOG = auto()              # Apenas registrar
    ADAPT = auto()            # Adaptar parâmetros da missão
    REENTANGLE = auto()       # Tentar re-emaranhamento
    HALT = auto()             # Parar operações na zona afetada
    ESCALATE = auto()         # Escalar para operador humano

@dataclass
class AlertState:
    """Estado para decisão de resposta a alerta."""
    health_ent: float           # Score de saúde do emaranhamento [0, 1]
    criticality: float          # Criticidade da missão [0, 1]
    decoherence_rate: float     # Taxa de decoerência [0, 1]
    resource_availability: float # Recursos disponíveis [0, 1]
    alert_level: str            # 'WARNING' ou 'CRITICAL'
    link_distance_ly: float     # Distância do link afetado

    def to_tensor(self) -> torch.Tensor:
        """Converte estado para tensor para input da rede."""
        alert_level_num = 1.0 if self.alert_level == 'CRITICAL' else 0.0
        return torch.tensor([
            self.health_ent,
            self.criticality,
            self.decoherence_rate,
            self.resource_availability,
            alert_level_num,
            min(1.0, self.link_distance_ly / 1000.0)  # normalizar distância
        ], dtype=torch.float32)

class CosmicAlertPolicyNetwork(nn.Module):
    """
    Rede crítica para política de resposta a alertas cósmicos.
    Input: estado normalizado (6 dimensões)
    Output: Q-values para cada ação (5 dimensões)
    """

    def __init__(self, state_dim: int = 6, action_dim: int = 5, hidden_dim: int = 64):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        return self.network(state)

class AutonomousAlertResponder:
    """
    Sistema de resposta autônoma a alertas cósmicos via RL.

    Treinado offline em simulações de degradação de emaranhamento.
    Usa Q-learning com replay buffer para atualização online.
    """

    def __init__(
        self,
        action_dim: int = 5,
        state_dim: int = 6,
        learning_rate: float = 1e-3,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay: float = 0.995,
        replay_buffer_size: int = 10000,
        batch_size: int = 32,
        target_update: int = 100
    ):
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update = target_update
        self.steps = 0

        # Redes
        self.policy_net = CosmicAlertPolicyNetwork(state_dim, action_dim)
        self.target_net = CosmicAlertPolicyNetwork(state_dim, action_dim)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        # Otimizador
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)

        # Replay buffer
        self.replay_buffer = deque(maxlen=replay_buffer_size)

        # Mapeamento ação → nome
        self.action_names = {i: action.name for i, action in enumerate(AlertAction)}

        # Histórico de decisões para auditoria
        self.decision_log: List[Dict] = []

    def select_action(self, state: AlertState, training: bool = False) -> Tuple[int, str]:
        """Seleciona ação baseada na política atual (com ε-greedy se training)."""
        state_tensor = state.to_tensor().unsqueeze(0)

        if training and np.random.random() < self.epsilon:
            # Exploração: ação aleatória
            action = np.random.randint(self.action_dim)
            selection_method = 'exploration'
        else:
            # Exploração: ação ótima pela política
            with torch.no_grad():
                q_values = self.policy_net(state_tensor)
                action = torch.argmax(q_values, dim=1).item()
            selection_method = 'exploitation'

        action_name = self.action_names[action]

        # Decaimento de ε
        if training:
            self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
            self.steps += 1

            # Atualizar target network periodicamente
            if self.steps % self.target_update == 0:
                self.target_net.load_state_dict(self.policy_net.state_dict())

        return action, selection_method

    def store_transition(
        self,
        state: AlertState,
        action: int,
        reward: float,
        next_state: Optional[AlertState],
        done: bool
    ):
        """Armazena transição no replay buffer para treino."""
        self.replay_buffer.append({
            'state': state.to_tensor(),
            'action': action,
            'reward': reward,
            'next_state': next_state.to_tensor() if next_state else None,
            'done': done
        })

    def train_step(self) -> Optional[float]:
        """Executa um passo de treino via Q-learning."""
        if len(self.replay_buffer) < self.batch_size:
            return None

        # Sample batch do replay buffer
        batch = [self.replay_buffer[i] for i in np.random.choice(len(self.replay_buffer), self.batch_size, replace=False)]

        # Converter para tensors
        states = torch.stack([t['state'] for t in batch])
        actions = torch.tensor([t['action'] for t in batch], dtype=torch.long)
        rewards = torch.tensor([t['reward'] for t in batch], dtype=torch.float32)
        dones = torch.tensor([t['done'] for t in batch], dtype=torch.float32)

        # Q(s,a) da policy net
        q_values = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # Q(s',a') da target net (para estados não-terminais)
        next_q_values = torch.zeros(self.batch_size)
        non_terminal = ~dones.bool()
        if non_terminal.any():
            next_states = torch.stack([t['next_state'] for t in batch if t['next_state'] is not None])
            with torch.no_grad():
                next_q = self.target_net(next_states).max(dim=1)[0]
            next_q_values[non_terminal] = next_q

        # Target: r + γ·max_a' Q(s',a')
        targets = rewards + self.gamma * next_q_values

        # Loss e backward
        loss = nn.functional.mse_loss(q_values, targets)
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=1.0)
        self.optimizer.step()

        return loss.item()

    def respond_to_alert(
        self,
        alert: Dict,
        cosmic_monitor: 'CosmicConsciousnessMonitor',
        training: bool = False
    ) -> Dict:
        """
        Gera resposta autônoma para um alerta cósmico.

        Returns:
            Dict com ação selecionada, justificativa e metadata
        """
        # Construir estado a partir do alerta
        link = cosmic_monitor.entanglement_links.get(alert['link_id'])
        if not link:
            return {'error': f"Link {alert['link_id']} not found"}

        state = AlertState(
            health_ent=link.compute_health_score(),
            criticality=link.mission_criticality,
            decoherence_rate=link.decoherence_factor,
            resource_availability=0.8,  # simplificação: consultar sistema de recursos
            alert_level=alert['alert_level'],
            link_distance_ly=link.distance_ly
        )

        # Selecionar ação via política
        action_idx, selection_method = self.select_action(state, training=training)
        action = AlertAction(action_idx)

        # Executar ação e calcular reward
        reward, execution_result = self._execute_action(action, alert, link, cosmic_monitor)

        # Registrar decisão para auditoria
        decision = {
            'timestamp': time.time(),
            'alert_id': alert['alert_id'],
            'link_id': alert['link_id'],
            'state': {
                'health_ent': state.health_ent,
                'criticality': state.criticality,
                'decoherence_rate': state.decoherence_rate
            },
            'action': action.name,
            'selection_method': selection_method,
            'reward': reward,
            'execution_result': execution_result
        }
        self.decision_log.append(decision)

        # Se em modo treino, armazenar transição para replay buffer
        if training:
            # Próximo estado simulado (simplificação)
            next_health = min(1.0, state.health_ent + reward * 0.1)
            next_state = AlertState(
                health_ent=next_health,
                criticality=state.criticality,
                decoherence_rate=max(0, state.decoherence_rate - 0.01),
                resource_availability=state.resource_availability,
                alert_level='WARNING' if next_health > 0.5 else 'CRITICAL',
                link_distance_ly=state.link_distance_ly
            )
            self.store_transition(state, action_idx, reward, next_state, done=(next_health > 0.9))
            # Treinar passo
            loss = self.train_step()
            decision['training_loss'] = loss

        return {
            'action': action.name,
            'reward': reward,
            'execution_result': execution_result,
            'decision_metadata': decision
        }

    def _execute_action(
        self,
        action: AlertAction,
        alert: Dict,
        link: 'CosmicEntanglementLink',
        cosmic_monitor: 'CosmicConsciousnessMonitor'
    ) -> Tuple[float, Dict]:
        """Executa ação e retorna reward + resultado."""
        if action == AlertAction.LOG:
            # Apenas registrar: reward pequeno positivo se alerta era WARNING
            reward = 0.1 if alert['alert_level'] == 'WARNING' else -0.1
            result = {'status': 'logged', 'message': alert['message']}

        elif action == AlertAction.ADAPT:
            # Adaptar parâmetros da missão: reward baseado em melhoria de saúde
            # Simulação: reduzir decoerência em 10%
            link.decoherence_factor *= 0.9
            new_health = link.compute_health_score()
            reward = (new_health - link.compute_health_score()) * 10  # escalar reward
            result = {
                'status': 'adapted',
                'new_decoherence': link.decoherence_factor,
                'health_improvement': reward
            }

        elif action == AlertAction.REENTANGLE:
            # Tentar re-emaranhamento: reward alto se sucesso
            reent_result = cosmic_monitor.request_reentanglement(
                link_id=alert['link_id'],
                via_galactic_core=True
            )
            if reent_result['status'] == 'success':
                reward = 1.0
                result = {'status': 'reentangled', **reent_result}
            else:
                reward = -0.5
                result = {'status': 'reentanglement_failed', **reent_result}

        elif action == AlertAction.HALT:
            # Parar operações: reward se evitar degradação maior
            # Simulação: congelar decoerência
            reward = 0.3 if link.decoherence_factor < 0.7 else -0.2
            result = {'status': 'operations_halted', 'frozen_decoherence': link.decoherence_factor}

        elif action == AlertAction.ESCALATE:
            # Escalar para humano: reward neutro, mas garante intervenção
            reward = 0.0
            result = {'status': 'escalated_to_human', 'alert_forwarded': True}

        else:
            reward = -1.0
            result = {'status': 'unknown_action'}

        return reward, result

    def get_policy_statistics(self) -> Dict:
        """Retorna estatísticas da política para monitoramento."""
        if not self.decision_log:
            return {'status': 'no_decisions_yet'}

        recent = self.decision_log[-100:]
        action_counts = {}
        for d in recent:
            action = d['action']
            action_counts[action] = action_counts.get(action, 0) + 1

        avg_reward = np.mean([d['reward'] for d in recent])

        return {
            'total_decisions': len(self.decision_log),
            'recent_action_distribution': action_counts,
            'avg_reward_last_100': avg_reward,
            'epsilon_current': self.epsilon,
            'training_steps': self.steps
        }

    def save_policy(self, path: str):
        """Salva política treinada para deploy."""
        torch.save({
            'policy_state_dict': self.policy_net.state_dict(),
            'target_state_dict': self.target_net.state_dict(),
            'epsilon': self.epsilon,
            'steps': self.steps,
            'decision_log_sample': self.decision_log[-100:]
        }, path)
        print(f"✅ Política salva em {path}")

    def load_policy(self, path: str) -> bool:
        """Carrega política treinada."""
        try:
            checkpoint = torch.load(path)
            self.policy_net.load_state_dict(checkpoint['policy_state_dict'])
            self.target_net.load_state_dict(checkpoint['target_state_dict'])
            self.epsilon = checkpoint.get('epsilon', self.epsilon)
            self.steps = checkpoint.get('steps', 0)
            print(f"✅ Política carregada de {path}")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar política: {e}")
            return False
