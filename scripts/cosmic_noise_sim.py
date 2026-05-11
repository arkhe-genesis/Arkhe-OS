#!/usr/bin/env python3
"""
SIMULADOR DE RUÍDO CÓSMICO (cosmic_noise_sim.py)
Estressa o código afim com padrões de erro não-aleatórios.
"""

import numpy as np

class CosmicNoiseSimulator:
    def __init__(self, code_length=16384):
        self.n = code_length

    def generate_burst_error(self, burst_length: int, num_bursts: int) -> np.ndarray:
        """
        Gera erros em rajada (ex: passagem de um múon).
        Cada rajada corrompe uma sequência contínua de qubits.
        """
        error = np.zeros(self.n, dtype=int)
        for _ in range(num_bursts):
            start = np.random.randint(0, self.n - burst_length)
            error[start:start+burst_length] = 1
        return error

    def generate_cosmic_ray_shower(self, num_rays: int, spread_radius: int) -> np.ndarray:
        """
        Simula um chuveiro de raios cósmicos.
        Cada raio atinge um qubit central e corrompe uma esfera de raio 'spread_radius'.
        """
        error = np.zeros(self.n, dtype=int)
        for _ in range(num_rays):
            center = np.random.randint(0, self.n)
            # Corrompe qubits dentro do raio (simulado como vizinhança circular em 2D)
            for i in range(max(0, center - spread_radius), min(self.n, center + spread_radius + 1)):
                if np.random.random() < 0.8:  # 80% de chance de corromper
                    error[i] = 1
        return error

    def generate_adversarial_pattern(self, target_logical: int) -> np.ndarray:
        """
        Gera um erro projetado para confundir o decodificador,
        concentrando-se em qubits de baixa confiabilidade (simulado).
        """
        error = np.zeros(self.n, dtype=int)
        # Concentra erros em padrões que parecem ciclos curtos para o BP
        # (embora a cintura seja 8, podemos testar padrões perigosos)
        for _ in range(20):
            start = np.random.randint(0, self.n - 4)
            error[start:start+4] = np.array([1, 0, 1, 1])  # padrão traiçoeiro
        return error

# Teste de resistência da cintura 8
if __name__ == "__main__":
    simulator = CosmicNoiseSimulator(16384)
    burst = simulator.generate_burst_error(50, 10)
    shower = simulator.generate_cosmic_ray_shower(100, 5)
    adversarial = simulator.generate_adversarial_pattern(0)

    print(f"Erro em rajada: {np.sum(burst)} qubits corrompidos.")
    print(f"Chuveiro cósmico: {np.sum(shower)} qubits corrompidos.")
    print(f"Padrão adversarial: {np.sum(adversarial)} qubits corrompidos.")
    # Em um experimento real, aplicaríamos este erro ao código e testaríamos a decodificação BP+OSD.
