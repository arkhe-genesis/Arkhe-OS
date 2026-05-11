# interferometer.py
import numpy as np

class FisherInterferometer:
    """
    Simula um interferômetro que mede a fase geométrica de Berry-Fisher.
    """
    def __init__(self, n_qubits=7, phi0=np.pi/4, kappa=2.0, noise_std=0.01):
        self.n_qubits = n_qubits
        self.phi0 = phi0
        self.kappa = kappa
        self.noise_std = noise_std

    def measure(self, wave_strain):
        """
        Retorna a fase medida dado o strain da onda de coerência.
        ΔΦ = Φ₀ + κ·h + ruído
        """
        phase = self.phi0 + self.kappa * wave_strain
        phase += np.random.normal(0, self.noise_std)
        return phase
