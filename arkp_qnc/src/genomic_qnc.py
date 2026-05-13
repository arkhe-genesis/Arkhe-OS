#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
genomic_qnc.py — Substrato 6176: Rede Quântica para Inteligência Genômica
Arquitetura completa que processa sequências de DNA/proteína via QNC.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import hashlib
import json

from .quantum_layers import QuantumDenseLayer, QuantumDenseConfig, fidelity
from .phi_c_attention import PhiCAttention, PhiCAttentionConfig
from arkp_sigha.sigha_core import FisherBuresManifold, NaturalGradientFlow

@dataclass
class GenomicQNCConfig:
    vocab_size: int = 4  # A, T, G, C
    max_sequence_length: int = 128
    embedding_dim: int = 8
    hidden_dim: int = 16
    num_classes: int = 2  # e.g., resistant vs sensitive
    num_attention_heads: int = 2
    phi_c_coupling: float = 0.1
    learning_rate: float = 0.05

class GenomicEmbedding:
    """
    Embedding quântico para sequências genômicas.
    Cada nucleotídeo → estado puro em espaço de Hilbert 4D.
    Sequência completa → produto tensorial com encoding posicional.
    """

    NUCLEOTIDE_STATES = {
        'A': np.array([1, 0, 0, 0], dtype=complex),
        'T': np.array([0, 1, 0, 0], dtype=complex),
        'G': np.array([0, 0, 1, 0], dtype=complex),
        'C': np.array([0, 0, 0, 1], dtype=complex),
    }

    def __init__(self, max_len: int = 128, embedding_dim: int = 8):
        self.max_len = max_len
        self.embedding_dim = embedding_dim
        # Encoding posicional como fatores de fase
        self.pos_phases = np.exp(2j * np.pi * np.arange(max_len)[:, None] / max_len)

    def encode_sequence(self, sequence: str) -> List[np.ndarray]:
        """
        Codifica sequência de DNA em lista de operadores densidade.
        Retorna: List[np.ndarray] de shape (max_len, dim, dim)
        """
        rho_list = []

        for i, nuc in enumerate(sequence[:self.max_len]):
            # Estado puro do nucleotídeo
            psi_base = self.NUCLEOTIDE_STATES.get(nuc.upper(),
                    np.array([0.25, 0.25, 0.25, 0.25]))  # Default: maximally mixed

            # Ajustar para embedding_dim (padding com zeros)
            psi = np.zeros(self.embedding_dim, dtype=complex)
            psi[:min(len(psi_base), self.embedding_dim)] = psi_base[:self.embedding_dim]
            if np.linalg.norm(psi) > 0:
                psi /= np.linalg.norm(psi)

            rho = np.outer(psi, psi.conj())

            # Aplicar encoding posicional (simplificado: fase global)
            phase = self.pos_phases[i % self.max_len, 0]
            rho = rho * phase.real  # Em implementação completa: conjugação unitária

            rho_list.append(rho)

        # Padding com estados maximally mixed
        while len(rho_list) < self.max_len:
            rho_list.append(np.eye(self.embedding_dim) / self.embedding_dim)

        return rho_list

    def pool_to_single(self, rho_list: List[np.ndarray]) -> np.ndarray:
        """Pool de lista de operadores para representação única."""
        # Média ponderada (pode ser substituída por atenção)
        return np.mean(rho_list, axis=0)

