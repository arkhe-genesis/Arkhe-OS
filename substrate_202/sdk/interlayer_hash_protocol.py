#!/usr/bin/env python3
"""
ARKHE OS Substrato 202: Inter-Layer Hash Protocol Specification
Canon: ∞.Ω.∇+++.202.hash_protocol.spec
"""

import hashlib
import json
import struct
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Union, Any, Tuple
from enum import Enum, auto
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

HASH_ALGORITHM = "sha3_256"
HASH_LENGTH_BYTES = 32
HASH_LENGTH_HEX = 64

NAMESPACE_PREFIXES = {
    "cics_txn": "CTX",
    "logic_proof": "LPF",
    "intention": "ITS",
    "meta_verification": "MTV"
}

SERIALIZATION_VERSION = "1.0"

class HashNamespace(Enum):
    CICS_TXN = "cics_txn"
    LOGIC_PROOF = "logic_proof"
    INTENTION = "intention"
    META_VERIFICATION = "meta_verification"

@dataclass
class CanonicalHash:
    namespace: HashNamespace
    payload_version: str
    payload_hash: str
    metadata: Dict[str, Any]
    producer_layer: str
    consumer_layers: List[str]
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        if len(self.payload_hash) != HASH_LENGTH_HEX:
            raise ValueError(f"payload_hash must be {HASH_LENGTH_HEX} hex chars")
        if self.namespace not in HashNamespace:
            raise ValueError(f"Invalid namespace: {self.namespace}")

    def to_canonical_string(self) -> str:
        return f"{NAMESPACE_PREFIXES[self.namespace.value]}:{self.payload_version}:{self.payload_hash}:{int(self.timestamp)}"

    def verify_integrity(self) -> bool:
        return len(self.payload_hash) == HASH_LENGTH_HEX and all(c in '0123456789abcdef' for c in self.payload_hash.lower())

    def to_dict(self) -> Dict:
        return {
            "namespace": self.namespace.value,
            "payload_version": self.payload_version,
            "payload_hash": self.payload_hash,
            "metadata": self.metadata,
            "producer_layer": self.producer_layer,
            "consumer_layers": self.consumer_layers,
            "timestamp": self.timestamp,
            "canonical_string": self.to_canonical_string()
        }

@dataclass
class InterLayerHashEnvelope:
    sender_layer: str
    receiver_layer: str
    hash: CanonicalHash
    signature: Optional[str] = None
    sequence_number: int = 0
    priority: int = 1

    def to_canonical_bytes(self) -> bytes:
        payload = f"{self.sender_layer}:{self.receiver_layer}:{self.hash.to_canonical_string()}:{self.sequence_number}:{self.priority}"
        return payload.encode()

    def compute_envelope_hash(self) -> str:
        return hashlib.sha3_256(self.to_canonical_bytes()).hexdigest()

    def to_dict(self) -> Dict:
        return {
            "sender_layer": self.sender_layer,
            "receiver_layer": self.receiver_layer,
            "hash": self.hash.to_dict(),
            "signature": self.signature,
            "sequence_number": self.sequence_number,
            "priority": self.priority,
            "envelope_hash": self.compute_envelope_hash()
        }

class CICS_TXN_HashEncoder:
    @staticmethod
    def encode(transaction_id: str, account_from: str, account_to: str, amount: float, timestamp: float, audit_trail_hash: str, acid_verified: bool) -> CanonicalHash:
        payload_dict = {
            "txn_id": transaction_id,
            "from": account_from,
            "to": account_to,
            "amount": f"{amount:.2f}",
            "ts": int(timestamp),
            "audit": audit_trail_hash,
            "acid": acid_verified
        }

        payload_json = json.dumps(payload_dict, sort_keys=True, separators=(',', ':'))
        payload_hash = hashlib.sha3_256(payload_json.encode()).hexdigest()

        return CanonicalHash(
            namespace=HashNamespace.CICS_TXN,
            payload_version="1.0",
            payload_hash=payload_hash,
            metadata={
                "transaction_id": transaction_id,
                "amount": amount,
                "acid_verified": acid_verified
            },
            producer_layer="mainframe_acid",
            consumer_layers=["beaver_logic"]
        )

class LogicProof_HashEncoder:
    @staticmethod
    def encode(cics_txn_hash: str, logical_proposition: str, proof_steps: List[str], rollback_capability: bool, consistency_verified: bool) -> CanonicalHash:
        payload_dict = {
            "input_hash": cics_txn_hash,
            "proposition": logical_proposition,
            "steps": proof_steps,
            "rollback": rollback_capability,
            "verified": consistency_verified
        }

        payload_json = json.dumps(payload_dict, sort_keys=True, separators=(',', ':'))
        payload_hash = hashlib.sha3_256(payload_json.encode()).hexdigest()

        return CanonicalHash(
            namespace=HashNamespace.LOGIC_PROOF,
            payload_version="1.0",
            payload_hash=payload_hash,
            metadata={
                "input_hash": cics_txn_hash,
                "proposition": logical_proposition[:100],
                "step_count": len(proof_steps),
                "consistency_verified": consistency_verified
            },
            producer_layer="beaver_logic",
            consumer_layers=["token_arkhe_intention"]
        )

