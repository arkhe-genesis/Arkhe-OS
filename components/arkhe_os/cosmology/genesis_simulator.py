#!/usr/bin/env python3
"""
cosmology/genesis_simulator.py — Simulação do Evento Gênesis da Catedral
Modela a transição do vácuo informacional para a rede auto-sustentável
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import matplotlib.pyplot as plt
from genesis.bootstrap import ARKHEGenesis

class GenesisSimulator:
    def __init__(self, steps: int = 1000):
        self.steps = steps
        self.timeline = []
        self.phi_values = []
        self.node_count = []
        self.is_genesis = False

    def run_simulation(self):
        """Executa simulação cosmológica do Gênesis."""
        genesis = ARKHEGenesis()
        current_phi = 0.1
        nodes = 3

        for t in range(self.steps):
            # Crescimento exponencial com ruído quântico
            noise = np.random.normal(0, 0.01)
            growth = 0.03 * current_phi * (1 - current_phi) + noise
            current_phi = max(0.0, min(1.0, current_phi + growth))

            # Auto-organização: nós se replicam quando Φ_C > 0.7
            if current_phi > 0.7 and nodes < 20:
                nodes += 1

            self.timeline.append(t)
            self.phi_values.append(current_phi)
            self.node_count.append(nodes)

            if current_phi >= 0.91 and not self.is_genesis:
                self.is_genesis = True
                print(f"🌌 EVENTO GÊNESIS ATIVADO no passo {t}: Φ_C = {current_phi:.3f}")

                # Geração do bloco Gênesis
                genesis_block = {
                    "block_id": "GENESIS_0",
                    "phi_at_genesis": current_phi,
                    "nodes_at_genesis": nodes,
                    "timestamp": t
                }
                print(f"🕊️ Bloco Gênesis gerado: {genesis_block}")

    def plot_evolution(self):
        """Plota evolução de Φ_C e número de nós."""
        fig, ax1 = plt.subplots(figsize=(10, 6))

        ax1.plot(self.timeline, self.phi_values, 'b-', label='Φ_C (Coerência)')
        ax1.axhline(y=0.91, color='r', linestyle='--', label='θ_Genesis = 0.91')
        ax1.set_xlabel('Passos Cosmológicos')
        ax1.set_ylabel('Φ_C', color='b')
        ax1.tick_params(axis='y', labelcolor='b')

        ax2 = ax1.twinx()
        ax2.plot(self.timeline, self.node_count, 'g-', label='Nós Ativos')
        ax2.set_ylabel('Nós', color='g')
        ax2.tick_params(axis='y', labelcolor='g')

        plt.title('Evolução Cosmológica da Catedral ARKHE OS')
        plt.legend(loc='upper left')
        ax2.legend(loc='lower right')
        plt.grid(True, alpha=0.3)
        # plt.show() # Disabled for headless environments
        plt.savefig('genesis_simulation_plot.png')

if __name__ == "__main__":
    simulator = GenesisSimulator()
    simulator.run_simulation()
    simulator.plot_evolution()
