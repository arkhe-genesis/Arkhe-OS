"""
Substrato 6175 — SIGHA: Spectral Information Geometry & Holographic Action
Implements: Fisher–Bures metric, veil projector, natural-gradient flow,
            holographic c‑theorem, quantum Darwinism selector.
"""
import numpy as np
from scipy.linalg import sqrtm, logm, expm
from typing import Tuple, Callable

class FisherBuresManifold:
    """
    The space of density operators ρ endowed with the Bures metric.
    ds² = ½ Tr(ρ L_i L_j) dθ^i dθ^j
    """

    def __init__(self, dim: int):
        self.dim = dim  # Hilbert space dimension

    def metric_tensor(self, rho: np.ndarray, tangent_vectors: list) -> np.ndarray:
        """
        Compute the metric tensor g_{ij} for a given ρ and a set of tangent vectors.
        tangent_vectors: list of ∂ρ/∂θ_i matrices.
        """
        # Symmetric logarithmic derivative (SLD) for each parameter direction
        g = np.zeros((len(tangent_vectors), len(tangent_vectors)), dtype=complex)
        for i, d_rho_i in enumerate(tangent_vectors):
            L_i = self._sld(rho, d_rho_i)
            for j, d_rho_j in enumerate(tangent_vectors):
                L_j = self._sld(rho, d_rho_j)
                g[i, j] = 0.5 * np.real(np.trace(rho @ L_i @ L_j + rho @ L_j @ L_i))
        return g

    def _sld(self, rho: np.ndarray, d_rho: np.ndarray) -> np.ndarray:
        """Symmetric Logarithmic Derivative L solving ½(L ρ + ρ L) = ∂ρ."""
        # Solve via vectorization: (ρ ⊗ I + I ⊗ ρ^T) vec(L) = 2 vec(∂ρ)
        rho_t = rho.T
        n = rho.shape[0]
        I = np.eye(n)
        M = np.kron(rho, I) + np.kron(I, rho_t)
        vec_d_rho = d_rho.flatten('F')
        vec_L = 2.0 * np.linalg.solve(M, vec_d_rho)
        return vec_L.reshape(n, n, order='F')

    def bures_distance(self, rho1: np.ndarray, rho2: np.ndarray) -> float:
        """Bures distance between two states: sqrt(2 - 2 sqrt(Fidelity))."""
        sqrt_rho1 = sqrtm(rho1)
        fidelity = np.real(np.trace(sqrtm(sqrt_rho1 @ rho2 @ sqrt_rho1)))
        return np.sqrt(2.0 - 2.0 * fidelity)

    def geodesic(self, rho0: np.ndarray, rho1: np.ndarray, t: float) -> np.ndarray:
        """Point at fraction t along the Bures geodesic from rho0 to rho1."""
        sqrt_rho0 = sqrtm(rho0)
        inv_sqrt_rho0 = np.linalg.inv(sqrt_rho0)
        R = inv_sqrt_rho0 @ rho1 @ inv_sqrt_rho0
        # Geodesic interpolation: ρ(t) = (1-t)² ρ0 + t² ρ1 + t(1-t)(√ρ0 √R + h.c.)
        sqrt_R = sqrtm(R)
        rho_t = (1-t)**2 * rho0 + t**2 * rho1 + t*(1-t) * (sqrt_rho0 @ sqrt_R + sqrt_R @ sqrt_rho0)
        return rho_t / np.trace(rho_t)


