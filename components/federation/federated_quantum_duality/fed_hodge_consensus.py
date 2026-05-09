# federation/federated_quantum_duality/fed_hodge_consensus.py
# Protocolo de consenso para dualidade quântica federada ★_ℋ^fed

import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import hashlib
import time
from collections import defaultdict

class ConsensusPhase(Enum):
    """Fases do protocolo de consenso dual."""
    PROPOSAL = auto()
    VOTE = auto()
    COMMIT = auto()
    FINALIZE = auto()

@dataclass
class DualOperatorProposal:
    """Proposta de operador dual para consenso federado."""
    proposal_id: str
    operator_hash: str  # hash do operador original O
    dual_operator_hash: str  # hash de ★_ℋ(O) computado localmente
    node_id: str
    timestamp: float
    signature: Optional[bytes] = None  # assinatura Ed25519 da proposta

    def verify_signature(self, public_key: bytes) -> bool:
        """Verifica assinatura da proposta (simplificação)."""
        if self.signature is None:
            return False
        # Em produção: verificar com ed25519-dalek
        return True

@dataclass
class ConsensusState:
    """Estado do consenso para uma proposta."""
    proposal: DualOperatorProposal
    votes: Dict[str, bool]  # node_id -> vote (True=accept)
    phase: ConsensusPhase
    quorum_size: int
    start_time: float

