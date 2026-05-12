#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/dao/governance.py — DAO Arkhe para Governança Constitucional
Sistema descentralizado para evolução dos princípios constitucionais.
Baseado em: MAC (Multi-Agent Constitutional) learning + votação on-chain.
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum, auto
import numpy as np

class ProposalStatus(Enum):
    """Status de uma proposta de governança."""
    DRAFT = auto()
    PENDING = auto()      # Aguardando votação
    ACTIVE = auto()       # Em votação
    APPROVED = auto()     # Aprovada, aguardando implementação
    REJECTED = auto()     # Rejeitada
    IMPLEMENTED = auto()  # Implementada na constituição
    EXPIRED = auto()      # Expirou sem quórum

@dataclass
class GovernanceProposal:
    """Proposta de alteração constitucional."""
    proposal_id: str
    title: str
    description: str
    amendment_type: str  # "add_principle", "modify_weight", "new_rule", etc.
    target_domain: Optional[str]
    proposed_change: Dict
    proposer: str
    proposer_signature: str
    created_at: float
    voting_starts: float
    voting_ends: float
    status: ProposalStatus = ProposalStatus.DRAFT
    votes: Dict[str, Dict] = field(default_factory=dict)  # voter_id -> {vote, stake, timestamp}
    quorum_required: float = 0.1  # 10% dos stakeholders
    approval_threshold: float = 0.66  # 2/3 para aprovação

    def canonical_hash(self) -> str:
        """Hash canônico da proposta para integridade."""
        data = {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "amendment_type": self.amendment_type,
            "target_domain": self.target_domain,
            "proposed_change": self.proposed_change,
            "created_at": self.created_at,
            "proposer": self.proposer
        }
        return hashlib.sha3_256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

    def get_vote_summary(self) -> Dict:
        """Retorna resumo dos votos atuais."""
        if not self.votes:
            return {"approve": 0, "reject": 0, "total_stake": 0}

        approve_stake = sum(
            v["stake"] for v in self.votes.values() if v["vote"] == "approve"
        )
        reject_stake = sum(
            v["stake"] for v in self.votes.values() if v["vote"] == "reject"
        )
        total_stake = approve_stake + reject_stake

        return {
            "approve": approve_stake,
            "reject": reject_stake,
            "total_stake": total_stake,
            "approval_rate": approve_stake / max(0.001, total_stake),
            "participation_rate": total_stake,  # Simplificado
            "quorum_met": total_stake >= self.quorum_required,
            "approval_threshold_met": (approve_stake / max(0.001, total_stake)) >= self.approval_threshold
        }

