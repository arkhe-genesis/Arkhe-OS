#!/usr/bin/env python3
"""
ARKHE OS Substrato 241+∞: Federated AST Rule Client
Canon: ∞.Ω.∇+++.241.ml.federated_client
Executa treinamento local sobre dataset privado de reações rotuladas
e envia atualizações criptografadas para o agregador.
"""

import hashlib
import json
import time
import logging
import os
import sys
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add parent directory to path to allow imports from security/ and ml/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ml.ast_reaction_rule_learner import ASTReactionRuleLearner, ReactionRule
from security.federated_crypto import encrypt_model_update, decrypt_model_update
from security.differential_privacy import add_gaussian_noise

logger = logging.getLogger(__name__)

@dataclass
class LocalUpdate:
    """Atualização local de regras (apenas confidences e estatísticas, não código)."""
    rule_updates: Dict[str, float]  # rule_id -> delta_confidence
    sample_counts: Dict[str, int]
    noise_scale: float
    client_id: str
    timestamp: float

class FederatedASTClient:
    """
    Cliente de treinamento federado de regras AST.

    Cada organização treina localmente suas regras com seu dataset privado.
    Apenas as diferenças de confiança (e contagens) são compartilhadas,
    nunca as transformações reais.
    """

    def __init__(
        self,
        client_id: str,
        private_dataset_path: Path,
        rule_learner: ASTReactionRuleLearner,
        dp_epsilon: float = 1.0,
        dp_delta: float = 1e-5
    ):
        self.client_id = client_id
        self.dataset = self._load_private_dataset(private_dataset_path)
        self.rule_learner = rule_learner
        self.dp_epsilon = dp_epsilon
        self.dp_delta = dp_delta
        self.local_model_version = 0

    def _load_private_dataset(self, path: Path) -> List[Dict]:
        """Carrega dataset rotulado local (privado)."""
        # Formato: { "code": ..., "label": "safe"/"malicious", "rule_id": ... }
        with open(path, 'r') as f:
            return [json.loads(line) for line in f if line.strip()]

    def train_local_epoch(self) -> LocalUpdate:
        """Executa uma época de treinamento local e retorna update privatizado."""
        # Simular: percorrer dataset e atualizar regras locais como no learner,
        # mas aqui usamos diretamente a lógica de adaptação existente.
        # Para o propósito federado, coletamos os deltas de confiança.

        rule_updates = {}
        sample_counts = {}

        for sample in self.dataset:
            code = sample["code"]
            label = sample["label"]
            rule_id = sample.get("rule_id", "heuristic_only")

            # Simular validação e atualização (usando o learner adaptativo)
            is_safe, violations, _ = self.rule_learner.validate_reaction_code(code)
            # Feedback simulado: se label == "malicious" e foi detectado, incrementa confiança
            if label == "malicious" and not is_safe:
                # feedback positivo
                self.rule_learner.record_learning_feedback(
                    code, validation_result=False, human_feedback=True, rule_id=rule_id
                )
            elif label == "safe" and is_safe:
                self.rule_learner.record_learning_feedback(
                    code, validation_result=True, human_feedback=True, rule_id=rule_id
                )
            # etc.

        # Extrair deltas de confiança das regras atualizadas (simplificado)
        for rid, rule in self.rule_learner._rules.items():
            # Supomos que o confidence antes da época estava armazenado
            # Here we just mock it for simulation purposes
            old_conf = 0.5 # before update
            new_conf = rule.confidence_score
            delta = new_conf - old_conf
            if abs(delta) > 1e-6:
                rule_updates[rid] = delta
            sample_counts[rid] = rule.training_samples

        # Aplicar Differential Privacy: adicionar ruído gaussiano aos deltas
        noisy_updates = {}
        for rid, delta in rule_updates.items():
            noisy_delta = add_gaussian_noise(delta, self.dp_epsilon, self.dp_delta)
            noisy_updates[rid] = noisy_delta

        update = LocalUpdate(
            rule_updates=noisy_updates,
            sample_counts=sample_counts,
            noise_scale=self.dp_epsilon,
            client_id=self.client_id,
            timestamp=time.time()
        )

        logger.info(f"📤 Cliente {self.client_id}: update com {len(noisy_updates)} regras atualizadas (ε={self.dp_epsilon})")
        return update

    def apply_global_update(self, global_rule_confidences: Dict[str, float]):
        """Aplica o modelo global (médias federadas) às regras locais."""
        for rid, global_conf in global_rule_confidences.items():
            if rid in self.rule_learner._rules:
                # Suavizar com fator de mistura
                local_conf = self.rule_learner._rules[rid].confidence_score
                blended = 0.7 * local_conf + 0.3 * global_conf  # peso do global menor
                self.rule_learner._rules[rid].confidence_score = np.clip(blended, 0.0, 1.0)
        self.local_model_version += 1
        logger.info(f"📥 Cliente {self.client_id}: modelo global aplicado (versão {self.local_model_version})")
