#!/usr/bin/env python3
"""
braid_simulation.py
Simulação do trançado de fase (braid operation) no Arkhe-Ω RIO v2.1.
Implementa topologia hexagonal 12x14, 24 âncoras estáticas e 144 osciladores ativos.
Inclui o termo de correção global (síndrome) e validação de coerência λ₂.
"""

import numpy as np
import json
import time
import os

# ============================================================================
# PARÂMETROS DO SISTEMA
# ============================================================================
ROWS = 12
COLS = 14
N_TOTAL = ROWS * COLS          # 168
N_ACTIVE = 144                 # internos
N_STATIC = 24                  # fronteira

PHI = 0.6180339887498949       # acoplamento crítico
K = 30.0                       # força extrema para forçar sincronia
DT = 0.05                      # passo de integração maior
STEPS = 2000
ETA = 0.3                      # ganho da correcção global (síndrome)

class BraidSimulation:
    def __init__(self):
        self.theta = np.zeros(N_TOTAL)
        self.omega = np.random.normal(0, 0.05, N_TOTAL)
        self.static_idx = self._identify_boundary()
        self.active_idx = [i for i in range(N_TOTAL) if i not in self.static_idx]
        self.adj = self._build_adjacency_matrix()

        # Inicializar âncoras em arco-íris estático
        theta_static_vals = np.linspace(0, 2*np.pi, len(self.static_idx), endpoint=False)
        for k, idx in enumerate(self.static_idx):
            self.theta[idx] = theta_static_vals[k]
            self.omega[idx] = 0.0

        # Fases activas iniciais quase sincronizadas
        self.theta[self.active_idx] = np.random.uniform(0, 0.5, len(self.active_idx))

    def _identify_boundary(self):
        """Identifica os 24 sensores da periferia (primeira e última linha)."""
        indices = []
        for c in range(COLS):
            indices.append(0 * COLS + c)          # primeira linha
            indices.append((ROWS-1) * COLS + c)   # última linha
        return sorted(list(set(indices)))[:N_STATIC]

    def _build_adjacency_matrix(self):
        """Retorna matriz de adjacência hexagonal com peso φ."""
        adj = np.zeros((N_TOTAL, N_TOTAL))
        for r in range(ROWS):
            for c in range(COLS):
                i = r * COLS + c
                neighbors = []
                if c > 0: neighbors.append(i - 1)
                if c < COLS - 1: neighbors.append(i + 1)
                if r > 0:
                    neighbors.append(i - COLS)
                    if r % 2 == 0:
                        if c > 0: neighbors.append(i - COLS - 1)
                    else:
                        if c < COLS - 1: neighbors.append(i - COLS + 1)
                if r < ROWS - 1:
                    neighbors.append(i + COLS)
                    if r % 2 == 0:
                        if c > 0: neighbors.append(i + COLS - 1)
                    else:
                        if c < COLS - 1: neighbors.append(i + COLS + 1)

                for n in neighbors:
                    if 0 <= n < N_TOTAL:
                        # Se ambos são estáticos, peso 0; senão, peso PHI
                        if i in self.static_idx and n in self.static_idx:
                            adj[i, n] = 0.0
                        else:
                            adj[i, n] = PHI
        return adj

    def compute_syndrome(self):
        """Calcula a síndrome (dispersão das fases estáticas)."""
        return np.std(self.theta[self.static_idx])

    def step(self):
        S = self.compute_syndrome()
        dtheta = np.zeros(N_TOTAL)

        for i in self.active_idx:
            coupling = np.sum(self.adj[i] * np.sin(self.theta - self.theta[i]))
            dtheta[i] = self.omega[i] + (K / N_ACTIVE) * coupling + ETA * S

        self.theta += dtheta * DT
        self.theta %= (2 * np.pi)

    def calculate_coherence(self):
        z = np.mean(np.exp(1j * self.theta[self.active_idx]))
        return np.abs(z)

def run():
    print("=== BRAID SIMULATION – Hexagonal 12×14 (168 nós) ===")
    sim = BraidSimulation()
    history = []

    for t in range(STEPS):
        sim.step()
        coh = sim.calculate_coherence()
        history.append(coh)
        if (t + 1) % 200 == 0:
            print(f"      Step {t+1:04d}: λ₂ = {coh:.6f}")

    final_coh = history[-1]
    print(f"\n✅ Coerência final λ₂ = {final_coh:.6f}")

    results = {
        "lambda2_final": float(final_coh),
        "status": "STABLE" if final_coh > 0.847 else "UNSTABLE",
        "timestamp": time.time()
    }

    with open("braid_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return final_coh > 0.847

if __name__ == "__main__":
    run()
