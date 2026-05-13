#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phi_c_attention.py — Substrato 6176: Atenção Quântica com Modulação Φ_C
Mecanismo de atenção onde scores são ponderados pela coerência local do campo Φ_C.
"""

import numpy as np
from scipy.linalg import sqrtm
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from .quantum_layers import fidelity, bures_distance

@dataclass
class PhiCAttentionConfig:
    query_dim: int
    key_dim: int
    value_dim: int
    num_heads: int = 1
    phi_c_coupling: float = 0.1  # λ na equação E[ψ] = E_folding + λ·C(ψ)

class PhiCAttention:
    """
    Atenção quântica com modulação por campo Φ_C.

    Equação:
      score(q, k) = fidelity(ρ_q, ρ_k) × φ_mod(ρ_k, Φ_C_field)
      onde φ_mod = 1 / (1 + d_Bures(ρ_k, Φ_C_coherent))
    """

    def __init__(self, config: PhiCAttentionConfig):
        self.config = config
        self.num_heads = config.num_heads

        # Projetores para query/key/value (como operadores)
        self.W_q = [self._init_projector(config.query_dim) for _ in range(config.num_heads)]
        self.W_k = [self._init_projector(config.key_dim) for _ in range(config.num_heads)]
        self.W_v = [self._init_projector(config.value_dim) for _ in range(config.num_heads)]

        # Campo Φ_C de referência (estado coerente ideal)
        self.phi_c_coherent = np.eye(config.key_dim) / config.key_dim

        self._cache: Dict = {}

    def _init_projector(self, dim: int) -> np.ndarray:
        """Inicializa projetor como operador densidade."""
        # Estado puro aleatório como ponto de partida
        psi = np.random.randn(dim) + 1j * np.random.randn(dim)
        psi /= np.linalg.norm(psi)
        return np.outer(psi, psi.conj())

    def compute_attention_scores(
        self,
        query_rhos: List[np.ndarray],
        key_rhos: List[np.ndarray],
        phi_c_field: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Calcula scores de atenção com modulação Φ_C.

        Args:
            query_rhos: Lista de operadores densidade de query
            key_rhos: Lista de operadores densidade de key
            phi_c_field: Campo Φ_C local (opcional, usa coerente padrão se None)

        Returns:
            Matriz de atenção normalizada (num_queries × num_keys)
        """
        phi_c_ref = phi_c_field if phi_c_field is not None else self.phi_c_coherent
        scores = np.zeros((len(query_rhos), len(key_rhos)))

        for i, q_rho in enumerate(query_rhos):
            for j, k_rho in enumerate(key_rhos):
                # Fidelidade quântica entre query e key
                fid = fidelity(q_rho, k_rho)

                # Modulação por coerência Φ_C
                if phi_c_field is not None:
                    bures_to_coherent = bures_distance(k_rho, phi_c_ref)
                    phi_mod = 1.0 / (1.0 + self.config.phi_c_coupling * bures_to_coherent)
                else:
                    phi_mod = 1.0

                scores[i, j] = fid * phi_mod

        # Normalização softmax
        exp_scores = np.exp(scores - np.max(scores, axis=1, keepdims=True))
        return exp_scores / (np.sum(exp_scores, axis=1, keepdims=True) + 1e-12)

    def forward(
        self,
        query_rhos: List[np.ndarray],
        key_rhos: List[np.ndarray],
        value_rhos: List[np.ndarray],
        phi_c_field: Optional[np.ndarray] = None
    ) -> List[np.ndarray]:
        """
        Forward pass completo de atenção.

        Returns:
            Lista de operadores densidade de saída (um por query)
        """
        # Calcular scores de atenção
        att_weights = self.compute_attention_scores(query_rhos, key_rhos, phi_c_field)

        # Aplicar atenção aos values
        output_rhos = []
        for i in range(len(query_rhos)):
            weighted_sum = np.zeros_like(value_rhos[0])
            for j, v_rho in enumerate(value_rhos):
                weighted_sum += att_weights[i, j] * v_rho

            # Normalizar
            trace = np.trace(weighted_sum)
            if trace > 1e-10:
                weighted_sum /= trace

            output_rhos.append(weighted_sum)

        self._cache['att_weights'] = att_weights
        return output_rhos

    def get_context_vector(self, query_rho: np.ndarray,
                          key_value_pairs: List[Tuple[np.ndarray, np.ndarray]],
                          phi_c_field: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Extrai vetor de contexto para uma única query.
        Conveniência para uso em classificação.
        """
        key_rhos = [kv[0] for kv in key_value_pairs]
        value_rhos = [kv[1] for kv in key_value_pairs]

        outputs = self.forward([query_rho], key_rhos, value_rhos, phi_c_field)
        return outputs[0] if outputs else np.zeros_like(key_rhos[0])
