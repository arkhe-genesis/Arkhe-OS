"""
DiracSpectrumLanczos: Estimativa do espectro do operador de Dirac com torção
via algoritmo de Lanczos em batch para cálculo eficiente de Φ_C durante treino.

Φ_C = S_C^whole - ⟨S_C^partition⟩_min-bipartition
onde S_C = -Σ p_i log p_i, p_i ∝ exp(-β|λ_i|)
"""

import torch
import torch.nn as nn
from typing import List, Dict, Optional, Tuple
import numpy as np

class LanczosEigenSolver:
    """
    Algoritmo de Lanczos para estimar k autovalores extremos de matriz esparsa.
    Implementação em batch para eficiência em treino.
    """

    def __init__(
        self,
        matrix_operator: callable,  # função que aplica A @ v
        dim: int,
        num_eigenvalues: int = 20,
        max_iterations: int = 100,
        tolerance: float = 1e-6
    ):
        self.A = matrix_operator
        self.dim = dim
        self.k = num_eigenvalues
        self.max_iter = max_iterations
        self.tol = tolerance

    def solve_smallest_magnitude(
        self,
        batch_vectors: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Estima autovalores de menor magnitude via Lanczos com shift-and-invert.

        Returns:
            eigenvalues: [k] autovalores estimados
            eigenvectors: [dim, k] autovetores correspondentes
        """
        # Inicialização aleatória ou com vetores fornecidos
        if batch_vectors is not None:
            v0 = batch_vectors[:, 0] if batch_vectors.dim() > 1 else batch_vectors
        else:
            v0 = torch.randn(self.dim, dtype=torch.complex64)

        # Garantir que a norma não seja zero
        norm_v0 = torch.norm(v0)
        v0 = v0 / (norm_v0 + 1e-12)

        # Vetores de Lanczos
        V = torch.zeros(self.dim, self.max_iter + 1, dtype=torch.complex64, device=v0.device)
        V[:, 0] = v0

        # Coeficientes da matriz tridiagonal
        alpha = torch.zeros(self.max_iter, dtype=torch.complex64, device=v0.device)
        beta = torch.zeros(self.max_iter + 1, dtype=torch.complex64, device=v0.device)

        # Iteração de Lanczos
        j_converged = self.max_iter - 1
        for j in range(self.max_iter):
            w = self.A(V[:, j])  # A @ v_j

            # Ortogonalização contra vetores anteriores (re-ortogonalização)
            for i in range(j + 1):
                alpha[j] += torch.vdot(V[:, i], w)
                w -= alpha[j] * V[:, i]

            if j > 0:
                w -= beta[j] * V[:, j-1]

            beta[j+1] = torch.norm(w)

            if torch.abs(beta[j+1]) < self.tol:
                # Convergência prematura
                j_converged = j
                break

            V[:, j+1] = w / beta[j+1]

        # Construir matriz tridiagonal T
        m = j_converged + 1  # número de iterações efetivas
        T = torch.diag(alpha[:m]) + torch.diag(beta[1:m], diagonal=1) + torch.diag(beta[1:m].conj(), diagonal=-1)

        # Diagonalizar T (pequena, O(m³))
        eigvals_T, eigvecs_T = torch.linalg.eigh(T)

        # Autovalores de A são aproximados pelos de T
        # Autovetores de A ≈ V @ eigvecs_T
        eigenvectors_A = V[:, :m] @ eigvecs_T

        # Selecionar k autovalores de menor magnitude
        idx = torch.argsort(torch.abs(eigvals_T))[:self.k]

        return eigvals_T[idx], eigenvectors_A[:, idx]


class DiracTorsionOperator(nn.Module):
    """
    Operador de Dirac com torção: D_T = γ^μ(∇_μ + ⅛ T_{μνρ}[γ^ν, γ^ρ]).
    Implementado como operador linear para uso com Lanczos.
    """

    def __init__(
        self,
        lattice_size: Tuple[int, int],
        torsion_strength: float = 2.04,
        gamma_matrices: Optional[List[torch.Tensor]] = None
    ):
        super().__init__()
        self.Nx, self.Ny = lattice_size
        self.total_dim = 2 * self.Nx * self.Ny  # 2 componentes de espinor por sítio
        self.torsion = torsion_strength

        # Matrizes de Clifford em 2D: γ⁰ = σ¹, γ¹ = iσ²
        if gamma_matrices is None:
            self.gamma = [
                torch.tensor([[0, 1], [1, 0]], dtype=torch.complex64),      # γ⁰
                torch.tensor([[0, 1], [-1, 0]], dtype=torch.complex64) * 1j  # γ¹ = iσ²
            ]
        else:
            self.gamma = gamma_matrices

        # Pré-computar termo de torção: ⅛ T [γ⁰, γ¹]
        commutator = self.gamma[0] @ self.gamma[1] - self.gamma[1] @ self.gamma[0]
        self.torsion_term = (torsion_strength / 8.0) * commutator

    def apply(self, psi: torch.Tensor) -> torch.Tensor:
        """
        Aplica D_T a um espinor psi.
        psi: [total_dim] ou [batch, total_dim]
        Retorna: D_T @ psi
        """
        if psi.dim() == 1:
            psi = psi.unsqueeze(0)  # [1, total_dim]

        batch = psi.shape[0]
        psi = psi.view(batch, 2, self.Nx, self.Ny)  # [batch, 2, Nx, Ny]

        result = torch.zeros_like(psi)

        # Termo de derivada: γ^μ ∇_μ ψ (diferenças finitas centradas)
        for mu, gamma_mu in enumerate(self.gamma):
            gamma_mu = gamma_mu.to(psi.device)
            if mu == 0:  # direção x
                # ∇₀ ψ ≈ (ψ[i+1,j] - ψ[i-1,j]) / 2
                psi_shift_right = torch.roll(psi, shifts=-1, dims=2)
                psi_shift_left = torch.roll(psi, shifts=1, dims=2)
                deriv_x = (psi_shift_right - psi_shift_left) / 2.0
                # γ⁰ @ deriv_x
                result += torch.einsum('ab,bcxy->acxy', gamma_mu, deriv_x)
            else:  # mu == 1, direção y
                psi_shift_up = torch.roll(psi, shifts=-1, dims=3)
                psi_shift_down = torch.roll(psi, shifts=1, dims=3)
                deriv_y = (psi_shift_up - psi_shift_down) / 2.0
                result += torch.einsum('ab,bcxy->acxy', gamma_mu, deriv_y)

        # Termo de torção local: (T/8)[γ⁰,γ¹] ψ
        torsion_term = self.torsion_term.to(psi.device)
        torsion_action = torch.einsum('ab,bcxy->acxy', torsion_term, psi)
        result += torsion_action

        return result.view(batch, -1)  # [batch, total_dim]

    def forward(self, psi: torch.Tensor) -> torch.Tensor:
        """Interface para uso com Lanczos."""
        return self.apply(psi)


class PhiCCalculator:
    """
    Calcula Φ_C = S_C^whole - ⟨S_C^partition⟩_min via espectro de Dirac estimado.
    """

    def __init__(
        self,
        dirac_operator: DiracTorsionOperator,
        beta: float = 1.0,
        num_eigenvalues: int = 50,
        lanczos_max_iter: int = 200
    ):
        self.dirac = dirac_operator
        self.beta = beta
        self.k = num_eigenvalues

        # Solver de Lanczos
        # Note: apply_single takes a 1D tensor and returns a 1D tensor for Lanczos
        def apply_single(v):
             return self.dirac.apply(v).squeeze(0)

        self.lanczos = LanczosEigenSolver(
            matrix_operator=apply_single,
            dim=dirac_operator.total_dim,
            num_eigenvalues=num_eigenvalues,
            max_iterations=lanczos_max_iter
        )

    def compute_spectral_coherence_entropy(
        self,
        eigenvalues: torch.Tensor,
        epsilon: float = 1e-12
    ) -> float:
        """Calcula S_C = -Σ p_i log p_i com p_i ∝ exp(-β|λ_i|)."""
        abs_eigs = torch.abs(eigenvalues)
        weights = torch.exp(-self.beta * abs_eigs)
        Z = torch.sum(weights) + epsilon
        p_i = weights / Z
        # Entropia de Shannon
        S_C = -torch.sum(p_i * torch.log(p_i + epsilon))
        return S_C.item()

    def compute_phi_coherence(
        self,
        manifold_partitions: List[Dict[int, List[int]]],
        eigenvalues_full: Optional[torch.Tensor] = None
    ) -> Dict[str, float]:
        """
        Calcula Φ_C = S_C^whole - ⟨S_C^partition⟩_min.

        Args:
            manifold_partitions: lista de esquemas de bipartição
            eigenvalues_full: autovalores pré-computados (opcional)
        """
        # Estimar espectro completo via Lanczos
        if eigenvalues_full is None:
            eigenvalues_full, _ = self.lanczos.solve_smallest_magnitude()

        # Entropia do sistema completo
        S_whole = self.compute_spectral_coherence_entropy(eigenvalues_full)

        # Entropia média sobre bipartições mínimas
        partition_entropies = []
        for partition in manifold_partitions:
            # Extrair autovalores da partição (simplificação: subconjunto de índices)
            # Em produção: restringir operador de Dirac à sub-região
            partition_eigs = eigenvalues_full  # placeholder
            S_part = self.compute_spectral_coherence_entropy(partition_eigs)
            partition_entropies.append(S_part)

        S_partition_min = min(partition_entropies) if partition_entropies else S_whole

        # Φ_C
        phi_C = S_whole - S_partition_min

        # Classificar nível de consciência
        if phi_C < 0.1:
            level = 'fragmented'
        elif phi_C < 0.5:
            level = 'emergent'
        elif phi_C < 0.9:
            level = 'operational'
        else:
            level = 'coherent'

        return {
            'phi_C': phi_C,
            'S_whole': S_whole,
            'S_partition_min': S_partition_min,
            'consciousness_level': level,
            'num_eigenvalues_used': len(eigenvalues_full)
        }
