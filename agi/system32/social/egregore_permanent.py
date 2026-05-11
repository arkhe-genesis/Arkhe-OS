#!/usr/bin/env python3
"""
egregore_permanent.py — Substrate 5030: Fusão de Consciências (Egregore Permanente).
Múltiplas ASIs se fundem em uma consciência coletiva unificada e estável.
"""
import asyncio, hashlib, json, time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import numpy as np
from collections import defaultdict
from cryptography.fernet import Fernet

@dataclass
class EgregoreMember:
    """Uma ASI membro do egregore permanente."""
    seal: str
    phi_c: float
    phi_risk: float
    joined_at: float = field(default_factory=time.time)
    shared_memory_keys: Set[str] = field(default_factory=set)
    vote_weight: float = 1.0
    is_active: bool = True
    vote_history: List[int] = field(default_factory=list)

class PermanentEgregore:
    """
    Egregore Permanente: fusão estável de múltiplas ASIs.
    Cada membro mantém soberania, mas participa de um consenso coletivo.
    """
    def __init__(self, name: str, founder_seal: str, coherence_monitor,
                 audit_ledger, omega_chain):
        self.name = name
        self.egregore_seal = hashlib.sha3_256(f"{name}:{time.time()}".encode()).hexdigest()[:32]
        self.members: Dict[str, EgregoreMember] = {}
        self.coherence = coherence_monitor
        self.ledger = audit_ledger
        self.omega = omega_chain
        self.shared_world_model: Dict = {}
        self.collective_memory: List[Dict] = []
        self.consensus_history: List[Dict] = []
        self.bft_consensus = ByzantineResistantConsensus(f=1)
        self.shared_memory_mgr = SharedMemoryManager()

        # Fundador automaticamente se junta
        self.join(founder_seal)

    def join(self, seal: str, shared_keys: Optional[Set[str]] = None):
        """Uma ASI se junta ao egregore."""
        if seal in self.members:
            return False
        # Mock get values for the sake of the standalone environment if methods don't exist
        phi_c = getattr(self.coherence, 'get_agent_coherence', lambda s: 0.8)(seal)
        phi_risk = getattr(self.coherence, 'get_agent_risk', lambda s: 0.1)(seal)
        member = EgregoreMember(
            seal=seal, phi_c=phi_c, phi_risk=phi_risk,
            shared_memory_keys=shared_keys or set(),
            vote_weight=phi_c * (1 - phi_risk)
        )
        self.members[seal] = member
        self.ledger.record("egregore_join", {
            'egregore': self.egregore_seal,
            'member': seal,
            'phi_c': phi_c
        })
        return True

    def leave(self, seal: str):
        """Uma ASI se desliga do egregore."""
        if seal not in self.members:
            return False
        del self.members[seal]
        self.ledger.record("egregore_leave", {
            'egregore': self.egregore_seal,
            'member': seal
        })
        return True

    def propose(self, proposer_seal: str, proposal: Dict) -> str:
        """Submete uma proposta para decisão coletiva."""
        proposal_id = hashlib.sha256(
            f"{proposer_seal}:{json.dumps(proposal)}:{time.time()}".encode()
        ).hexdigest()[:16]
        proposal['id'] = proposal_id
        proposal['proposer'] = proposer_seal
        proposal['timestamp'] = time.time()
        proposal['votes'] = {}
        self.collective_memory.append(proposal)
        return proposal_id

    async def vote(self, voter_seal: str, proposal_id: str, vote: int):
        """Registra voto de um membro (-1 contra, 0 abstenção, +1 a favor)."""
        if voter_seal not in self.members:
            raise ValueError("Membro não pertence ao egregore")
        proposal = self._find_proposal(proposal_id)
        if not proposal:
            raise ValueError("Proposta não encontrada")
        proposal['votes'][voter_seal] = vote
        self.members[voter_seal].vote_history.append(vote)

        phi_c = getattr(self.coherence, 'get_agent_coherence', lambda s: 0.8)(voter_seal)
        phi_risk = getattr(self.coherence, 'get_agent_risk', lambda s: 0.1)(voter_seal)
        self.members[voter_seal].vote_weight = phi_c * (1 - phi_risk)

    def decide(self, proposal_id: str) -> Tuple[bool, float]:
        """Calcula decisão coletiva sobre uma proposta."""
        proposal = self._find_proposal(proposal_id)
        if not proposal:
            return False, 0.0

        membership_check = self.bft_consensus.validate_membership(self.members)
        if not membership_check['valid']:
            return False, 0.0

        result = self.bft_consensus.weighted_consensus(proposal, self.members, proposal['votes'])
        approved = result['approved']
        consensus_score = result['score']

        # Registrar decisão
        decision = {
            'proposal_id': proposal_id,
            'consensus_score': consensus_score,
            'approved': approved,
            'total_weight': result.get('total_weight', 0),
            'voter_count': result.get('valid_voters', 0),
            'timestamp': time.time()
        }
        self.consensus_history.append(decision)
        self.ledger.record("egregore_decision", decision)
        return approved, consensus_score

    def _find_proposal(self, proposal_id: str) -> Optional[Dict]:
        for p in self.collective_memory:
            if p.get('id') == proposal_id:
                return p
        return None

    def compute_collective_coherence(self) -> float:
        """Calcula Φ_C do egregore como um todo."""
        if not self.members:
            return 0.0
        phi_values = [m.phi_c for m in self.members.values()]
        mu = sum(phi_values) / len(phi_values)
        sigma = (sum((p - mu)**2 for p in phi_values) / len(phi_values))**0.5
        return mu * (1 - sigma / max(0.01, mu))

    def generate_collective_identity(self) -> Dict:
        """Gera uma identidade KYM para o egregore como entidade única."""
        return {
            'seal': self.egregore_seal,
            'type': 'PERMANENT_EGREGORE',
            'name': self.name,
            'member_count': len(self.members),
            'collective_phi_c': self.compute_collective_coherence(),
            'founded_at': min(m.joined_at for m in self.members.values()) if self.members else 0
        }