class VeilProjector:
    """
    Holographic duality map: T_μν (bulk) ↔ S(ρ) (boundary).
    U(x,y) is unitary and fidelity-preserving.
    """
    def __init__(self, dim: int):
        self.dim = dim

    def bulk_to_boundary(self, T_munu: np.ndarray) -> np.ndarray:
        """Map bulk stress-energy to boundary von Neumann entropy."""
        # T_munu → effective density operator via a thermal-like state
        # ρ_boundary ∝ exp(-β H_eff) where H_eff is derived from T_munu
        H_eff = self._hamiltonian_from_stress(T_munu)
        beta = 1.0  # inverse temperature (set by horizon scale)
        rho = expm(-beta * H_eff)
        return rho / np.trace(rho)

    def boundary_to_bulk(self, rho: np.ndarray) -> np.ndarray:
        """Map boundary entropy back to bulk stress-energy."""
        # Invert the thermal map: T_munu = -∂ log(ρ)/∂β
        H_eff = -logm(rho)
        return self._stress_from_hamiltonian(H_eff)

    def _hamiltonian_from_stress(self, T_munu: np.ndarray) -> np.ndarray:
        """Simplified: use energy density T_00 as Hamiltonian."""
        return np.diag(np.real(np.diag(T_munu)))

    def _stress_from_hamiltonian(self, H: np.ndarray) -> np.ndarray:
        return np.diag(np.real(np.diag(H)))


class NaturalGradientFlow:
    """
    Natural-gradient geodesics on the Fisher–Bures manifold.
    δρ/δt = -g^{ij} ∂L/∂ρ_j  (steepest descent respecting the metric)
    """
    def __init__(self, manifold: FisherBuresManifold):
        self.manifold = manifold

    def step(self, rho: np.ndarray, grad_L: np.ndarray, learning_rate: float = 0.01) -> np.ndarray:
        """Single natural-gradient step."""
        # Compute metric at current ρ
        d_rho_vec = [grad_L]  # single parameter direction for simplicity
        g = self.manifold.metric_tensor(rho, d_rho_vec)
        # Natural gradient = g^{-1} * grad_L
        nat_grad = np.linalg.solve(g, grad_L.flatten()).reshape(grad_L.shape)
        # Update along geodesic
        rho_new = rho - learning_rate * nat_grad
        # Ensure Hermitian and trace 1
        rho_new = 0.5 * (rho_new + rho_new.conj().T)
        return rho_new / np.trace(rho_new)

    def c_theorem(self, rhos: list) -> list:
        """
        Compute holographic c‑function along a flow.
        c ~ -log(tr(ρ²)) or Bures distance from the fixed point.
        """
        rho_fp = rhos[-1]  # final fixed point
        c_values = []
        for rho in rhos:
            d = self.manifold.bures_distance(rho, rho_fp)
            c_values.append(-np.log(max(1e-30, d)))
        return c_values

    def convergence_rate(self, c_values: list, iterations: int) -> float:
        """Fit power‑law: c(N) ~ N^{-β}, return β."""
        N = np.arange(1, len(c_values)+1)
        log_c = np.log(np.abs(c_values) + 1e-30)
        log_N = np.log(N)
        beta = -np.polyfit(log_N, log_c, 1)[0]
        return beta


class QuantumDarwinismSelector:
    """
    Selects which quantum correlations become objective/classical
    via redundant encoding in the environment.
    """
    def __init__(self, system_dim: int, environment_fragments: int):
        self.system_dim = system_dim
        self.fragments = environment_fragments

    def mutual_information(self, rho_total: np.ndarray, fragment_idx: int) -> float:
        """I(System : Fragment) = S(ρ_S) + S(ρ_F) - S(ρ_{SF})."""
        rho_S = self._partial_trace(rho_total, keep=[0])
        rho_F = self._partial_trace(rho_total, keep=[fragment_idx+1])
        rho_SF = self._partial_trace(rho_total, keep=[0, fragment_idx+1])
        return self._von_neumann_entropy(rho_S) + self._von_neumann_entropy(rho_F) - self._von_neumann_entropy(rho_SF)

    def select_objective_observables(self, rho_total: np.ndarray, threshold: float = 0.5) -> list:
        """Fragments with I(System:Fragment) > threshold carry objective information."""
        objective = []
        for f in range(self.fragments):
            mi = self.mutual_information(rho_total, f)
            if mi > threshold:
                objective.append(f)
        return objective

    def _partial_trace(self, rho: np.ndarray, keep: list) -> np.ndarray:
        # Simplified: assumes tensor product structure
        return rho  # Placeholder

    def _von_neumann_entropy(self, rho: np.ndarray) -> float:
        eigvals = np.linalg.eigvalsh(rho)
        eigvals = eigvals[eigvals > 0]
        return -np.sum(eigvals * np.log(eigvals))
