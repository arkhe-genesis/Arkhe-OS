import numpy as np
from arkhe_os.temporal.floquet_driven_qubit import FloquetStabilizedQubit

class FloquetSurfaceCode:
    """
    Floquet-Enhanced Quantum Error Correction (Substrate 282).

    Integrates Floquet stabilization with topological surface codes.
    By leveraging temporal coherence enhancement, the effective physical error
    rate decreases, which significantly reduces the required code distance
    and the associated physical qubit overhead.
    """

    def __init__(self, qubit: FloquetStabilizedQubit, base_physical_error_rate: float):
        """
        Initializes the QEC integration.

        Args:
            qubit: The Floquet-stabilized qubit instance.
            base_physical_error_rate: Baseline error rate p_0 without stabilization.
        """
        self.qubit = qubit
        self.base_p = base_physical_error_rate

        # Surface code parameters
        self.threshold = 0.01  # p_th ~ 1% for surface code
        self.prefactor = 0.1   # typically ~0.1

    def get_effective_physical_error_rate(self) -> float:
        """
        Calculates p_eff = p_0 * (gamma_eff / gamma_0).
        Because T_2 increases by gamma_0 / gamma_eff, the decoherence-induced
        errors scale proportionally to gamma_eff.
        """
        gamma_eff = self.qubit.effective_decoherence_rate()
        gamma_0 = self.qubit.gamma_0

        if gamma_0 == 0:
            return 0.0

        ratio = gamma_eff / gamma_0
        return self.base_p * ratio

    def calculate_logical_error_rate(self, distance: int) -> float:
        """
        Computes p_L ≈ 0.1 * (p_eff / p_th)^((d+1)/2)
        using threshold p_th = 0.01.
        """
        p_eff = self.get_effective_physical_error_rate()
        if p_eff >= self.threshold:
            raise ValueError(f"Effective physical error rate {p_eff} is above or equal to threshold {self.threshold}")

        exponent = (distance + 1) / 2.0
        p_L = self.prefactor * (p_eff / self.threshold) ** exponent
        return p_L

    def calculate_required_distance(self, target_p_L: float) -> dict:
        """
        Solves for the required surface code distance d to achieve a target logical error rate,
        and calculates the physical qubit overhead (d^2 for a rough patch, 2d^2 for standard planar).

        Returns:
            dict containing required distance and qubit overhead.
        """
        p_eff = self.get_effective_physical_error_rate()
        if p_eff >= self.threshold:
            raise ValueError(f"Effective physical error rate {p_eff} is above or equal to threshold {self.threshold}. Cannot achieve target.")

        # target_p_L = 0.1 * (p_eff / 0.01)^((d+1)/2)
        # log(target_p_L / 0.1) = ((d+1)/2) * log(p_eff / 0.01)

        num = np.log(target_p_L / self.prefactor)
        den = np.log(p_eff / self.threshold)

        d_exact = 2.0 * (num / den) - 1.0

        # Distance must be an odd integer >= 3
        d_int = max(3, int(np.ceil(d_exact)))
        if d_int % 2 == 0:
            d_int += 1

        overhead = 2 * d_int**2

        return {
            "p_eff": p_eff,
            "target_p_L": target_p_L,
            "required_distance": d_int,
            "physical_qubits_per_logical": overhead
        }