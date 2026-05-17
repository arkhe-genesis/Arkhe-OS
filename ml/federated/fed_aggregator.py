#!/usr/bin/env python3
"""
ARKHE OS Substrato 241+∞: Federated AST Aggregator
Canon: ∞.Ω.∇+++.241.ml.federated_aggregator
Agrega atualizações criptografadas de múltiplos clientes usando
Secure Aggregation (média ponderada com ruído DP) e distribui o modelo global.
"""

import hashlib
import json
import time
import logging
import os
import sys
import numpy as np
from typing import Dict, List
from collections import defaultdict

# Add parent directory to path to allow imports from security/ and ml/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from security.federated_crypto import encrypt_model_update, decrypt_model_update
from security.differential_privacy import add_gaussian_noise
from .fed_ast_client import LocalUpdate

logger = logging.getLogger(__name__)

class FederatedAggregator:
    """
    Agregador central (pode ser descentralizado com computação multipartidária).
    """

    def __init__(self, dp_epsilon_global: float = 2.0):
        self.global_rule_confidences: Dict[str, float] = {}
        self.round = 0
        self.dp_epsilon_global = dp_epsilon_global

    def aggregate_round(self, client_updates: List[LocalUpdate]) -> Dict[str, float]:
        """
        Recebe updates de todos os clientes, agrega via FedAvg com pesos
        baseados no número de amostras, e aplica ruído DP adicional.
        """
        # Coletar deltas por regra
        rule_deltas = defaultdict(list)
        rule_weights = defaultdict(list)

        for update in client_updates:
            for rid, delta in update.rule_updates.items():
                rule_deltas[rid].append(delta)
                # peso = número de amostras locais para aquela regra
                count = update.sample_counts.get(rid, 1)
                rule_weights[rid].append(count)

        new_global = {}
        for rid in rule_deltas:
            # Média ponderada dos deltas
            deltas = np.array(rule_deltas[rid])
            weights = np.array(rule_weights[rid])
            weighted_avg = np.average(deltas, weights=weights)

            # Adicionar ruído DP global
            noisy_avg = add_gaussian_noise(weighted_avg, self.dp_epsilon_global, delta=1e-6)

            # Atualizar confiança global (partindo da confiança global anterior)
            old_global_conf = self.global_rule_confidences.get(rid, 0.5)
            new_conf = np.clip(old_global_conf + noisy_avg, 0.0, 1.0)
            new_global[rid] = new_conf

        self.global_rule_confidences.update(new_global)
        self.round += 1
        logger.info(f"🔄 Rodada {self.round}: {len(new_global)} regras agregadas (ε_global={self.dp_epsilon_global})")
        return self.global_rule_confidences

    def get_global_model(self) -> Dict[str, float]:
        return self.global_rule_confidences
