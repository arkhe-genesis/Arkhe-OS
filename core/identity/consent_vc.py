from typing import Dict, Any, List
import datetime
import hashlib
import uuid

class ConsentCredential:
    """Verifiable Credential for granular, revocable consent."""

    @staticmethod
    def issue(participant_did: str, researcher_did: str, consent_scope: Dict[str, Any], validity_days: int) -> Dict[str, Any]:
        issuance_date = datetime.datetime.now(datetime.timezone.utc)
        expiration_date = issuance_date + datetime.timedelta(days=validity_days)

        token_id = str(uuid.uuid4())

        return {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://w3id.org/arkhe/credentials/v1"
            ],
            "id": f"urn:uuid:consent-{token_id}",
            "type": ["VerifiableCredential", "ArkheConsentCredential"],
            "issuer": participant_did,
            "issuanceDate": issuance_date.isoformat(),
            "expirationDate": expiration_date.isoformat(),
            "credentialSubject": {
                "id": researcher_did,
                "consentScope": consent_scope,
                "researchPurpose": "Longitudinal plasticity mapping in orthogonal witness protocols",
                "protocolAdherenceProof": "pending-zk-proof"
            },
            "proof": {
                "type": "Ed25519Signature2020",
                "created": issuance_date.isoformat(),
                "verificationMethod": f"{participant_did}#key-1",
                "proofPurpose": "assertionMethod",
                "proofValue": "zSTUB_SIGNATURE"
            }
        }

class MetacognitiveTag:
    """Verifiable Credential for participant metacognitive tagging."""

    @staticmethod
    def issue(participant_did: str, session_hash: str, tag_type: str, tag_value: float, narrative_note: str, phase_context: Dict[str, float]) -> Dict[str, Any]:
        issuance_date = datetime.datetime.now(datetime.timezone.utc)
        tag_id = str(uuid.uuid4())

        return {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://w3id.org/arkhe/credentials/v1"
            ],
            "id": f"urn:uuid:tag-{tag_id}",
            "type": ["VerifiableCredential", "ArkheMetacognitiveTag"],
            "issuer": participant_did,
            "issuanceDate": issuance_date.isoformat(),
            "credentialSubject": {
                "id": f"did:arkhe:session:{session_hash}",
                "tagType": tag_type,
                "tagValue": tag_value,
                "narrativeNote": narrative_note,
                "phaseContext": phase_context
            },
            "proof": {
                "type": "Ed25519Signature2020",
                "created": issuance_date.isoformat(),
                "verificationMethod": f"{participant_did}#key-1",
                "proofPurpose": "assertionMethod",
                "proofValue": "zSTUB_SIGNATURE"
            }
        }

class RevocationRegistry:
    """Cryptographic + DID-Compliant Revocation Registry using StatusList2021."""

    def __init__(self, participant_did: str):
        self.participant_did = participant_did
        self.revoked_credentials: Dict[str, Dict[str, Any]] = {}

    def revoke_credential(self, credential_id: str, reason: str = "participant_request") -> Dict[str, Any]:
        revocation_hash = hashlib.sha256(credential_id.encode()).hexdigest()
        revocation_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        self.revoked_credentials[credential_id] = {
            "revocation_hash": revocation_hash,
            "timestamp": revocation_timestamp,
            "reason": reason
        }

        return self.generate_status_list()

    def generate_status_list(self) -> Dict[str, Any]:
        """Generates a StatusList2021 entry."""
        # Note: A real implementation would generate a bitstring encoded list
        encoded_list_stub = "H4sIAAAAAAAAA-STUB-ENCODED-LIST-GZIP-BASE64"

        latest_revocation = list(self.revoked_credentials.values())[-1] if self.revoked_credentials else None

        doc = {
            "@context": "https://w3id.org/vc/status-list/2021/v1",
            "id": f"{self.participant_did}#revocation-list-1",
            "type": "StatusList2021",
            "statusPurpose": "revocation",
            "encodedList": encoded_list_stub,
        }

        if latest_revocation:
            doc["arkhe:revocationMetadata"] = {
                "cryptographicRevocationHash": latest_revocation["revocation_hash"],
                "revocationTimestamp": latest_revocation["timestamp"],
                "reason": latest_revocation["reason"]
            }

        return doc

    def is_revoked(self, credential_id: str) -> bool:
        return credential_id in self.revoked_credentials
