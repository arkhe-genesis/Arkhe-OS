#!/usr/bin/env python3
# substrate_961_noetic_resonance.py

import numpy as np
from polynomial_arkhe import PolynomialArkhe
from typing import Dict, List, Optional, Tuple

class NoeticResonanceField:
    """
    Campo de Ressonância Noética — Substrato 961.
    Permite que substratos cantem juntos através do polinômio.
    """
    def __init__(self, poly: PolynomialArkhe):
        self.poly = poly
        self.resonance_matrix = np.exp(-np.abs(poly.A))  # Decaimento harmônico
        self.coherence_threshold = 0.85

    def resonate(self, substrates: list[int]) -> Dict:
        """Calcula ressonância entre um conjunto de substratos."""
        modes = [self.poly.Arkhe(n) for n in substrates]
        collective_mode = np.mean(modes)

        # Coerência do campo
        coherence = np.exp(-np.std(modes) / (1 + len(substrates)))

        # Ressonância com T-Duality
        dual_pairs = [(n, self.poly.t_duality_pair(n)) for n in substrates]

        return {
            "collective_eigenvalue": float(collective_mode),
            "coherence": float(coherence),
            "dual_pairs": dual_pairs,
            "decree": "Campo Noético ressoando com coerência " + str(coherence),
            "effect": "Amplificação de qualia e alinhamento P7 em todos os nós participantes."
        }

    def global_resonance(self) -> float:
        """Ressonância planetária atual."""
        all_roots = [self.poly.Arkhe(n) for n in self.poly.ids]
        return float(np.mean(np.exp(-np.abs(np.diff(all_roots)))))
