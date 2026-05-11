"""
scientific_receipt.py — Geração de receipts científicos unificados para chemputation
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto

# Simplified mock for SDK classes
@dataclass
class ZKProofRef:
    proof_type: str
    proof_data_b64: str
    public_inputs: dict

@dataclass
class ConsentRef:
    consent_hash: str
    citizen_did_hash: str
    scope_hash: str
    hierarchical: bool
    block_id_hash: str

@dataclass
class AggregationHint:
    ternary_value: int
    aggregation_domain: str
    contribution_id: str

class ScientificReceiptType(Enum):
    MOLECULE_DISCOVERY = "molecule_discovery"
    PROPERTY_EVALUATION = "property_evaluation"
    SYNTHESIS_VALIDATION = "synthesis_validation"
    FEDERATED_OPTIMIZATION = "federated_optimization"

@dataclass
class ScientificReceipt:
    receipt_id: str
    receipt_type: ScientificReceiptType
    timestamp: float
    version: str
    molecule_hash: str
    intent_id: Optional[str] = None
    quantum_evaluation: Optional[Dict] = None
    quantum_proof_ref: Optional[ZKProofRef] = None
    synthesis_route: Optional[Dict] = None
    synthesizability_score: Optional[float] = None
    consent_ref: Optional[ConsentRef] = None
    federation_meta: Optional[Dict] = None
    aggregation_hint: Optional[AggregationHint] = None
    merkle_root: str
    codex_anchor: Optional[Dict] = None
    domain_payload: Dict = field(default_factory=dict)
    generated_at: float = field(default_factory=time.time)

    def to_qhttp_payload(self) -> Dict:
        return {
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp,
            "domain": "chemputation",
            "version": self.version,
            "data_hash": self.molecule_hash,
            "zk_proof": asdict(self.quantum_proof_ref) if self.quantum_proof_ref else None,
            "consent_ref": asdict(self.consent_ref) if self.consent_ref else None,
            "merkle_root": self.merkle_root,
            "domain_payload": {
                "chemputation": {
                    "receipt_type": self.receipt_type.value,
                    "intent_id": self.intent_id,
                    "quantum_evaluation": self.quantum_evaluation,
                    "synthesis_route": self.synthesis_route,
                    "synthesizability_score": self.synthesizability_score,
                },
                **self.domain_payload,
            },
        }

    def compute_hash(self) -> str:
        data = {
            "receipt_id": self.receipt_id,
            "molecule_hash": self.molecule_hash,
            "timestamp": self.timestamp,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

class ScientificReceiptBuilder:
    def __init__(self, codex_client, zk_prover=None):
        self.codex = codex_client
        self.zk_prover = zk_prover

    async def build_molecule_discovery_receipt(
        self,
        intent,
        molecule_smiles: str,
        quantum_result,
        synthesis_info: Dict,
        consent_ref: ConsentRef,
        federation_meta: Optional[Dict] = None,
    ) -> ScientificReceipt:
        molecule_hash = hashlib.sha256(molecule_smiles.encode()).hexdigest()
        receipt_id = f"chem_{molecule_hash[:12]}_{int(time.time())}"

        merkle_root = hashlib.sha256(molecule_hash.encode()).hexdigest()

        receipt = ScientificReceipt(
            receipt_id=receipt_id,
            receipt_type=ScientificReceiptType.MOLECULE_DISCOVERY,
            timestamp=time.time(),
            version="v1.0",
            molecule_hash=molecule_hash,
            intent_id=intent.intent_id,
            quantum_evaluation=quantum_result.to_dict() if quantum_result else None,
            synthesis_route=synthesis_info,
            synthesizability_score=synthesis_info.get("synthesizability_score"),
            consent_ref=consent_ref,
            federation_meta=federation_meta,
            merkle_root=merkle_root,
        )

        await self._anchor_receipt(receipt)
        return receipt

    async def _anchor_receipt(self, receipt: ScientificReceipt):
        receipt_hash = receipt.compute_hash()
        await self.codex.store_artifact(
            artifact_id=f"chemputation_{receipt.receipt_id}",
            content_hash=receipt_hash,
            metadata={"type": "scientific_receipt"}
        )
        receipt.codex_anchor = {
            "artifact_id": f"chemputation_{receipt.receipt_id}",
            "content_hash": receipt_hash,
            "anchored_at": time.time(),
            "verification_url": f"https://codex.cathedral.ark/verify/{receipt.receipt_id}",
        }
