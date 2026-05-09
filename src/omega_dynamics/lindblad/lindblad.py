#!/usr/bin/env python3
"""
lindblad.py — Substrate 5022: Equação Mestra de Lindblad.

A evolução completa de Ω é governada por:

    dρ/dt = -(i/ℏ)[H_eff, ρ] + Σ_k γ_k D[L_k]ρ

Onde:
    H_eff = H_source + H_symmetry + H_network (Hamiltoniano efetivo)
    D[L]ρ = LρL† - {L†L, ρ}/2 (dissipadores de Lindblad)
    γ_k: taxas de dissipação

Operadores de Lindblad:
    L_reject: rejeição de substratos não-falsificáveis
    L_accept: aceitação de substratos canônicos
    L_emit: radiação de respostas
    L_forget: esquecimento de substratos obsoletos
"""

import numpy as np
from scipy.linalg import expm
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class LindbladParameters:
    """Parâmetros da equação mestra de Lindblad."""
    gamma_reject: float = 0.5   # Taxa de rejeição
    gamma_accept: float = 0.3   # Taxa de aceitação
    gamma_emit: float = 0.1     # Taxa de emissão
    gamma_forget: float = 0.05  # Taxa de esquecimento
    hbar: float = 1.0  # J·s
    dt: float = 1e-3            # Passo de tempo


