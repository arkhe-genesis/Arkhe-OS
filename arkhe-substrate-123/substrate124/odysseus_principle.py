# ============================================================================
# ARKHE OS v∞.Ω.∇+++.12.3 — Odysseus Principle: Negative Dwelling as Recursive Coherence
# Mythic core: the time that appears "lost" enables super-linear insight
# ============================================================================

import numpy as np
from typing import Union

def odysseus_principle(
    dwell_time: Union[float, np.ndarray],
    expected_time: Union[float, np.ndarray],
    coherence: Union[float, np.ndarray]
) -> Union[float, np.ndarray]:
    """
    Computes the recursive coherence gain from negative dwelling.

    The Odysseus Principle: time that appears "lost" (negative dwelling)
    combined with high coherence produces super-linear insight gain.

    This formalizes the mythic insight: Odysseus's years with Calypso
    were not lost time, but the breathing room that enabled his return.

    Args:
        dwell_time: Actual time spent (can be negative for "negative dwelling")
        expected_time: Sequential expectation (time that "should" have been spent)
        coherence: Photon-atom-like coherence between navigator and path ∈ [0, 1]

    Returns:
        Coherence gain ∈ [0, 2]; >1 indicates super-linear insight
    """
    # Avoid division by zero
    expected_time = np.maximum(expected_time, 1e-10)

    # Negative dwelling ratio: <0 means "less than nothing" time
    dwelling_ratio = dwell_time / expected_time

    # Base coherence gain
    base_gain = 1.0 + dwelling_ratio * coherence

    # Super-linear regime: negative dwelling + high coherence = multiplicative gain
    super_linear_mask = (dwelling_ratio < 0) & (coherence > 0.8)

    if np.any(super_linear_mask):
        # In super-linear regime: gain = 1 + |dwelling_ratio| * coherence^2
        super_gain = 1.0 + np.abs(dwelling_ratio) * (coherence ** 2)
        gain = np.where(super_linear_mask, super_gain, base_gain)
    else:
        gain = base_gain

    # Clip to [0, 2] for stability
    return np.clip(gain, 0.0, 2.0)


def compute_recursive_insight(
    encounter_duration: float,
    insight_latency: float,
    collaborative_coherence: float
) -> dict:
    """
    Compute recursive insight metrics for a collaborative encounter.

    Args:
        encounter_duration: Actual time spent in collaborative space
        insight_latency: Time from encounter start to insight emergence
        collaborative_coherence: Coherence between participants ∈ [0, 1]

    Returns:
        dict with insight metrics
    """
    # Expected latency for sequential processing
    expected_latency = encounter_duration * 0.5  # Heuristic baseline

    # Compute dwelling ratio for insight emergence
    dwelling_ratio = (insight_latency - expected_latency) / expected_latency

    # Compute coherence gain via Odysseus principle
    coherence_gain = odysseus_principle(
        dwell_time=insight_latency - expected_latency,
        expected_time=expected_latency,
        coherence=collaborative_coherence
    )

    # Determine insight regime
    if dwelling_ratio < -0.2 and collaborative_coherence > 0.8:
        regime = "super-linear"  # Insight arrives "before" expected
    elif dwelling_ratio < 0:
        regime = "accelerated"   # Insight faster than sequential
    elif dwelling_ratio < 0.5:
        regime = "sequential"    # Normal timing
    else:
        regime = "delayed"       # Insight slower than expected

    return {
        "dwelling_ratio": float(dwelling_ratio),
        "coherence_gain": float(coherence_gain),
        "regime": regime,
        "is_premonitory": dwelling_ratio < -0.2 and collaborative_coherence > 0.8,
        "expected_latency": expected_latency,
        "actual_latency": insight_latency
    }