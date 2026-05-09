import pytest
import time
import hashlib
from core.recovery.social_recovery import (
    SocialRecoveryProtocol,
    GuardianZKProof,
    RecoveryExecution,
    pq_secret_share,
    pq_encrypt,
    pq_decrypt,
    pq_secret_reconstruct,
    generate_zk_proof_of_valid_share,
    verify_zk_proof,
    EncryptedShareResponse
)


def test_pq_secret_sharing_mock():
    secret = b"master_secret_123"
    shares = pq_secret_share(secret, 5, 3)
    assert len(shares) == 5
    recon = pq_secret_reconstruct(shares[:3], 3)
    assert recon == b"reconstructed_secret_from_3_shares"


def test_guardian_zk_proof():
    share = b"share_1"
    public_commitment = b"public_commitment"
    guardian_did = "did:arkhe:guardian1"

    proof = GuardianZKProof.generate(share, public_commitment, guardian_did)
    assert proof.proof_data == "proof_did:arkhe:guardian1"

    is_valid = GuardianZKProof.verify(proof, public_commitment, guardian_did)
    assert is_valid == True

    is_valid_wrong_did = GuardianZKProof.verify(proof, public_commitment, "did:arkhe:guardian2")
    assert is_valid_wrong_did == False


def test_social_recovery_protocol_init():
    participant_id = "did:arkhe:participant1"
    master_secret = b"my_super_secret"
    guardians = ["did:arkhe:g1", "did:arkhe:g2", "did:arkhe:g3", "did:arkhe:g4", "did:arkhe:g5"]
    threshold = 3
    conditions = {"time_lock": 24}

    protocol = SocialRecoveryProtocol(participant_id, master_secret, guardians, threshold, conditions)

    assert len(protocol.shares) == 5
    assert len(protocol.encrypted_shares) == 5
    assert protocol.policy["participant_id"] == participant_id
    assert protocol.policy["threshold"] == threshold
    assert protocol.policy_signature.startswith("sig_")


def test_recovery_execution():
    participant_id = "did:arkhe:participant1"
    master_secret = b"my_super_secret"
    guardians = ["did:arkhe:g1", "did:arkhe:g2", "did:arkhe:g3"]
    threshold = 2

    protocol = SocialRecoveryProtocol(participant_id, master_secret, guardians, threshold, {})
    executor = RecoveryExecution(protocol.policy)

    request = executor.initiate(participant_id, "lost key", b"auth_proof_bio")

    # Mock guardian responses
    responses = []
    for g in guardians[:2]: # Provide 2 shares to meet threshold
        zk_proof = GuardianZKProof.generate(protocol.shares[guardians.index(g)], protocol.policy["public_commitment"], g)
        responses.append(EncryptedShareResponse(
            guardian_did=g,
            encrypted_share=protocol.encrypted_shares[g],
            zk_proof=zk_proof
        ))

    participant_recovery_key = "pk_" + participant_id
    recovered_secret = executor.collect_and_reconstruct(request, responses, participant_recovery_key)

    assert recovered_secret is not None
    assert recovered_secret == b"reconstructed_secret_from_2_shares"

def test_recovery_execution_fails_threshold():
    participant_id = "did:arkhe:participant1"
    master_secret = b"my_super_secret"
    guardians = ["did:arkhe:g1", "did:arkhe:g2", "did:arkhe:g3"]
    threshold = 3

    protocol = SocialRecoveryProtocol(participant_id, master_secret, guardians, threshold, {})
    executor = RecoveryExecution(protocol.policy)

    request = executor.initiate(participant_id, "lost key", b"auth_proof_bio")

    # Mock guardian responses, but only 2 (threshold is 3)
    responses = []
    for g in guardians[:2]:
        zk_proof = GuardianZKProof.generate(protocol.shares[guardians.index(g)], protocol.policy["public_commitment"], g)
        responses.append(EncryptedShareResponse(
            guardian_did=g,
            encrypted_share=protocol.encrypted_shares[g],
            zk_proof=zk_proof
        ))

    participant_recovery_key = "pk_" + participant_id
    recovered_secret = executor.collect_and_reconstruct(request, responses, participant_recovery_key)

    assert recovered_secret is None
