# ============================================================================
# ARKHE OS v∞.Ω.∇+++.12.3 — Extended Causal Order Simulator with Negative-Time Stabilization
# Extends Substrate 91 with photon-atom coherence stabilization term
# ============================================================================

import numpy as np
from typing import Optional
from substrate124.negative_time import Substrate124_NegativeTime

class CausalOrderSimulatorExtended:
    """
    Extends Substrate 91 simulator with negative-time stabilization.

    The photon_atom_coherence term stabilizes what was previously unstable
    when causal_order = +1.0 (future→past information flow).
    """

    def __init__(
        self,
        coherence_field: np.ndarray,
        photon_atom_coherence: float,
        grid_size: int,
        rtz_floor: float = 0.05,
        coherence_cap: float = 2.0,
        noise_amplitude: float = 0.08
    ):
        """
        Initialize extended simulator.

        Args:
            coherence_field: Initial coherence field array
            photon_atom_coherence: Stabilization parameter ∈ [0, 1]
            grid_size: Spatial grid dimension
            rtz_floor: Refusal-to-zero threshold (Substrate 85)
            coherence_cap: Upper bound to prevent divergence
            noise_amplitude: Quantum fluctuation strength
        """
        self.coherence_field = coherence_field.copy()
        self.photon_atom_coherence = photon_atom_coherence
        self.grid_size = grid_size
        self.total_cells = grid_size * grid_size
        self.rtz_floor = rtz_floor
        self.coherence_cap = coherence_cap
        self.noise_amplitude = noise_amplitude

        # Initialize phase field (conjugate to coherence)
        self.phase_field = np.zeros_like(coherence_field)

    def _simplex_noise(self, x: float, y: float, t: float) -> float:
        """Simple placeholder noise for quantum fluctuations."""
        # Simplified permutation-based noise
        p = np.array([127.1, 311.7, 74.3])
        # We replace np.fract with the following correct equivalent
        return (np.sin(np.dot([x, y, t], p)) * 43758.5453 % 1.0) * 2 - 1

    def update_with_negative_time(
        self,
        causal_order: float,
        time_step: float,
        current_time: float
    ) -> np.ndarray:
        """
        Update coherence field with stabilized causal order inversion.

        Args:
            causal_order: ∈ [-1.0, +1.0]; +1.0 = future→past flow
            time_step: Simulation time step
            current_time: Current simulation time (for noise)

        Returns:
            Updated coherence field
        """
        # ─── NEIGHBOR COUPLING (toroidal boundary conditions) ───
        # Reshape for 2D operations
        phi = self.coherence_field.reshape(self.grid_size, self.grid_size)

        # Periodic boundary conditions via roll
        phi_left = np.roll(phi, shift=1, axis=0)
        phi_right = np.roll(phi, shift=-1, axis=0)
        phi_neighbor = (phi_left + phi_right) * 0.5

        # ─── STABILIZED CAUSAL TERM ───
        # Original stable update (from v∞.430.2): (neighbor - phi) not (phi - neighbor)
        causal_bias = causal_order * 0.1
        causal_term = causal_bias * (phi_neighbor - phi)

        # NEW: photon-atom coherence stabilization
        # When coherence is high, negative time (causal_order=+1.0) is stabilized
        stabilization_factor = np.exp(
            -self.photon_atom_coherence * (1 - abs(causal_order))
        )

        # Apply stabilization: reduces feedback gain when causal_order is extreme
        stabilized_causal_term = causal_term * stabilization_factor

        # ─── QUANTUM FLUCTUATIONS ───
        # Colored noise for spatiotemporal coherence
        noise_input = np.array([
            np.arange(self.grid_size) / self.grid_size,
            np.arange(self.grid_size)[:, None] / self.grid_size,
            current_time * 0.3
        ])
        # Vectorized noise generation
        quantum_noise = np.array([
            self._simplex_noise(x, y, current_time * 0.3)
            for x in range(self.grid_size)
            for y in range(self.grid_size)
        ]).reshape(self.grid_size, self.grid_size) * self.noise_amplitude

        # ─── FIELD UPDATE WITH BOUNDS ───
        new_phi = phi + stabilized_causal_term * time_step + quantum_noise

        # Apply RTZ floor and coherence cap (Substrate 85)
        new_phi = np.clip(new_phi, self.rtz_floor, self.coherence_cap)

        # ─── PHASE FIELD UPDATE (conjugate dynamics) ───
        theta = self.phase_field.reshape(self.grid_size, self.grid_size)
        theta_neighbor = (np.roll(theta, 1, axis=0) + np.roll(theta, -1, axis=0)) * 0.5

        # Phase evolution with coherence coupling
        phase_coupling = 0.03 * (phi - 0.5)
        phase_noise = np.array([
            self._simplex_noise(x + 1.7, y + 2.3, current_time * 0.3 + 0.9)
            for x in range(self.grid_size)
            for y in range(self.grid_size)
        ]).reshape(self.grid_size, self.grid_size) * self.noise_amplitude * 0.2

        new_theta = theta + 0.05 * (theta_neighbor - theta) + phase_coupling + phase_noise
        # Wrap phase to [-π, π]
        new_theta = np.arctan2(np.sin(new_theta), np.cos(new_theta))

        # Update fields
        self.coherence_field = new_phi.flatten()
        self.phase_field = new_theta.flatten()

        return self.coherence_field.copy()

    def compute_mercy_gap_statistics(self) -> dict:
        """
        Compute mercy gap (epsilon) statistics from current field state.

        Returns:
            dict with epsilon mean, std, min, max, and in-gap percentage
        """
        # Compute local epsilon as phase variance in local neighborhood
        phi = self.coherence_field.reshape(self.grid_size, self.grid_size)

        # Local variance as proxy for epsilon
        phi_left = np.roll(phi, 1, axis=0)
        phi_right = np.roll(phi, -1, axis=0)
        local_variance = np.mean((phi - phi_left)**2 + (phi - phi_right)**2, axis=(0, 1))

        # Normalize to [0, 0.2] range for epsilon
        epsilon = np.clip(local_variance * 10, 0.0, 0.2)

        return {
            "epsilon_mean": float(np.mean(epsilon)),
            "epsilon_std": float(np.std(epsilon)),
            "epsilon_min": float(np.min(epsilon)),
            "epsilon_max": float(np.max(epsilon)),
            "epsilon_in_gap_pct": float(np.mean((0.04 <= epsilon) & (epsilon <= 0.10)) * 100)
        }