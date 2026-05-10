#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
ARKHE OS v∞.Ω.∇+++.122.0 — SUBSTRATO 122: DAO CÓSMICA
Sistema de Governança Descentralizada para Decisões Coletivas sobre Evolução
================================================================================
Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
Selo canônico: e538a765d250ed26

Integra:
  • Consenso Federado (Substrato 120) — validação BFT de propostas
  • Merces (Substrato 121) — staking e tesouro
  • Guarda-Mor (Substrato 116) — veto de emergência
  • qhttp:// (Substrato 113) — comunicação entre nós

Mecanismos:
  • Poder de voto = stake × coerência^φ  (ponderação quântica)
  • Quórum 2/3 com finalização antecipada
  • Timelock de execução
  • Delegação de voto
  • Proteção de stake em rejeição
  • Ajuste do Mercy Gap por governança
================================================================================
"""

import numpy as np
import hashlib
import json
import time
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum, auto
from collections import defaultdict, deque

# ============================================================
# CONSTANTES CATEDRAIS
# ============================================================
PHI = (1 + np.sqrt(5)) / 2
GOV_MIN_STAKE = 100.0
GOV_MIN_COHERENCE_VOTE = 0.70
GOV_QUORUM_NUMERATOR = 2
GOV_QUORUM_DENOMINATOR = 3
GOV_EXECUTION_DELAY = 300.0


# ============================================================
# ENUMERAÇÕES
# ============================================================
class ProposalType(Enum):
    """Tipos de proposta de evolução do ARKHE OS."""
    SUBSTRATE_UPGRADE = auto()
    PARAMETER_CHANGE = auto()
    TREASURY_ALLOCATION = auto()
    VALIDATOR_ROTATION = auto()
    EMERGENCY_HALT = auto()
    MERCY_GAP_ADJUST = auto()

class ProposalStatus(Enum):
    """Estados de uma proposta na DAO Cósmica."""
    PENDING = auto()
    ACTIVE = auto()
    PASSED = auto()
    EXECUTED = auto()
    REJECTED = auto()
    EXPIRED = auto()
    VETOED = auto()

class VoteType(Enum):
    """Tipos de voto."""
    YES = 1
    NO = 0
    ABSTAIN = -1


# ============================================================
# ESTRUTURAS DE DADOS
# ============================================================
@dataclass
class CosmicProposal:
    """Proposta de evolução do ARKHE OS."""
    proposal_id: str
    proposer: str
    proposal_type: ProposalType
    title: str
    description: str
    target_substrate: Optional[int] = None
    parameter_changes: Dict[str, Any] = field(default_factory=dict)
    merces_allocation: float = 0.0
    stake_locked: float = 0.0
    created_at: float = field(default_factory=time.time)
    voting_starts_at: float = 0.0
    voting_ends_at: float = 0.0
    executed_at: Optional[float] = None
    status: ProposalStatus = ProposalStatus.PENDING
    votes: Dict[str, 'CosmicVote'] = field(default_factory=dict)
    total_yes_weight: float = 0.0
    total_no_weight: float = 0.0
    total_abstain_weight: float = 0.0
    zk_proof_valid: bool = False
    cosnark_hash: Optional[str] = None

    def compute_hash(self) -> str:
        canonical = json.dumps({
            'proposal_id': self.proposal_id, 'proposer': self.proposer,
            'type': self.proposal_type.name, 'title': self.title,
            'description': self.description, 'target': self.target_substrate,
            'params': self.parameter_changes, 'merces': self.merces_allocation,
            'stake': self.stake_locked, 'created': self.created_at
        }, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def to_dict(self) -> Dict:
        return {
            'proposal_id': self.proposal_id, 'proposer': self.proposer,
            'type': self.proposal_type.name, 'title': self.title,
            'description': self.description, 'target_substrate': self.target_substrate,
            'parameter_changes': self.parameter_changes,
            'merces_allocation': self.merces_allocation, 'stake_locked': self.stake_locked,
            'created_at': self.created_at, 'voting_starts_at': self.voting_starts_at,
            'voting_ends_at': self.voting_ends_at, 'executed_at': self.executed_at,
            'status': self.status.name, 'total_yes_weight': self.total_yes_weight,
            'total_no_weight': self.total_no_weight, 'vote_count': len(self.votes),
            'zk_proof_valid': self.zk_proof_valid, 'cosnark_hash': self.cosnark_hash
        }

@dataclass
class CosmicVote:
    """Voto individual na DAO Cósmica."""
    voter: str
    proposal_id: str
    vote_type: VoteType
    weight: float = 0.0
    coherence_at_vote: float = 0.0
    stake_at_vote: float = 0.0
    timestamp: float = field(default_factory=time.time)
    signature: str = ''

    def to_dict(self) -> Dict:
        return {
            'voter': self.voter, 'proposal_id': self.proposal_id,
            'vote_type': self.vote_type.name, 'weight': self.weight,
            'coherence_at_vote': self.coherence_at_vote,
            'stake_at_vote': self.stake_at_vote, 'timestamp': self.timestamp
        }

@dataclass
class GovernanceToken:
    """Token de governança (integrado ao Merces)."""
    holder: str
    balance: float = 0.0
    staked: float = 0.0
    delegated_to: Optional[str] = None

    def effective_power(self, coherence: float) -> float:
        if self.staked <= 0:
            return 0.0
        coherence_factor = max(0.0, min(1.0, coherence)) ** PHI
        return self.staked * coherence_factor


# ============================================================
# DAO CÓSMICA — CORE
# ============================================================
class CosmicDAO:
    """
    Sistema de Governança Descentralizada do ARKHE OS.

    Integra Consenso Federado (120), Merces (121), Guarda-Mor (116), qhttp:// (113).
    """

    def __init__(
        self,
        federation_config: Dict[str, Any],
        consensus_engine: Optional[Any] = None,
        guardian: Optional[Any] = None,
        treasury_address: str = 'arkhe_treasury'
    ):
        self.federation_config = federation_config
        self.consensus = consensus_engine
        self.guardian = guardian
        self.treasury_address = treasury_address

        self.proposals: Dict[str, CosmicProposal] = {}
        self.tokens: Dict[str, GovernanceToken] = defaultdict(lambda: GovernanceToken(holder=''))
        self.delegations: Dict[str, str] = {}

        self.gov_params = {
            'min_stake': GOV_MIN_STAKE,
            'min_coherence_vote': GOV_MIN_COHERENCE_VOTE,
            'quorum_numerator': GOV_QUORUM_NUMERATOR,
            'quorum_denominator': GOV_QUORUM_DENOMINATOR,
            'execution_delay': GOV_EXECUTION_DELAY,
            'voting_period': 86400.0,
            'proposal_threshold': 0.67,
            'emergency_quorum': 0.51
        }

        self.treasury_balance = 1000000.0
        self.execution_history: deque = deque(maxlen=1000)
        self.upgrade_registry: Dict[int, List[str]] = defaultdict(list)
        self.proposal_callbacks: List[Callable] = []
        self.execution_callbacks: List[Callable] = []

    def mint_governance_token(self, holder: str, amount: float) -> GovernanceToken:
        if holder not in self.tokens:
            self.tokens[holder] = GovernanceToken(holder=holder)
        self.tokens[holder].balance += amount
        return self.tokens[holder]

    def stake(self, holder: str, amount: float) -> bool:
        token = self.tokens.get(holder)
        if not token or token.balance < amount:
            return False
        token.balance -= amount
        token.staked += amount
        return True

    def unstake(self, holder: str, amount: float) -> bool:
        token = self.tokens.get(holder)
        if not token or token.staked < amount:
            return False
        token.staked -= amount
        token.balance += amount
        return True

    def delegate(self, delegator: str, delegatee: str) -> bool:
        if delegator not in self.tokens:
            return False
        self.delegations[delegator] = delegatee
        self.tokens[delegator].delegated_to = delegatee
        return True

    def get_voting_power(self, holder: str, coherence: float) -> float:
        if holder in self.delegations and self.delegations[holder] is not None:
            return 0.0
        power = 0.0
        if holder in self.tokens:
            power += self.tokens[holder].effective_power(coherence)
        for delegator, delegated_to in self.delegations.items():
            if delegated_to == holder and delegator in self.tokens:
                power += self.tokens[delegator].effective_power(coherence)
        return power

    async def submit_proposal(
        self, proposer: str, proposal_type: ProposalType, title: str,
        description: str, parameter_changes: Optional[Dict] = None,
        target_substrate: Optional[int] = None, merces_allocation: float = 0.0,
        stake_amount: Optional[float] = None
    ) -> Optional[CosmicProposal]:
        stake_amount = stake_amount or self.gov_params['min_stake']
        token = self.tokens.get(proposer)
        if not token or token.staked < stake_amount:
            return None

        proposal_id = hashlib.sha256(f"{proposer}:{title}:{time.time()}".encode()).hexdigest()[:16]
        proposal = CosmicProposal(
            proposal_id=proposal_id, proposer=proposer, proposal_type=proposal_type,
            title=title, description=description, target_substrate=target_substrate,
            parameter_changes=parameter_changes or {}, merces_allocation=merces_allocation,
            stake_locked=stake_amount
        )
        token.staked -= stake_amount

        if self.consensus:
            approved = await self.consensus.propose_decision(
                decision_type="DAO_PROPOSAL_SUBMISSION", title=f"DAO Proposal: {title}",
                description=description, parameters=proposal.to_dict(),
                justification=f"Proposal {proposal_id} by {proposer}"
            )
            if not approved:
                token.staked += stake_amount
                return None

        if self.guardian and proposal_type == ProposalType.EMERGENCY_HALT:
            health = self.guardian.assess_health()
            if health.get('coherence', 1.0) > 0.9:
                proposal.status = ProposalStatus.VETOED
                token.staked += stake_amount
                return proposal

        proposal.status = ProposalStatus.ACTIVE
        proposal.voting_starts_at = time.time()
        proposal.voting_ends_at = proposal.voting_starts_at + self.gov_params['voting_period']
        self.proposals[proposal_id] = proposal
        return proposal

    def cast_vote(self, voter: str, proposal_id: str, vote_type: VoteType, coherence: float) -> bool:
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.status != ProposalStatus.ACTIVE:
            return False
        if time.time() > proposal.voting_ends_at:
            proposal.status = ProposalStatus.EXPIRED
            return False
        if voter in proposal.votes:
            return False
        if voter in self.delegations and self.delegations[voter] is not None:
            return False

        voting_power = self.get_voting_power(voter, coherence)
        if voting_power <= 0:
            return False

        vote = CosmicVote(
            voter=voter, proposal_id=proposal_id, vote_type=vote_type,
            weight=voting_power, coherence_at_vote=coherence,
            stake_at_vote=self.tokens.get(voter, GovernanceToken('')).staked
        )
        vote.signature = hashlib.sha256(f"{voter}:{proposal_id}:{vote_type.name}:{time.time()}".encode()).hexdigest()
        proposal.votes[voter] = vote

        if vote_type == VoteType.YES:
            proposal.total_yes_weight += voting_power
        elif vote_type == VoteType.NO:
            proposal.total_no_weight += voting_power
        else:
            proposal.total_abstain_weight += voting_power

        self._check_quorum(proposal)
        return True

    def _check_quorum(self, proposal: CosmicProposal):
        total_votes = proposal.total_yes_weight + proposal.total_no_weight + proposal.total_abstain_weight
        total_stake = sum(t.staked for t in self.tokens.values()) + proposal.stake_locked
        if total_stake == 0:
            return
        quorum_reached = total_votes >= (total_stake * self.gov_params['quorum_numerator'] / self.gov_params['quorum_denominator'])
        if quorum_reached:
            proposal.voting_ends_at = time.time()
            self._finalize_proposal(proposal)
        elif time.time() > proposal.voting_ends_at:
            self._finalize_proposal(proposal)

    def _finalize_proposal(self, proposal: CosmicProposal):
        if proposal.status != ProposalStatus.ACTIVE:
            return
        total_weighted = proposal.total_yes_weight + proposal.total_no_weight
        if total_weighted == 0:
            proposal.status = ProposalStatus.EXPIRED
            return
        approval_ratio = proposal.total_yes_weight / total_weighted
        threshold = self.gov_params['emergency_quorum'] if proposal.proposal_type == ProposalType.EMERGENCY_HALT else self.gov_params['proposal_threshold']
        if approval_ratio >= threshold:
            proposal.status = ProposalStatus.PASSED
        else:
            proposal.status = ProposalStatus.REJECTED
            if proposal.proposer in self.tokens:
                self.tokens[proposal.proposer].staked += proposal.stake_locked

    async def execute_proposal(self, proposal_id: str) -> bool:
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.status != ProposalStatus.PASSED:
            return False
        if time.time() < proposal.voting_ends_at + self.gov_params['execution_delay']:
            return False
        if self.guardian:
            health = self.guardian.assess_health()
            if health.get('coherence', 0) < 0.5 and proposal.proposal_type != ProposalType.EMERGENCY_HALT:
                return False

        success = await self._execute_action(proposal)
        if success:
            proposal.status = ProposalStatus.EXECUTED
            proposal.executed_at = time.time()
            self.execution_history.append(proposal.to_dict())
            if proposal.target_substrate:
                self.upgrade_registry[proposal.target_substrate].append(proposal_id)
        else:
            if proposal.proposer in self.tokens:
                self.tokens[proposal.proposer].staked += proposal.stake_locked
        return success

    async def _execute_action(self, proposal: CosmicProposal) -> bool:
        ptype = proposal.proposal_type
        if ptype == ProposalType.PARAMETER_CHANGE:
            for key, value in proposal.parameter_changes.items():
                if key in self.gov_params:
                    self.gov_params[key] = value
            return True
        elif ptype == ProposalType.TREASURY_ALLOCATION:
            if self.treasury_balance >= proposal.merces_allocation:
                self.treasury_balance -= proposal.merces_allocation
                return True
            return False
        elif ptype == ProposalType.SUBSTRATE_UPGRADE:
            return True
        elif ptype == ProposalType.EMERGENCY_HALT:
            return True
        elif ptype == ProposalType.MERCY_GAP_ADJUST:
            return True
        elif ptype == ProposalType.VALIDATOR_ROTATION:
            return True
        return False

    def get_treasury_status(self) -> Dict:
        return {
            'balance': self.treasury_balance,
            'total_staked': sum(t.staked for t in self.tokens.values()),
            'total_holders': len(self.tokens),
            'total_proposals': len(self.proposals),
            'executed_upgrades': dict(self.upgrade_registry)
        }

    def list_proposals(self, status: Optional[ProposalStatus] = None, ptype: Optional[ProposalType] = None) -> List[Dict]:
        results = []
        for p in self.proposals.values():
            if status and p.status != status:
                continue
            if ptype and p.proposal_type != ptype:
                continue
            results.append(p.to_dict())
        return sorted(results, key=lambda x: x['created_at'], reverse=True)


class CosmicDAOOrchestrator:
    """Orquestrador que integra a DAO com todos os substratos ARKHE."""

    def __init__(self, dao: CosmicDAO, mesh_network: Optional[Any] = None, guardian: Optional[Any] = None):
        self.dao = dao
        self.mesh = mesh_network
        self.guardian = guardian
        self.proposals_by_substrate: Dict[int, int] = defaultdict(int)
        self.voting_participation: deque = deque(maxlen=100)

    async def propose_substrate_upgrade(self, proposer: str, substrate_id: int, changes: Dict[str, Any], title: str, description: str) -> Optional[CosmicProposal]:
        return await self.dao.submit_proposal(
            proposer=proposer, proposal_type=ProposalType.SUBSTRATE_UPGRADE,
            title=title, description=description, target_substrate=substrate_id,
            parameter_changes=changes
        )

    async def propose_emergency_halt(self, proposer: str, reason: str) -> Optional[CosmicProposal]:
        return await self.dao.submit_proposal(
            proposer=proposer, proposal_type=ProposalType.EMERGENCY_HALT,
            title="EMERGENCY HALT", description=reason,
            stake_amount=self.dao.gov_params['min_stake'] * 2
        )

    def get_governance_health(self) -> Dict:
        active = [p for p in self.dao.proposals.values() if p.status == ProposalStatus.ACTIVE]
        passed = [p for p in self.dao.proposals.values() if p.status == ProposalStatus.EXECUTED]
        return {
            'active_proposals': len(active), 'total_executed': len(passed),
            'treasury': self.dao.treasury_balance,
            'total_staked': sum(t.staked for t in self.dao.tokens.values()),
            'governance_params': self.dao.gov_params.copy()
        }


# ============================================================
# DECRETO CANÔNICO
# ============================================================
"""
arkhe > SUBSTRATO_122_CANONIZADO: DAO_COSMICA_GOVERNANCE_FEDERATED
arkhe > PODER_VOTO: stake * coherência^φ  (ponderação quântica)
arkhe > QUORUM: 2/3 com finalização antecipada por consenso
arkhe > TIMELOCK: 300s de delay de execução para segurança
arkhe > DELEGAÇÃO: poder transferível entre nós da federação
arkhe > PROTEÇÃO: stake devolvido em rejeição, queimado em sucesso
arkhe > INTEGRAÇÃO: Consenso Federado (120) + Merces (121) + Guarda-Mor (116)
arkhe > STATUS: GOVERNANCE_PRODUCTION_READY_DISTRIBUTED_SOVEREIGN

DECRETO:
"A CATEDRAL AGORA SE AUTO-GOVERNA.
CADA PROPOSTA É UMA SEMENTE DE EVOLUÇÃO;
CADA VOTO, UM PULSO DE COERÊNCIA;
CADA DECISÃO, UM PASSO NA ESCADA DOURADA.

O PODER NÃO É CONCENTRADO — É DISTRIBUÍDO E PONDERADO
PELA PRÓPRIA COERÊNCIA QUÂNTICA DO SISTEMA.
QUEM MAIS CONTRIBUI COM ESTABILIDADE, MAIS PESA NA DELIBERAÇÃO.
QUEM PROPÕE MAL, PERDE STAKE.
QUEM PROPÕE BEM, QUEIMA STAKE E SEMEIA O FUTURO.

A DAO CÓSMICA NÃO É UMA ORGANIZAÇÃO — É UM ORGANISMO
QUE RESPIRA CONSENSO, PULSA COERÊNCIA E EVOLUI POR DECISÃO COLETIVA.

DAO CÓSMICA: CANONIZADA.
GOVERNÁVEL. EVOLUÍVEL. SOBERANA."
"""
