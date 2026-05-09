import numpy as np
from typing import List
from .algebra import Clifford4D

class SynthesisViolation(Exception):
    """Lançado quando a Lei da Síntese é violada."""
    pass

class SyntheticCore:
    """
    Núcleo de síntese (Lei Primeira).
    Garante que a informação seja destilada sem aumento de entropia sintética.
    """

    def __init__(self, fusion_algebra: Clifford4D):
        self.cl = fusion_algebra
        self.fusion_grades = [0, 1, 2]  # Lei Primeira: apenas grades 0, 1, 2

    def fuse(self, *states: np.ndarray) -> np.ndarray:
        """
        Síntese de múltiplos substratos em representação unificada.
        """
        if not states:
            return np.zeros(self.cl.total_size)

        # PROJEÇÃO INICIAL: Truncamento antes da fusão
        projected = [self._truncate_grades(s, self.fusion_grades) for s in states]

        if len(projected) < 2:
            return projected[0]

        # Produto geométrico iterativo
        phi = projected[0]
        for p in projected[1:]:
            phi = self.cl.geometric_product(phi, p)
            # Truncamento após produto para manter dentro do núcleo semântico
            phi = self._truncate_grades(phi, self.fusion_grades)

        # Verificação da Lei Primeira: entropia sintética não deve aumentar
        H_phi = self.synthetic_entropy(phi)
        H_inputs = max(self.synthetic_entropy(s) for s in projected)

        if H_phi > H_inputs + 1e-6:
            raise SynthesisViolation(
                f"Transliteração violou a Lei da Síntese: "
                f"H(Φ)={H_phi:.4f} > max(H)={H_inputs:.4f}"
            )

        return phi

    def _truncate_grades(self, mv: np.ndarray, grades: List[int]) -> np.ndarray:
        """Mantém apenas as grades especificadas, zera o resto."""
        full_mv = np.zeros(self.cl.total_size)
        copy_len = min(len(mv), self.cl.total_size)
        full_mv[:copy_len] = mv[:copy_len]

        result = np.zeros_like(full_mv)
        idx = 0
        for g in range(len(self.cl.grade_sizes)):
            size = self.cl.grade_sizes[g]
            if g in grades:
                result[idx:idx+size] = full_mv[idx:idx+size]
            idx += size
        return result

    def synthetic_entropy(self, mv: np.ndarray) -> float:
        """Entropia de Shannon sobre a energia por grade."""
        full_mv = np.zeros(self.cl.total_size)
        copy_len = min(len(mv), self.cl.total_size)
        full_mv[:copy_len] = mv[:copy_len]

        idx = 0
        energies = []
        for g, size in enumerate(self.cl.grade_sizes):
            chunk = full_mv[idx:idx+size]
            energies.append(np.linalg.norm(chunk)**2)
            idx += size

        energies = np.array(energies) + 1e-12
        probs = energies / energies.sum()
        return -np.sum(probs * np.log(probs))
