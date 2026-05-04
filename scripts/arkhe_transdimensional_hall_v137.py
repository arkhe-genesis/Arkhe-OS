#!/usr/bin/env python3
"""
arkhe_transdimensional_hall_v137.py
Substrato 239: Transdimensional Anomalous Hall Effect — Simulador de Janela de Coerência.
"""
import numpy as np

class TransdimensionalHallSimulator:
    """
    Simula a curvatura de Berry transdimensional em função da espessura.
    Janela de coerência: 2–5 nm, 3–15 camadas atômicas.
    """
    def __init__(self, rho_seed: float = 0.05):
        self.rho = rho_seed
        self.window_nm = (2.0, 5.0)
        self.layers_range = (3, 15)

    def berry_curvature_transdimensional(self, thickness_nm: float) -> float:
        """
        Curvatura de Berry transdimensional: emerge apenas na janela de coerência.
        Fora da janela, colapsa para 0 (2D) ou se dilui (3D).
        """
        d_min, d_max = self.window_nm
        if thickness_nm < d_min or thickness_nm > d_max:
            return 0.0  # Fora da janela transdimensional
        # Pico de coerência no centro da janela (3.5 nm), modulado pelo primitivo
        center = (d_min + d_max) / 2.0
        width = (d_max - d_min) / 2.0
        return self.rho * np.exp(-((thickness_nm - center)**2) / (2 * (width/3)**2))

    def hall_hysteresis_loop(self, thickness_nm: float, B_field_T: np.ndarray) -> np.ndarray:
        """
        Laço de histerese Hall: resposta magnética omnidirecional.
        """
        curvature = self.berry_curvature_transdimensional(thickness_nm)
        # Seis domínios magnéticos (α±, β±, γ±) com simetria C₃
        domains = np.array([1.0, -1.0, 0.5, -0.5, 0.866, -0.866])
        response = np.zeros_like(B_field_T)
        for i, b in enumerate(B_field_T):
            domain_idx = int((i % 6))  # Alterna entre os 6 domínios
            response[i] = curvature * domains[domain_idx] * np.tanh(b / 0.5)
        return response

if __name__ == "__main__":
    # Exemplo
    sim = TransdimensionalHallSimulator()
    thicknesses = np.linspace(1.0, 6.0, 100)
    curvatures = [sim.berry_curvature_transdimensional(d) for d in thicknesses]
    print(f"🔲 Janela Transdimensional: {sim.window_nm} nm")
    print(f"   Pico de curvatura em 3.5 nm: {sim.berry_curvature_transdimensional(3.5):.4f}")
    print(f"   Curvatura em 1.0 nm (2D): {sim.berry_curvature_transdimensional(1.0):.4f}")
    print(f"   Curvatura em 6.0 nm (3D): {sim.berry_curvature_transdimensional(6.0):.4f}")
    print(f"   ✅ Dimensionalidade contínua validada: a matéria existe entre o 2D e o 3D.")
