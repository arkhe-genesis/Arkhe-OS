# ============================================================================
# ARKHE OS v∞.Ω.∇+++.13 — Substrate 125: Projected Lorentz-Contortion Dynamics
# Purpose: Covariant momentum balance with torsion response and chronometric modulation
# ============================================================================

import numpy as np
from typing import Tuple, Callable
from dataclasses import dataclass

@dataclass
class ContortionTensor:
    """
    Rank-(1,1) Lorentz response tensor K^μ_ν.
    16 components, decomposed into trace, antisymmetric, traceless symmetric.
    """
    components: np.ndarray  # Shape (4,4)

    def __post_init__(self):
        assert self.components.shape == (4, 4), "Contortion must be 4x4"
        self.trace = np.trace(self.components)
        self.antisymmetric = 0.5 * (self.components - self.components.T)
        self.symmetric_traceless = 0.5 * (self.components + self.components.T) - (self.trace / 4) * np.eye(4)

class ProjectedLorentzContortion:
    """
    Implements: Dp^μ/dτ = P^μ_α(u)[F_ext^α + K^α_β θ_Δ(τ) u^β]
    Preserves rest mass exactly via orthogonal projector.
    """

    def __init__(
        self,
        contortion: ContortionTensor,
        chronometric_phase_fn: Callable[[float], float],
        c: float = 299792458.0
    ):
        self.K = contortion.components
        self.theta = chronometric_phase_fn
        self.c = c
        self.c2 = c**2

    def projector(self, u: np.ndarray) -> np.ndarray:
        """
        P^μ_α = δ^μ_α - u^μ u_α / c²
        Guarantees u_μ P^μ_α = 0
        """
        # u_α = η_αβ u^β (Minkowski metric signature +---)
        eta = np.diag([1, -1, -1, -1])
        u_lower = eta @ u
        P = np.eye(4) - np.outer(u, u_lower) / self.c2
        return P

    def compute_acceleration(
        self,
        u: np.ndarray,
        p: np.ndarray,
        F_ext: np.ndarray,
        tau: float,
        dt: float = 1e-3
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute covariant derivative Dp^μ/dτ and update p^μ.

        Returns:
            (dp_dtau, p_new)
        """
        # Validate u·u = c²
        eta = np.diag([1, -1, -1, -1])
        u_norm = u @ eta @ u
        assert np.abs(u_norm - self.c2) < 1e-4 * self.c2, "Four-velocity not normalized"

        # Chronometric phase
        theta_tau = self.theta(tau)

        # Contortion coupling term: K^α_β θ_Δ(τ) u^β
        contortion_term = self.K @ (theta_tau * u)

        # Total unprojected force
        F_total = F_ext + contortion_term

        # Project onto subspace orthogonal to u
        P = self.projector(u)
        dp_dtau = P @ F_total

        # Update momentum (Euler step; higher-order RK4 recommended for production)
        p_new = p + dp_dtau * dt

        # Re-normalize to preserve mass exactly (numerical drift correction)
        # p_new = m u_new; enforce u_new·u_new = c²
        p_norm = np.sqrt(np.abs(p_new @ eta @ p_new))
        m = p_norm / self.c
        p_new = (p / m) * self.c  # Project back to mass shell

        return dp_dtau, p_new

    def verify_mass_preservation(self, u: np.ndarray, p: np.ndarray) -> bool:
        """
        Verify that projector guarantees dp·u = 0 → dm/dτ = 0
        """
        eta = np.diag([1, -1, -1, -1])
        dp_dtau, _ = self.compute_acceleration(u, p, np.zeros(4), 0.0)
        u_lower = eta @ u
        return np.abs(u_lower @ dp_dtau) < 1e-12

# Example: Chronometric phase locked to λ_Δ = 3722/2705
def chronometric_phase_tau(tau: float, lambda_delta: float = 3722/2705, tau0: float = 1.0) -> float:
    return np.sin(lambda_delta * tau / tau0)

# Usage:
# K = ContortionTensor(np.random.randn(4,4) * 1e-15)  # Small torsion coupling
# dyn = ProjectedLorentzContortion(K, chronometric_phase_tau)
# dp_dtau, p_new = dyn.compute_acceleration(u, p, F_ext, tau=0.0, dt=1e-6)
