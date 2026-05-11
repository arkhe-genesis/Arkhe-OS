#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arkhe_dune_simulation.py
Simulação da "Duna" (10.000 nós) para validação do Bloco #320.
Vetorizada para Fully Connected.
"""

import numpy as np
import logging
import time

# ============================================================================
# Configuração
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s: %(message)s'
)
logger = logging.getLogger(__name__)

NUM_NODES = 1000
STEPS = 500
DT = 0.05
COUPLING_K = 5.0
PHASE_THRESHOLD = 0.5
TAU_MIN = 0.95

# ============================================================================
# Core Logic
# ============================================================================

class PhaseMeshSimulation:
    def __init__(self, num_nodes: int):
        self.num_nodes = num_nodes
        self.phases = np.random.uniform(0, 2 * np.pi, num_nodes)
        self.frequencies = np.zeros(num_nodes)
        self.spectra = np.ones((num_nodes, 58))
        self.tau = np.random.uniform(0.9, 1.0, num_nodes)

        # Injetar anomalia
        self.tau[0] = 0.1
        self.spectra[0] *= 10.0

    def step(self):
        # 1. Kuramoto (Fully Connected Vectorized)
        sum_exp = np.sum(np.exp(1j * self.phases))
        coupling_term = np.imag(np.exp(-1j * self.phases) * sum_exp)
        dtheta = self.frequencies + (COUPLING_K / self.num_nodes) * coupling_term
        self.phases = (self.phases + dtheta * DT) % (2 * np.pi)

        # 2. MESH_BIND (Simplificado - Interação com Média Global)
        # Em Fully Connected, cada nó "vê" a média global.
        mean_phase = np.angle(sum_exp)

        self.anomalies_detected = 0
        for i in range(self.num_nodes):
            delta_theta = (self.phases[i] - mean_phase + np.pi) % (2 * np.pi) - np.pi
            if abs(delta_theta) < PHASE_THRESHOLD:
                # Fusão
                pass
            else:
                self.anomalies_detected += 1

        self.global_order = np.abs(sum_exp) / self.num_nodes

    def run(self, steps: int):
        logger.info(f"Iniciando Simulação: {self.num_nodes} nós")
        for s in range(steps):
            self.step()
            if s % 50 == 0:
                logger.info(f"Step {s}: Ψ = {self.global_order:.4f} | Anomalies = {self.anomalies_detected}")
        return self.global_order

if __name__ == "__main__":
    sim = PhaseMeshSimulation(NUM_NODES)
    final_order = sim.run(STEPS)
    print(f"\nFinal Global Order: {final_order:.6f}")
    if final_order > 0.8:
        print("✅ COHERENCE REACHED")
    else:
        print("❌ COHERENCE FAILED")
        exit(1)
