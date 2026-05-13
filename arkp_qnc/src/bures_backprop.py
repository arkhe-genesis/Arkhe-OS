#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bures_backprop.py — Backpropagation completo através de operações quânticas
Implementa regra da cadeia quântica na variedade de Fisher-Bures.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import numpy as np
from scipy.linalg import sqrtm, logm, expm, fractional_matrix_power
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class QuantumGradient:
    """Gradiente quântico na variedade de Fisher-Bures."""
    grad_rho: np.ndarray  # Gradiente w.r.t. operador densidade
    metric_tensor: Optional[np.ndarray] = None  # Tensor métrico (opcional)
    natural_direction: Optional[np.ndarray] = None  # Direção natural (G⁻¹·grad)

class BuresBackpropagator:
    """Backpropagation através de operações quânticas na variedade de Fisher-Bures."""

    @staticmethod
    def fidelity_gradient(rho: np.ndarray, sigma: np.ndarray) -> np.ndarray:
        """
        Calcula gradiente da fidelidade F(ρ,σ) w.r.t. ρ.

        Fórmula: ∂F/∂ρ = ½ (√σ (√σ ρ √σ)^{-½} √σ)
        """
        sqrt_sigma = sqrtm(sigma)
        inner = sqrt_sigma @ rho @ sqrt_sigma
        inner_sqrt_inv = fractional_matrix_power(inner + np.eye(inner.shape[0]) * 1e-12, -0.5)
        grad = 0.5 * sqrt_sigma @ inner_sqrt_inv @ sqrt_sigma
        return (grad + grad.conj().T) / 2  # Garantir Hermitiano

    @staticmethod
    def bures_distance_gradient(rho: np.ndarray, sigma: np.ndarray) -> np.ndarray:
        """Gradiente da distância de Bures w.r.t. ρ."""
        fid_grad = BuresBackpropagator.fidelity_gradient(rho, sigma)
        fid = np.real(np.trace(sqrtm(sqrtm(rho) @ sigma @ sqrtm(rho))))
        # d(d_Bures)/dρ = -1/√(2-2F) · dF/dρ
        denominator = np.sqrt(2 - 2 * fid + 1e-12)
        return -fid_grad / denominator

    @staticmethod
    def quantum_channel_gradient(
        rho: np.ndarray,
        kraus_operators: List[np.ndarray],
        grad_output: np.ndarray,
    ) -> List[np.ndarray]:
        """
        Backprop através de canal quântico: ρ' = Σᵢ Kᵢ ρ Kᵢ†

        Retorna gradientes w.r.t. cada operador de Kraus Kᵢ.
        """
        grads = []
        for K in kraus_operators:
            # ∂L/∂K = grad_output @ ρ @ K†
            grad_K = grad_output @ rho @ K.conj().T
            grads.append(grad_K)
        return grads

    @staticmethod
    def natural_gradient_step(
        rho: np.ndarray,
        grad: np.ndarray,
        lr: float,
        manifold_dim: int,
    ) -> np.ndarray:
        """
        Passo de gradiente natural na variedade de Fisher-Bures.

        Fórmula: ρ_{t+1} = Exp_ρ(-η · G⁻¹(ρ) · ∇L)
        onde G é o tensor métrico de Fisher-Bures.
        """
        # Aproximação: usar métrica Euclidiana como proxy
        # Em produção: calcular tensor métrico exato via derivadas de segunda ordem
        natural_direction = grad  # Placeholder: G⁻¹ ≈ I

        # Exponencial de mapa na variedade (aproximação de primeira ordem)
        rho_updated = rho - lr * natural_direction

        # Projetar para operador densidade válido
        return BuresBackpropagator.project_to_density_matrix(rho_updated)

    @staticmethod
    def project_to_density_matrix(rho: np.ndarray) -> np.ndarray:
        """Projeta matriz arbitrária para operador densidade válido."""
        # 1. Hermitianizar
        rho = (rho + rho.conj().T) / 2

        # 2. Projeção para positivo-semidefinido
        eigvals, eigvecs = np.linalg.eigh(rho)
        eigvals = np.maximum(eigvals, 0)

        # 3. Normalizar traço
        trace = np.sum(eigvals)
        if trace > 1e-10:
            eigvals /= trace

        return eigvecs @ np.diag(eigvals) @ eigvecs.conj().T

    @staticmethod
    def backprop_through_attention(
        query_rho: np.ndarray,
        key_rhos: List[np.ndarray],
        value_rhos: List[np.ndarray],
        grad_output: np.ndarray,
        phi_c_field: np.ndarray,
        phi_c_coupling: float,
    ) -> Tuple[np.ndarray, List[np.ndarray], List[np.ndarray]]:
        """
        Backprop através de atenção quântica com modulação Φ_C.

        Retorna: (grad_query, grad_keys, grad_values)
        """
        # 1. Calcular scores de atenção (forward)
        scores = []
        for key_rho in key_rhos:
            fid = np.real(np.trace(sqrtm(sqrtm(query_rho) @ key_rho @ sqrtm(query_rho))))
            bures_to_phi = np.sqrt(2 - 2 * np.real(np.trace(
                sqrtm(sqrtm(key_rho) @ phi_c_field @ sqrtm(key_rho))
            )))
            phi_mod = 1.0 / (1.0 + phi_c_coupling * bures_to_phi)
            scores.append(fid * phi_mod)

        # Softmax
        exp_scores = np.exp(np.array(scores) - np.max(scores))
        att_weights = exp_scores / (np.sum(exp_scores) + 1e-12)

        # 2. Gradiente w.r.t. values (mais direto)
        grad_values = [att_weights[i] * grad_output for i in range(len(value_rhos))]

        # 3. Gradiente w.r.t. keys (via fidelidade e modulação Φ_C)
        grad_keys = []
        for i, key_rho in enumerate(key_rhos):
            # Gradiente da fidelidade
            fid_grad = BuresBackpropagator.fidelity_gradient(query_rho, key_rho)
            # Gradiente da modulação Φ_C
            bures_to_phi = np.sqrt(2 - 2 * np.real(np.trace(
                sqrtm(sqrtm(key_rho) @ phi_c_field @ sqrtm(key_rho))
            )))
            phi_mod_grad = -phi_c_coupling / (1.0 + phi_c_coupling * bures_to_phi)**2
            # Combinar
            grad_key = (att_weights[i] * grad_output) * (
                phi_mod * fid_grad +
                np.real(np.trace(sqrtm(sqrtm(query_rho) @ key_rho @ sqrtm(query_rho)))) * phi_mod_grad *
                BuresBackpropagator.bures_distance_gradient(key_rho, phi_c_field)
            )
            grad_keys.append(grad_key)

        # 4. Gradiente w.r.t. query (similar a keys)
        grad_query = np.zeros_like(query_rho)
        for i, key_rho in enumerate(key_rhos):
            fid_grad = BuresBackpropagator.fidelity_gradient(key_rho, query_rho)  # Simétrico
            grad_query += att_weights[i] * np.real(np.trace(grad_output @ value_rhos[i])) * fid_grad

        return grad_query, grad_keys, grad_values
