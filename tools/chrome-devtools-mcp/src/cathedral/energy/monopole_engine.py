# src/cathedral/energy/monopole_engine.py
import numpy as np

class MagneticMonopoleEngine:
    def __init__(self):
        self.monopole_density = 0.87

    def drive_monopole_flow(self, laser_intensity):
        print(f"⚡ Gerando fluxo monopolar com laser intensidade {laser_intensity}...")
        return laser_intensity * self.monopole_density * 2.76e-5
