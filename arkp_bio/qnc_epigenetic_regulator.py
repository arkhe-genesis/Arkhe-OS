#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qnc_epigenetic_regulator.py — Substrato 6180: Regulador QNC-Epigenético Integrado
Modelo que integra QNC com epigenética quântica para regulação gênica.

Arquitetura:
  RNA Embedding → Epigenetic Attention → QNC Core → Expression Prediction
"""

import numpy as np
from scipy.linalg import sqrtm
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from src.arkhe.layers.sigha_core import FisherBuresManifold, NaturalGradientFlow
from arkp_bio.rna_quantum_embedding import RNAEmbedding, RNAType
from arkp_bio.epigenetic_operators import (
    MethylationOperator, HistoneModificationField,
    EpigeneticState, EpigeneticMark
)

@dataclass
class QNCEpigeneticConfig:
    """Configuração do modelo integrado QNC-epigenético."""
    max_rna_length: int = 512
    embedding_dim: int = 32
    hidden_dim: int = 64
    num_attention_heads: int = 4
    phi_c_coupling: float = 0.15
    epigenetic_coupling: float = 0.2
    learning_rate: float = 0.02
    num_classes: int = 2  # expresso/não-expresso ou níveis discretos

class EpigeneticAttention:
    """
    Mecanismo de atenção quântica modulada por epigenética.

    A atenção é ponderada não apenas por similaridade quântica,
    mas também por acessibilidade epigenética da região alvo.
    """

    def __init__(self, query_dim: int, key_dim: int, value_dim: int, num_heads: int = 4):
        self.query_dim = query_dim
        self.key_dim = key_dim
        self.value_dim = value_dim
        self.num_heads = num_heads
        self.head_dim = query_dim // num_heads

        # Projetores para cada head
        self.W_q = [np.eye(self.head_dim, dtype=complex) / self.head_dim
                   for _ in range(num_heads)]
        self.W_k = [np.eye(self.head_dim, dtype=complex) / self.head_dim
                   for _ in range(num_heads)]
        self.W_v = [np.eye(self.head_dim, dtype=complex) / self.head_dim
                   for _ in range(num_heads)]

        # Manifold para otimização
        self.manifold = FisherBuresManifold(self.head_dim)
        self.flow = NaturalGradientFlow(self.manifold)

    def compute_epigenetic_attention(
        self,
        query_rho: np.ndarray,
        key_rhos: List[np.ndarray],
        value_rhos: List[np.ndarray],
        epigenetic_accessibility: List[float],
    ) -> np.ndarray:
        """
        Calcula atenção com modulação epigenética.

        Args:
            query_rho: Operador densidade da query
            key_rhos: Lista de operadores densidade das keys
            value_rhos: Lista de operadores densidade dos values
            epigenetic_accessibility: Lista de scores de acessibilidade epigenética

        Returns:
            Operador densidade de saída ponderado
        """
        scores = []

        for i, (key_rho, accessibility) in enumerate(zip(key_rhos, epigenetic_accessibility)):
            # Fidelidade quântica entre query e key
            fid = self._quantum_fidelity(query_rho, key_rho)

            # Modulação epigenética: regiões mais acessíveis recebem mais atenção
            epi_weight = accessibility ** 1.5  # Exponencial para ênfase

            # Score combinado
            score = fid * epi_weight
            scores.append(score)

        # Softmax
        scores = np.array(scores)
        exp_scores = np.exp(scores - np.max(scores))
        weights = exp_scores / (np.sum(exp_scores) + 1e-12)

        # Aplicar atenção aos values
        output = sum(w * v for w, v in zip(weights, value_rhos))

        # Normalizar
        trace = np.trace(output)
        if trace > 1e-10:
            output /= trace

        return output

    def _quantum_fidelity(self, rho1: np.ndarray, rho2: np.ndarray) -> float:
        """Calcula fidelidade de Uhlmann entre dois estados quânticos."""
        sqrt_rho1 = sqrtm(rho1)
        inner = sqrt_rho1 @ rho2 @ sqrt_rho1
        fid = np.real(np.trace(sqrtm(inner)))
        return np.clip(fid, 0.0, 1.0)

    def update_weights(self, grad: np.ndarray, lr: float):
        """Atualiza pesos via gradiente natural."""
        for i in range(self.num_heads):
            head_grad = grad[i * self.head_dim:(i+1) * self.head_dim,
                           i * self.head_dim:(i+1) * self.head_dim]
            self.W_q[i] = self.flow.step(self.W_q[i], head_grad, lr)

class QNCEpigeneticRegulator:
    """
    Regulador integrado QNC-epigenético para predição de expressão gênica.

    Arquitetura:
      1. RNA Embedding: codifica sequência de RNA em operadores quânticos
      2. Epigenetic Attention: atenção modulada por acessibilidade epigenética
      3. QNC Core: processamento via rede neural quântica regularizada
      4. Expression Output: predição de nível de expressão
    """

    def __init__(self, config: QNCEpigeneticConfig):
        self.config = config

        # Componentes
        self.rna_embedding = RNAEmbedding(
            max_len=config.max_rna_length,
            embedding_dim=config.embedding_dim,
            rna_type=RNAType.mRNA
        )
        self.epi_attention = EpigeneticAttention(
            query_dim=config.embedding_dim,
            key_dim=config.embedding_dim,
            value_dim=config.embedding_dim,
            num_heads=config.num_attention_heads
        )

        # Classificador quântico
        self.classifier_weights = [
            np.eye(config.embedding_dim, dtype=complex) / config.embedding_dim
            for _ in range(config.num_classes)
        ]

        # Campo Φ_C para regularização
        self.phi_c_field = np.eye(config.embedding_dim, dtype=complex) / config.embedding_dim

        # Operadores epigenéticos
        self.methylation_op = MethylationOperator()

        # Otimizador
        self.manifold = FisherBuresManifold(config.embedding_dim)
        self.optimizer = NaturalGradientFlow(self.manifold)

        # Histórico
        self.training_history: List[Dict] = []

    def forward(
        self,
        rna_sequence: str,
        epigenetic_marks: List[EpigeneticState],
        baseline_expression: float = 0.5,
    ) -> Dict:
        """
        Forward pass para predição de expressão gênica.

        Args:
            rna_sequence: Sequência de RNA (mRNA)
            epigenetic_marks: Lista de marcas epigenéticas na região
            baseline_expression: Nível basal de expressão

        Returns:
            Dict com predições e métricas
        """
        # 1. Embedding de RNA
        rho_sequence = self.rna_embedding.encode_sequence(rna_sequence)

        # 2. Calcular acessibilidade epigenética para cada posição
        epi_accessibility = self._compute_epigenetic_accessibility(
            epigenetic_marks, len(rho_sequence)
        )

        # 3. Pooling via atenção epigenética
        query_rho = self.rna_embedding.pool_to_single(rho_sequence)
        context_rho = self.epi_attention.compute_epigenetic_attention(
            query_rho, rho_sequence, rho_sequence, epi_accessibility
        )

        # 4. Aplicar operador de metilação se relevante
        if any(m.mark == EpigeneticMark.DNA_5mC for m in epigenetic_marks):
            context_rho = self.methylation_op.apply(context_rho)

        # 5. Classificação quântica
        logits = []
        for w in self.classifier_weights:
            logit = np.real(np.trace(context_rho @ w))
            logits.append(logit)

        # Converter para probabilidades
        probs = np.exp(logits - np.max(logits))
        probs /= np.sum(probs) + 1e-12

        # 6. Ajustar por campo de histonas se disponível
        if epigenetic_marks:
            histone_field = HistoneModificationField(epigenetic_marks)
            histone_adjustment = histone_field.predict_gene_expression(baseline_expression)
            if len(probs) == 2:
                probs[1] = 0.2 * probs[1] + 0.8 * histone_adjustment
                probs[0] = 1.0 - probs[1]
                probs[0] = 1.0 - probs[1]
            probs /= np.sum(probs) + 1e-12

        return {
            'expression_prob': probs[1] if len(probs) > 1 else probs[0],
            'confidence': np.max(probs),
            'epigenetic_accessibility': np.mean(epi_accessibility),
            'phi_c_coherence': np.real(np.trace(self.phi_c_field)),
            'logits': logits,
        }

    def _compute_epigenetic_accessibility(
        self,
        marks: List[EpigeneticState],
        sequence_length: int,
    ) -> List[float]:
        """Calcula score de acessibilidade para cada posição da sequência."""
        accessibility = np.ones(sequence_length) * 0.5  # Default: 50% acessível

        # Aplicar influência das marcas epigenéticas
        for mark_state in marks:
            pos = mark_state.position
            if 0 <= pos < sequence_length:
                # Marcas de ativação aumentam acessibilidade
                if mark_state.mark in {EpigeneticMark.H3K4me3, EpigeneticMark.H3K27ac}:
                    accessibility[pos] = min(1.0, accessibility[pos] + 0.3 * mark_state.confidence)
                # Marcas de repressão diminuem acessibilidade
                elif mark_state.mark in {EpigeneticMark.H3K27me3, EpigeneticMark.H3K9me3, EpigeneticMark.DNA_5mC}:
                    accessibility[pos] = max(0.0, accessibility[pos] - 0.3 * mark_state.confidence)

        # Suavizar com vizinhança (janela de 50bp)
        window = 50
        smoothed = np.convolve(accessibility, np.ones(window)/window, mode='same')

        return smoothed.tolist()

    def train_step(
        self,
        rna_sequence: str,
        epigenetic_marks: List[EpigeneticState],
        label: int,  # 0 = não-expresso, 1 = expresso
        lr: float = None,
    ) -> Dict:
        """Um passo de treinamento."""
        lr = lr or self.config.learning_rate

        # Forward
        result = self.forward(rna_sequence, epigenetic_marks)

        # Loss: cross-entropy
        pred_prob = result['expression_prob']
        loss = -np.log(pred_prob if label == 1 else 1 - pred_prob + 1e-12)

        # Gradiente w.r.t. logits
        grad_logits = np.array([pred_prob - label, label - pred_prob])

        # Backprop através do classificador (simplificado)
        for i, w in enumerate(self.classifier_weights):
            weight_grad = grad_logits[i] * self.phi_c_field
            try:
                self.classifier_weights[i] = self.optimizer.step(w + np.eye(w.shape[0]) * 1e-4, weight_grad, lr)
            except Exception:
                self.classifier_weights[i] = w - lr * weight_grad
                self.classifier_weights[i] = 0.5 * (self.classifier_weights[i] + self.classifier_weights[i].conj().T)
                self.classifier_weights[i] = self.classifier_weights[i] / np.trace(self.classifier_weights[i])

        # Regularização por Φ_C
        if np.random.random() < 0.1:  # Aplicar ocasionalmente
            phi_grad = self.config.phi_c_coupling * (self.phi_c_field - np.eye(self.config.embedding_dim)/self.config.embedding_dim)
            try:
                self.phi_c_field = self.optimizer.step(self.phi_c_field + np.eye(self.phi_c_field.shape[0]) * 1e-4, phi_grad, lr * 0.5)
            except Exception:
                self.phi_c_field = self.phi_c_field - lr * 0.5 * phi_grad
                self.phi_c_field = 0.5 * (self.phi_c_field + self.phi_c_field.conj().T)
                self.phi_c_field = self.phi_c_field / np.trace(self.phi_c_field)

        # Métricas
        metrics = {
            'loss': float(loss),
            'predicted': int(np.argmax([1-pred_prob, pred_prob])),
            'confidence': result['confidence'],
            'epi_accessibility': result['epigenetic_accessibility'],
        }

        self.training_history.append(metrics)
        return metrics

    def predict_expression(
        self,
        rna_sequence: str,
        epigenetic_marks: List[EpigeneticState],
    ) -> Tuple[int, float]:
        """Prediz classe de expressão e confiança."""
        result = self.forward(rna_sequence, epigenetic_marks)
        predicted_class = 1 if result['expression_prob'] > 0.5 else 0
        return predicted_class, result['confidence']
