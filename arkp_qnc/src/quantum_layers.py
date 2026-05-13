#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quantum_layers.py — Substrato 6176: Camadas Neurais Quânticas
Implementa operações neurais onde pesos são operadores densidade
e ativações são transformações completamente positivas.
"""

import numpy as np
from scipy.linalg import sqrtm, expm, logm
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Union
import hashlib

# Import SIGHA core for natural gradient
from arkp_sigha.sigha_core import FisherBuresManifold, NaturalGradientFlow

# ============================================================================
# UTILITÁRIOS QUÂNTICOS
# ============================================================================

def fidelity(rho1: np.ndarray, rho2: np.ndarray) -> float:
    """Calcula fidelidade de Uhlmann entre dois estados quânticos."""
    sqrt_rho1 = sqrtm(rho1)
    fid = np.real(np.trace(sqrtm(sqrt_rho1 @ rho2 @ sqrt_rho1)))
    return max(0.0, min(1.0, fid))

def bures_distance(rho1: np.ndarray, rho2: np.ndarray) -> float:
    """Distância de Bures entre estados quânticos."""
    return np.sqrt(2.0 - 2.0 * fidelity(rho1, rho2))

def partial_trace(rho: np.ndarray, subsystem_dims: List[int], trace_out: List[int]) -> np.ndarray:
    """Traço parcial sobre subsistemas especificados."""
    # Implementação simplificada para 2 subsistemas
    if len(subsystem_dims) == 2 and trace_out == [1]:
        d1, d2 = subsystem_dims
        rho_reshaped = rho.reshape(d1, d2, d1, d2)
        return np.trace(rho_reshaped, axis1=1, axis2=3)
    return rho  # Placeholder

# ============================================================================
# CAMADA QUÂNTICA DENSE
# ============================================================================

@dataclass
class QuantumDenseConfig:
    input_dim: int
    output_dim: int
    activation: str = 'quantum_softmax'
    use_bias: bool = True
    weight_init: str = 'maximally_mixed'

class QuantumDenseLayer:
    """
    Camada densa quântica: pesos são operadores densidade.

    Operação: ρ_out = Σ_i W_i ρ_in W_i† + b (se bias habilitado)
    onde W_i são operadores de Kraus aprendíveis.
    """

    def __init__(self, config: QuantumDenseConfig):
        self.config = config
        self.input_dim = config.input_dim
        self.output_dim = config.output_dim

        # Inicializar pesos como operadores densidade
        if config.weight_init == 'maximally_mixed':
            self.weights = [np.eye(config.input_dim) / config.input_dim
                          for _ in range(config.output_dim)]
        elif config.weight_init == 'random_pure':
            self.weights = [self._random_pure_state(config.input_dim)
                          for _ in range(config.output_dim)]
        else:
            raise ValueError(f"Unknown weight_init: {config.weight_init}")

        # Bias como operador densidade adicional
        self.bias = np.eye(config.output_dim) / config.output_dim if config.use_bias else None

        # Manifold para otimização natural
        self.manifold = FisherBuresManifold(config.input_dim)
        self.flow = NaturalGradientFlow(self.manifold)

        # Cache para backprop
        self._cache: Dict = {}

    def _random_pure_state(self, dim: int) -> np.ndarray:
        """Gera estado puro aleatório em dimensão especificada."""
        psi = np.random.randn(dim) + 1j * np.random.randn(dim)
        psi /= np.linalg.norm(psi)
        return np.outer(psi, psi.conj())

    def forward(self, rho_in: np.ndarray) -> np.ndarray:
        """
        Forward pass: aplica transformação quântica.
        rho_in: operador densidade de entrada (input_dim × input_dim)
        Retorna: operador densidade de saída (output_dim × output_dim)
        """
        # Aplicar operadores de Kraus
        rho_out = np.zeros((self.output_dim, self.output_dim), dtype=complex)

        for i, W in enumerate(self.weights):
            # Projetar para espaço de saída (simplificado: padding/truncation)
            W_op = np.zeros((self.output_dim, self.input_dim), dtype=complex)
            min_dim = min(self.input_dim, self.output_dim)
            W_op[:min_dim, :min_dim] = W[:min_dim, :min_dim]

            rho_out += W_op @ rho_in @ W_op.conj().T

        # Adicionar bias se habilitado
        if self.bias is not None:
            rho_out = 0.9 * rho_out + 0.1 * self.bias

        # Normalizar para traço unitário
        trace = np.trace(rho_out)
        if trace > 1e-10:
            rho_out /= trace

        # Cache para backprop
        self._cache['rho_in'] = rho_in
        self._cache['rho_out'] = rho_out

        return rho_out

    def backward(self, grad_rho_out: np.ndarray, lr: float = 0.01) -> List[np.ndarray]:
        """
        Backward pass via gradiente natural na variedade de Fisher-Bures.
        grad_rho_out: gradiente w.r.t. saída
        lr: taxa de aprendizado
        Retorna: gradientes w.r.t. pesos
        """
        rho_in = self._cache.get('rho_in')
        if rho_in is None:
            raise RuntimeError("forward() must be called before backward()")

        weight_grads = []

        grad_out_aligned = np.zeros((self.input_dim, self.input_dim), dtype=complex)
        min_dim = min(self.input_dim, self.output_dim)
        grad_out_aligned[:min_dim, :min_dim] = grad_rho_out[:min_dim, :min_dim]

        for i, W in enumerate(self.weights):
            # Gradiente simplificado: ∂L/∂W ≈ grad_out @ ρ_in @ W†
            grad_W = grad_out_aligned @ rho_in @ W.conj().T

            # Passo de gradiente natural
            W_updated = self.flow.step(W, grad_W, lr=lr)

            # Projetar para operador densidade válido (Hermitiano, positivo, traço 1)
            W_updated = self._project_to_density_matrix(W_updated)

            weight_grads.append(W_updated - W)
            self.weights[i] = W_updated

        return weight_grads

    def _project_to_density_matrix(self, rho: np.ndarray) -> np.ndarray:
        """Projeta matriz arbitrária para operador densidade válido."""
        # 1. Tornar Hermitiano
        rho = (rho + rho.conj().T) / 2

        # 2. Projetar para positivo-semidefinido (eigenvalue clipping)
        eigvals, eigvecs = np.linalg.eigh(rho)
        eigvals = np.maximum(eigvals, 0)

        # 3. Normalizar traço
        trace = np.sum(eigvals)
        if trace > 1e-10:
            eigvals /= trace
        else:
            # Em caso de degeneração, usar estado maximally mixed
            eigvals = np.ones_like(eigvals) / rho.shape[0]
            eigvecs = np.eye(rho.shape[0])

        return eigvecs @ np.diag(eigvals) @ eigvecs.conj().T

    def get_weights_serializable(self) -> Dict:
        """Retorna pesos em formato serializável para checkpoint."""
        return {
            'weights': [w.tolist() for w in self.weights],
            'bias': self.bias.tolist() if self.bias is not None else None,
            'config': self.config.__dict__,
        }