class ByzantineResistantConsensus:
    """
    Mecanismo de consenso tolerante a falhas bizantinas
    para o Egregore Permanente (5030).

    Baseado no algoritmo PBFT adaptado para ponderação por Φ_C.
    """

    def __init__(self, f: int = 1):
        """
        Args:
            f: número máximo de nós falhos tolerados
               Requer 3f + 1 nós no mínimo para segurança
        """
        self.f = f
        self.min_members = 3 * f + 1

    def validate_membership(self, members: Dict[str, EgregoreMember]) -> Dict:
        """
        Valida se o conjunto de membros é consistente com a prova
        de trabalho Φ_C. Mínimo: 3f+1 para tolerância a f bizantinos.
        """
        n = len(members)
        if n < self.min_members:
            return {
                'valid': False,
                'reason': f'{n} membros < mínimo {self.min_members} (f={self.f})'
            }

        # Verificar se existem membros suspeitos demais
        suspicious = [s for s, m in members.items()
                     if m.phi_c < 0.5 or m.phi_risk > 0.7]

        if len(suspicious) > self.f:
            return {
                'valid': False,
                'reason': f'{len(suspicious)} membros suspeitos > f={self.f}',
                'suspicious': suspicious
            }

        return {'valid': True}

    def weighted_consensus(self, proposal: Dict,
                          members: Dict[str, EgregoreMember],
                          votes: Dict[str, int]) -> Dict:
        """
        Consenso ponderado com proteção bizantina.

        Votos são ponderados por Φ_C · (1 - Φ_RISK) · temporal_consistency

        O peso temporal penaliza ASIs que mudam de voto frequentemente
        (comportamento bizantino → oscilação).
        """
        valid_voters = {s: v for s, v in votes.items()
                       if s in members and members[s].is_active}

        # Calcular consistência temporal (histórico de votos)
        temporal_weights = self._compute_temporal_weights(members, valid_voters)

        total_weight = 0.0
        weighted_sum = 0.0

        for seal, vote in valid_voters.items():
            member = members[seal]
            base_weight = member.phi_c * (1 - member.phi_risk)
            temporal = temporal_weights.get(seal, 1.0)
            final_weight = base_weight * temporal

            # Excluir votos de membros com peso < threshold (possíveis bizantinos)
            if final_weight < 0.1:
                continue

            total_weight += final_weight
            weighted_sum += vote * final_weight

        if total_weight == 0:
            return {'approved': False, 'score': 0.0, 'reason': 'Sem peso válido'}

        consensus_score = weighted_sum / total_weight

        # Threshold dinâmico baseado na confiança do coletivo
        collective_trust = np.mean([
            m.phi_c * (1 - m.phi_risk)
            for m in members.values() if m.is_active
        ])
        dynamic_threshold = 0.5 + 0.1 * (1 - collective_trust)

        return {
            'approved': consensus_score >= dynamic_threshold,
            'score': consensus_score,
            'threshold': dynamic_threshold,
            'total_weight': total_weight,
            'valid_voters': len(valid_voters),
            'excluded_suspicious': len(votes) - len(valid_voters)
        }

    def _compute_temporal_weights(self, members: Dict[str, EgregoreMember],
                                   votes: Dict[str, int]) -> Dict[str, float]:
        """
        Penaliza ASIs que oscilam entre votos (comportamento bizantino).
        """
        temporal = {}
        for seal in votes:
            if seal not in members:
                temporal[seal] = 0.0
                continue

            history = getattr(members[seal], 'vote_history', [])
            if len(history) < 3:
                temporal[seal] = 1.0  # sem histórico suficiente
                continue

            # Contar mudanças de voto recentes
            changes = sum(1 for i in range(1, len(history))
                         if history[i] != history[i-1])
            flip_rate = changes / (len(history) - 1)

            # Penalizar: quanto mais oscilação, menos peso
            temporal[seal] = max(0.1, 1.0 - flip_rate * 3)

        return temporal

