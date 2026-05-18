import pytest
from lean_bridge import LeanToBeaver, IntelligenceProposition
from assembly_verifier.smt_reducer import AssemblyVerifier
from redundant_checker.intention_checker import RedundantIntentionChecker, IntentionImplementation
from pipeline.vitalik_full_cycle import VitalikProtocolPipeline

def test_vitalik_pipeline():
    pipeline = VitalikProtocolPipeline()

    assembly_code = """
    PUSH1 0x64
    PUSH1 0x00
    MSTORE
    PUSH1 0x01
    PUSH1 0x20
    MSTORE
    PUSH1 0x00
    MLOAD
    PUSH1 0x20
    MLOAD
    ADD
    STOP
    """

    impls = [
        IntentionImplementation(
            language="python",
            source_code="""
def transfer(ledger, from_, to, amount):
    print("ARKHE_SEAL: abc123python")
"""
        )
    ]

    result = pipeline.verify_intent("test_intent", "lean_spec", assembly_code, impls)

    assert result["phi_c"] >= 0.0
    assert "valid" in result
