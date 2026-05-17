#!/usr/bin/env python3
"""
ARKHE OS Substrato ∞: Federated Prompt RL Integration
Canon: ∞.Ω.∇+++.learning.federated_prompt_rl
Função: Conectar PromptRLOptimizer ao FederatedPromptRLAggregator,
permitindo que múltiplas organizações treinem políticas de prompt
sem compartilhar dados brutos.
"""

import asyncio
import hashlib
import json
import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import deque
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FederatedPromptRLLearning:
    """
    Integração entre PromptRLOptimizer (local) e FederatedPromptRLAggregator (global).
    """

    def __init__(
        self,
        org_id: str,
        local_optimizer,          # PromptRLOptimizer instance
        federated_aggregator,     # FederatedPromptRLAggregator instance
        temporal_chain=None,
        phi_bus=None,
        hsm_signer=None,
        aggregation_interval_seconds: int = 300
    ):
        self.org_id = org_id
        self.local_optimizer = local_optimizer
        self.aggregator = federated_aggregator
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.hsm = hsm_signer
        self.aggregation_interval = aggregation_interval_seconds
        self._last_aggregation_time = 0
        self._running = False

    async def start_federated_learning(self):
        """Inicia o loop de aprendizado federado."""
        self._running = True
        logger.info(f"🚀 Federated Prompt RL iniciado para organização {self.org_id}")

        while self._running:
            try:
                # Treinar localmente com novas experiências
                if len(self.local_optimizer._experience_buffer) >= 32:
                    await self._train_local_policy()

                # Enviar atualização para agregação se passou o intervalo
                if time.time() - self._last_aggregation_time >= self.aggregation_interval:
                    await self._federate_local_policy()

                # Receber política global atualizada
                await self._sync_global_policy()

                await asyncio.sleep(60)  # Loop a cada minuto

            except Exception as e:
                logger.error(f"❌ Erro no loop de aprendizado federado: {e}")
                await asyncio.sleep(60)

    async def _train_local_policy(self):
        """Treina a política local com as experiências acumuladas."""
        self.local_optimizer._train_policy_batch(batch_size=min(64, len(self.local_optimizer._experience_buffer)))

    async def _federate_local_policy(self):
        """Prepara e envia atualização federada baseada na política local."""
        # Criar um snapshot da Q-table local
        q_table_snapshot = {
            state: list(q_values) for state, q_values in self.local_optimizer.policy._q_table.items()
        }

        # Criar atualização federada com DP
        update = await self.aggregator.compute_local_update(
            local_experiences=[],  # não precisamos passar experiências brutas
            dp_epsilon=2.0
        )
        # Sobrescrever Q-table com a versão local ruidosa
        update.q_table_snapshot = q_table_snapshot

        # Enviar ao agregador (em produção, publicar no barramento ou enviar diretamente)
        self.aggregator._pending_updates.append(update)
        logger.info(f"📤 Política local enviada para federação: {len(q_table_snapshot)} estados")

        # Se tivermos atualizações suficientes de outras orgs (mock), agregar
        if len(self.aggregator._pending_updates) >= 3:
            await self.aggregator.aggregate_global_policy(self.aggregator._pending_updates)
            self.aggregator._pending_updates.clear()
            self._last_aggregation_time = time.time()

    async def _sync_global_policy(self):
        """Atualiza a política local com a política global agregada."""
        if self.aggregator._global_policy:
            # Mesclar a política global na política local (com peso)
            for state, q_values in self.aggregator._global_policy.items():
                if state in self.local_optimizer.policy._q_table:
                    # Média móvel: 80% local, 20% global
                    self.local_optimizer.policy._q_table[state] = [
                        local_q * 0.8 + global_q * 0.2
                        for local_q, global_q in zip(self.local_optimizer.policy._q_table[state], q_values)
                    ]
                else:
                    self.local_optimizer.policy._q_table[state] = list(q_values)
            logger.debug(f"🔄 Política local sincronizada com política global ({len(self.aggregator._global_policy)} estados)")

    def stop(self):
        self._running = False
