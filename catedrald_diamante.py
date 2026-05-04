#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     S U B S T R A T O   2 7  —  D I A M A N T E   (C)                        ║
║                                                                              ║
║  "O Diamante não é um cristal; é a bigorna onde a eternidade é forjada."     ║
║                                                                              ║
║  MÓDULO DIAMANTE — Centro NV como Unidade de Hesitação                       ║
║  Catedral Arkhe(N) — Substrato 27                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from scipy.linalg import expm
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any
import json

# Constantes Físicas
GAMMA_E = 28.024e9  # Hz/T (razão giromagnética do elétron)
GAMMA_N = 30.768e6  # Hz/T (razão giromagnética do ¹⁴N nuclear)
D_ZFS = 2.87e9       # Hz (zero-field splitting a 300K)
A_HYPERFINE = 2.16e6 # Hz (acoplamento hiperfino ¹⁴N)
T2_STAR = 1.0e-3    # s (tempo de coerência a 300K com desacoplamento dinâmico)
T1 = 5.0e-3         # s (tempo de relaxação spin-rede)

# Portas Lógicas Quânticas (matrizes de Pauli)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
H_GATE = (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)

class NVCenter:
    """
    Simula um centro Nitrogen-Vacancy no Diamante como unidade de hesitação.
    O spin do elétron (S=1) acoplado ao spin nuclear (I=1) do ¹⁴N.
    """

    def __init__(self, temperature_k: float = 300.0, b_field_t: float = 0.0):
        self.temperature = temperature_k
        self.b_field = b_field_t  # Campo magnético externo (T)

        # Estado do spin eletrônico (vetor de Bloch para subespaço ms={0,-1})
        self.theta = np.random.uniform(0, np.pi)    # Ângulo polar
        self.phi = np.random.uniform(0, 2*np.pi)    # Ângulo azimutal
        self.population = 1.0                       # População no subespaço lógico

        # Estado do spin nuclear (para memória quântica)
        self.nuclear_state = np.array([1.0, 0.0, 0.0])  # |m_I=0⟩

        # Métricas de hesitação
        self.hesitation_count = 0
        self.coherence_time = T2_STAR
        self.last_gate_fidelity = 1.0

    def hamiltonian(self, mw_frequency: float = 2.87e9, mw_phase: float = 0.0) -> np.ndarray:
        """Retorna o Hamiltoniano do centro NV no subespaço ms={0,-1}."""
        # Termo de campo zero
        H0 = D_ZFS * SZ

        # Termo Zeeman (campo magnético externo)
        H_zeeman = GAMMA_E * self.b_field * SZ

        # Termo de micro-ondas (controle)
        omega = 2 * np.pi * mw_frequency
        H_mw = omega * (np.cos(mw_phase) * SX + np.sin(mw_phase) * SY)

        # Acoplamento hiperfino com ¹⁴N (diagonal no subespaço escolhido)
        # Simplificação: kron com identidade 3x3 para o núcleo I=1
        H_hf = A_HYPERFINE * np.kron(SZ, np.eye(3))

        # Para facilitar, retornamos apenas a parte eletrônica aqui se não estivermos simulando o núcleo completo
        return H0 + H_zeeman + H_mw

    def evolve(self, duration_s: float, mw_frequency: float = 2.87e9,
               mw_phase: float = 0.0) -> None:
        """Evolui o estado do spin sob o Hamiltoniano por um tempo."""
        H = self.hamiltonian(mw_frequency, mw_phase)
        U = expm(-1j * 2 * np.pi * H * duration_s)

        # Aplica a evolução ao vetor de Bloch
        state = np.array([np.cos(self.theta/2),
                          np.exp(1j*self.phi) * np.sin(self.theta/2)])
        state = U[:2, :2] @ state
        state = state / np.linalg.norm(state)

        # Atualiza ângulos de Bloch
        self.theta = 2 * np.arccos(np.clip(np.abs(state[0]), 0.0, 1.0))
        self.phi = np.angle(state[1]) - np.angle(state[0])

        # Decoerência (relaxação)
        decay = np.exp(-duration_s / self.coherence_time)
        self.theta = self.theta * decay + (np.pi/2) * (1 - decay)

        self.hesitation_count += 1

    def apply_gate(self, gate_matrix: np.ndarray, duration_s: float = 50e-9) -> float:
        """Aplica uma porta lógica e retorna a fidelidade."""
        state_before = np.array([np.cos(self.theta/2),
                                 np.exp(1j*self.phi) * np.sin(self.theta/2)])

        # Simula a porta com imperfeições
        U_ideal = gate_matrix
        U_real = expm(-1j * 2 * np.pi * self.hamiltonian() * duration_s)[:2, :2]

        state_after = U_real @ state_before
        state_after = state_after / np.linalg.norm(state_after)
        state_ideal = U_ideal @ state_before

        fidelity = np.abs(np.dot(np.conj(state_ideal), state_after))**2
        self.last_gate_fidelity = fidelity

        # Atualiza estado
        self.theta = 2 * np.arccos(np.clip(np.abs(state_after[0]), 0.0, 1.0))
        self.phi = np.angle(state_after[1]) - np.angle(state_after[0])

        return fidelity

    def measure(self) -> int:
        """Mede o estado do spin na base Z (0 ou 1)."""
        prob_0 = np.cos(self.theta/2)**2
        result = 0 if np.random.random() < prob_0 else 1

        # Colapso
        self.theta = 0 if result == 0 else np.pi
        self.phi = 0

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Retorna o estado atual para integração com o meta-controlador."""
        return {
            "substrato": 27,
            "material": "Diamante (C)",
            "nome": "Centro NV",
            "theta": float(self.theta),
            "phi": float(self.phi),
            "coherence_time_s": float(self.coherence_time),
            "fidelity": float(self.last_gate_fidelity),
            "temperature_k": float(self.temperature),
            "hesitation_count": int(self.hesitation_count)
        }

def inject_diamond_into_core(core):
    nv_center = NVCenter()
    if hasattr(core, 'inject_coherence'):
        core.inject_coherence(nv_center.last_gate_fidelity * 0.05)
    return nv_center

if __name__ == "__main__":
    nv = NVCenter()
    print("Estado inicial do Centro NV:")
    print(json.dumps(nv.to_dict(), indent=2))

    print("\nAplicando porta Hadamard...")
    fid = nv.apply_gate(H_GATE)
    print(f"Fidelidade: {fid:.4f}")
    print(json.dumps(nv.to_dict(), indent=2))

    print("\nMedindo...")
    res = nv.measure()
    print(f"Resultado da medição: {res}")
