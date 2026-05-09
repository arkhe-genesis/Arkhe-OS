import pytest
import os
import json
from core.identity.did_manager import DIDManager
from core.identity.data_vault import DataVault
from core.identity.consent_vc import ConsentCredential, MetacognitiveTag, RevocationRegistry
from core.identity.zk_adherence import generate_zk_adherence_proof, verify_zk_adherence_proof

def test_did_manager():
    seed = b"test_participant_seed"
    manager = DIDManager("mock_root_hash")

    public_key_mock = b"mock_ed25519_public_key"
    doc = manager.create_did_document(public_key_mock, {"sessionCount": 5})

    assert doc["id"] == "did:arkhe:participant:mock_root_hash"
    assert "mock_root_hash#key-1" in doc["verificationMethod"][0]["id"]
    assert doc["arkhe:participantMetadata"]["sessionCount"] == 5

def test_data_vault():
    participant_did = "did:arkhe:participant:mock"
    private_key = b"super_secret_key"

    vault = DataVault(participant_did, private_key)

    record_data = {"eeg_alpha": 0.5, "eeg_theta": 0.8}
    vault.store_record("record_1", record_data, ["high_theta", "session_42"])

    # Retrieve
    retrieved = vault.retrieve_record("record_1")
    assert retrieved == record_data

    # Retrieve non-existent
    assert vault.retrieve_record("record_2") is None

    # Search ZK commitments
    matches = vault.search_zk_commitments("high_theta")
    assert matches == ["record_1"]

    no_matches = vault.search_zk_commitments("low_theta")
    assert no_matches == []

def test_consent_credentials():
    vc = ConsentCredential.issue("did:issuer", "did:researcher", {"raw_EEG": False}, 30)
    assert vc["type"] == ["VerifiableCredential", "ArkheConsentCredential"]
    assert vc["credentialSubject"]["consentScope"]["raw_EEG"] is False

    tag = MetacognitiveTag.issue("did:issuer", "hash123", "insight", 0.9, "Felt good", {"theta_normalized": 0.1})
    assert tag["type"] == ["VerifiableCredential", "ArkheMetacognitiveTag"]
    assert tag["credentialSubject"]["tagValue"] == 0.9

def test_revocation_registry():
    registry = RevocationRegistry("did:participant")

    status_list = registry.revoke_credential("urn:uuid:vc-123", "participant_request")

    assert registry.is_revoked("urn:uuid:vc-123") is True
    assert registry.is_revoked("urn:uuid:vc-456") is False
    assert status_list["arkhe:revocationMetadata"]["reason"] == "participant_request"

def test_zk_adherence():
    participant_did = "did:arkhe:participant:mock_hash"

    zk_proof = generate_zk_adherence_proof(participant_did, "[0.9, 1.0]", "[0.04, 0.10]")

    assert zk_proof["type"] == ["VerifiableCredential", "ArkheZeroKnowledgeAdherence"]

    # Valid verification
    assert verify_zk_adherence_proof(zk_proof) is True

    # Invalid verification (tampered data)
    zk_proof["credentialSubject"]["adherenceClaims"][0]["range"] = "[0.5, 0.6]"
    assert verify_zk_adherence_proof(zk_proof) is False
