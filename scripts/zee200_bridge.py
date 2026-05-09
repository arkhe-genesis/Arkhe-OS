#!/usr/bin/env python3
"""
ARKHE OS — ZEE200 Bridge: Python → circom
v∞.Ω.1.1 → GTZK Track 1-3 Integration
"""

import numpy as np
import json

PHI = (1 + np.sqrt(5)) / 2
Q = np.exp(1j * np.pi / 5)

F = np.array([
    [1/PHI, 1/np.sqrt(PHI)],
    [1/np.sqrt(PHI), -1/PHI]
], dtype=complex)

SIGMA1 = np.array([[Q, 0], [0, -Q**(-1)]], dtype=complex)
SIGMA2 = F @ SIGMA1 @ np.linalg.inv(F)

def matrix_to_circom_input(M: np.ndarray, name: str = "M") -> dict:
    """Converte matriz complexa 2×2 para entrada circom."""
    return {
        f"{name}_re_00": float(M[0,0].real),
        f"{name}_im_00": float(M[0,0].imag),
        f"{name}_re_01": float(M[0,1].real),
        f"{name}_im_01": float(M[0,1].imag),
        f"{name}_re_10": float(M[1,0].real),
        f"{name}_im_10": float(M[1,0].imag),
        f"{name}_re_11": float(M[1,1].real),
        f"{name}_im_11": float(M[1,1].imag),
    }

def verify_unitarity(M: np.ndarray, tol: float = 1e-10) -> bool:
    """Verifica se M é unitária."""
    return np.allclose(M.conj().T @ M, np.eye(2), atol=tol)

def verify_braid_relation(M1: np.ndarray, M2: np.ndarray, tol: float = 1e-10) -> bool:
    """Verifica se M1, M2 satisfazem σ₁σ₂σ₁ = σ₂σ₁σ₂."""
    lhs = M1 @ M2 @ M1
    rhs = M2 @ M1 @ M2
    return np.allclose(lhs, rhs, atol=tol)

if __name__ == "__main__":
    # Gerar inputs para circom
    inputs = {}
    inputs.update(matrix_to_circom_input(SIGMA1, "sigma1"))
    inputs.update(matrix_to_circom_input(SIGMA2, "sigma2"))

    # Verificações prévias
    assert verify_unitarity(SIGMA1), "SIGMA1 não é unitária!"
    assert verify_unitarity(SIGMA2), "SIGMA2 não é unitária!"
    assert verify_braid_relation(SIGMA1, SIGMA2), "Relação de trança falhou!"

    # Salvar para snarkjs
    with open("braid_element_input.json", "w") as f:
        json.dump(inputs, f, indent=2)

    print("✅ Inputs gerados para circom: braid_element_input.json")
    print(f"   σ₁ = {SIGMA1[0,0]:.6f} ...")
    print(f"   σ₂ = {SIGMA2[0,0]:.6f} ...")
    print(f"   Unitariedade: OK")
    print(f"   Relação de trança: OK")