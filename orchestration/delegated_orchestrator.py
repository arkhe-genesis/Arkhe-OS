import hashlib
import time
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class AgentProposal:
    agent_id: str
    operation: str
    payload: Dict[str, Any]
    phi_c: float
    nonce: str
    canonical_seal: Optional[str] = None

    def canonical_hash(self) -> str:
        """Gerar hash canônico da proposta."""
        # A proposta json string canônica
        proposal_dict = {
            "agent_id": self.agent_id,
            "operation": self.operation,
            "payload": self.payload,
            "phi_c": self.phi_c,
            "nonce": self.nonce
        }
        proposal_json = json.dumps(proposal_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha3_256(proposal_json.encode()).hexdigest()

@dataclass
class ValidationResult:
    approved: bool = False
    rejected: bool = False
    reason: str = ""
    orchestrator_seal: Optional[str] = None
    validated_at: float = 0.0

class DelegatedOrchestrator:
    def __init__(self, orchestrator_id: str = "orchestrator_01"):
        self.orchestrator_id = orchestrator_id
        self._used_nonces = set()

    async def validate_proposal(self, proposal: AgentProposal) -> ValidationResult:
        # 1. Validar coerência Φ_C
        if proposal.phi_c < 0.95:
            return ValidationResult(rejected=True, reason="phi_c_below_threshold")

        # 2. Verificar selo canônico
        if not proposal.canonical_seal:
            return ValidationResult(rejected=True, reason="missing_canonical_seal")

        # Verificar se o selo bate com o hash canônico
        if proposal.canonical_seal != proposal.canonical_hash():
            return ValidationResult(rejected=True, reason="invalid_canonical_seal")

        # 3. Verificar Capsicum status do agente (via /proc)
        if not await self._verify_capsicum_mode(proposal.agent_id):
            return ValidationResult(rejected=True, reason="agent_not_in_capsicum")

        # 4. Verificar nonce anti-replay
        if await self._nonce_already_used(proposal.nonce):
            return ValidationResult(rejected=True, reason="replay_detected")

        # 5. Gerar selo do orquestrador
        orchestrator_seal = hashlib.sha3_256(
            f"{proposal.canonical_hash()}:{proposal.agent_id}:{time.time()}".encode()
        ).hexdigest()

        return ValidationResult(
            approved=True,
            orchestrator_seal=orchestrator_seal,
            validated_at=time.time()
        )

    async def _verify_capsicum_mode(self, agent_id: str) -> bool:
        """Simula verificação do capability mode do agente via /proc/[pid]/status."""
        # Em produção verificaria o `/proc/<pid>/status` procurando `CapBnd`
        return True

    async def _nonce_already_used(self, nonce: str) -> bool:
        """Verifica cache de nonces recentes para prevenir ataques de replay."""
        if nonce in self._used_nonces:
            return True
        self._used_nonces.add(nonce)
        return False

class MultiOrchestratorConsensus:
    def __init__(self, orchestrators: List[DelegatedOrchestrator]):
        self.orchestrators = orchestrators

    async def validate_consensus(self, proposal: AgentProposal) -> ValidationResult:
        """Busca consenso entre múltiplos orquestradores para evitar ponto único de falha."""
        results = await asyncio.gather(*(o.validate_proposal(proposal) for o in self.orchestrators))

        approved_count = sum(1 for r in results if r.approved)
        required_consensus = len(self.orchestrators) // 2 + 1

        if approved_count >= required_consensus:
            # Retorna o resultado do primeiro que aprovou (ou pode combinar selos)
            for r in results:
                if r.approved:
                    return r

        return ValidationResult(rejected=True, reason="consensus_failed")
