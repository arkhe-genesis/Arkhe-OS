import numpy as np
from typing import Dict, Any

class BiophotonCoherenceSensor:
    """
    Sensor de coerência neural via detecção de biophotons.
    Mede λ₂ do cérebro através de emissão óptica ultra-fraca (UPE).
    """

    def __init__(self,
                 wavelength_range=(400, 800),  # nm
                 integration_time=30,          # segundos
                 dark_count_rate=50):          # counts/s
        """
        Inicializa sensor de fotocontagem de alta sensibilidade.
        """
        self.wl_range = wavelength_range
        self.t_int = integration_time
        self.dark_count = dark_count_rate
        self.qe = 0.4  # Eficiência quântica 40%

    def measure_coherence(self,
                          photon_counts: np.ndarray,
                          time_series: np.ndarray) -> Dict[str, Any]:
        """
        Calcula λ₂ a partir de estatísticas de contagem de fótons.

        Args:
            photon_counts: Array de contagens de fótons por bin temporal
            time_series: Tempos de aquisição (s)
        """
        # 1. Intensidade total
        total_counts = np.sum(photon_counts)
        intensity = total_counts / self.t_int

        # 2. Coerência temporal: função de correlação g^(2)(τ)
        g2 = self._compute_g2_correlation(photon_counts)

        # Coerência laser-like: g^(2)(0) < 1 (sub-Poissonian)
        # Coerência térmica: g^(2)(0) = 2 (Bose-Einstein)
        coherence_indicator = 2 - g2[0] if len(g2) > 0 else 0.0

        # 3. Coerência espectral (largura de linha mock)
        spectral_width = 5.0 # nm
        spectral_coherence = 100 / spectral_width

        # 4. λ₂ combinado
        lambda2 = (coherence_indicator * 0.5 +
                   np.clip(spectral_coherence / 20, 0, 1) * 0.3 +
                   np.clip(intensity / 1000, 0, 1) * 0.2)

        return {
            'lambda2_biophoton': float(np.clip(lambda2, 0, 1)),
            'intensity': float(intensity),
            'g2_zero': float(g2[0]) if len(g2) > 0 else 2.0,
            'state': self._classify_state(lambda2)
        }

    def _compute_g2_correlation(self, counts: np.ndarray) -> np.ndarray:
        if len(counts) < 2: return np.array([2.0])
        counts_norm = counts - np.mean(counts)
        autocorr = np.correlate(counts_norm, counts_norm, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        return autocorr / autocorr[0] if autocorr[0] > 0 else np.array([2.0])

    def _classify_state(self, lambda2: float) -> str:
        if lambda2 < 0.3: return "INCOHERENT_THERMAL"
        if lambda2 < 0.7: return "WEAK_COHERENCE"
        if lambda2 < 0.9: return "STRONG_COHERENCE"
        return "SUPER_RADIANCE_TZINOR"
