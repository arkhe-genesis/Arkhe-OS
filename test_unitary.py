import numpy as np
import scipy.linalg

DIMENSION = 17
PHI = (1 + 5**0.5) / 2

matrix = np.zeros((DIMENSION, DIMENSION), dtype=complex)
for i in range(DIMENSION):
    for j in range(DIMENSION):
        phase = (PHI ** i * np.pi ** j) % (2 * np.pi)
        matrix[i, j] = np.exp(1j * phase)

# We want the entanglement matrix to be unitary.
# Let's orthonormalize the matrix using QR decomposition.
Q, R = scipy.linalg.qr(matrix)

identity = Q.conj().T @ Q
print("Is unitary?", np.allclose(identity, np.eye(DIMENSION), atol=1e-10))