class DAOArkheGovernance:
    """
    DAO Arkhe para governança descentralizada da Constituição.

    Características:
    - Propostas de alteração constitucional com votação ponderada por stake
    - MAC learning: princípios evoluem baseado em casos reais de verificação
    - Transparência total: todas as propostas e votos são públicos
    - Resistência a captura: múltiplos mecanismos de defesa contra centralização
    """

    def __init__(self, initial_stake_distribution: Optional[Dict[str, float]] = None):
        self.proposals: Dict[str, GovernanceProposal] = {}
        self.stake_distribution = initial_stake_distribution or {}
        self._constitution_history: List[Dict] = []  # Histórico de alterações
        self._mac_learning_buffer: List[Dict] = []  # Casos para aprendizado MAC

    def create_proposal(
        self,
        title: str,
        description: str,
        amendment_type: str,
        proposed_change: Dict,
        proposer: str,
        proposer_signature: str,
        target_domain: Optional[str] = None,
        voting_duration_days: int = 7
    ) -> str:
        """Cria nova proposta de governança."""
        # Gerar ID único
        proposal_id = hashlib.sha3_256(
            f"{title}:{proposer}:{time.time()}".encode()
        ).hexdigest()[:16]

        now = time.time()
        proposal = GovernanceProposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            amendment_type=amendment_type,
            target_domain=target_domain,
            proposed_change=proposed_change,
            proposer=proposer,
            proposer_signature=proposer_signature,
            created_at=now,
            voting_starts=now + 86400,  # 24h para preparação
            voting_ends=now + (voting_duration_days * 86400),
            status=ProposalStatus.PENDING
        )

        self.proposals[proposal_id] = proposal
        return proposal_id

    def cast_vote(
        self,
        proposal_id: str,
        voter: str,
        vote: str,  # "approve" or "reject"
        stake: float,
        voter_signature: str
    ) -> Dict:
        """Registra voto em uma proposta."""
        if proposal_id not in self.proposals:
            raise ValueError(f"Proposta {proposal_id} não encontrada")

        proposal = self.proposals[proposal_id]

        # Verificar período de votação
        now = time.time()
        if now < proposal.voting_starts:
            raise ValueError("Votação ainda não iniciou")
        if now > proposal.voting_ends:
            raise ValueError("Votação encerrada")
        if proposal.status != ProposalStatus.ACTIVE:
            proposal.status = ProposalStatus.ACTIVE

        # Verificar stake do votante (simulado)
        voter_stake = self.stake_distribution.get(voter, 0.0)
        if stake > voter_stake:
            raise ValueError(f"Stake insuficiente: máximo {voter_stake}")

        # Registrar voto
        proposal.votes[voter] = {
            "vote": vote,
            "stake": stake,
            "timestamp": now,
            "signature": voter_signature
        }

        # Verificar se votação pode ser finalizada
        self._check_proposal_completion(proposal_id)

        return proposal.get_vote_summary()

    def _check_proposal_completion(self, proposal_id: str):
        """Verifica se proposta atingiu condições para finalização."""
        proposal = self.proposals[proposal_id]
        summary = proposal.get_vote_summary()
        now = time.time()

        # Condição 1: Tempo expirado
        if now > proposal.voting_ends:
            if summary["quorum_met"] and summary["approval_threshold_met"]:
                proposal.status = ProposalStatus.APPROVED
                self._implement_proposal(proposal)
            else:
                proposal.status = ProposalStatus.REJECTED
            return

        # Condição 2: Quórum e aprovação atingidos antecipadamente
        if summary["quorum_met"] and summary["approval_threshold_met"]:
            # Esperar 24h para votos tardios (simulado)
            if now > proposal.voting_starts + 86400:
                proposal.status = ProposalStatus.APPROVED
                self._implement_proposal(proposal)

    def _implement_proposal(self, proposal: GovernanceProposal):
        """Implementa proposta aprovada na constituição."""
        # Em produção: atualizar constituição em todos os nós
        # Aqui: registrar no histórico para auditoria
        self._constitution_history.append({
            "proposal_id": proposal.proposal_id,
            "amendment_type": proposal.amendment_type,
            "target_domain": proposal.target_domain,
            "proposed_change": proposal.proposed_change,
            "implemented_at": time.time(),
            "implemented_by": "DAO_CONSENSUS"
        })
        proposal.status = ProposalStatus.IMPLEMENTED

    def mac_learning_update(self, case_result: Dict):
        """
        Atualiza aprendizado MAC (Multi-Agent Constitutional).
        Casos de verificação alimentam refinamento dos princípios.
        """
        # Buffer de casos para aprendizado
        self._mac_learning_buffer.append({
            "claim": case_result.get("claim"),
            "verdict": case_result.get("verdict"),
            "confidence": case_result.get("confidence"),
            "principles_applied": case_result.get("principles"),
            "outcome": case_result.get("outcome"),  # "correct", "false_positive", etc.
            "timestamp": time.time()
        })

        # Trigger de aprendizado periódico (simulado)
        if len(self._mac_learning_buffer) >= 100:
            self._run_mac_learning_cycle()

    def _run_mac_learning_cycle(self):
        """Executa ciclo de aprendizado MAC para refinar princípios."""
        # Em produção: treinar modelo de ajuste de pesos
        # Aqui: heurística simplificada
        from collections import defaultdict

        # Analisar casos recentes
        principle_performance = defaultdict(list)
        for case in self._mac_learning_buffer[-100:]:
            for principle in case.get("principles_applied", []):
                # Penalizar princípios que levaram a falsos positivos
                if case["outcome"] == "false_positive":
                    principle_performance[principle].append(-0.01)
                elif case["outcome"] == "false_negative":
                    principle_performance[principle].append(-0.02)
                else:
                    principle_performance[principle].append(0.0)

        # Sugerir ajustes de peso (em produção: criar proposta automática)
        adjustments = {}
        for principle, scores in principle_performance.items():
            avg_score = np.mean(scores)
            if abs(avg_score) > 0.005:  # Threshold para sugestão
                adjustments[principle] = {
                    "current_weight": 0.2,  # Placeholder
                    "suggested_adjustment": avg_score * 0.1,
                    "rationale": f"Performance média: {avg_score:.4f}"
                }

        # Limpar buffer
        self._mac_learning_buffer = []

        return adjustments

    def verify_signature(self, signature: str, payload: Dict) -> bool:
        """Verifica assinatura criptográfica (simulado)."""
        # Em produção: verificar com chaves públicas dos stakeholders
        # Aqui: validação simplificada
        expected = hashlib.sha3_256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        return signature.startswith(expected[:16])

    def get_active_proposals_count(self) -> int:
        """Retorna número de propostas ativas."""
        return sum(
            1 for p in self.proposals.values()
            if p.status in [ProposalStatus.PENDING, ProposalStatus.ACTIVE]
        )

    def get_proposal(self, proposal_id: str) -> Optional[Dict]:
        """Retorna detalhes de uma proposta."""
        if proposal_id not in self.proposals:
            return None
        proposal = self.proposals[proposal_id]
        return {
            **asdict(proposal),
            "vote_summary": proposal.get_vote_summary(),
            "status": proposal.status.name
        }