class GenomicQNC:
    """
    Rede Neural Quântica para análise genômica.

    Arquitetura:
      Embedding → QuantumConv1D → Φ_C-Attention → QuantumDense → Classifier
    """

    def __init__(self, config: GenomicQNCConfig):
        self.config = config

        # Componentes
        self.embedding = GenomicEmbedding(config.max_sequence_length, config.hidden_dim)

        # Camada de atenção com modulação Φ_C
        att_config = PhiCAttentionConfig(
            query_dim=config.hidden_dim,
            key_dim=config.hidden_dim,
            value_dim=config.hidden_dim,
            num_heads=config.num_attention_heads,
            phi_c_coupling=config.phi_c_coupling
        )
        self.attention = PhiCAttention(att_config)

        # Camadas densas quânticas para classificação
        self.classifier = QuantumDenseLayer(
            QuantumDenseConfig(
                input_dim=config.hidden_dim,
                output_dim=config.num_classes,
                activation='quantum_softmax'
            )
        )

        # Otimizador SIGHA
        self.manifold = FisherBuresManifold(config.hidden_dim)
        self.optimizer = NaturalGradientFlow(self.manifold)

        # Campo Φ_C treinável (inicializado como estado coerente)
        self.phi_c_field = np.eye(config.hidden_dim, dtype=complex) / config.hidden_dim

        # Métricas de treinamento
        self.training_history: List[Dict] = []

    def forward(self, sequence: str) -> np.ndarray:
        """
        Forward pass completo.

        Args:
            sequence: String de DNA (A/T/G/C)

        Returns:
            Logits de classificação (array de shape [num_classes])
        """
        # 1. Embedding genômico
        rho_sequence = self.embedding.encode_sequence(sequence)

        # 2. Pool para representação única (pode ser substituído por convolução)
        query_rho = self.embedding.pool_to_single(rho_sequence)

        # 3. Atenção Φ_C-gated (self-attention sobre posições)
        context_rho = self.attention.get_context_vector(
            query_rho,
            [(rho, rho) for rho in rho_sequence],  # Key=Value para self-attention
            self.phi_c_field
        )

        # 4. Classificação
        logits_rho = self.classifier.forward(context_rho)

        # Extrair logits como valores reais (diagonal do operador)
        logits = np.real(np.diag(logits_rho))

        return logits

    def train_step(self, sequence: str, label: int, lr: float = None) -> Dict:
        """
        Um passo de treinamento com backpropagation quântico.

        Args:
            sequence: Sequência de DNA
            label: Label inteiro (0 ou 1 para classificação binária)
            lr: Taxa de aprendizado (usa config.default se None)

        Returns:
            Dict com métricas do passo
        """
        lr = lr or self.config.learning_rate

        # Forward
        logits = self.forward(sequence)

        # Loss: cross-entropy quântica (simplificada para classical logits)
        probs = np.exp(logits - np.max(logits))
        probs /= np.sum(probs) + 1e-12
        loss = -np.log(probs[label] + 1e-12)

        # Gradiente w.r.t. logits
        grad_logits = probs.copy()
        grad_logits[label] -= 1.0

        # Backprop através do classifier (simplificado)
        # Em implementação completa: backprop através de operações quânticas
        grad_context = grad_logits[0] * np.eye(self.config.hidden_dim) / self.config.hidden_dim

        # Atualizar classifier com gradiente natural
        self.classifier.backward(grad_context, lr=lr)

        # Atualizar campo Φ_C para maximizar coerência em exemplos corretos
        if probs[label] > 0.5:  # Apenas se predição estiver correta
            self._update_phi_c_field(sequence, label, lr * 0.1)

        # Registrar métricas
        metrics = {
            'loss': float(loss),
            'predicted_class': int(np.argmax(probs)),
            'confidence': float(np.max(probs)),
            'phi_c_coherence': float(fidelity(self.phi_c_field, np.eye(self.config.hidden_dim) / self.config.hidden_dim)),
        }

        self.training_history.append(metrics)
        return metrics

    def _update_phi_c_field(self, sequence: str, label: int, lr: float):
        """Atualiza campo Φ_C para reforçar coerência em padrões corretos."""
        # Heurística: mover Φ_C em direção aos estados que levaram à predição correta
        rho_sequence = self.embedding.encode_sequence(sequence)
        avg_rho = self.embedding.pool_to_single(rho_sequence)

        # Gradiente natural em direção a avg_rho
        grad = avg_rho - self.phi_c_field
        self.phi_c_field = self.optimizer.step(self.phi_c_field, grad, lr=lr)

        # Projetar para operador densidade válido
        self.phi_c_field = self.classifier._project_to_density_matrix(self.phi_c_field)

    def predict(self, sequence: str) -> Tuple[int, float]:
        """Prediz classe e confiança para uma sequência."""
        logits = self.forward(sequence)
        probs = np.exp(logits - np.max(logits))
        probs /= np.sum(probs) + 1e-12

        predicted_class = int(np.argmax(probs))
        confidence = float(np.max(probs))

        return predicted_class, confidence

    def save_checkpoint(self, path: str):
        """Salva checkpoint do modelo."""
        checkpoint = {
            'config': self.config.__dict__,
            'classifier_weights': self.classifier.get_weights_serializable(),
            'phi_c_field': self.phi_c_field.tolist(),
            'training_history': self.training_history,
            'integrity_proof': hashlib.sha3_256(
                json.dumps(self.config.__dict__, sort_keys=True).encode()
            ).hexdigest()[:16],
        }

        import pickle
        with open(path, 'wb') as f:
            pickle.dump(checkpoint, f)

    @classmethod
    def load_checkpoint(cls, path: str) -> 'GenomicQNC':
        """Carrega modelo de checkpoint."""
        import pickle
        with open(path, 'rb') as f:
            checkpoint = pickle.load(f)

        config = GenomicQNCConfig(**checkpoint['config'])
        model = cls(config)

        # Restaurar pesos (implementação simplificada)
        model.phi_c_field = np.array(checkpoint['phi_c_field'])
        model.training_history = checkpoint['training_history']

        return model
