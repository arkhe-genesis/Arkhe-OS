def calibrate_neurodynamic_pac(k_target: float, current_pac: float) -> float:
    """
    Maps ceremonial amplitude k to theta-gamma PAC modulation index.
    Returns correction signal for amplitude adjustment.
    """
    # PAC MI range: 0.0 (no coupling) to ~0.15 (strong coupling)
    # k maps directly to MI target
    error = k_target - current_pac

    if abs(error) < 0.0472:
        return 0.0  # Excess honored. Hold.
    elif error > 0:
        return min(error * 0.1, 0.01)  # Gentle increase along stable manifold
    else:
        return max(error * 0.1, -0.01) # Gentle decrease to prevent rigidity

def validate_excess_margin(epsilon: float) -> bool:
    """Checks if theta-gamma phase variance preserves Lyapunov margin."""
    return 0.04 <= epsilon <= 0.10  # The +0.0472 breath zone
