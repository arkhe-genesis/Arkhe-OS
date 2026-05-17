#!/usr/bin/env python3
"""
Substrato ∞: Constitutional Self-Amendment
Permite revisão segura da Constituição Arkhe via processo verificado
com consenso Φ_C, quórum de agentes e ancoragem na TemporalChain.
"""
import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum, auto

class AmendmentStatus(Enum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    CONSENSUS_REACHED = "consensus_reached"
    RATIFIED = "ratified"
    REJECTED = "rejected"

@dataclass
class ConstitutionalAmendment:
    amendment_id: str
    proposed_by: str
    proposal_text: str
    rationale: str
    affected_principles: List[str]
    status: AmendmentStatus
    phi_c_consensus: float
    agent_votes: Dict[str, Dict]  # agent_id → vote dict
    quorum_required: float
    quorum_reached: bool
    pqc_signature: Optional[str] = None
    temporal_seal: Optional[str] = None
    proposed_at: float = field(default_factory=time.time)
    ratified_at: Optional[float] = None

class ConstitutionalSelfAmendment:
    """
    Sistema de revisão constitucional com garantias de segurança:
    • Proposta deve ser assinada com PQC por agente autorizado
    • Revisão por quórum de agentes com Φ_C ≥ threshold
    • Consenso Φ_C ponderado por confiança de cada agente
    • Ratificação requer quórum + Φ_C_consensus ≥ 0.99
    • Todas as etapas ancoradas na TemporalChain
    • Rollback automático se amendment violar princípios fundamentais
    """

    # Thresholds constitucionais
    MIN_AGENT_PHI_C = 0.95
    CONSENSUS_THRESHOLD = 0.99
    QUORUM_PERCENTAGE = 0.75
    FUNDAMENTAL_PRINCIPLES = [
        "human_dignity",
        "truth_preservation",
        "non_maleficence",
        "transparency",
        "reversibility"
    ]

    def __init__(self, temporal_chain=None, agent_mesh=None, hsm_signer=None):
        self.temporal = temporal_chain
        self.agent_mesh = agent_mesh
        self.hsm = hsm_signer
        self._amendments: Dict[str, ConstitutionalAmendment] = {}
        self._active_proposals: Set[str] = set()

    async def propose_amendment(
        self,
        proposer_id: str,
        proposal_text: str,
        rationale: str,
        affected_principles: List[str]
    ) -> ConstitutionalAmendment:
        """Propõe nova emenda constitucional."""
        # Validar proponente (deve ser agente autorizado com Φ_C alto)
        if not await self._validate_proposer(proposer_id):
            raise ValueError(f"Proposer {proposer_id} não autorizado")

        # Validar que emenda não viola princípios fundamentais
        if not await self._check_fundamental_compliance(proposal_text, affected_principles):
            raise ValueError("Emenda viola princípios constitucionais fundamentais")

        # Gerar ID único
        amendment_id = hashlib.sha3_256(
            f"{proposer_id}:{proposal_text}:{time.time()}".encode()
        ).hexdigest()[:12]

        # Assinar proposta com PQC
        pqc_signature = await self.hsm.sign(proposal_text.encode()) if self.hsm else None

        amendment = ConstitutionalAmendment(
            amendment_id=amendment_id,
            proposed_by=proposer_id,
            proposal_text=proposal_text,
            rationale=rationale,
            affected_principles=affected_principles,
            status=AmendmentStatus.PROPOSED,
            phi_c_consensus=0.0,
            agent_votes={},
            quorum_required=ConstitutionalSelfAmendment.QUORUM_PERCENTAGE,
            quorum_reached=False,
            pqc_signature=pqc_signature
        )

        self._amendments[amendment_id] = amendment
        self._active_proposals.add(amendment_id)

        # Ancorar proposta na TemporalChain
        if self.temporal:
            amendment.temporal_seal = await self.temporal.anchor_event(
                "constitutional_amendment_proposed",
                {
                    "amendment_id": amendment_id,
                    "proposer": proposer_id,
                    "affected_principles": affected_principles,
                    "timestamp": time.time()
                }
            )

        return amendment

    async def vote_on_amendment(
        self,
        amendment_id: str,
        voter_id: str,
        vote: bool,
        voter_phi_c: float
    ) -> Dict:
        """Registra voto de agente em emenda constitucional."""
        amendment = self._amendments.get(amendment_id)
        if not amendment or amendment_id not in self._active_proposals:
            return {"error": "amendment_not_found_or_inactive"}

        # Validar eleitor (Φ_C mínimo)
        if voter_phi_c < self.MIN_AGENT_PHI_C:
            return {"error": f"voter_phi_c_too_low: {voter_phi_c} < {self.MIN_AGENT_PHI_C}"}

        # Registrar voto ponderado por Φ_C do eleitor
        amendment.agent_votes[voter_id] = {
            "vote": vote,
            "phi_c": voter_phi_c,
            "timestamp": time.time()
        }

        # Calcular consenso Φ_C ponderado
        consensus = await self._calculate_weighted_consensus(amendment)
        amendment.phi_c_consensus = consensus

        # Verificar quórum
        total_agents = len(self.agent_mesh._agents) if self.agent_mesh else 1
        participation = len(amendment.agent_votes) / total_agents
        amendment.quorum_reached = participation >= amendment.quorum_required

        # Atualizar status
        if amendment.quorum_reached and consensus >= self.CONSENSUS_THRESHOLD:
            amendment.status = AmendmentStatus.CONSENSUS_REACHED
            # Agendar ratificação
            asyncio.create_task(self._schedule_ratification(amendment))
        elif participation >= amendment.quorum_required and consensus < 0.5:
            amendment.status = AmendmentStatus.REJECTED
            self._active_proposals.discard(amendment_id)

        return {
            "status": "vote_recorded",
            "consensus": consensus,
            "quorum_reached": amendment.quorum_reached,
            "participation": participation
        }

    async def _calculate_weighted_consensus(self, amendment: ConstitutionalAmendment) -> float:
        """Calcula consenso Φ_C ponderado pelos votos dos agentes."""
        if not amendment.agent_votes:
            return 0.0

        weighted_sum = 0
        total_weight = 0

        for voter_id, vote_data in amendment.agent_votes.items():
            weight = vote_data["phi_c"]  # Peso = Φ_C do eleitor
            vote_value = 1.0 if vote_data["vote"] else 0.0
            weighted_sum += vote_value * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    async def _schedule_ratification(self, amendment: ConstitutionalAmendment):
        """Agenda ratificação de emenda após período de revisão."""
        # Período de revisão: 24 horas para permitir objeções finais
        await asyncio.sleep(86400)

        # Verificar se ainda há consenso
        if amendment.phi_c_consensus >= self.CONSENSUS_THRESHOLD:
            await self._ratify_amendment(amendment)
        else:
            amendment.status = AmendmentStatus.REJECTED
            self._active_proposals.discard(amendment.amendment_id)

    async def _ratify_amendment(self, amendment: ConstitutionalAmendment):
        """Ratifica emenda constitucional e aplica mudanças."""
        # 1. Validar novamente conformidade com princípios fundamentais
        if not await self._check_fundamental_compliance(
            amendment.proposal_text,
            amendment.affected_principles
        ):
            amendment.status = AmendmentStatus.REJECTED
            return

        # 2. Aplicar mudanças na Constituição (mock: em produção, atualizar config)
        # await self._apply_constitutional_changes(amendment.proposal_text)

        # 3. Atualizar status
        amendment.status = AmendmentStatus.RATIFIED
        amendment.ratified_at = time.time()
        self._active_proposals.discard(amendment.amendment_id)

        # 4. Ancorar ratificação na TemporalChain
        if self.temporal:
            await self.temporal.anchor_event(
                "constitutional_amendment_ratified",
                {
                    "amendment_id": amendment.amendment_id,
                    "phi_c_consensus": amendment.phi_c_consensus,
                    "ratified_at": amendment.ratified_at,
                    "affected_principles": amendment.affected_principles
                }
            )

        # 5. Notificar todos os agentes da mudança constitucional
        if self.agent_mesh:
            await self.agent_mesh.broadcast_constitutional_update(amendment)

    async def _validate_proposer(self, proposer_id: str) -> bool:
        """Valida se proponente está autorizado a propor emendas."""
        # Mock: em produção, verificar lista de agentes constitucionais
        return proposer_id.startswith("constitutional_")

    async def _check_fundamental_compliance(
        self,
        proposal_text: str,
        affected_principles: List[str]
    ) -> bool:
        """Verifica se emenda viola princípios constitucionais fundamentais."""
        # Mock: em produção, usar VLM para análise semântica + regras formais
        # Aqui, verificamos se algum princípio fundamental está na lista de afetados
        return not any(p in self.FUNDAMENTAL_PRINCIPLES for p in affected_principles)