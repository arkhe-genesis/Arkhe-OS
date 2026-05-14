#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
genomic_qnc.py — Genomic Quantum Neural Coding
Módulo principal para QNC genômico com transfer learning.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from arkp_qnc.src.qnc_transfer import MultiSpeciesQNC
from arkp_sigha.src.sigha_phi_c import FisherBuresManifold, NaturalGradientFlow


@dataclass
class GenomicQNCConfig:
    """Configuração para GenomicQNC."""
    max_len: int = 128
    hidden_dim: int = 8
    num_classes: int = 2
    phi_c_coupling: float = 0.1
    learning_rate: float = 0.05
    lambda_phi: float = 0.1


class GenomicQNC:
    """Rede neural quântica para análise genômica."""

    def __init__(self, config: GenomicQNCConfig = None):
        self.config = config or GenomicQNCConfig()
        self.model = MultiSpeciesQNC(
            max_len=self.config.max_len,
            hidden_dim=self.config.hidden_dim
        )
        self.manifold = FisherBuresManifold(self.config.hidden_dim)
        self.flow = NaturalGradientFlow(self.manifold)
        self.phi_c_field = np.eye(self.config.hidden_dim, dtype=complex) / self.config.hidden_dim
        self.loss_history = []

    def train(self, sequences: List[str], labels: List[int], epochs: int = 50) -> List[float]:
        """Treina o modelo em sequências genômicas."""
        for epoch in range(epochs):
            epoch_loss = 0.0
            for seq, label in zip(sequences, labels):
                loss = self.model._train_step(seq, label, "default", self.config.learning_rate)
                epoch_loss += loss
            avg_loss = epoch_loss / len(sequences)
            self.loss_history.append(avg_loss)
        return self.loss_history

    def predict(self, sequence: str) -> int:
        """Prediz classe para sequência genômica."""
        return self.model.predict(sequence, "default")

    def predict_proba(self, sequence: str) -> np.ndarray:
        """Retorna probabilidades de classe."""
        logits = self.model.forward(sequence, "default")
        exp_logits = np.exp(logits - np.max(logits))
        return exp_logits / np.sum(exp_logits)

    def get_phi_c(self) -> float:
        """Retorna valor atual de Φ_C."""
        return float(np.real(np.trace(self.phi_c_field)))

    def update_phi_c(self, new_phi_c_field: np.ndarray):
        """Atualiza campo Φ_C."""
        self.phi_c_field = new_phi_c_field
        self.model.phi_c_field = new_phi_c_field