class FederatedHodgeConsensus:
    """
    Protocolo de consenso para dualidade quântica federada.

    Garante que múltiplos nós concordem sobre o resultado de ★_ℋ(O)
    mesmo com operadores de conjugação J_j locais diferentes.
    """

    def __init__(
        self,
        node_id: str,
        total_nodes: int,
        byzantine_tolerance: int,
        signing_key: bytes,
        verification_keys: Dict[str, bytes]
    ):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.byzantine_tolerance = byzantine_tolerance
        self.quorum_size = total_nodes - byzantine_tolerance
        self.signing_key = signing_key
        self.verification_keys = verification_keys

        # Estado de consensos ativos
        self.active_consensus: Dict[str, ConsensusState] = {}

        # Cache de operadores duais verificados
        self.verified_duals: Dict[str, np.ndarray] = {}

        # Canal de comunicação (simulado)
        self.message_queue: List[Dict] = []

    def propose_dual_operator(
        self,
        operator: np.ndarray,
        operator_id: str
    ) -> str:
        """
        Propõe operador dual para consenso federado.

        Returns:
            proposal_id para rastreamento
        """
        # Calcular dual local: ★_ℋ(O) = J O† J^{-1}
        dual_local = self._compute_local_dual(operator)

        # Hashes para consenso
        op_hash = hashlib.sha256(operator.tobytes()).hexdigest()
        dual_hash = hashlib.sha256(dual_local.tobytes()).hexdigest()

        # Criar proposta assinada
        proposal = DualOperatorProposal(
            proposal_id=f"dual_{operator_id}_{time.time()}",
            operator_hash=op_hash,
            dual_operator_hash=dual_hash,
            node_id=self.node_id,
            timestamp=time.time()
        )
        # Assinar proposta (simplificação)
        proposal.signature = hashlib.sha256(
            f"{proposal.proposal_id}{proposal.dual_operator_hash}".encode()
        ).digest()

        # Iniciar estado de consenso
        self.active_consensus[proposal.proposal_id] = ConsensusState(
            proposal=proposal,
            votes={},
            phase=ConsensusPhase.PROPOSAL,
            quorum_size=self.quorum_size,
            start_time=time.time()
        )

        # Broadcast proposta (simulado)
        self._broadcast({'type': 'proposal', 'data': proposal})

        return proposal.proposal_id

    def _compute_local_dual(self, operator: np.ndarray) -> np.ndarray:
        """Computa dual local ★_ℋ(O) = J O† J^{-1}."""
        # Operador de conjugação de carga J para este nó
        # Para n qubits: J = ⊗^n (iσ²) ∘ K
        n_qubits = int(np.log2(operator.shape[0]) / 2)
        if n_qubits <= 0:
            return operator.T.conj()

        # Construir J unitário
        sigma2 = np.array([[0, -1j], [1j, 0]])
        try:
            J_unitary = np.kron.reduce([1j * sigma2] * n_qubits)
        except AttributeError:
            J_unitary = 1j * sigma2
            for _ in range(1, n_qubits):
                J_unitary = np.kron(J_unitary, 1j * sigma2)

        # ★_ℋ(O) = J O† J†
        O_dag = operator.T.conj()
        return J_unitary @ O_dag @ J_unitary.T.conj()

    def process_message(self, message: Dict) -> Optional[Dict]:
        """
        Processa mensagem recebida de outro nó.

        Returns:
            Resposta a ser enviada (se aplicável)
        """
        msg_type = message.get('type')

        if msg_type == 'proposal':
            return self._handle_proposal(message['data'])
        elif msg_type == 'vote':
            return self._handle_vote(message['data'])
        elif msg_type == 'commit':
            return self._handle_commit(message['data'])

        return None

    def _handle_proposal(self, proposal: DualOperatorProposal) -> Optional[Dict]:
        """Processa proposta recebida."""
        # Verificar assinatura
        if proposal.node_id in self.verification_keys:
            if not proposal.verify_signature(self.verification_keys[proposal.node_id]):
                return None  # proposta inválida

        # Verificar se já temos este consenso
        if proposal.proposal_id in self.active_consensus:
            return None

        # Iniciar votação: computar dual local e comparar hashes
        # (em produção: verificar equivalência sob sincronização de J)
        local_accept = True  # simplificação: aceitar se assinatura válida

        # Enviar voto
        vote_msg = {
            'type': 'vote',
            'proposal_id': proposal.proposal_id,
            'voter_id': self.node_id,
            'vote': local_accept,
            'timestamp': time.time()
        }
        self._broadcast(vote_msg)

        # Atualizar estado local
        if proposal.proposal_id not in self.active_consensus:
            self.active_consensus[proposal.proposal_id] = ConsensusState(
                proposal=proposal,
                votes={self.node_id: local_accept},
                phase=ConsensusPhase.VOTE,
                quorum_size=self.quorum_size,
                start_time=time.time()
            )

        return None

    def _handle_vote(self, vote_data: Dict) -> Optional[Dict]:
        """Processa voto recebido."""
        proposal_id = vote_data['proposal_id']
        if proposal_id not in self.active_consensus:
            return None

        state = self.active_consensus[proposal_id]

        # Registrar voto
        state.votes[vote_data['voter_id']] = vote_data['vote']

        # Verificar se atingiu quórum
        accept_count = sum(1 for v in state.votes.values() if v)
        if accept_count >= state.quorum_size and state.phase == ConsensusPhase.VOTE:
            # Transicionar para COMMIT
            state.phase = ConsensusPhase.COMMIT

            # Broadcast commit
            commit_msg = {
                'type': 'commit',
                'proposal_id': proposal_id,
                'committer_id': self.node_id,
                'quorum_votes': {k: v for k, v in state.votes.items() if v},
                'timestamp': time.time()
            }
            self._broadcast(commit_msg)

            return None

        return None

    def _handle_commit(self, commit_data: Dict) -> Optional[Dict]:
        """Processa commit recebido."""
        proposal_id = commit_data['proposal_id']
        if proposal_id not in self.active_consensus:
            return None

        state = self.active_consensus[proposal_id]

        # Verificar quórum de commits (simplificação)
        if len(commit_data['quorum_votes']) >= state.quorum_size:
            # Consenso atingido: armazenar dual verificado
            # (em produção: recuperar operador dual completo via protocolo de recuperação)
            self.verified_duals[proposal_id] = None  # placeholder

            state.phase = ConsensusPhase.FINALIZE

            return {
                'type': 'consensus_reached',
                'proposal_id': proposal_id,
                'dual_operator_id': f"dual_{proposal_id}"
            }

        return None

    def get_verified_dual(self, proposal_id: str) -> Optional[np.ndarray]:
        """Recupera operador dual verificado por consenso."""
        return self.verified_duals.get(proposal_id)

    def _broadcast(self, message: Dict):
        """Simula broadcast de mensagem para outros nós."""
        # Em produção: enviar via libp2p/gossipsub
        self.message_queue.append(message)

    def get_consensus_status(self, proposal_id: str) -> Dict:
        """Retorna status de um consenso em andamento."""
        if proposal_id not in self.active_consensus:
            return {'error': 'proposal not found'}

        state = self.active_consensus[proposal_id]
        return {
            'proposal_id': proposal_id,
            'phase': state.phase.name,
            'votes_received': len(state.votes),
            'accept_votes': sum(1 for v in state.votes.values() if v),
            'quorum_size': state.quorum_size,
            'elapsed_seconds': time.time() - state.start_time
        }
