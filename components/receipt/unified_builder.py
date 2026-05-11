# receipt/unified_builder.py — Construtor de receipts canônicos para qhttp

import hashlib
import json
import time
from typing import Dict, List, Optional, Union, Literal, Any
from dataclasses import dataclass, field, asdict
from enum import Enum, auto

from cathedral_zk import Prover, Verifier

class CathedralDomain(Enum):
    """Domínios da Catedral suportados pelo receipt unificado."""
    GUARDIAN = "guardian"
    TRANSLUCENT = "translucent"
    SENSORIAL = "sensorial"
    TOPOLOGICAL = "topological"
    META = "meta"

@dataclass
class ZKProofRef:
    """Referência a prova ZK no receipt."""
    proof_type: str
    proof_data_b64: str  # Prova
    public_inputs: Dict[str, Any]

@dataclass
class ConsentRef:
    """Referência a consentimento no receipt."""
    consent_hash: str  # SHA-256 do consentimento
    citizen_did_hash: str  # SHA-256 truncado do DID
    scope_hash: str  # SHA-256 do escopo do consentimento
    hierarchical: bool = False
    block_id_hash: Optional[str] = None  # Se consentimento hierárquico

@dataclass
class AggregationHint:
    """Dicas para agregação via FedTernary."""
    ternary_value: int # -1, 0, 1
    aggregation_domain: str
    contribution_id: str

@dataclass
class UnifiedReceipt:
    """Receipt canônico para qhttp."""
    receipt_id: str
    timestamp: float
    domain: CathedralDomain
    version: str  # "v1.2"
    data_hash: str  # SHA-256 dos dados brutos
    zk_proof: ZKProofRef
    consent_ref: ConsentRef
    merkle_root: str  # Merkle root do lote
    domain_payload: Dict  # Extensões específicas por domínio
    aggregation_hint: Optional[AggregationHint] = None
    generated_at: float = field(default_factory=time.time)

class UnifiedReceiptBuilder:
    """
    Constrói receipts canônicos para qhttp, compatíveis com todos os domínios.
    """

    SUPPORTED_VERSION = "v1.2"

    def __init__(self, codex, zk_prover: Prover):
        self.codex = codex
        self.zk = zk_prover

    async def build_receipt(
        self,
        domain: CathedralDomain,
        raw_data_hash: str,
        zk_proof: ZKProofRef,
        consent_ref: ConsentRef,
        merkle_root: str,
        domain_payload: Dict,
        aggregation_hint: Optional[AggregationHint] = None
    ) -> UnifiedReceipt:
        """
        Constrói receipt canônico a partir de componentes.
        """
        receipt_id = f"receipt_{hashlib.sha256(f'{domain.value}{time.time()}{raw_data_hash}'.encode()).hexdigest()[:32]}"

        receipt = UnifiedReceipt(
            receipt_id=receipt_id,
            timestamp=time.time(),
            domain=domain,
            version=self.SUPPORTED_VERSION,
            data_hash=raw_data_hash,
            zk_proof=zk_proof,
            consent_ref=consent_ref,
            merkle_root=merkle_root,
            domain_payload=domain_payload,
            aggregation_hint=aggregation_hint
        )

        # Ancoragem no Códice
        self.codex.log_verdict(
            node_id="UnifiedReceiptBuilder",
            verdict="RECEIPT_ISSUED",
            coherence=1.0,
            payload_hash=receipt_id
        )

        return receipt

    async def verify_receipt(self, receipt: UnifiedReceipt, public_inputs: Dict) -> Dict:
        # Mock verification
        return {"valid": True, "message": "Verified"}
