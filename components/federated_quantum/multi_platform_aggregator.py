#!/usr/bin/env python3
"""
multi_platform_aggregator.py — Agregação federada entre plataformas quânticas heterogêneas.
Suporta supercondutores (IBM), íons (IonQ) e fotônicos (Xanadu) com ponderação por fidelidade.
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import hashlib
import time

@dataclass
class PlatformConfig:
    """Configuração de uma plataforma quântica na federação."""
    platform_id: str  # 'ibm', 'ionq', 'xanadu', etc.
    epsilon: float  # parâmetro de privacidade
    base_fidelity: float  # fidelidade média histórica
    latency_ms: float  # latência típica de comunicação
    cost_per_shot: float  # custo relativo por shot

    def compute_weight(self, current_fidelity: float) -> float:
        """Calcula peso da plataforma baseado em fidelidade e custo."""
        # Peso ∝ fidelidade / (epsilon * custo * latência)
        return current_fidelity / (self.epsilon * self.cost_per_shot * (1 + self.latency_ms / 1000))

@dataclass
class FederatedQuantumConfig:
    """Configuração global para federação multi-plataforma."""
    platforms: Dict[str, PlatformConfig]
    aggregation_window: int = 10  # rounds para agregação
    min_participants: int = 2  # mínimo de plataformas para agregar
    global_epsilon: float = 1.0  # privacidade global

class MultiPlatformFederatedAggregator:
    """
    Agregador federado para políticas quânticas entre múltiplas plataformas.
    """

    def __init__(self, config: FederatedQuantumConfig):
        self.config = config
        self.platform_buffers: Dict[str, List[Dict]] = {
            pid: [] for pid in config.platforms
        }
        self.round_counter = 0
        self.aggregation_history: List[Dict] = []

    def submit_platform_update(
        self,
        platform_id: str,
        update: Dict[str, torch.Tensor],
        current_fidelity: float,
        round_num: int,
        metadata: Optional[Dict] = None
    ) -> str:
        """Submete atualização de uma plataforma específica."""
        if platform_id not in self.config.platforms:
            raise ValueError(f"Unknown platform: {platform_id}")

        # Clipping para limitar sensibilidade
        clipped_update = self._clip_update(update)

        # Gerar ID único
        update_id = hashlib.sha256(
            f"{platform_id}_{round_num}_{time.time()}".encode()
        ).hexdigest()[:12]

        # Armazenar no buffer da plataforma
        self.platform_buffers[platform_id].append({
            'id': update_id,
            'update': clipped_update,
            'fidelity': current_fidelity,
            'timestamp': time.time(),
            'metadata': metadata or {}
        })

        return update_id

    def _clip_update(self, update: Dict[str, torch.Tensor], max_norm: float = 1.0) -> Dict[str, torch.Tensor]:
        """Aplica clipping L2 às atualizações."""
        clipped = {}
        for name, param in update.items():
            param_norm = torch.norm(param)
            if param_norm > max_norm:
                clipped[name] = param * (max_norm / param_norm)
            else:
                clipped[name] = param
        return clipped

    def aggregate_multi_platform(self, round_num: int) -> Optional[Dict[str, torch.Tensor]]:
        """
        Agrega atualizações de múltiplas plataformas com ponderação por fidelidade.
        """
        # Coletar plataformas com dados suficientes
        active_platforms = []
        for pid, config in self.config.platforms.items():
            buffer = self.platform_buffers[pid]
            if len(buffer) >= 1:  # Pelo menos uma atualização
                active_platforms.append((pid, config, buffer[-1]))

        if len(active_platforms) < self.config.min_participants:
            return None

        # Calcular pesos ponderados
        weights = {}
        total_weight = 0.0
        for pid, config, entry in active_platforms:
            weight = config.compute_weight(entry['fidelity'])
            weights[pid] = weight
            total_weight += weight

        if total_weight == 0:
            return None

        # Normalizar pesos
        weights = {pid: w / total_weight for pid, w in weights.items()}

        # Agregação ponderada com ruído diferencial
        aggregated = {}
        param_names = active_platforms[0][2]['update'].keys()

        for name in param_names:
            # Média ponderada das atualizações
            weighted_sum = torch.zeros_like(active_platforms[0][2]['update'][name])
            for pid, config, entry in active_platforms:
                weighted_sum += weights[pid] * entry['update'][name]

            # Adicionar ruído DP global
            noise_scale = self._compute_noise_scale(total_weight)
            noisy_param = weighted_sum + torch.randn_like(weighted_sum) * noise_scale
            aggregated[name] = noisy_param

        # Registrar agregação
        self.aggregation_history.append({
            'round': round_num,
            'platforms': [pid for pid, _, _ in active_platforms],
            'weights': weights,
            'timestamp': time.time()
        })

        # Limpar buffers das plataformas participantes
        for pid, _, _ in active_platforms:
            if self.platform_buffers[pid]:
                self.platform_buffers[pid].pop()

        return aggregated

    def _compute_noise_scale(self, total_weight: float) -> float:
        """Calcula escala de ruído para privacidade diferencial global."""
        # σ = (sensitivity * sqrt(2 * ln(1.25/δ))) / (ε * total_weight)
        sensitivity = 1.0  # assumida
        delta = 1e-5
        epsilon = self.config.global_epsilon

        return sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / (epsilon * total_weight)

    def get_federation_health(self) -> Dict[str, any]:
        """Retorna saúde da federação multi-plataforma."""
        health = {}
        for pid, config in self.config.platforms.items():
            buffer = self.platform_buffers[pid]
            health[pid] = {
                'pending_updates': len(buffer),
                'base_fidelity': config.base_fidelity,
                'epsilon': config.epsilon,
                'latency_ms': config.latency_ms,
                'cost_per_shot': config.cost_per_shot
            }

        return {
            'platforms': health,
            'rounds_completed': self.round_counter,
            'aggregation_history_count': len(self.aggregation_history),
            'timestamp': time.time()
        }
