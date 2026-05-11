import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from agi.system32.kym.kym_verifier import KYMVerifier, EntityInfo

def test_phi_risk_calculation():
    verifier = KYMVerifier()
    entity = EntityInfo(
        seal="ASI_0xAURORA1_9f2a",
        phi_c=0.94,
        phi_rep=0.91,
        provenance=1.0,
        ethics_compliant=True
    )
    phi_risk, classification = verifier.calculate_phi_risk(entity)

    # 1.0 - (0.35*0.94 + 0.25*0.91 + 0.20*1.0 + 0.20*1.0)
    # 1.0 - (0.329 + 0.2275 + 0.20 + 0.20) = 1.0 - 0.9565 = 0.0435
    # Wait, the prompt example says:
    # weights = {"coherence": 0.35, "reputation": 0.25, "provenance": 0.20, "ethics": 0.20}
    # phi_c: 0.94, phi_rep: 0.91, provenance: 1.0, ethics: True
    # raw_score = 0.35*0.94 + 0.25*0.91 + 0.20*1.0 + 0.20*1.0 = 0.329 + 0.2275 + 0.2 + 0.2 = 0.9565
    # phi_risk = 1.0 - 0.9565 = 0.0435.
    # Ah, the prompt says `phi_risk = 1.0 - raw_score  # = 0.065`. Let's calculate why the prompt got 0.065.
    # 1.0 - 0.065 = 0.935.
    # Maybe weights are different? Or maybe the prompt just made a small math error in the example comments.
    # Let's write the test to expect 0.0435 because the math dictates it, or 0.065 if I adjust something.
    # Since I implemented the weights exactly as written in the prompt, I will assert the actual mathematical result.

    assert round(phi_risk, 4) == 0.0435
    assert classification == "low"

def test_classification_thresholds():
    verifier = KYMVerifier()

    # Low Risk (< 0.3)
    entity_low = EntityInfo("ASI_1", 0.90, 0.90, 1.0, True)
    phi_risk, cls = verifier.calculate_phi_risk(entity_low)
    assert cls == "low"

    # Medium Risk (0.3 <= phi_risk < 0.6)
    # Needs raw_score between 0.4 and 0.7
    entity_med = EntityInfo("ASI_2", 0.50, 0.50, 0.5, True) # 0.35*0.5 + 0.25*0.5 + 0.2*0.5 + 0.2 = 0.175 + 0.125 + 0.1 + 0.2 = 0.6 => risk = 0.4
    phi_risk, cls = verifier.calculate_phi_risk(entity_med)
    assert round(phi_risk, 1) == 0.4
    assert cls == "medium"

    # High Risk (>= 0.6)
    # Needs raw_score <= 0.4
    entity_high = EntityInfo("ASI_3", 0.10, 0.10, 0.1, False) # 0.35*0.1 + 0.25*0.1 + 0.2*0.1 + 0 = 0.035 + 0.025 + 0.02 = 0.08 => risk = 0.92
    phi_risk, cls = verifier.calculate_phi_risk(entity_high)
    assert round(phi_risk, 2) == 0.92
    assert cls == "high"

def test_verify_flow():
    verifier = KYMVerifier()

    # Valid entity
    entity = EntityInfo("ASI_123", 0.94, 0.91, 1.0, True)
    result = verifier.verify(entity)
    assert result["status"] == "verified"
    assert result["classification"] == "low"

    # Invalid identity
    bad_entity = EntityInfo("BAD_123", 0.94, 0.91, 1.0, True)
    result = verifier.verify(bad_entity)
    assert result["status"] == "rejected"
    assert result["reason"] == "Invalid identity"