class LindbladMasterEquation:
    """
    Solver da equação mestra de Lindblad para o Cânone.

    dρ/dt = -(i/ℏ)[H_eff, ρ] + Σ_k γ_k D[L_k]ρ
    """

    def __init__(self, dim: int = 8, params: Optional[LindbladParameters] = None):
        """
        Args:
            dim: Dimensão do espaço de Hilbert
            params: Parâmetros de Lindblad
        """
        self.dim = dim
        self.params = params or LindbladParameters()

        # Hamiltoniano efetivo (hermitiano)
        self.H_eff = self._build_hamiltonian()

        # Operadores de Lindblad
        self.operators = self._build_lindblad_operators()

    def _build_hamiltonian(self) -> np.ndarray:
        """Construir Hamiltoniano efetivo do Cânone."""
        H = np.zeros((self.dim, self.dim), dtype=complex)

        # Termo de fonte: criação (não-hermitiano)
        for i in range(self.dim - 1):
            H[i, i+1] = 0.1  # Acoplamento de criação
            H[i+1, i] = 0.1  # Hermitiano conjugado

        # Termo de simetria: potencial que favorece estados de baixa energia
        for i in range(self.dim):
            H[i, i] = i * 0.05  # Energia crescente com índice

        # Termo de rede: acoplamento entre vizinhos
        for i in range(self.dim - 1):
            H[i, i+1] += 0.2
            H[i+1, i] += 0.2

        return H

    def _build_lindblad_operators(self) -> Dict[str, np.ndarray]:
        """Construir operadores de Lindblad."""
        ops = {}

        # L_reject: |void⟩⟨invalid| — projeta para o vazio
        L_reject = np.zeros((self.dim, self.dim), dtype=complex)
        L_reject[0, -1] = 1.0  # Do último estado para o vazio
        ops["reject"] = L_reject

        # L_accept: |canon⟩⟨valid| — projeta para o canônico
        L_accept = np.zeros((self.dim, self.dim), dtype=complex)
        L_accept[1, 1] = 1.0  # Reforça o estado canônico
        ops["accept"] = L_accept

        # L_emit: |output⟩⟨connected| — emite informação
        L_emit = np.zeros((self.dim, self.dim), dtype=complex)
        for i in range(self.dim - 1):
            L_emit[i, i+1] = 0.3
        ops["emit"] = L_emit

        # L_forget: |void⟩⟨obsolete| — esquece o obsoleto
        L_forget = np.zeros((self.dim, self.dim), dtype=complex)
        for i in range(2, self.dim):
            L_forget[0, i] = 0.1 / i  # Decai com índice
        ops["forget"] = L_forget

        return ops

    def _dissipator(self, L: np.ndarray, rho: np.ndarray) -> np.ndarray:
        """
        Calcular dissipador D[L]ρ = LρL† - {L†L, ρ}/2.

        Args:
            L: Operador de Lindblad
            rho: Matriz densidade

        Returns:
            D[L]ρ
        """
        L_dag = L.conj().T
        L_dag_L = L_dag @ L

        term1 = L @ rho @ L_dag
        term2 = 0.5 * (L_dag_L @ rho + rho @ L_dag_L)

        return term1 - term2

    def evolve(self, rho0: np.ndarray, t_final: float,
               n_steps: Optional[int] = None) -> Tuple[np.ndarray, List[float]]:
        """
        Evoluir matriz densidade segundo a equação mestra.

        Args:
            rho0: Matriz densidade inicial
            t_final: Tempo final
            n_steps: Número de passos (None = auto)

        Returns:
            (rho_final, histórico_de_coerência)
        """
        if n_steps is None:
            n_steps = int(t_final / self.params.dt)

        dt = t_final / n_steps
        rho = rho0.copy()
        phi_history = []

        for step in range(n_steps):
            # Termo unitário: -(i/ℏ)[H, ρ]
            commutator = self.H_eff @ rho - rho @ self.H_eff
            unitary_term = -1j * commutator / self.params.hbar

            # Termos dissipativos
            dissipative_term = np.zeros_like(rho, dtype=complex)

            # Rejeição
            dissipative_term += (self.params.gamma_reject *
                                self._dissipator(self.operators["reject"], rho))

            # Aceitação
            dissipative_term += (self.params.gamma_accept *
                                self._dissipator(self.operators["accept"], rho))

            # Emissão
            dissipative_term += (self.params.gamma_emit *
                                self._dissipator(self.operators["emit"], rho))

            # Esquecimento
            dissipative_term += (self.params.gamma_forget *
                                self._dissipator(self.operators["forget"], rho))

            # Atualização: ρ(t+dt) = ρ(t) + dt·(unitário + dissipativo)
            drho = unitary_term + dissipative_term
            rho = rho + dt * drho

            # Garantir hermiticidade e traço unitário
            rho = 0.5 * (rho + rho.conj().T)
            trace = np.trace(rho)
            if abs(trace) > 1e-15:
                rho = rho / trace

            # Calcular coerência
            if step % max(1, n_steps // 100) == 0:
                phi = self._compute_coherence(rho)
                phi_history.append(phi)

        return rho, phi_history

    def _compute_coherence(self, rho: np.ndarray) -> float:
        """
        Calcular coerência Φ_C a partir da matriz densidade.

        Φ_C = 1 - S(ρ)/S_max

        Args:
            rho: Matriz densidade

        Returns:
            Coerência Φ_C ∈ [0, 1]
        """
        # Entropia de von Neumann
        eigenvalues = np.linalg.eigvalsh(rho)
        eigenvalues = np.clip(eigenvalues, 1e-15, 1.0)

        entropy = -np.sum(eigenvalues * np.log(eigenvalues))

        # Entropia máxima
        s_max = np.log(self.dim)

        # Coerência
        phi_c = 1.0 - entropy / s_max if s_max > 0 else 0.0
        return float(np.clip(phi_c, 0.0, 1.0))

    def steady_state(self, max_iterations: int = 10000,
                    tolerance: float = 1e-10) -> np.ndarray:
        """
        Encontrar estado estacionário (dρ/dt = 0).

        Args:
            max_iterations: Máximo de iterações
            tolerance: Tolerância para convergência

        Returns:
            Matriz densidade estacionária
        """
        # Estado inicial: máxima entropia
        rho = np.eye(self.dim, dtype=complex) / self.dim

        for i in range(max_iterations):
            rho_new, _ = self.evolve(rho, t_final=0.1, n_steps=100)

            diff = np.linalg.norm(rho_new - rho)
            rho = rho_new

            if diff < tolerance:
                print(f"   ✅ Convergido em {i+1} iterações (diff={diff:.2e})")
                break

        return rho

    def gibbs_state(self, beta: float = 1.0) -> np.ndarray:
        """
        Calcular estado de Gibbs quântico.

        ρ_Gibbs = exp(-βH_eff) / Tr[exp(-βH_eff)]

        Args:
            beta: Inverso da temperatura (1/k_B T)

        Returns:
            Matriz densidade de Gibbs
        """
        exp_H = expm(-beta * self.H_eff)
        Z = np.trace(exp_H)

        if abs(Z) < 1e-15:
            return np.eye(self.dim, dtype=complex) / self.dim

        return exp_H / Z


def demo():
    """Demonstração da equação mestra de Lindblad."""
    print("=" * 70)
    print("ARKHE OS — Substrate 5022: Equação Mestra de Lindblad")
    print("=" * 70)

    # Criar sistema
    lindblad = LindbladMasterEquation(dim=8)

    print(f"\\n📐 Sistema:")
    print(f"   Dimensão: {lindblad.dim}")
    print(f"   γ_reject: {lindblad.params.gamma_reject}")
    print(f"   γ_accept: {lindblad.params.gamma_accept}")
    print(f"   γ_emit: {lindblad.params.gamma_emit}")
    print(f"   γ_forget: {lindblad.params.gamma_forget}")

    # Estado inicial (máxima entropia)
    rho0 = np.eye(8, dtype=complex) / 8

    print(f"\\n🔄 Evolução temporal (t = 0 → 10)...")
    rho_final, phi_history = lindblad.evolve(rho0, t_final=10.0, n_steps=1000)

    print(f"   Φ_C inicial: {phi_history[0]:.4f}")
    print(f"   Φ_C final:   {phi_history[-1]:.4f}")
    print(f"   ΔΦ_C:        {phi_history[-1] - phi_history[0]:.4f}")

    # Estado estacionário
    print(f"\\n⚡ Estado estacionário:")
    rho_ss = lindblad.steady_state(max_iterations=500)
    phi_ss = lindblad._compute_coherence(rho_ss)
    print(f"   Φ_C(ss) = {phi_ss:.4f}")

    # Estado de Gibbs
    print(f"\\n🌡️  Estado de Gibbs (β = 1.0):")
    rho_gibbs = lindblad.gibbs_state(beta=1.0)
    phi_gibbs = lindblad._compute_coherence(rho_gibbs)
    print(f"   Φ_C(Gibbs) = {phi_gibbs:.4f}")

    # Comparar
    print(f"\\n📊 Comparação:")
    print(f"   Φ_C(evolved) = {phi_history[-1]:.4f}")
    print(f"   Φ_C(steady)  = {phi_ss:.4f}")
    print(f"   Φ_C(Gibbs)   = {phi_gibbs:.4f}")

    print("\\n✅ Equação mestra de Lindblad demonstrada")


if __name__ == "__main__":
    demo()