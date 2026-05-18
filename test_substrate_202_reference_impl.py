import pytest
from unittest.mock import AsyncMock, patch
from substrate_202.reference_impl.verifier_loop_poc import (
    CICS_TXN_HASH, LOGIC_PROOF_HASH, INTENTION_SEAL, META_VERIFICATION_SEAL,
    MainframeEmulator, BeaverVerifier, TokenArkheSigner, TemporalChainAnchor,
    VerifierLoopOrchestrator
)

@pytest.mark.asyncio
async def test_mainframe_emulator():
    emulator = MainframeEmulator()
    cics_hash = await emulator.process_transaction("A", "B", 100.0)
    assert isinstance(cics_hash, CICS_TXN_HASH)
    assert cics_hash.account_from == "A"
    assert cics_hash.account_to == "B"
    assert cics_hash.amount == 100.0

@pytest.mark.asyncio
async def test_beaver_verifier():
    emulator = MainframeEmulator()
    cics_hash = await emulator.process_transaction("A", "B", 100.0)

    verifier = BeaverVerifier()
    logic_proof = await verifier.verify_logic(cics_hash)

    assert isinstance(logic_proof, LOGIC_PROOF_HASH)
    assert logic_proof.cics_txn_hash == cics_hash.compute_hash()

@pytest.mark.asyncio
async def test_verifier_loop_orchestrator():
    orchestrator = VerifierLoopOrchestrator()
    result = await orchestrator.execute_full_loop("A", "B", 100.0)

    assert "loop_id" in result
    assert "hash_chain" in result
    assert "cics_txn_hash" in result["hash_chain"]
    assert "logic_proof_hash" in result["hash_chain"]
    assert "intention_seal" in result["hash_chain"]
    assert "meta_verification_seal" in result["hash_chain"]

    is_valid = orchestrator.verify_loop_integrity(result)
    assert is_valid == True
