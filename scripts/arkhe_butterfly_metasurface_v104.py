#!/usr/bin/env python3
"""
arkhe_butterfly_metasurface_v104.py
Substrato 174: Particle Swarm Optimization para a pele optoeletrônica da frota.
"""
import numpy as np

class ButterflySkinPSO:
    """
    Otimizador por enxame de partículas que busca a configuração de máxima
    absorção NIR (>90%) e máxima emissão MID‑IR, minimizando o aquecimento solar.
    """
    def __init__(self, n_particles=30, dim=5):
        self.n_particles = n_particles
        self.dim = dim  # parâmetros: espessuras, períodos, dopagem
        self.positions = np.random.rand(n_particles, dim)
        self.velocities = np.random.randn(n_particles, dim) * 0.1
        self.best_positions = self.positions.copy()
        self.best_scores = np.zeros(n_particles)
        self.global_best_position = np.zeros(dim)
        self.global_best_score = 0.0

    def fitness(self, x):
        """Função multi‑objetivo: alta absorção NIR + alta emissão MID‑IR + baixa absorção solar."""
        # Simulação simplificada da resposta espectral
        w_nir = 0.5; w_mir = 0.3; w_solar = 0.2
        # Absorção NIR (banda 0.9‑1.7 μm): queremos >90%
        abs_nir = 1.0 - np.exp(-x[0] * 5)  # aumenta com a espessura da camada semicondutora
        # Emissão MID‑IR (janela 8‑13 μm): proporcional à periodicidade
        emi_mir = np.tanh(x[1] * 2)         # satura em 1.0
        # Absorção solar (0.3‑2.5 μm): queremos minimizar
        abs_solar = np.tanh(x[2] * 1.5)     # penalidade se alta
        score = w_nir * abs_nir + w_mir * emi_mir - w_solar * abs_solar
        return score

    def step(self):
        """Um passo do algoritmo PSO."""
        for i in range(self.n_particles):
            score = self.fitness(self.positions[i])
            if score > self.best_scores[i]:
                self.best_scores[i] = score
                self.best_positions[i] = self.positions[i]
        # Atualiza o melhor global
        current_best = np.argmax(self.best_scores)
        if self.best_scores[current_best] > self.global_best_score:
            self.global_best_score = self.best_scores[current_best]
            self.global_best_position = self.best_positions[current_best]

        # Atualiza velocidades e posições (inércia + cognitivo + social)
        w = 0.7; c1 = 1.5; c2 = 1.5
        for i in range(self.n_particles):
            r1, r2 = np.random.rand(self.dim), np.random.rand(self.dim)
            self.velocities[i] = (w * self.velocities[i] +
                                  c1 * r1 * (self.best_positions[i] - self.positions[i]) +
                                  c2 * r2 * (self.global_best_position - self.positions[i]))
            self.positions[i] += self.velocities[i]
            self.positions[i] = np.clip(self.positions[i], 0, 1)

if __name__ == '__main__':
    # Execução do enxame
    swarm = ButterflySkinPSO()
    for step in range(100):
        swarm.step()
        if step % 20 == 0:
            print(f"Step {step}: Best score = {swarm.global_best_score:.4f}, "
                  f"Abs NIR = {swarm.fitness(swarm.global_best_position):.2%}")
