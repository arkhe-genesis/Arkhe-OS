from typing import List, Any
from enum import Enum

class ConsensusResult(Enum):
    ACCEPTED = "accepted"
    PENDING_MORE_VOTES = "pending_more_votes"
    REJECTED_DUAL_SIG_MISSING = "rejected_dual_sig_missing"

class Block:
    pass

class BeltHybridConsensus:
    """Consenso híbrido para zonas com <=2 nós físicos."""

    def __init__(self, physical_nodes: List[str], virtual_relays: int = 2):
        self.physical_nodes = physical_nodes  # ["Ceres", "Vesta"]
        self.virtual_relays = virtual_relays  # Orbiting relay satellites

    def _dual_physical_signature(self, proposal: Block) -> bool:
        return True

    def _collect_virtual_relay_votes(self, proposal: Block, timeout_s: int) -> List[Any]:
        return ["vote_1", "vote_2"]

    def propose_block(self, proposal: Block) -> ConsensusResult:
        # Fase 1: Assinatura dupla dos nós físicos (obrigatória)
        if not self._dual_physical_signature(proposal):
            return ConsensusResult.REJECTED_DUAL_SIG_MISSING

        # Fase 2: Validação assíncrona dos relays virtuais (tolerância a falhas)
        virtual_votes = self._collect_virtual_relay_votes(proposal, timeout_s=3600)

        # Regra de decisão: 2/3 dos validadores totais (físicos + virtuais)
        total_validators = len(self.physical_nodes) + self.virtual_relays
        required_votes = (2 * total_validators) // 3 + 1

        if len(virtual_votes) + len(self.physical_nodes) >= required_votes:
            return ConsensusResult.ACCEPTED
        else:
            return ConsensusResult.PENDING_MORE_VOTES
