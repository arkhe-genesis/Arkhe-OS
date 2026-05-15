#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
federated_privacy.py
Validação de privacidade diferencial em federated learning.
"""

import numpy as np

class DifferentialPrivacyValidator:
    def __init__(self, epsilon=1.0, delta=1e-5):
        self.epsilon = epsilon
        self.delta = delta

    def add_laplace_noise(self, data: np.ndarray, sensitivity: float) -> np.ndarray:
        """Adiciona ruído Laplace para garantir privacidade diferencial."""
        scale = sensitivity / self.epsilon
        noise = np.random.laplace(0, scale, data.shape)
        return data + noise

    def validate_gradient_update(self, gradient: np.ndarray, sensitivity: float) -> bool:
        """
        Valida se o gradiente atualizado respeita as garantias de privacidade
        antes de ser compartilhado no aprendizado federado.
        """
        # Em um cenário real, aqui teríamos a validação formal.
        # Simulamos verificando se as normas do gradiente estão dentro de limites esperados
        norm = np.linalg.norm(gradient)
        if norm > sensitivity * 10: # threshold de simulação
            return False
        return True
