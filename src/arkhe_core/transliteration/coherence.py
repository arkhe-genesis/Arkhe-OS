import numpy as np
import hashlib
from typing import Tuple
from .dependencies import K6O_Cathedral

class CoherenceViolation(Exception):
    """Lançado quando a Lei da Coerência é violada."""
    pass

class CoherenceEnforcer:
    """
    Garante que toda transliteração preserve a fase interna (Lei Segunda).
    """

    def __init__(self, k6o_network: K6O_Cathedral):
        self.k6o = k6o_network
        self.K_c = 0.1

    def transliterate(self, state: np.ndarray, source_phase: float,
                      target_substrate: str) -> Tuple[np.ndarray, float]:
        """
        Transfere estado mantendo coerência de fase.
        """
        r_global = self.k6o.measure_global_order()
        K = self.k6o.mean_coupling()
        r_critical = (2 / np.pi) * np.arctan(K / self.K_c) if self.K_c > 0 else 1.0

        if r_global < r_critical:
             raise CoherenceViolation(f"Sistema em decoerência global: r={r_global:.4f} < r_crit={r_critical:.4f}")

        max_noise = np.sqrt(max(0, (1 - r_global) / 2))
        rotor_angle = self._generate_rotor_angle(target_substrate)

        phase_error = np.random.normal(0, max_noise * 0.1) if max_noise > 0 else 0
        target_phase = (source_phase + rotor_angle + phase_error) % (2 * np.pi)

        actual_shift = (target_phase - source_phase) % (2 * np.pi)
        coherence = np.abs(np.exp(1j * (actual_shift - rotor_angle)))

        if coherence < 0.95:
            raise CoherenceViolation(f"Erro de fase local excessivo: {coherence:.4f}")

        return state, target_phase

    def _generate_rotor_angle(self, substrate_id: str) -> float:
        """Gera ângulo de rotação unitária determinística por substrato."""
        hash_val = int(hashlib.sha256(substrate_id.encode()).hexdigest(), 16)
        return (hash_val % (2**32)) / (2**32) * 2 * np.pi
