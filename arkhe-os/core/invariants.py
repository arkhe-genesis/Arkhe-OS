# =========================================================
# ARKHE OS - Verificador de Invariantes
# =========================================================
from core.constants import GHOST, LOOPSEAL, GAP_SOV, PHI_AUREA
from core.proof import Severity, VerificationResult

class InvariantVerifier:
    @staticmethod
    def check_ghost(checks: list) -> tuple:
        """Coerencia epistemica: ausencia de contradicoes."""
        failures = sum(1 for _, sev, _, _ in checks if sev in (Severity.FAIL, Severity.CRITICAL))
        warnings = sum(1 for _, sev, _, _ in checks if sev == Severity.WARN)
        ghost_value = 1.0 if (failures + warnings) == 0 else 0.5
        return ghost_value, ghost_value >= GHOST

    @staticmethod
    def check_loopseal(chain: list) -> tuple:
        """Fechamento circular: teoria -> experimento -> teoria."""
        loopseal_value = 1.0 if len(chain) >= 2 else 0.5
        return loopseal_value, loopseal_value >= LOOPSEAL

    @staticmethod
    def check_gap(gaps: list, total_checks: int) -> tuple:
        """Soberania epistemica: lacunas documentadas."""
        gap_value = 1.0 - (len(gaps) / total_checks) if total_checks > 0 else 1.0
        return gap_value, gap_value >= 0.85

    @staticmethod
    def check_phi(a: float, b: float) -> tuple:
        """Proporcao aurea entre dois componentes."""
        ratio = a / b if b > 0 else 0
        deviation = abs(ratio - PHI_AUREA)
        phi_value = max(0.0, 1.0 - deviation / PHI_AUREA)
        return phi_value, phi_value > 0.5
