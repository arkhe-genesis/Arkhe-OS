# forensic_audit_protocol.py — Mecanismo de Auditoria Forense Cross-Ecosystem

import hashlib
import json
import time
from enum import Enum, auto
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from audit_logger import DecisionType

class InvestigationStatus(Enum):
    REQUESTED = auto()
    AUTHORIZED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    DENIED = auto()

@dataclass
class ForensicEvidence:
    evidence_id: str
    decision_id: str
    jurisdiction: str
    zk_logic_proof: str  # Prova ZK de que a lógica seguiu o protocolo
    blind_replay_output: str # Hash do resultado da re-execução sem dados reais
    timestamp: float = field(default_factory=time.time)

class ForensicAuditManager:
    """
    Gerencia investigações forenses entre ecossistemas e jurisdições.
    Permite auditoria profunda sem expor dados de cidadãos (Blind Replay).
    """

    def __init__(self, audit_logger: Any, compliance_engine: Any):
        self.audit = audit_logger
        self.compliance = compliance_engine
        self.investigations: Dict[str, InvestigationStatus] = {}

    async def request_investigation(self, decision_id: str, requester_jurisdiction: str, reason: str) -> str:
        """Inicia uma requisição de auditoria forense."""
        investigation_id = f"inv_{hashlib.sha256(f'{decision_id}{requester_jurisdiction}'.encode()).hexdigest()[:12]}"

        # Log da requisição de auditoria
        await self.audit.log_decision(
            decision_type=DecisionType.FORENSIC_INVESTIGATION,
            context={
                "investigation_id": investigation_id,
                "decision_id": decision_id,
                "jurisdiction": requester_jurisdiction,
                "reason": reason
            },
            explainability={"natural_language": f"Auditoria forense solicitada pela jurisdição {requester_jurisdiction} para a decisão {decision_id}"},
            compliance_tags=["forensic_audit", "transparency"],
            expected_impact={"benefit": 1.0, "risk": 0.05}
        )

        self.investigations[investigation_id] = InvestigationStatus.REQUESTED
        return investigation_id

    async def generate_forensic_evidence(self, investigation_id: str, decision_id: str, target_jurisdiction: str) -> ForensicEvidence:
        """Gera evidência forense preservando a privacidade (Blind Replay)."""
        record = await self.audit.get_decision(decision_id)
        if not record:
            raise ValueError("Decision record not found")

        # 1. Blind Replay: Re-executa a lógica com os inputs originais (mas apenas gera o hash do output)
        # Em um sistema real, isso usaria um ambiente TEE (Trusted Execution Environment)
        blind_output = hashlib.sha256(json.dumps(record.context, sort_keys=True, default=str).encode()).hexdigest()

        # 2. ZK Proof (Simulado): Prova que a lógica do ComplianceEngine autorizou a decisão
        # Usamos uma string fixa para demonstração de verificação de versão da lógica
        zk_proof = "bf0ee428d47ad9f5f336e5fe193918ec" + hashlib.sha256(decision_id.encode()).hexdigest()

        evidence = ForensicEvidence(
            evidence_id=f"ev_{investigation_id}",
            decision_id=decision_id,
            jurisdiction=target_jurisdiction,
            zk_logic_proof=zk_proof,
            blind_replay_output=blind_output
        )

        self.investigations[investigation_id] = InvestigationStatus.COMPLETED

        # Log do envio da evidência
        await self.audit.log_decision(
            decision_type=DecisionType.CROSS_JURISDICTION_AUDIT,
            context={
                "investigation_id": investigation_id,
                "evidence_id": evidence.evidence_id,
                "target": target_jurisdiction
            },
            explainability={"natural_language": f"Evidência forense gerada e enviada para {target_jurisdiction}. Dados sensíveis foram preservados via Blind Replay."},
            compliance_tags=["cross_border_audit", "privacy_by_design"],
            expected_impact={"benefit": 1.0, "risk": 0.0}
        )

        return evidence

    def verify_forensic_evidence(self, evidence: ForensicEvidence, expected_logic_hash: str) -> bool:
        """Verifica a validade da evidência recebida por uma jurisdição externa."""
        # 1. Verifica se o ZK logic proof é consistente com o esperado para aquela versão do protocolo
        if not evidence.zk_logic_proof.startswith(expected_logic_hash):
            return False

        # 2. Verifica integridade temporal
        if time.time() - evidence.timestamp > 3600 * 24 * 30: # 30 dias de validade
            return False

        return True
