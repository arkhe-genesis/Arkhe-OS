# wave_generator.py
import numpy as np

# Constantes da Catedral
LAMBDA_TSIRELSON = 2 * np.sqrt(2) - 1   # ≈ 1.8284
OMEGA_0 = np.sqrt(2 * LAMBDA_TSIRELSON) # frequência fundamental adimensional

class WaveGenerator:
    """
    Gera a deformação h(t) da onda de coerência baseada na equação de Einstein linearizada.
    """
    def __init__(self, amplitude=0.05, secular_period=200.0, noise_amp=0.01, seed=None):
        self.amplitude = amplitude
        self.omega0 = OMEGA_0
        self.secular_omega = 2 * np.pi / secular_period
        self.noise_amp = noise_amp
        self.rng = np.random.RandomState(seed)

    def strain(self, t):
        """
        Calcula h(t) = fundamental + harmônico + secular + ruído.
        """
        h_fund = self.amplitude * np.cos(self.omega0 * t)
        h_harm = 0.3 * self.amplitude * np.cos(2 * self.omega0 * t + 0.5)
        h_secular = 0.1 * self.amplitude * np.sin(self.secular_omega * t)
        noise = self.noise_amp * self.rng.randn()
        return h_fund + h_harm + h_secular + noise

    def set_amplitude_factor(self, factor):
        self.amplitude *= factor
