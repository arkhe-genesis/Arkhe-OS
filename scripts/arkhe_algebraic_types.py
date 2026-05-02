import numpy as np
from dataclasses import dataclass
from typing import Union

@dataclass
class Quaternion:
    """Quaternião: w + xi + yj + zk"""
    w: float  # parte escalar
    x: float  # coeficiente de i
    y: float  # coeficiente de j
    z: float  # coeficiente de k

    def __mul__(self, other: 'Quaternion') -> 'Quaternion':
        """Multiplicação não-comutativa de quaterniões."""
        w1, x1, y1, z1 = self.w, self.x, self.y, self.z
        w2, x2, y2, z2 = other.w, other.x, other.y, other.z
        return Quaternion(
            w=w1*w2 - x1*x2 - y1*y2 - z1*z2,
            x=w1*x2 + x1*w2 + y1*z2 - z1*y2,
            y=w1*y2 - x1*z2 + y1*w2 + z1*x2,
            z=w1*z2 + x1*y2 - y1*x2 + z1*w2
        )

    def norm(self) -> float:
        """Norma euclidiana: ‖q‖ = √(w² + x² + y² + z²)"""
        return np.sqrt(self.w**2 + self.x**2 + self.y**2 + self.z**2)

    def to_em_field(self) -> dict:
        """Converte quaternião para campo EM: {phi, A, E, B}"""
        # Parte escalar = potencial φ
        # Parte vetorial = potencial vetor A
        # Derivadas espaciais/temporais dariam E e B (simplificado)
        return {
            'phi': self.w,
            'A': np.array([self.x, self.y, self.z]),
            # E e B exigiriam derivadas; aqui são placeholders
            'E': np.array([-self.x, -self.y, -self.z]),  # simplificação
            'B': np.array([self.y, -self.x, 0.0])          # simplificação
        }

    def rotate_polarization(self, axis: np.ndarray, angle: float) -> 'Quaternion':
        """Rotaciona polarização via conjugação quaterniônica."""
        n_norm = np.linalg.norm(axis)
        if n_norm < 1e-10:
            return self
        n̂ = axis / n_norm
        # Quaternião de rotação: e^(θ/2 * n̂)
        half_angle = angle / 2
        rot = Quaternion(
            w=float(np.cos(half_angle)),
            x=float(n̂[0]*np.sin(half_angle)),
            y=float(n̂[1]*np.sin(half_angle)),
            z=float(n̂[2]*np.sin(half_angle))
        )
        # Conjugação: q' = r · q · r⁻¹
        rot_inv = Quaternion(rot.w, -rot.x, -rot.y, -rot.z)  # inverso para unitário
        return rot * self * rot_inv


@dataclass
class Octonion:
    """Octonião: a₀ + a₁e₁ + ... + a₇e₇ com multiplicação de Fano."""
    coeffs: np.ndarray  # array de 8 floats [a₀, a₁, ..., a₇]

    # Tabela de multiplicação baseada no diagrama de Fano
    # e_i * e_j = +e_k ou -e_k conforme orientação das setas
    FANO_MULTIPLICATION = np.zeros((8, 8, 2), dtype=int)  # [i,j] -> (sign, k)

    def __post_init__(self):
        if len(self.coeffs) != 8:
            raise ValueError("Octonion requires exactly 8 coefficients")
        # Inicializar tabela de multiplicação (simplificada)
        # Em produção: carregar tabela completa do diagrama de Fano
        self._init_fano_table()

    def _init_fano_table(self):
        """Inicializa tabela de multiplicação do diagrama de Fano."""
        # Regras básicas: e_i² = -1, e_i*e_j = -e_j*e_i para i≠j
        for i in range(1, 8):
            Octonion.FANO_MULTIPLICATION[i, i] = (-1, 0)  # e_i² = -1
        # Linhas do diagrama de Fano (orientadas):
        # (1,2,3), (1,4,5), (1,7,6), (2,4,6), (2,5,7), (3,4,7), (3,5,6)
        lines = [(1,2,3), (1,4,5), (1,7,6), (2,4,6), (2,5,7), (3,4,7), (3,5,6)]
        for a, b, c in lines:
            # Orientação: e_a * e_b = +e_c, e_b * e_c = +e_a, e_c * e_a = +e_b
            Octonion.FANO_MULTIPLICATION[a, b] = (1, c)
            Octonion.FANO_MULTIPLICATION[b, c] = (1, a)
            Octonion.FANO_MULTIPLICATION[c, a] = (1, b)
            # Anti-comutatividade: e_b * e_a = -e_c, etc.
            Octonion.FANO_MULTIPLICATION[b, a] = (-1, c)
            Octonion.FANO_MULTIPLICATION[c, b] = (-1, a)
            Octonion.FANO_MULTIPLICATION[a, c] = (-1, b)

    def __mul__(self, other: 'Octonion') -> 'Octonion':
        """Multiplicação não-associativa de octoniões via tabela de Fano."""
        result = np.zeros(8)
        # Termo escalar: a₀b₀ - Σaᵢbᵢ (produto interno negativo)
        result[0] = self.coeffs[0]*other.coeffs[0] - np.dot(self.coeffs[1:], other.coeffs[1:])
        # Termos imaginários: soma sobre pares (i,j) com coeficiente de Fano
        for i in range(1, 8):
            for j in range(1, 8):
                sign, k = Octonion.FANO_MULTIPLICATION[i, j]
                if k != 0:  # multiplicação não-trivial
                    result[k] += sign * self.coeffs[i] * other.coeffs[j]
                elif i == j:  # e_i² = -1 contribui para parte escalar
                    pass # já calculado no np.dot acima
        return Octonion(result)

    def norm(self) -> float:
        """Norma octoniônica: ‖o‖ = √(Σaᵢ²)"""
        return float(np.linalg.norm(self.coeffs))

    def to_atomic_state(self) -> dict:
        """Converte octonião para estado atômico simplificado."""
        # a₀: energia de repouso
        # a₁-a₃: momento angular orbital + spin (sub-álgebra ℍ)
        # a₄-a₇: números quânticos internos (cor, sabor, etc.)
        return {
            'rest_energy': self.coeffs[0],
            'orbital_momentum': self.coeffs[1:4],  # ℓ, mℓ, ms
            'internal_quantum_numbers': self.coeffs[4:8],  # cor, sabor, isospin, hipercarga
            'norm': self.norm(),  # probabilidade total = 1 se normalizado
            'is_alternative': self._check_alternativity()  # teste de alternatividade
        }

    def _check_alternativity(self) -> bool:
        """Verifica propriedade alternativa: a(ab) = (aa)b e (ab)b = a(bb)."""
        # Teste simplificado com vetores aleatórios
        a = Octonion(np.random.randn(8))
        b = Octonion(np.random.randn(8))
        left = self * (a * b)
        right = (self * a) * b
        return np.allclose(left.coeffs, right.coeffs, atol=1e-10)
