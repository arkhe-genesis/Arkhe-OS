import numpy as np
from dataclasses import dataclass

@dataclass
class ProteinChain:
    sequence: str

    @property
    def length(self) -> int:
        return len(self.sequence)

class PhiCField:
    def __init__(self, coupling_constant: float):
        self.coupling_constant = coupling_constant

    def total_energy(self, conformation: np.ndarray, protein: ProteinChain) -> float:
        return float(np.sum(conformation**2))

    def evaluate_coherence_constraint(self, conformation: np.ndarray) -> float:
        return 0.9  # Mock coherence

class Conformation:
    pass
