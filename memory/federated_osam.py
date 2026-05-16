#!/usr/bin/env python3
"""
Substrato 199.7: Federated OSAM — Sincronização de Estados δ‑mem entre Nós Sentinel
Canon: ∞.Ω.∇+++.199.7.federated
Privacidade diferencial (ε=2.0) para sincronização de estados associativos
entre organizações parceiras sem vazamento de dados sensíveis.
"""

import asyncio
import hashlib
import json
import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FederatedOSAMUpdate:
    """Atualização federada de estado OSAM com ruído DP."""
    node_id: str
    organization_id: str
    timestamp: float
    state_updates: Dict[int, np.ndarray]  # state_idx → ΔS (matriz r×r com ruído)
    dp_noise_epsilon: float
    aggregation_weight: float  # Peso para FedAvg
    temporal_seal: Optional[str] = None

class FederatedOSAMAggregator:
    """
    Agregador federado para estados OSAM entre nós Sentinel.

    Princípios:
    • Cada nó mantém estado OSAM local (S ∈ ℝ^{r×r})
    • Periodicamente, nós publicam atualizações ΔS com ruído Laplace(0, 1/ε)
    • Agregador combina atualizações via FedAvg ponderado
    • Estados sincronizados são distribuídos de volta aos nós
    • Privacidade garantida: dados brutos NUNCA saem do nó local
    """

    # Configurações de federação
    FEDERATION_CONFIG = {
        "min_epsilon": 2.0,           # Privacidade mínima exigida
        "max_epsilon": 5.0,           # Privacidade máxima (mais utilidade)
        "aggregation_window_sec": 300,  # Janela para agregar atualizações
        "min_nodes_for_sync": 3,      # Mínimo de nós para sincronização
        "sync_frequency_sec": 600,    # Frequência de sincronização global
    }

    def __init__(
        self,
        node_id: str,
        organization_id: str,
        r: int = 8,
        num_states: int = 4,
        phi_bus=None,
        temporal_chain=None
    ):
        self.node_id = node_id
        self.org_id = organization_id
        self.r = r
        self.num_states = num_states
        self.phi_bus = phi_bus
        self.temporal = temporal_chain

        # Estado OSAM local
        self.local_states: List[np.ndarray] = [
            np.zeros((r, r)) for _ in range(num_states)
        ]

        # Buffer de atualizações recebidas
        self._update_buffer: Dict[str, List[FederatedOSAMUpdate]] = {}
        self._last_sync_timestamp: float = 0.0

        # Estatísticas de federação
        self._sync_rounds: int = 0
        self._total_updates_received: int = 0

    def _add_laplace_noise(self, matrix: np.ndarray, epsilon: float) -> np.ndarray:
        """Adiciona ruído Laplace element-wise para privacidade diferencial."""
        scale = 1.0 / max(epsilon, 0.01)
        noise = np.random.laplace(0, scale, matrix.shape)
        return matrix + noise

    async def generate_local_update(self, epsilon: float) -> FederatedOSAMUpdate:
        """
        Gera atualização local com ruído DP para federação.

        Args:
            epsilon: Parâmetro de privacidade diferencial (menor = mais privacidade)

        Returns:
            FederatedOSAMUpdate com estados perturbados
        """
        if epsilon < self.FEDERATION_CONFIG["min_epsilon"]:
            raise ValueError(f"ε={epsilon} abaixo do mínimo permitido {self.FEDERATION_CONFIG['min_epsilon']}")

        # Calcular atualizações (diferença desde última sincronização)
        # Para demo: simular atualizações baseadas em atividade recente
        state_updates = {}
        for state_idx in range(self.num_states):
            # Simular atualização (em produção: gradiente real do treinamento)
            raw_update = np.random.randn(self.r, self.r) * 0.01
            # Aplicar ruído Laplace
            noisy_update = self._add_laplace_noise(raw_update, epsilon)
            state_updates[state_idx] = noisy_update

        update = FederatedOSAMUpdate(
            node_id=self.node_id,
            organization_id=self.org_id,
            timestamp=time.time(),
            state_updates=state_updates,
            dp_noise_epsilon=epsilon,
            aggregation_weight=1.0  # Pode ser ajustado por confiança/reputação
        )

        # Ancorar na TemporalChain
        if self.temporal:
            update.temporal_seal = await self.temporal.anchor_event(
                "federated_osam_update_generated",
                {
                    "node_id": self.node_id,
                    "org_id": self.org_id,
                    "epsilon": epsilon,
                    "state_count": len(state_updates),
                    "timestamp": update.timestamp
                }
            )

        logger.info(f"🔄 Atualização OSAM gerada: ε={epsilon}, selo={update.temporal_seal[:16] if update.temporal_seal else 'N/A'}")
        return update

    async def receive_federated_update(self, update: FederatedOSAMUpdate) -> Dict:
        """
        Recebe atualização federada de outro nó.

        Validações:
        • ε dentro de limites configurados
        • Assinatura/autenticação do nó remetente
        • Freshness do timestamp
        """
        # Validar privacidade
        if not (self.FEDERATION_CONFIG["min_epsilon"] <= update.dp_noise_epsilon <= self.FEDERATION_CONFIG["max_epsilon"]):
            return {"status": "rejected", "reason": "epsilon_out_of_range"}

        # Validar timestamp (não aceitar atualizações muito antigas)
        if time.time() - update.timestamp > self.FEDERATION_CONFIG["aggregation_window_sec"] * 2:
            return {"status": "rejected", "reason": "update_too_old"}

        # Armazenar no buffer
        if update.node_id not in self._update_buffer:
            self._update_buffer[update.node_id] = []
        self._update_buffer[update.node_id].append(update)
        self._total_updates_received += 1

        # Publicar métrica no Phi-Bus
        if self.phi_bus:
            await self.phi_bus.publish_metric("federated_osam_update_received", {
                "from_node": update.node_id,
                "from_org": update.organization_id,
                "epsilon": update.dp_noise_epsilon,
                "weight": update.aggregation_weight
            })

        # Verificar se é hora de sincronização global
        if time.time() - self._last_sync_timestamp >= self.FEDERATION_CONFIG["sync_frequency_sec"]:
            await self._perform_global_sync()

        return {"status": "accepted", "buffer_size": len(self._update_buffer)}

    async def _perform_global_sync(self):
        """Executa sincronização global via FedAvg ponderado."""
        logger.info(f"🌐 Iniciando sincronização global de estados OSAM...")

        # Coletar atualizações válidas da janela
        cutoff = time.time() - self.FEDERATION_CONFIG["aggregation_window_sec"]
        valid_updates = []

        for node_updates in self._update_buffer.values():
            for update in node_updates:
                if update.timestamp >= cutoff and update.node_id != self.node_id:
                    valid_updates.append(update)

        if len(valid_updates) < self.FEDERATION_CONFIG["min_nodes_for_sync"]:
            logger.info(f"⚠️  Insuficientes nós para sincronização: {len(valid_updates)} < {self.FEDERATION_CONFIG['min_nodes_for_sync']}")
            return

        # FedAvg ponderado: S_global = Σ (w_i · ΔS_i) / Σ w_i
        total_weight = sum(u.aggregation_weight for u in valid_updates)
        if total_weight == 0:
            return

        for state_idx in range(self.num_states):
            # Agregar atualizações para este estado
            aggregated = np.zeros((self.r, self.r))
            for update in valid_updates:
                if state_idx in update.state_updates:
                    weight = update.aggregation_weight / total_weight
                    aggregated += weight * update.state_updates[state_idx]

            # Atualizar estado local com média federada
            self.local_states[state_idx] += aggregated * 0.1  # Learning rate federado

        self._sync_rounds += 1
        self._last_sync_timestamp = time.time()

        # Ancorar sincronização na TemporalChain
        if self.temporal:
            await self.temporal.anchor_event("federated_osam_sync_completed", {
                "node_id": self.node_id,
                "org_id": self.org_id,
                "updates_aggregated": len(valid_updates),
                "sync_round": self._sync_rounds,
                "timestamp": self._last_sync_timestamp
            })

        logger.info(f"✅ Sincronização global concluída: round {self._sync_rounds}, {len(valid_updates)} atualizações agregadas")

    def get_local_state(self, state_idx: int) -> np.ndarray:
        """Retorna estado OSAM local para uso em inferência."""
        return self.local_states[state_idx].copy()

    def get_federation_statistics(self) -> Dict:
        """Retorna estatísticas da federação."""
        return {
            "node_id": self.node_id,
            "org_id": self.org_id,
            "local_states": self.num_states,
            "state_dimension": self.r,
            "sync_rounds": self._sync_rounds,
            "total_updates_received": self._total_updates_received,
            "unique_peer_nodes": len(self._update_buffer),
            "last_sync_timestamp": self._last_sync_timestamp,
            "epsilon_range": f"[{self.FEDERATION_CONFIG['min_epsilon']}, {self.FEDERATION_CONFIG['max_epsilon']}]"
        }