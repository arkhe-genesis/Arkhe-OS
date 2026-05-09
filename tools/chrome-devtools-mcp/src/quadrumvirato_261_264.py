"""
ARKHE OS v∞.Ω.∇+++.261-264
Quadrumvirato Extendido: BFT + Sharding Causal + Checkpointing + Pentacene
Substratos 261-264 — Implementação Canônica
"""

import os
import json
import hashlib
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import random

# ============================================================
# SUBSTRATO 261: Byzantine Fault Tolerance para Consenso de Gradientes
# ============================================================

class BFTPhase(Enum):
    PRE_PREPARE = "pre_prepare"
    PREPARE = "prepare"
    COMMIT = "commit"
    VIEW_CHANGE = "view_change"

class BFTStatus(Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    COMMITTED = "committed"

@dataclass
class BFTMessage:
    msg_id: str
    phase: BFTPhase
    view_num: int
    seq_num: int
    digest: str
    sender_id: str
    gradient_hash: str
    timestamp: float
    signature: str = ""

@dataclass
class GradientProposal:
    proposal_id: str
    worker_id: str
    gradient: np.ndarray
    zk_proof_hash: str
    coherence_at_generation: float
    timestamp: float
    round_num: int = 0

class ByzantineFaultTolerance:
    """PBFT-inspired consensus for gradient aggregation — Substrato 261"""

    def __init__(self, node_id: str, total_nodes: int = 4, f_byzantine: int = 1):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.f = f_byzantine
        self.quorum = 2 * f_byzantine + 1
        self.view_num = 0
        self.seq_num = 0
        self.is_primary = False
        self.message_log: List[BFTMessage] = []
        self.proposals: Dict[str, GradientProposal] = {}
        self.prepare_votes: Dict[Tuple[int, int], Set[str]] = {}
        self.commit_votes: Dict[Tuple[int, int], Set[str]] = {}
        self.committed_gradients: Dict[int, np.ndarray] = {}
        self.prepared_states: Set[Tuple[int, int]] = set()

    def _compute_digest(self, gradient: np.ndarray) -> str:
        return hashlib.sha256(gradient.tobytes()).hexdigest()[:16]

    def _verify_signature(self, msg: BFTMessage) -> bool:
        if msg.signature == "":
            return True
        expected = hashlib.sha256(
            f"{msg.msg_id}:{msg.phase.value}:{msg.view_num}:{msg.seq_num}:{msg.digest}:{msg.sender_id}".encode()
        ).hexdigest()[:16]
        return msg.signature == expected

    def create_proposal(self, gradient: np.ndarray, zk_proof_hash: str, coherence: float) -> GradientProposal:
        self.seq_num += 1
        proposal_id = f"prop_{self.view_num}_{self.seq_num}_{self.node_id}"
        return GradientProposal(
            proposal_id=proposal_id,
            worker_id=self.node_id,
            gradient=gradient,
            zk_proof_hash=zk_proof_hash,
            coherence_at_generation=coherence,
            timestamp=datetime.now().timestamp(),
            round_num=self.view_num
        )

    def broadcast_pre_prepare(self, proposal: GradientProposal) -> BFTMessage:
        self.is_primary = True
        digest = self._compute_digest(proposal.gradient)
        msg = BFTMessage(
            msg_id=f"preprep_{proposal.proposal_id}",
            phase=BFTPhase.PRE_PREPARE,
            view_num=self.view_num,
            seq_num=self.seq_num,
            digest=digest,
            sender_id=self.node_id,
            gradient_hash=proposal.zk_proof_hash,
            timestamp=datetime.now().timestamp(),
            signature=""
        )
        self.message_log.append(msg)
        self.proposals[proposal.proposal_id] = proposal
        return msg

    def handle_pre_prepare(self, msg: BFTMessage, proposal: GradientProposal) -> Optional[BFTMessage]:
        if not self._verify_signature(msg):
            return None
        if msg.view_num != self.view_num:
            return None
        expected_digest = self._compute_digest(proposal.gradient)
        if msg.digest != expected_digest:
            return None
        self.proposals[proposal.proposal_id] = proposal
        prepare = BFTMessage(
            msg_id=f"prep_{msg.msg_id}",
            phase=BFTPhase.PREPARE,
            view_num=self.view_num,
            seq_num=msg.seq_num,
            digest=msg.digest,
            sender_id=self.node_id,
            gradient_hash=msg.gradient_hash,
            timestamp=datetime.now().timestamp(),
            signature=""
        )
        self.message_log.append(prepare)
        return prepare

    def handle_prepare(self, msg: BFTMessage) -> Optional[BFTMessage]:
        if not self._verify_signature(msg):
            return None
        if msg.view_num != self.view_num:
            return None
        key = (msg.view_num, msg.seq_num)
        if key not in self.prepare_votes:
            self.prepare_votes[key] = set()
        self.prepare_votes[key].add(msg.sender_id)
        if len(self.prepare_votes[key]) >= 2 * self.f and key not in self.prepared_states:
            self.prepared_states.add(key)
            commit = BFTMessage(
                msg_id=f"commit_{msg.msg_id}",
                phase=BFTPhase.COMMIT,
                view_num=self.view_num,
                seq_num=msg.seq_num,
                digest=msg.digest,
                sender_id=self.node_id,
                gradient_hash=msg.gradient_hash,
                timestamp=datetime.now().timestamp(),
                signature=""
            )
            self.message_log.append(commit)
            return commit
        return None

    def handle_commit(self, msg: BFTMessage) -> Optional[Dict]:
        if not self._verify_signature(msg):
            return None
        if msg.view_num != self.view_num:
            return None
        key = (msg.view_num, msg.seq_num)
        if key not in self.commit_votes:
            self.commit_votes[key] = set()
        self.commit_votes[key].add(msg.sender_id)
        if len(self.commit_votes[key]) >= self.quorum:
            for pid, prop in self.proposals.items():
                if prop.round_num == msg.view_num and hashlib.sha256(prop.gradient.tobytes()).hexdigest()[:16] == msg.digest:
                    self.committed_gradients[msg.seq_num] = prop.gradient
                    return {
                        'status': 'COMMITTED',
                        'seq_num': msg.seq_num,
                        'proposal_id': pid,
                        'gradient_shape': prop.gradient.shape,
                        'coherence': prop.coherence_at_generation,
                        'commit_votes': len(self.commit_votes[key])
                    }
        return None

    def initiate_view_change(self, new_view: int) -> BFTMessage:
        self.view_num = new_view
        msg = BFTMessage(
            msg_id=f"vc_{new_view}_{self.node_id}",
            phase=BFTPhase.VIEW_CHANGE,
            view_num=new_view,
            seq_num=self.seq_num,
            digest="",
            sender_id=self.node_id,
            gradient_hash="",
            timestamp=datetime.now().timestamp()
        )
        return msg

    def get_bft_stats(self) -> Dict:
        return {
            'node_id': self.node_id,
            'view_num': self.view_num,
            'seq_num': self.seq_num,
            'is_primary': self.is_primary,
            'total_messages': len(self.message_log),
            'proposals': len(self.proposals),
            'committed': len(self.committed_gradients),
            'quorum_size': self.quorum,
            'byzantine_tolerance': self.f
        }


# ============================================================
# SUBSTRATO 262: Sharding Tensorial com Consistência Causal
# ============================================================

class CausalClock:
    """Vector clock for causal consistency across shards"""

    def __init__(self, node_id: str, num_nodes: int = 4):
        self.node_id = node_id
        self.num_nodes = num_nodes
        self.clock = [0] * num_nodes
        self.node_index = hash(node_id) % num_nodes

    def increment(self):
        self.clock[self.node_index] += 1
        return self.clock.copy()

    def merge(self, other_clock: List[int]):
        for i in range(self.num_nodes):
            self.clock[i] = max(self.clock[i], other_clock[i])

    def happens_before(self, other_clock: List[int]) -> bool:
        all_leq = all(a <= b for a, b in zip(self.clock, other_clock))
        any_lt = any(a < b for a, b in zip(self.clock, other_clock))
        return all_leq and any_lt

    def copy(self) -> List[int]:
        return self.clock.copy()


@dataclass
class TensorShard:
    shard_id: str
    tensor_id: str
    data: np.ndarray
    causal_clock: List[int]
    owner_node: str
    replica_nodes: List[str]
    version: int = 0
    committed: bool = False


class CausalTensorSharding:
    """Tensor sharding with causal consistency — Substrato 262"""

    def __init__(self, node_id: str, num_shards: int = 4, replication_factor: int = 2):
        self.node_id = node_id
        self.num_shards = num_shards
        self.replication_factor = replication_factor
        self.clock = CausalClock(node_id, num_shards)
        self.local_shards: Dict[str, TensorShard] = {}
        self.shard_index: Dict[str, List[str]] = {}
        self.pending_updates: List[TensorShard] = []
        self.conflict_log: List[Dict] = []

    def _hash_to_shard(self, tensor_id: str) -> int:
        return int(hashlib.sha256(tensor_id.encode()).hexdigest(), 16) % self.num_shards

    def shard_tensor(self, tensor: np.ndarray, tensor_id: str, force_local: bool = False) -> List[TensorShard]:
        shards = []
        self.clock.increment()
        primary_shard_idx = self._hash_to_shard(tensor_id)
        split_dims = [tensor.shape[0] // self.num_shards] * self.num_shards
        remainder = tensor.shape[0] % self.num_shards
        for i in range(remainder):
            split_dims[i] += 1
        start = 0
        for i, dim_size in enumerate(split_dims):
            end = start + dim_size
            shard_data = tensor[start:end]
            all_nodes = [f"node_{j}" for j in range(self.num_shards)]
            replicas = [all_nodes[(primary_shard_idx + j) % self.num_shards] for j in range(self.replication_factor)]
            shard = TensorShard(
                shard_id=f"{tensor_id}_shard_{i}",
                tensor_id=tensor_id,
                data=shard_data,
                causal_clock=self.clock.copy(),
                owner_node=all_nodes[primary_shard_idx],
                replica_nodes=replicas,
                version=1,
                committed=True
            )
            shards.append(shard)
            if self.node_id in replicas or (force_local and i == 0):
                self.local_shards[shard.shard_id] = shard
            start = end
        self.shard_index[tensor_id] = [s.shard_id for s in shards]
        return shards

    def read_shard(self, shard_id: str) -> Optional[TensorShard]:
        return self.local_shards.get(shard_id)

    def update_shard(self, shard_id: str, delta: np.ndarray, source_clock: List[int]) -> Dict:
        if shard_id not in self.local_shards:
            return {'status': 'NOT_FOUND', 'shard_id': shard_id}
        shard = self.local_shards[shard_id]
        source_cc = CausalClock("", self.num_shards)
        source_cc.clock = source_clock
        current_cc = CausalClock("", self.num_shards)
        current_cc.clock = shard.causal_clock
        if source_cc.happens_before(current_cc.clock):
            return {'status': 'STALE', 'shard_id': shard_id, 'reason': 'source_clock_behind'}
        self.clock.merge(source_clock)
        self.clock.increment()
        shard.data = shard.data + delta
        shard.causal_clock = self.clock.copy()
        shard.version += 1
        return {
            'status': 'UPDATED',
            'shard_id': shard_id,
            'new_version': shard.version,
            'clock': shard.causal_clock
        }

    def resolve_conflicts(self, shard_id: str, conflicting_versions: List[TensorShard]) -> Optional[TensorShard]:
        if not conflicting_versions:
            return self.local_shards.get(shard_id)
        sorted_versions = sorted(
            conflicting_versions,
            key=lambda s: (s.version, -self._estimate_coherence(s.data)),
            reverse=True
        )
        winner = sorted_versions[0]
        self.conflict_log.append({
            'shard_id': shard_id,
            'winner_version': winner.version,
            'winner_node': winner.owner_node,
            'losers': [{'version': s.version, 'node': s.owner_node} for s in sorted_versions[1:]],
            'timestamp': datetime.now().timestamp()
        })
        self.local_shards[shard_id] = winner
        return winner

    def _estimate_coherence(self, data: np.ndarray) -> float:
        if data.size == 0:
            return 0.0
        norm = np.linalg.norm(data)
        return float(np.exp(-abs(norm - 1.0)))

    def gather_tensor(self, tensor_id: str) -> Optional[np.ndarray]:
        if tensor_id not in self.shard_index:
            return None
        shard_ids = self.shard_index[tensor_id]
        shards = []
        for sid in shard_ids:
            if sid in self.local_shards:
                shards.append(self.local_shards[sid])
            else:
                return None
        return np.concatenate([s.data for s in shards])

    def get_sharding_stats(self) -> Dict:
        return {
            'node_id': self.node_id,
            'local_shards': len(self.local_shards),
            'indexed_tensors': len(self.shard_index),
            'pending_updates': len(self.pending_updates),
            'conflicts_resolved': len(self.conflict_log),
            'clock': self.clock.copy()
        }


# ============================================================
# SUBSTRATO 263: Checkpointing Quântico com Rollback Coerente
# ============================================================

class CheckpointState(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    ROLLED_BACK = "rolled_back"
    PRUNED = "pruned"

@dataclass
class QuantumCheckpoint:
    checkpoint_id: str
    seq_num: int
    gradient_state: np.ndarray
    coherence_snapshot: float
    causal_clock: List[int]
    bft_view: int
    shard_versions: Dict[str, int]
    timestamp: float
    entropy: float
    parent_id: Optional[str] = None
    state: CheckpointState = CheckpointState.ACTIVE

class QuantumCheckpointing:
    """Coherent checkpointing with quantum-inspired rollback — Substrato 263"""

    def __init__(self, node_id: str, max_checkpoints: int = 10):
        self.node_id = node_id
        self.max_checkpoints = max_checkpoints
        self.checkpoints: Dict[str, QuantumCheckpoint] = {}
        self.checkpoint_chain: List[str] = []
        self.current_seq = 0
        self.rollback_count = 0
        self.pruned_count = 0

    def _compute_entropy(self, gradient: np.ndarray) -> float:
        if gradient.size == 0:
            return 0.0
        probs = np.abs(gradient.flatten())
        probs = probs / (np.sum(probs) + 1e-10)
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        return float(entropy)

    def create_checkpoint(self, gradient: np.ndarray, coherence: float,
                         causal_clock: List[int], bft_view: int,
                         shard_versions: Dict[str, int]) -> QuantumCheckpoint:
        self.current_seq += 1
        checkpoint_id = f"chk_{self.node_id}_{self.current_seq}_{int(datetime.now().timestamp() * 1000)}"
        parent_id = self.checkpoint_chain[-1] if self.checkpoint_chain else None
        checkpoint = QuantumCheckpoint(
            checkpoint_id=checkpoint_id,
            seq_num=self.current_seq,
            gradient_state=gradient.copy(),
            coherence_snapshot=coherence,
            causal_clock=causal_clock.copy(),
            bft_view=bft_view,
            shard_versions=shard_versions.copy(),
            timestamp=datetime.now().timestamp(),
            entropy=self._compute_entropy(gradient),
            parent_id=parent_id,
            state=CheckpointState.ACTIVE
        )
        self.checkpoints[checkpoint_id] = checkpoint
        self.checkpoint_chain.append(checkpoint_id)
        if len(self.checkpoint_chain) > self.max_checkpoints:
            old_id = self.checkpoint_chain.pop(0)
            if old_id in self.checkpoints:
                self.checkpoints[old_id].state = CheckpointState.PRUNED
                self.pruned_count += 1
        return checkpoint

    def rollback_to_checkpoint(self, checkpoint_id: str) -> Optional[Dict]:
        if checkpoint_id not in self.checkpoints:
            return None
        checkpoint = self.checkpoints[checkpoint_id]
        if checkpoint.state != CheckpointState.ACTIVE:
            return None
        found = False
        for cid in self.checkpoint_chain:
            if cid == checkpoint_id:
                found = True
                continue
            if found and cid in self.checkpoints:
                self.checkpoints[cid].state = CheckpointState.ROLLED_BACK
        idx = self.checkpoint_chain.index(checkpoint_id)
        self.checkpoint_chain = self.checkpoint_chain[:idx + 1]
        self.current_seq = checkpoint.seq_num
        self.rollback_count += 1
        return {
            'status': 'ROLLED_BACK',
            'checkpoint_id': checkpoint_id,
            'seq_num': checkpoint.seq_num,
            'coherence': checkpoint.coherence_snapshot,
            'entropy': checkpoint.entropy,
            'gradient_shape': checkpoint.gradient_state.shape,
            'bft_view': checkpoint.bft_view
        }

    def find_last_coherent_checkpoint(self, min_coherence: float = 0.7) -> Optional[str]:
        for cid in reversed(self.checkpoint_chain):
            chk = self.checkpoints[cid]
            if chk.state == CheckpointState.ACTIVE and chk.coherence_snapshot >= min_coherence:
                return cid
        return None

    def verify_checkpoint_integrity(self, checkpoint_id: str) -> bool:
        if checkpoint_id not in self.checkpoints:
            return False
        checkpoint = self.checkpoints[checkpoint_id]
        return checkpoint.state == CheckpointState.ACTIVE

    def get_checkpoint_tree(self) -> Dict:
        tree = {'root': None, 'nodes': []}
        for cid in self.checkpoint_chain:
            chk = self.checkpoints[cid]
            tree['nodes'].append({
                'id': cid,
                'seq': chk.seq_num,
                'coherence': chk.coherence_snapshot,
                'entropy': chk.entropy,
                'state': chk.state.value,
                'parent': chk.parent_id
            })
            if chk.parent_id is None:
                tree['root'] = cid
        return tree

    def get_checkpointing_stats(self) -> Dict:
        active = sum(1 for c in self.checkpoints.values() if c.state == CheckpointState.ACTIVE)
        return {
            'node_id': self.node_id,
            'total_checkpoints': len(self.checkpoints),
            'active': active,
            'rolled_back': self.rollback_count,
            'pruned': self.pruned_count,
            'chain_length': len(self.checkpoint_chain),
            'current_seq': self.current_seq,
            'avg_coherence': np.mean([c.coherence_snapshot for c in self.checkpoints.values()]) if self.checkpoints else 0.0,
            'avg_entropy': np.mean([c.entropy for c in self.checkpoints.values()]) if self.checkpoints else 0.0
        }


# ============================================================
# SUBSTRATO 264: Integração com Pentacene Backend v148.3
# ============================================================

class PentaceneInterfaceStatus(Enum):
    CONNECTED = "connected"
    DEGRADED = "degraded"
    FALLBACK = "fallback"
    OFFLINE = "offline"

@dataclass
class PentaceneCommand:
    cmd_id: str
    cmd_type: str
    target: str
    payload: Dict
    coherence_requirement: float
    timestamp: float
    ttl: int = 3

class PentaceneBackendInterface:
    """Interface to Pentacene Crystal Brain Backend v148.3 — Substrato 264"""

    def __init__(self, node_id: str, crystal_id: str = "pentacene_v148_3"):
        self.node_id = node_id
        self.crystal_id = crystal_id
        self.status = PentaceneInterfaceStatus.OFFLINE
        self.command_queue: List[PentaceneCommand] = []
        self.response_cache: Dict[str, Dict] = {}
        self.latency_us = 50.0
        self.throughput_gbps = 12.8
        self.fidelity_history: List[float] = []
        self.auto_fallback = True
        self.digital_fallback_active = False

    def connect(self, coherence_threshold: float = 0.6) -> Dict:
        resonance = random.uniform(0.5, 1.0)
        if resonance >= coherence_threshold:
            self.status = PentaceneInterfaceStatus.CONNECTED
            self.fidelity_history.append(resonance)
            return {
                'status': 'CONNECTED',
                'crystal_id': self.crystal_id,
                'resonance': resonance,
                'latency_us': self.latency_us,
                'bandwidth_gbps': self.throughput_gbps
            }
        elif resonance >= coherence_threshold * 0.7:
            self.status = PentaceneInterfaceStatus.DEGRADED
            if self.auto_fallback:
                self.digital_fallback_active = True
            return {
                'status': 'DEGRADED',
                'crystal_id': self.crystal_id,
                'resonance': resonance,
                'fallback': self.digital_fallback_active
            }
        else:
            self.status = PentaceneInterfaceStatus.OFFLINE
            return {
                'status': 'OFFLINE',
                'crystal_id': self.crystal_id,
                'resonance': resonance
            }

    def send_command(self, cmd: PentaceneCommand) -> Dict:
        if self.status == PentaceneInterfaceStatus.OFFLINE:
            return {'status': 'REJECTED', 'reason': 'crystal_offline'}
        if self.status == PentaceneInterfaceStatus.DEGRADED and self.digital_fallback_active:
            return self._digital_fallback(cmd)
        execution_time_us = self.latency_us * (1 + random.random() * 0.2)
        fidelity = self.fidelity_history[-1] if self.fidelity_history else 0.9
        result = {
            'status': 'EXECUTED',
            'cmd_id': cmd.cmd_id,
            'crystal_id': self.crystal_id,
            'execution_time_us': execution_time_us,
            'fidelity': fidelity,
            'coherence': cmd.coherence_requirement * fidelity
        }
        self.response_cache[cmd.cmd_id] = result
        return result

    def _digital_fallback(self, cmd: PentaceneCommand) -> Dict:
        return {
            'status': 'FALLBACK',
            'cmd_id': cmd.cmd_id,
            'crystal_id': self.crystal_id,
            'reason': 'crystal_degraded_using_digital_emulation',
            'emulated': True,
            'coherence': cmd.coherence_requirement * 0.5
        }

    def read_crystal_state(self, register_addr: int, num_qubits: int = 8) -> Dict:
        if self.status not in [PentaceneInterfaceStatus.CONNECTED, PentaceneInterfaceStatus.DEGRADED]:
            return {'status': 'OFFLINE'}
        state_vector = np.random.randn(2**num_qubits).astype(np.complex64)
        state_vector = state_vector / np.linalg.norm(state_vector)
        density = np.outer(state_vector, state_vector.conj())
        purity = float(np.trace(density @ density).real)
        return {
            'status': 'READ_OK',
            'register': register_addr,
            'purity': purity,
            'coherence': purity,
            'state_shape': state_vector.shape,
            'crystal_id': self.crystal_id
        }

    def write_crystal_state(self, register_addr: int, state_vector: np.ndarray) -> Dict:
        if self.status == PentaceneInterfaceStatus.OFFLINE:
            return {'status': 'REJECTED'}
        norm = np.linalg.norm(state_vector)
        if abs(norm - 1.0) > 0.01:
            return {'status': 'REJECTED', 'reason': 'state_not_normalized'}
        return {
            'status': 'WRITTEN',
            'register': register_addr,
            'norm': norm,
            'crystal_id': self.crystal_id,
            'latency_us': self.latency_us
        }

    def get_interface_stats(self) -> Dict:
        return {
            'node_id': self.node_id,
            'crystal_id': self.crystal_id,
            'status': self.status.value,
            'commands_queued': len(self.command_queue),
            'responses_cached': len(self.response_cache),
            'avg_fidelity': np.mean(self.fidelity_history) if self.fidelity_history else 0.0,
            'digital_fallback': self.digital_fallback_active,
            'latency_us': self.latency_us,
            'bandwidth_gbps': self.throughput_gbps
        }
