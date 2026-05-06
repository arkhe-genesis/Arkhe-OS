# audit_logger.py — Logger imutável para decisões automatizadas

import asyncio
import time
import hashlib
import json
import logging
import hmac
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto

# Fallback para nacl se não estiver disponível
try:
    import nacl.signing
    HAS_NACL = True
except ImportError:
    HAS_NACL = False

from codex_crystal import CrystalCodexMemory

class DecisionType(Enum):
    """Tipos de decisões automatizadas que requerem auditoria."""
    PROACTIVE_ALERT = auto()
    RECOVERY_ACTION = auto()
    MODEL_PROMOTION = auto()
    THRESHOLD_ADJUSTMENT = auto()
    ROLLBACK_EXECUTION = auto()
    MANUAL_OVERRIDE = auto()

@dataclass
class AuditRecord:
    """Registro imutável de uma decisão automatizada."""
    decision_id: str
    decision_type: DecisionType
    timestamp: float
    causal_clock: Dict[str, int]
    context: Dict[str, Any]
    explainability: Dict[str, Any]
    compliance_tags: List[str]
    expected_impact: Dict[str, float]
    signature: str
    merkle_root: Optional[str] = None

class AuditLogger:
    """
    Logger imutável para decisões automatizadas da Catedral.
    Cada registro é assinado, gravado no Códice e replicado cross-region.
    """

    def __init__(self, codex: CrystalCodexMemory, signing_key_bytes: bytes):
        self.codex = codex
        self.key_bytes = signing_key_bytes
        self._record_counter = 0

        if HAS_NACL:
            self.signing_key = nacl.signing.SigningKey(signing_key_bytes)
            self.verify_key = self.signing_key.verify_key
        else:
            logging.warning("[AUDIT] PyNaCl não encontrado. Usando HMAC-SHA256 para simulação de assinatura.")

    async def log_decision(
        self,
        decision_type: DecisionType,
        context: Dict[str, Any],
        explainability: Dict[str, Any],
        compliance_tags: List[str],
        expected_impact: Dict[str, float],
        causal_clock: Optional[Dict[str, int]] = None
    ) -> AuditRecord:
        """Registra uma decisão automatizada de forma imutável e auditável."""
        decision_id = f"dec_{int(time.time() * 1e6)}_{self._record_counter}"
        self._record_counter += 1

        if causal_clock is None:
            causal_clock = {"cathedral": int(time.time())}

        record = AuditRecord(
            decision_id=decision_id,
            decision_type=decision_type,
            timestamp=time.time(),
            causal_clock=causal_clock,
            context=context,
            explainability=explainability,
            compliance_tags=compliance_tags,
            expected_impact=expected_impact,
            signature=""
        )

        # Assina o registro
        record_dict = asdict(record)
        record_dict.pop("signature")
        record_dict.pop("merkle_root")
        # Normaliza o enum para o hash
        record_dict["decision_type"] = record_dict["decision_type"].name

        message = json.dumps(record_dict, sort_keys=True).encode()

        if HAS_NACL:
            signed = self.signing_key.sign(message)
            record.signature = signed.signature.hex()
        else:
            # Simulação com HMAC
            sig = hmac.new(self.key_bytes, message, hashlib.sha256).hexdigest()
            record.signature = sig

        # Grava no Códice Cristalino
        merkle_root = await self.codex.store_audit_record(record)
        record.merkle_root = merkle_root

        logging.info(f"[AUDIT] Decisão registrada: {decision_id} ({decision_type.name})")
        return record

    def verify_record_integrity(self, record: AuditRecord) -> bool:
        """Verifica integridade e autenticidade de um registro."""
        record_dict = asdict(record)
        record_dict.pop("signature")
        record_dict.pop("merkle_root")
        record_dict["decision_type"] = record_dict["decision_type"].name

        message = json.dumps(record_dict, sort_keys=True).encode()

        if HAS_NACL:
            try:
                self.verify_key.verify(message, bytes.fromhex(record.signature))
                return True
            except Exception:
                return False
        else:
            expected = hmac.new(self.key_bytes, message, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, record.signature)

    async def get_decision(self, decision_id: str) -> Optional[AuditRecord]:
        return await self.codex.get_audit_record(decision_id)

    async def query_decisions(self, **kwargs) -> List[AuditRecord]:
        return await self.codex.query_audit_records(**kwargs)
