import numpy as np

class JonesRepresentationNumPy:
    """Representação de Jones vetorizada com NumPy."""

    def __init__(self):
        self.q = np.exp(1j * np.pi / 5)
        self.PHI = (1 + np.sqrt(5)) / 2

        # Matrizes 2×2
        self.SIGMA1 = np.array([[self.q, 0], [0, -self.q**(-1)]], dtype=complex)
        F = np.array([[1/self.PHI, 1/np.sqrt(self.PHI)],
                      [1/np.sqrt(self.PHI), -1/self.PHI]], dtype=complex)
        F_inv = np.linalg.inv(F)
        self.SIGMA2 = F @ self.SIGMA1 @ F_inv

        self.gates = {
            'I': np.eye(2, dtype=complex),
            'σ₁': self.SIGMA1,
            'σ₂': self.SIGMA2,
            'σ₁⁻¹': np.linalg.inv(self.SIGMA1),
            'σ₂⁻¹': np.linalg.inv(self.SIGMA2),
        }

    def compile_circuit(self, braid_word: list) -> complex:
        """Compila uma palavra de trança em um invariante de Jones usando NumPy."""
        if not braid_word:
            return 2.0 / (self.PHI + 1/self.PHI)

        # Get matrices
        matrices = [self.gates[braid] for braid in braid_word]

        if len(matrices) == 1:
            M = matrices[0]
        else:
            # We can implement a pure einsum if we have a stack of matrices
            # but for dynamic words, multi_dot is efficient and uses underlying BLAS
            M = np.linalg.multi_dot(matrices)

        return np.trace(M) / (self.PHI + 1/self.PHI)
