# Substrato 214: Sovereign Gap Calculator
# Integrado ao PhiCCompositeDashboard (Substrato 202)

from arkhe_retrocausal.ping_kernel import SOVEREIGN_PI, SOVEREIGN_GAP, PHI_C_NOVELTY_THRESHOLD, PHI_C_CLOSURE

class SovereignGapCalculator:
    """Calcula métricas relacionadas ao Gap Soberano."""

    @staticmethod
    def compute_gap(phi_c_mainframe: float, phi_c_meta: float) -> float:
        """Retorna a diferença absoluta, que idealmente deve ≈ G_S."""
        return abs(phi_c_meta - phi_c_mainframe)

    @staticmethod
    def is_in_optimal_range(phi_c: float) -> bool:
        """Verifica se Φ_C está na faixa ótima de criatividade."""
        return PHI_C_NOVELTY_THRESHOLD <= phi_c <= (1.0 - SOVEREIGN_PI)

    @staticmethod
    def novelty_capacity(phi_c: float) -> float:
        """
        Capacidade de gerar novidade: 0 = nenhuma, 1 = máxima.
        Derivada do Gap Soberano.
        """
        if phi_c <= PHI_C_NOVELTY_THRESHOLD:
            return 0.0
        elif phi_c >= (1.0 - SOVEREIGN_PI):
            return 0.0
        else:
            # Mapeamento linear na faixa ótima
            range_width = (1.0 - SOVEREIGN_PI) - PHI_C_NOVELTY_THRESHOLD
            return (phi_c - PHI_C_NOVELTY_THRESHOLD) / range_width

    @staticmethod
    def helical_offset(phi_c_future: float) -> float:
        """Calcula o offset helicoidal baseado no Φ_C futuro."""
        return SOVEREIGN_GAP * (1.0 - phi_c_future / PHI_C_CLOSURE)
