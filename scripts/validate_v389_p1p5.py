#!/usr/bin/env python3
"""
Validation script for Chemical Gluing Bridge (v∞.389.1) compliance with P1-P5
"""
import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.chemical_gluing_bridge import ChemicalGluingLoop, ChemicalCandidate

def test_p1p5_compliance():
    # P5: The loop sets explicit conventions/bounds matching the paper
    loop = ChemicalGluingLoop()

    # 1. Test evaluate_capture_regime (Thermodynamic Capture constraints)

    # Valid candidate (inside bounds)
    cand_valid = ChemicalCandidate(
        smiles="Valid_SMILES",
        delta_h=55.0,        # in [40.0, 70.0]
        wt_percent=6.0,      # >= 5.5
        pour_point=20.0,     # <= 40.0
        sa_score=3.0         # <= 5.0
    )
    is_capture, score = loop.evaluate_capture_regime(cand_valid)
    assert is_capture is True, "Valid candidate should be in CAPTURE regime"
    assert score > 0.0, "Score should be positive for CAPTURE candidate"

    # Invalid candidate (delta_h outside bounds)
    cand_invalid_dh = ChemicalCandidate(
        smiles="Invalid_DH",
        delta_h=80.0,        # outside [40.0, 70.0]
        wt_percent=6.0,
        pour_point=20.0,
        sa_score=3.0
    )
    is_capture, _ = loop.evaluate_capture_regime(cand_invalid_dh)
    assert is_capture is False, "Candidate with out-of-bounds delta_h should not be CAPTURE"

    # Invalid candidate (wt_percent too low)
    cand_invalid_wt = ChemicalCandidate(
        smiles="Invalid_WT",
        delta_h=55.0,
        wt_percent=4.0,      # < 5.5
        pour_point=20.0,
        sa_score=3.0
    )
    is_capture, _ = loop.evaluate_capture_regime(cand_invalid_wt)
    assert is_capture is False, "Candidate with low wt_percent should not be CAPTURE"

    # 2. Test step_gluing_cycle (P3: Full pipeline execution)

    def mock_llm_explore(seeds):
        # Generates two new candidates
        return [
            ChemicalCandidate("LLM_Gen1", 60.0, 6.2, 15.0, 2.5), # Should pass
            ChemicalCandidate("LLM_Gen2", 30.0, 6.2, 15.0, 2.5)  # Should fail (dh too low)
        ]

    def mock_ml_filter(candidates):
        # Simply passes all generated candidates for this test
        return candidates

    initial_seeds = [
        ChemicalCandidate("Seed1", 50.0, 6.0, 30.0, 4.0)
    ]

    captured = loop.step_gluing_cycle(initial_seeds, mock_llm_explore, mock_ml_filter)

    assert len(captured) == 1, f"Expected 1 captured candidate, got {len(captured)}"
    assert captured[0].smiles == "LLM_Gen1", "Only LLM_Gen1 should have been captured"
    assert len(loop.history) == 1, "History should have 1 entry for the step"

    print("✅ ALL P1-P5 CHECKS PASSED")

if __name__ == "__main__":
    test_p1p5_compliance()
