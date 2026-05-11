import pytest
import asyncio
import numpy as np
import hashlib
import json
from audit_logger import AuditLogger
from src.arkhe_core.quantum.codex import QuantumCodex
from cathedral_zk import Prover, Verifier
from fedternary.unifier import FedTernaryUnifier, TernaryValue
from zk_mesh_surrogate import SurrogateZKMeshVerifier, MeshDecompositionStrategy
from hierarchical_consent import HierarchicalConsentManager
from receipt.unified_builder import UnifiedReceiptBuilder, CathedralDomain, ZKProofRef, ConsentRef

@pytest.mark.asyncio
async def test_topological_pentalogy_integration():
    # Setup
    codex = QuantumCodex()
    prover = Prover()
    verifier = Verifier()
    audit = AuditLogger()

    # 1. FedTernary Unificado
    fed_unifier = FedTernaryUnifier(codex, prover, audit_logger=audit)

    # Generate contributions from 3 labs
    contributions = []
    for i in range(3):
        contrib = await fed_unifier.generate_contribution(
            participant_id=f"lab_{i}",
            domain_name="photonic_phase",
            continuous_value=0.6 if i < 2 else -0.6,
            private_data_hash=f"hash_data_{i}"
        )
        contributions.append(contrib)

    # Aggregate
    reputations = {f"lab_{i}": 0.9 for i in range(3)}
    agg_result = await fed_unifier.aggregate_contributions(
        domain_name="photonic_phase",
        contributions=contributions,
        participant_reputations=reputations,
        verifier=verifier
    )
    assert agg_result.consensus_reached is True
    assert agg_result.aggregated_value in [TernaryValue.AGREE, TernaryValue.DISAGREE, TernaryValue.NEUTRAL]

    # 2. Surrogate ZK
    surrogate_verifier = SurrogateZKMeshVerifier(prover)
    N = 16
    target_unitary = np.eye(N, dtype=complex)
    phases = np.zeros((N, N))
    couplings = np.zeros((N, N))

    proof = await surrogate_verifier.generate_surrogate_proof(
        target_unitary, phases, couplings,
        decomposition_strategy=MeshDecompositionStrategy.BLOCK_DIAGONAL
    )

    verif_result = await surrogate_verifier.verify_surrogate_proof(proof, verifier, 0.01)
    assert verif_result["valid"] is True

    # 3. Hierarchical Consent
    consent_manager = HierarchicalConsentManager(codex, prover)
    chip_layout = {"elements": {"e0": {"topological_invariant": "chern_number", "invariant_value": 1, "role": "inter_region_coupler"}}}
    blocks = consent_manager.create_topological_block(chip_layout)
    assert len(blocks) > 0

    block_id = blocks[0].block_id
    citizen_did = "did:arkhe:citizen:001"
    consent = await consent_manager.grant_block_consent(
        block_id, citizen_did, "test_scope", {"type": "permanent"}
    )

    hier_proof = await consent_manager.generate_hierarchical_proof(
        consent.consent_id, [], {"op": "test"}
    )

    consent_verif = await consent_manager.verify_hierarchical_proof(hier_proof)
    assert consent_verif["valid"] is True

    # 4. Unified Receipt qhttp
    receipt_builder = UnifiedReceiptBuilder(codex, prover)

    unified_receipt = await receipt_builder.build_receipt(
        domain=CathedralDomain.TOPOLOGICAL,
        raw_data_hash=hashlib.sha256(b"raw").hexdigest(),
        zk_proof=ZKProofRef(
            proof_type="mesh_verification",
            proof_data_b64="c29tZV9wcm9vZg==",
            public_inputs={"N": 16}
        ),
        consent_ref=ConsentRef(
            consent_hash=hashlib.sha256(b"consent").hexdigest(),
            citizen_did_hash="1234567890abcdef",
            scope_hash=hashlib.sha256(b"scope").hexdigest()
        ),
        merkle_root="0" * 64,
        domain_payload={"mesh_type": "clements", "mesh_size": 16, "unitary_hash": "h", "error_bound": 0.01}
    )

    assert unified_receipt.domain == CathedralDomain.TOPOLOGICAL
    assert unified_receipt.version == "v1.2"

    receipt_verif = await receipt_builder.verify_receipt(unified_receipt, {})
    assert receipt_verif["valid"] is True

    print("=== INTEGRATION TEST FOR FS-90/91 PASSED ===")
