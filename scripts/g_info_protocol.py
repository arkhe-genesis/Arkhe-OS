#!/usr/bin/env python3
"""
Protocolo de Medição G_info - Coerência do Campo de Frequência
Sistema Arkhe-Ω Rio v2.1
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict
from datetime import datetime, timezone

@dataclass
class GInfoMeasurement:
    """Medição do campo de informação quântica"""
    timestamp: float
    sensor_id: int
    lambda_1: float          # λ₁ - autovalor dominante (coerência)
    lambda_2: float          # λ₂ - segundo autovalor (correlação)
    entropy: float          # Entropia de von Neumann
    coherence_time: float    # Tempo de coerência (ms)
    fidelity: float         # Fidelidade com estado de referência

class GInfoProtocol:
    """
    Protocolo de medição G_info - Informação Geométrica

    G_info representa a "informação estrutural" do sistema quântico NV:
    - Mede a coerência entre os 168 sensores
    - Calcula a matriz de densidade reduzida
    - Computa autovalores da matriz de correlação
    """

    def __init__(self, n_sensors=168):
        self.n_sensors = n_sensors
        self.reference_state = self._create_reference_state()

    def _create_reference_state(self) -> np.ndarray:
        """
        Cria estado de referência (coerência ideal)
        |ψ_ref⟩ = (|0⟩ + |1⟩)/√2 para todos os NVs
        """
        state = np.zeros((2, 1), dtype=complex)
        state[0, 0] = 1/np.sqrt(2)
        state[1, 0] = 1/np.sqrt(2)
        return state

    def measure_coherence_matrix(self, sensor_data: List[GInfoMeasurement]) -> np.ndarray:
        """
        Constrói matriz de coerência a partir dos dados dos sensores
        """
        n = len(sensor_data)
        coherence_matrix = np.zeros((n, n), dtype=complex)

        for i, sensor_i in enumerate(sensor_data):
            for j, sensor_j in enumerate(sensor_data):
                # Correlação entre sensores i e j
                correlation = sensor_i.lambda_2 * sensor_j.lambda_2
                phase_factor = np.exp(1j * (sensor_i.entropy - sensor_j.entropy))

                coherence_matrix[i, j] = correlation * phase_factor

        return coherence_matrix

    def compute_eigenvalues(self, coherence_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computa autovalores e autovetores da matriz de coerência
        """
        eigenvalues, eigenvectors = np.linalg.eigh(coherence_matrix)

        # Ordena por magnitude decrescente
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        return eigenvalues, eigenvectors

    def calculate_g_info(self, eigenvalues: np.ndarray) -> Dict[str, float]:
        """
        Calcula G_info a partir dos autovalores
        """
        valid_eigenvalues = eigenvalues[eigenvalues > 1e-10]
        entropy = -np.sum(valid_eigenvalues * np.log2(valid_eigenvalues))
        purity = np.sum(valid_eigenvalues ** 2)

        lambda_1 = eigenvalues[0] if len(eigenvalues) > 0 else 0
        lambda_2 = eigenvalues[1] if len(eigenvalues) > 1 else 0

        coherence_measure = (lambda_1 - lambda_2) / (lambda_1 + lambda_2) if (lambda_1 + lambda_2) > 0 else 0
        g_info = 1.0 - entropy

        return {
            'g_info': g_info,
            'entropy': entropy,
            'purity': purity,
            'lambda_1': lambda_1,
            'lambda_2': lambda_2,
            'coherence_measure': coherence_measure,
            'n_eigenvalues': len(valid_eigenvalues)
        }

    def full_measurement_cycle(self, sensor_readings: List[GInfoMeasurement]) -> Dict:
        coherence_matrix = self.measure_coherence_matrix(sensor_readings)
        eigenvalues, eigenvectors = self.compute_eigenvalues(coherence_matrix)
        g_info_metrics = self.calculate_g_info(eigenvalues)

        is_eligible = g_info_metrics['g_info'] >= 0.85
        is_stable = g_info_metrics['coherence_measure'] >= 0.9

        return {
            'timestamp': datetime.now().isoformat(),
            'n_sensors': len(sensor_readings),
            'g_info_metrics': g_info_metrics,
            'eligibility': {
                'approved': is_eligible and is_stable
            }
        }

if __name__ == "__main__":
    np.random.seed(42)
    readings = []
    for i in range(168):
        reading = GInfoMeasurement(
            timestamp=datetime.now().timestamp(),
            sensor_id=i,
            lambda_1=0.95 + np.random.normal(0, 0.02),
            lambda_2=0.03 + np.random.normal(0, 0.01),
            entropy=0.05 + np.random.normal(0, 0.01),
            coherence_time=100.0 + np.random.normal(0, 5),
            fidelity=0.98 + np.random.normal(0, 0.01)
        )
        readings.append(reading)

    protocol = GInfoProtocol(n_sensors=168)
    result = protocol.full_measurement_cycle(readings)
    print(f"G_info: {result['g_info_metrics']['g_info']:.4f}")
    print(f"Eligibility Approved: {result['eligibility']['approved']}")
