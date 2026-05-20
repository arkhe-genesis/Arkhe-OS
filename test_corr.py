import math
import numpy as np

DIMENSION = 17
PHI = (1 + math.sqrt(5)) / 2

matrix = np.zeros((DIMENSION, DIMENSION), dtype=complex)
for i in range(DIMENSION):
    for j in range(DIMENSION):
        phase = (PHI ** i * math.pi ** j) % (2 * math.pi)
        matrix[i, j] = np.exp(1j * phase) / np.sqrt(DIMENSION)

expected_signature = np.abs(matrix @ np.ones(DIMENSION) / np.sqrt(DIMENSION))

def simulate_atlas_portal_signature() -> np.ndarray:
    signature = np.zeros(17)
    for k in range(17):
        phase = (PHI ** 17 / (math.factorial(17) * math.pi)) * k * 2 * math.pi
        signature[k] = np.abs(np.sin(phase) * np.exp(-k / 17))
    norm = np.linalg.norm(signature)
    if norm == 0:
        return signature
    return signature / norm

detected_signature = simulate_atlas_portal_signature()

correlation = np.corrcoef(expected_signature, detected_signature)[0, 1]
print("Correlation:", correlation)
