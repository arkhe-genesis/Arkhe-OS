#!/usr/bin/env python3
"""
dp_aggregator.py — Agregador federado para políticas quânticas com privacidade diferencial.
Implementa Gaussian mechanism para agregação segura de atualizações de múltiplos qubits/zones.
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import hashlib
import time

@dataclass
class DPConfig:
    """Configuração para privacidade diferencial federada."""
    epsilon: float = 1.0  # parâmetro de privacidade (menor = mais privacidade)
    delta: float = 1e-5   # probabilidade de falha de privacidade
    sensitivity: float = 1.0  # sensibilidade L2 das atualizações
    clipping_norm: float = 1.0  # norma máxima para clipping de gradientes
    aggregation_window: int = 10  # número de rounds para agregação

class FederatedQuantumAggregator:
    """
    Agregador federado para políticas de mitigação quântica com privacidade diferencial.
    """

    def __init__(self, config: DPConfig, num_participants: int):
        self.config = config
        self.num_participants = num_participants

        # Calcular ruído para Gaussian mechanism
        # σ = (sensitivity * sqrt(2 * ln(1.25/δ))) / ε
        self.noise_multiplier = (
            config.sensitivity * np.sqrt(2 * np.log(1.25 / config.delta)) / config.epsilon
        )

        # Buffer para agregação
        self.update_buffer: Dict[int, List[Dict]] = {}
        self.round_counter = 0

        # Histórico de agregações para auditoria
        self.aggregation_log: List[Dict] = []

    def clip_update(self, update: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Aplica clipping L2 às atualizações para limitar sensibilidade."""
        clipped = {}
        for name, param in update.items():
            param_norm = torch.norm(param)
            if param_norm > self.config.clipping_norm:
                clipped[name] = param * (self.config.clipping_norm / param_norm)
            else:
                clipped[name] = param
        return clipped

    def add_noise(self, update: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Adiciona ruído Gaussiano para privacidade diferencial."""
        noisy = {}
        for name, param in update.items():
            noise = torch.randn_like(param) * self.noise_multiplier * self.config.clipping_norm
            noisy[name] = param + noise
        return noisy

    def submit_update(
        self,
        participant_id: str,
        update: Dict[str, torch.Tensor],
        round_num: int,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Submete atualização de participante para agregação federada.

        Returns:
            update_id para rastreamento
        """
        # Clipping para limitar sensibilidade
        clipped_update = self.clip_update(update)

        # Gerar ID único para a atualização
        update_id = hashlib.sha256(
            f"{participant_id}_{round_num}_{time.time()}".encode()
        ).hexdigest()[:12]

        # Armazenar no buffer
        if round_num not in self.update_buffer:
            self.update_buffer[round_num] = []

        self.update_buffer[round_num].append({
            'id': update_id,
            'participant_id': participant_id,
            'update': clipped_update,
            'metadata': metadata or {},
            'timestamp': time.time()
        })

        return update_id

    def aggregate_round(self, round_num: int) -> Optional[Dict[str, torch.Tensor]]:
        """
        Agrega atualizações de um round específico com privacidade diferencial.

        Returns:
            Atualização agregada com ruído DP, ou None se não houver dados suficientes
        """
        if round_num not in self.update_buffer:
            return None

        updates = self.update_buffer[round_num]

        # Verificar número mínimo de participantes para privacidade
        if len(updates) < max(2, self.num_participants // 4):
            return None

        # Agregação: média das atualizações
        aggregated = {}
        param_names = updates[0]['update'].keys()

        for name in param_names:
            # Coletar parâmetros de todos os participantes
            params = [u['update'][name] for u in updates]

            # Média simples
            mean_param = torch.stack(params).mean(dim=0)

            # Adicionar ruído DP
            noisy_param = mean_param + torch.randn_like(mean_param) * self.noise_multiplier * self.config.clipping_norm / np.sqrt(len(updates))

            aggregated[name] = noisy_param

        # Registrar agregação para auditoria
        self.aggregation_log.append({
            'round': round_num,
            'num_participants': len(updates),
            'noise_multiplier': self.noise_multiplier,
            'epsilon': self.config.epsilon,
            'timestamp': time.time()
        })

        # Limpar buffer do round
        del self.update_buffer[round_num]

        return aggregated

    def get_privacy_accountant(self) -> Dict[str, Union[float, int, str]]:
        """Retorna métricas de privacidade para auditoria."""
        # Cálculo simplificado de privacy budget gasto
        # Em produção: usar privacy accountant do TensorFlow Privacy ou Opacus
        rounds_completed = len(self.aggregation_log)

        # Composição básica: ε_total ≈ k * ε / sqrt(n) para k rounds
        epsilon_spent = rounds_completed * self.config.epsilon / np.sqrt(self.num_participants)

        return {
            'epsilon_per_round': self.config.epsilon,
            'delta': self.config.delta,
            'rounds_completed': rounds_completed,
            'epsilon_total_estimate': epsilon_spent,
            'privacy_guarantee': f'({epsilon_spent:.2f}, {self.config.delta})-DP'
        }

    def export_audit_log(self, path: str):
        """Exporta log de agregações para auditoria externa."""
        import json
        audit_data = {
            'config': {
                'epsilon': self.config.epsilon,
                'delta': self.config.delta,
                'sensitivity': self.config.sensitivity,
                'num_participants': self.num_participants
            },
            'aggregations': self.aggregation_log,
            'privacy_accountant': self.get_privacy_accountant(),
            'export_timestamp': time.time()
        }

        with open(path, 'w') as f:
            json.dump(audit_data, f, indent=2)
        print(f"✅ Audit log exportado para {path}")