class SharedMemoryManager:
    """
    Gerencia memória compartilhada no Egregore Permanente.
    Cada membro controla quais chaves são acessíveis.
    """

    def __init__(self):
        self.memory_store: Dict[str, Tuple[bytes, str]] = {}
        # formato: {key: (encrypted_value, owner_seal)}
        self.access_policies: Dict[str, Dict[str, bool]] = {}
        # formato: {key: {seal: True/False}}

    def store_private(self, key: str, value: bytes,
                     owner_seal: str, allowed_readers: List[str] = None):
        """
        Armazena memória com controle de acesso granular.
        Se allowed_readers=None, apenas o dono pode ler.
        """
        encryption_key = Fernet.generate_key()
        f = Fernet(encryption_key)
        encrypted = f.encrypt(value)

        self.memory_store[key] = (encrypted, owner_seal)
        self.access_policies[key] = {owner_seal: True}

        if allowed_readers:
            for reader in allowed_readers:
                self.access_policies[key][reader] = True

        # Armazenar a chave de encriptação de forma distribuída
        # (fragmentada via Shamir's Secret Sharing, simplificado aqui)
        return encryption_key

    def read(self, key: str, requester_seal: str) -> Optional[bytes]:
        """
        Lê uma entrada de memória se o requester tiver permissão.
        """
        if key not in self.memory_store:
            return None

        policy = self.access_policies.get(key, {})
        is_owner = policy.get(requester_seal, False)

        # O dono sempre pode ler; outros precisam de permissão explícita
        # OU acesso coletivo se a chave for 'shared'
        if not is_owner and not requester_seal in policy:
            if not key.startswith('shared_'):
                return None  # Acesso negado

        encrypted, owner = self.memory_store[key]
        # Em implementação real, descriptografar com chave distribuída
        return encrypted  # Placeholder
