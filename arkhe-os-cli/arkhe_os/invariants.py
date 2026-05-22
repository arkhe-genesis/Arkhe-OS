from .constants import GHOST, LOOPSEAL, GAP_SOV, PHI_AUREA

def verify_all_invariants(subsystems):
    """Verifies all invariants"""
    phi_c_vals = []
    if isinstance(subsystems, dict):
        for sub_id, sub_obj in subsystems.items():
             phi_c_vals.append(getattr(sub_obj, "phi_c", 0.999))

    avg_phi_c = sum(phi_c_vals) / len(phi_c_vals) if phi_c_vals else 0.999

    return {
        "Ghost": {"status": verify_ghost(avg_phi_c), "phi_c": avg_phi_c},
        "Loopseal": {"status": verify_loopseal(avg_phi_c), "phi_c": avg_phi_c},
        "Gap": {"status": verify_gap(avg_phi_c), "phi_c": avg_phi_c},
        "GoldenRatio": {"status": verify_golden_ratio(avg_phi_c), "phi_c": avg_phi_c}
    }

def verify_ghost(phi_c):
    return phi_c > GHOST

def verify_loopseal(phi_c):
    return phi_c > LOOPSEAL

def verify_gap(phi_c):
    return phi_c < GAP_SOV

def verify_golden_ratio(phi_c):
    return phi_c < PHI_AUREA
