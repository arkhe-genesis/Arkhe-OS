import numpy as np
from typing import List, Tuple

class Clifford4D:
    """
    Álgebra geométrica Cl(4,0) para estados mentais e transliteração.
    Baseado no ANEXO BY e ANEXO CE.
    """

    def __init__(self):
        self.dims = 4
        self.grade_sizes = [1, 4, 6, 4, 1]  # escalar, vetor, bivector, trivector, pseudoscalar
        self.total_size = sum(self.grade_sizes)

    def geometric_product(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Produto geométrico simplificado em Cl(4,0), focado em grades 0, 1, 2."""
        result = np.zeros(self.total_size)

        # Parte Escalar: s_a*s_b + v_a·v_b
        result[0] = a[0] * b[0] + np.dot(a[1:5], b[1:5])

        # Parte Vetorial: s_a*v_b + s_b*v_a
        result[1:5] = a[0] * b[1:5] + b[0] * a[1:5]

        # Parte Bivectorial: s_a*b_b + s_b*b_a + v_a∧v_b
        v_a = a[1:5]
        v_b = b[1:5]
        wedge = np.outer(v_a, v_b) - np.outer(v_b, v_a)
        result[5:11] = a[0] * b[5:11] + b[0] * a[5:11] + self._bivector_part(wedge)

        return result

    def _bivector_part(self, wedge: np.ndarray) -> np.ndarray:
        """Extrai componentes bivectoriais de uma matriz antissimétrica."""
        return np.array([
            wedge[0,1], wedge[0,2], wedge[0,3],
            wedge[1,2], wedge[1,3], wedge[2,3]
        ])

    def rotate(self, multivector: np.ndarray, plane: Tuple[int,int], angle: float) -> np.ndarray:
        """Rotação via rotor: R = exp(-angle/2 * e_{ij})"""
        rotor = np.zeros(self.total_size)
        rotor[0] = np.cos(angle / 2)
        idx = self._bivector_index(plane)
        rotor[5 + idx] = -np.sin(angle / 2)

        # R * M * ~R
        temp = self.geometric_product(rotor, multivector)
        rotor_conj = rotor.copy()
        rotor_conj[5 + idx] *= -1
        return self.geometric_product(temp, rotor_conj)

    def _bivector_index(self, plane: Tuple[int,int]) -> int:
        mapping = {(0,1):0, (0,2):1, (0,3):2, (1,2):3, (1,3):4, (2,3):5}
        return mapping.get(plane, 0)
