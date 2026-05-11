import pytest
from core.regulatory.compliance_layer import RegulatoryComplianceLayer, EthicalLedger, RevocationVC, RevocationScope

def test_fda_audit_package():
    layer = RegulatoryComplianceLayer(trial_did="did:test", jurisdiction="FDA")
    pkg = layer.generate_fda_audit_package("did:inspector:1")
    assert pkg is not None
    assert "Raw participant data is not included" in pkg.verification_instructions

def test_gdpr_erasure_request():
    layer = RegulatoryComplianceLayer(trial_did="did:test", jurisdiction="GDPR")
    res = layer.handle_gdpr_erasure_request("did:participant:1")
    assert res.erasure_type == "cryptographic_tombstoning"
    assert res.historical_research_preserved is True
