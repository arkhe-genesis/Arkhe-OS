import time
import uuid
import hashlib
import json
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Dict, List, Optional, Any

class DecisionType(Enum):
    PROACTIVE_ALERT = auto()
    RECOVERY_ACTION = auto()
    MANUAL_OVERRIDE = auto()
    POLICY_CHANGE = auto()
    DATA_PROCESSING = auto()
    FIRMWARE_CHECKPOINT = auto()
    FIRMWARE_COMMIT = auto()
    FIRMWARE_ROLLBACK = auto()
    FORENSIC_INVESTIGATION = auto()
    CROSS_JURISDICTION_AUDIT = auto()
    CROSS_BORDER_MIGRATION = auto()
    FEDERATED_LEARNING_ROUND = auto()
    DATA_RECONCILIATION = auto()
    COUNCIL_OF_MIRRORS_AUDIT = auto()
    TOPOLOGICAL_CONFIG_REPROG = auto()
    ZK_MESH_VERIFICATION = auto()
    DISORDER_BENCHMARK = auto()
    FEDTERNARY_AGGREGATION = auto()

@dataclass
class AuditRecord:
    decision_id: str
    decision_type: DecisionType
    timestamp: float
    context: Dict[str, Any]
    explainability: Dict[str, Any]
    compliance_tags: List[str]
    expected_impact: Dict[str, Any]
    merkle_root: Optional[str] = None
    signature: Optional[str] = None
    model_version: Optional[str] = None

    def to_dict(self):
        d = asdict(self)
        d['decision_type'] = self.decision_type.name
        return d

class AuditLogger:
    def __init__(self):
        self.ledger: Dict[str, AuditRecord] = {}

    async def log_decision(
        self,
        decision_type: DecisionType,
        context: Dict[str, Any],
        explainability: Dict[str, Any],
        compliance_tags: List[str],
        expected_impact: Dict[str, Any],
        model_version: Optional[str] = None
    ) -> str:
        decision_id = f"dec_{int(time.time() * 1e6)}_{uuid.uuid4().hex[:6]}"
        record = AuditRecord(
            decision_id=decision_id,
            decision_type=decision_type,
            timestamp=time.time(),
            context=context,
            explainability=explainability,
            compliance_tags=compliance_tags,
            expected_impact=expected_impact,
            model_version=model_version
        )

        # Calculate a simple "merkle_root" as a hash of the record data
        record_json = json.dumps(record.to_dict(), sort_keys=True, default=str)
        record.merkle_root = hashlib.sha256(record_json.encode()).hexdigest()
        record.signature = f"sig_{record.merkle_root[:16]}" # Mock signature

        self.ledger[decision_id] = record
        return decision_id

    async def get_decision(self, decision_id: str) -> Optional[AuditRecord]:
        return self.ledger.get(decision_id)

    def verify_signature(self, record: AuditRecord) -> bool:
        """Verifica a assinatura digital do registro (Simulado)."""
        if not record.signature: return False
        return record.signature.startswith("sig_")

    def verify_hash_chain(self, record: AuditRecord) -> bool:
        """Verifica a integridade do hash do registro."""
        # For verification, we must replicate exactly how the hash was created in log_decision
        # In log_decision:
        #   record = AuditRecord(..., merkle_root=None, signature=None, ...)
        #   record_json = json.dumps(record.to_dict(), sort_keys=True, default=str)
        #   record.merkle_root = hashlib.sha256(record_json.encode()).hexdigest()

        data = record.to_dict()
        data['merkle_root'] = None
        data['signature'] = None

        computed = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
        return computed == record.merkle_root

    def query(self, decision_type: Optional[DecisionType] = None, limit: int = 10) -> List[AuditRecord]:
        results = list(self.ledger.values())
        if decision_type:
            results = [r for r in results if r.decision_type == decision_type]

        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]
