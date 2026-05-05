# arkhe_os/sensors/quantum_magnetometer.py
import numpy as np
import time
from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class GeomagneticVector:
    """Vetor completo do campo geomagnético medido."""
    H_total: float        # Intensidade total em A/m
    D: float               # Declinação em graus
    I: float               # Inclinação em graus
    X: float               # Componente Norte
    Y: float               # Componente Leste
    Z: float               # Componente Vertical (down)
    gradient: np.ndarray   # Gradiente local [dH/dx, dH/dy, dH/dz]

class QuantumMagnetoFrameSensor:
    """
    Implementa o sensor da patente RU2680629C2: três anéis ortogonais
    de substância com alta permeabilidade, bombeados magneticamente.
    """
    def __init__(self, working_substance_mu: float = 1e5,
                 turns: int = 100, area: float = 1e-4):
        self.mu = working_substance_mu
        self.N = turns
        self.S = area              # seção transversal do núcleo (m²)
        self.mu0 = 1.257e-6        # permeabilidade do vácuo (V·s/A·m)
        self.calibration_factor = self.N * self.S * self.mu0 * self.mu
        # Inicialmente calibrado com H de referência
        self._reference_emf = None
        self._baseline_H = None

    def calibrate(self, known_H: float, measured_emf: float):
        """Calibração com campo conhecido (ex.: bobina padrão)."""
        self._baseline_H = known_H
        self._reference_emf = measured_emf

    def read_field_from_emf(self, emf: float) -> float:
        """Converte FEM lida em intensidade H (A/m)."""
        if self._baseline_H is None or self._reference_emf is None:
            return emf / self.calibration_factor
        return (emf / self._reference_emf) * self._baseline_H

    def measure_vector(self) -> GeomagneticVector:
        """
        Lê as FEMs dos três enrolamentos ortogonais
        e compõe o vetor completo.
        (Em hardware real, seria leitura ADC sincronizada)
        """
        # Simulação: gerar componentes proporcionais ao campo real + ruído
        true_H = np.array([18.0, 2.0, 45.0])  # uT, exemplo
        emf_noise = np.random.normal(0, 1e-6, 3)
        emf = true_H * self.calibration_factor + emf_noise
        X, Y, Z = [self.read_field_from_emf(e) for e in emf]
        H = np.sqrt(X**2 + Y**2)
        D = np.degrees(np.arctan2(Y, X))
        I = np.degrees(np.arctan2(Z, H))
        grad = self._compute_gradient()
        return GeomagneticVector(
            H_total=H, D=D, I=I, X=X, Y=Y, Z=Z, gradient=grad
        )

    def _compute_gradient(self) -> np.ndarray:
        # Simplificação: gradiente zero, mas poderia usar sensores auxiliares
        return np.zeros(3)
