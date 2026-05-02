#!/usr/bin/env python3
"""
torsional_coherence.py
Implementa a métrica de coerência torsional $\tau$ para estruturas OR de n camadas.
"""
import numpy as np

class TorsionalCoherenceEvaluator:
    """
    Avalia a coerência torsional da estrutura.
    """

    def __init__(self, layers=12, segments=16):
        self.layers = layers
        self.segments = segments
        self.total_nodes = layers * segments

    def evaluate_torsion(self, state_matrix: np.ndarray) -> np.ndarray:
        """
        Calcula a métrica de coerência torsional para cada camada.

        Args:
            state_matrix: matriz de estados (nodes x features) ou apenas vetor de fases.

        Returns:
            Vetor com a métrica tau para cada uma das 12 camadas.
        """
        if len(state_matrix.shape) == 1:
            phases = state_matrix
        else:
            # Assumindo que a fase é a primeira feature ou que state_matrix são fases
            phases = state_matrix.mean(axis=1) if len(state_matrix.shape) > 1 else state_matrix

        tau_per_layer = np.zeros(self.layers)

        for l in range(self.layers):
            start_idx = l * self.segments
            end_idx = (l + 1) * self.segments
            layer_phases = phases[start_idx:end_idx]

            # Parametro de ordem torsional (baseado na variancia das diferencas de fase na camada)
            # Uma camada com fases altamente alinhadas tem coerencia proxima de 1.0
            if len(layer_phases) > 0:
                # Usa order parameter global na camada como proxy para coerencia torsional
                coherence = np.abs(np.mean(np.exp(1j * layer_phases)))
                tau_per_layer[l] = coherence

        return tau_per_layer
