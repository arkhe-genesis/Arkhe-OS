"""Substrato 278 — Arkhe-Resonance: A Frequência e a Álgebra da Estrutura."""
import numpy as np

CANONICAL_FREQ_HZ = 39_420.0
CANONICAL_OMEGA = 2.0 * 3.1415926535 * CANONICAL_FREQ_HZ

def lie_bracket_nonzero(A, B, tol=1e-9):
    """Verifica se [A, B] != 0."""
    comm = A @ B - B @ A
    return np.linalg.norm(comm) > tol
