import numpy as np
from typing import Dict, Any, List

class BiophotonCoherenceSensor:
    """
    Sensor de coerência neural via detecção de biophotons.
    Mede λ₂ do cérebro através de emissão óptica ultra-fraca (UPE).
    """

    def __init__(self,
                 wavelength_range=(400, 800),  # nm
                 integration_time=30,          # segundos
                 dark_count_rate=50):          # counts/s
        self.wl_range = wavelength_range
        self.t_int = integration_time
        self.dark_count = dark_count_rate
        self.qe = 0.4  # Eficiência quântica

    def measure_coherence(self,
                          photon_counts: np.ndarray,
                          time_series: np.ndarray) -> Dict[str, Any]:
        """
        Calcula λ₂ a partir de estatísticas de contagem de fótons.
        """
        # 1. Intensidade total
        total_counts = np.sum(photon_counts)
        intensity = total_counts / (self.t_int + 1e-10)

        # 2. Coerência temporal: g2(0)
        # Poisson (Coerente): g2=1. Térmico: g2=2. Sub-Poisson (Super-radiante): g2<1
        mean_c = np.mean(photon_counts)
        var_c = np.var(photon_counts)
        if mean_c > 0:
            g2_0 = 1.0 + (var_c - mean_c) / (mean_c**2 + 1e-10)
        else:
            g2_0 = 2.0

        coherence_indicator = float(np.clip(2.0 - g2_0, 0, 1.5))

        # 3. Combined λ₂
        lambda2 = 0.7 * (coherence_indicator / 1.5) + 0.3 * (intensity / 1000.0)
        lambda2 = float(np.clip(lambda2, 0, 1))

        return {
            'lambda2_biophoton': lambda2,
            'intensity': float(intensity),
            'g2_zero': float(g2_0),
            'status': self._classify_state(lambda2)
        }

    def _classify_state(self, lambda2: float) -> str:
        if lambda2 < 0.2: return "INCOHERENT_THERMAL"
        if lambda2 < 0.5: return "WEAK_COHERENCE"
        if lambda2 < 0.9: return "STRONG_COHERENCE"
        return "SUPER_RADIANCE_TZINOR"