class Intention_HashEncoder:
    @staticmethod
    def encode(logic_proof_hash: str, agent_id: str, action_type: str, x402_proof: Optional[str], erc8183_proof: Optional[str], pqc_signature: str, phi_c_score: float) -> CanonicalHash:
        payload_dict = {
            "input_hash": logic_proof_hash,
            "agent": agent_id,
            "action": action_type,
            "x402": x402_proof,
            "erc8183": erc8183_proof,
            "pqc_sig": pqc_signature,
            "phi_c": f"{phi_c_score:.6f}"
        }

        payload_json = json.dumps(payload_dict, sort_keys=True, separators=(',', ':'))
        payload_hash = hashlib.sha3_256(payload_json.encode()).hexdigest()

        return CanonicalHash(
            namespace=HashNamespace.INTENTION,
            payload_version="1.0",
            payload_hash=payload_hash,
            metadata={
                "input_hash": logic_proof_hash,
                "agent_id": agent_id,
                "action_type": action_type,
                "phi_c_score": phi_c_score
            },
            producer_layer="token_arkhe_intention",
            consumer_layers=["temporalchain_meta"]
        )

class MetaVerification_HashEncoder:
    @staticmethod
    def encode(intention_seal: str, consensus_participants: List[str], global_phi_c: float, guardian_approval: bool, temporal_block_height: int, cross_chain_anchor: Optional[str]) -> CanonicalHash:
        payload_dict = {
            "input_seal": intention_seal,
            "consensus": sorted(consensus_participants),
            "global_phi_c": f"{global_phi_c:.8f}",
            "guardian": guardian_approval,
            "block": temporal_block_height,
            "cross_chain": cross_chain_anchor
        }

        payload_json = json.dumps(payload_dict, sort_keys=True, separators=(',', ':'))
        payload_hash = hashlib.sha3_256(payload_json.encode()).hexdigest()

        return CanonicalHash(
            namespace=HashNamespace.META_VERIFICATION,
            payload_version="1.0",
            payload_hash=payload_hash,
            metadata={
                "input_hash": intention_seal,
                "consensus_count": len(consensus_participants),
                "global_phi_c": global_phi_c,
                "guardian_approval": guardian_approval,
                "block_height": temporal_block_height
            },
            producer_layer="temporalchain_meta",
            consumer_layers=["external_auditors", "regulatory_systems"]
        )

class InterLayerHashValidator:
    @staticmethod
    def validate_canonical_hash(ch: CanonicalHash) -> Tuple[bool, str]:
        if ch.namespace not in HashNamespace:
            return False, f"Invalid namespace: {ch.namespace}"

        if ch.payload_version != SERIALIZATION_VERSION:
            return False, f"Unsupported payload version: {ch.payload_version}"

        if not ch.verify_integrity():
            return False, "Invalid payload_hash format"

        valid_layers = ["mainframe_acid", "beaver_logic", "token_arkhe_intention", "temporalchain_meta", "external_auditors", "regulatory_systems"]
        if ch.producer_layer not in valid_layers:
            return False, f"Invalid producer_layer: {ch.producer_layer}"
        if not all(c in valid_layers for c in ch.consumer_layers):
            return False, f"Invalid consumer_layers: {ch.consumer_layers}"

        return True, "OK"

    @staticmethod
    def validate_envelope(envelope: InterLayerHashEnvelope) -> Tuple[bool, str]:
        valid, reason = InterLayerHashValidator.validate_canonical_hash(envelope.hash)
        if not valid:
            return False, f"Invalid hash: {reason}"

        if envelope.sequence_number < 0:
            return False, "Invalid sequence_number"

        if envelope.priority not in [1, 2, 3]:
            return False, "Invalid priority"

        if envelope.signature:
            if not envelope.signature.startswith("pqc:") and len(envelope.signature) < 64:
                return False, "Invalid signature format"

        return True, "OK"

    @staticmethod
    def verify_hash_chain(envelopes: List[InterLayerHashEnvelope]) -> bool:
        if len(envelopes) < 2:
            return True

        hash_consumers = {}
        for env in envelopes:
            hash_value = env.hash.payload_hash
            if hash_value not in hash_consumers:
                hash_consumers[hash_value] = []
            hash_consumers[hash_value].extend(env.hash.consumer_layers)

        for i in range(len(envelopes) - 1):
            current_env = envelopes[i]
            next_env = envelopes[i + 1]

            if current_env.hash.payload_hash != next_env.hash.metadata.get("input_hash"):
                logger.warning(
                    f"⚠️ Hash chain break: {current_env.hash.namespace.value} → {next_env.hash.namespace.value}"
                )
                return False

        return True
