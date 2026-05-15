#!/usr/bin/env python3
"""
Substrato 9041 — Otimizador de Ângulos Críticos via Quantum Neural Coding (QNC)
Utiliza uma rede neural treinada com propriedades de materiais para prever
ângulos de torção que maximizam a coerência Φ_C.
"""

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple, Optional
from .materials_2d_db import MoireMaterial, MaterialClass

class QNCCriticalAngleOptimizer:
    """
    Otimizador baseado em QNC para descoberta de ângulos críticos.

    O modelo aprende a correlação entre propriedades fundamentais
    (bandgap, SOC, lattice constant) e os ângulos de torção que
    resultam em máxima coerência Φ_C.
    """

    def __init__(self):
        self.model = MLPRegressor(
            hidden_layer_sizes=(128, 64, 32),
            activation='relu',
            solver='adam',
            max_iter=1000,
            random_state=42
        )
        self.scaler = StandardScaler()
        self._trained = False

        # Features de entrada esperadas
        self.feature_names = [
            "lattice_constant_a",
            "monolayer_bandgap_ev",
            "spin_orbit_coupling_ev",
            "valley_coherence_time_ps",
            "spin_coherence_time_ps",
        ]

    def prepare_training_data(self, catalog: Dict[str, MoireMaterial]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepara dados de treinamento a partir do catálogo de materiais.

        Cada material contribui com seu ângulo crítico primário (mais relevante)
        como label de treinamento.

        Returns:
            X: features normalizadas
            y: ângulo crítico (em graus)
        """
        X, y = [], []

        for key, mat in catalog.items():
            # Usar o primeiro ângulo crítico como label principal
            if mat.critical_angles:
                features = [
                    mat.lattice_constant_a,
                    mat.monolayer_bandgap_ev,
                    mat.spin_orbit_coupling_ev,
                    mat.valley_coherence_time_ps,
                    mat.spin_coherence_time_ps,
                ]
                X.append(features)
                y.append(mat.critical_angles[0])  # Ângulo crítico primário

        X_scaled = self.scaler.fit_transform(np.array(X))
        return X_scaled, np.array(y)

    def train(self, catalog: Dict[str, MoireMaterial]) -> None:
        """
        Treina o modelo QNC com o catálogo de materiais disponível.
        """
        X, y = self.prepare_training_data(catalog)
        if len(X) < 5:
            print("⚠️  Dados insuficientes para treinamento QNC — mínimo 5 materiais necessários.")
            return

        self.model.fit(X, y)
        self._trained = True
        print(f"✅ QNC Critical Angle Optimizer treinado com {len(X)} materiais.")

    def predict_optimal_angle(
        self,
        material: MoireMaterial,
        temperature_k: float = 4.2,
    ) -> float:
        """
        Prediz o ângulo de torção ótimo para um novo material.

        Args:
            material: Material a ser analisado
            temperature_k: Temperatura de operação

        Returns:
            Ângulo ótimo previsto em graus
        """
        if not self._trained:
            # Fallback: retornar o ângulo crítico já conhecido ou uma heurística
            return material.critical_angles[0] if material.critical_angles else 0.0

        features = np.array([[
            material.lattice_constant_a,
            material.monolayer_bandgap_ev,
            material.spin_orbit_coupling_ev,
            material.valley_coherence_time_ps,
            material.spin_coherence_time_ps,
        ]])

        features_scaled = self.scaler.transform(features)
        predicted_angle = self.model.predict(features_scaled)[0]

        # Ajustar pela temperatura
        # (Modelo treinado para baixa temperatura; aplicar correção se necessário)
        if temperature_k > 4.2:
            # Pequena correção empírica: ângulo ótimo tende a variar com T
            correction = 0.01 * (temperature_k - 4.2)
            predicted_angle += correction

        return max(0.0, float(predicted_angle))

    def optimize_via_gradient_ascent(
        self,
        material: MoireMaterial,
        initial_guess: float = 1.0,
        learning_rate: float = 0.05,
        steps: int = 50,
        temperature_k: float = 4.2,
    ) -> Tuple[float, float]:
        """
        Otimiza o ângulo de torção via gradiente ascendente sobre Φ_C.

        Utiliza uma aproximação numérica do gradiente da função Φ_C(θ)
        para encontrar o pico de coerência mais próximo.

        Returns:
            (ângulo ótimo, Φ_C máximo alcançado)
        """
        current_angle = initial_guess
        best_phi = material.compute_phi_c_at_angle(current_angle, temperature_k)

        for _ in range(steps):
            # Aproximar gradiente numericamente
            epsilon = 0.01
            phi_plus = material.compute_phi_c_at_angle(current_angle + epsilon, temperature_k)
            phi_minus = material.compute_phi_c_at_angle(current_angle - epsilon, temperature_k)
            gradient = (phi_plus - phi_minus) / (2 * epsilon)

            # Atualizar ângulo na direção do gradiente
            current_angle += learning_rate * gradient

            # Manter no intervalo [0, 90]
            current_angle = max(0.0, min(90.0, current_angle))

            current_phi = material.compute_phi_c_at_angle(current_angle, temperature_k)
            if current_phi > best_phi:
                best_phi = current_phi

        return round(current_angle, 4), round(best_phi, 4)
