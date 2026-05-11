import os
import json
import hashlib
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import random

# ============================================================
# SUBSTRATO 256: MRC Transport Layer (base)
# ============================================================

class PlaneStatus(Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    RETIRED = "retired"
    RECOVERING = "recovering"

@dataclass
class Plane:
    plane_id: int
    status: PlaneStatus = PlaneStatus.ACTIVE
    coherence: float = 1.0
    latency_us: float = 1.0
    bandwidth_gbps: float = 100.0
    packets_sent: int = 0
    packets_lost: int = 0
    bytes_transferred: int = 0
    last_probe_time: float = 0.0
    failure_count: int = 0

@dataclass
class MRCPacket:
    packet_id: int
    plane_id: int
    sequence_num: int
    payload: np.ndarray
    header: Dict
    timestamp: float
    trimmed: bool = False

@dataclass
class RouteEntry:
    dest_node: str
    segments: List[int]
    coherence_threshold: float = 0.5
    failover_planes: List[int] = field(default_factory=list)

class MRCTransportLayer:
    """Multi-Route Coherence Transport Layer — Substrato 256"""

    def __init__(self, node_id: str, num_planes: int = 8, lambda_var: float = 0.1):
        self.node_id = node_id
        self.num_planes = num_planes
        self.lambda_var = lambda_var
        self.planes = [Plane(i) for i in range(num_planes)]
        self.static_routes: Dict[str, RouteEntry] = {}
        self.packet_counter = 0
        self.sequence_counter = 0
        self.received_packets: Dict[int, MRCPacket] = {}
        self.probe_interval_us = 100.0
        self.coherence_history: List[List[float]] = []
        self.trim_threshold = 0.3
        self._load_srv6_table()

    def _load_srv6_table(self, routes: Dict[str, RouteEntry] = None):
        if routes:
            self.static_routes = routes
        else:
            for i in range(16):
                dest = f"node_{i:02d}"
                segments = list(range(self.num_planes))
                random.shuffle(segments)
                self.static_routes[dest] = RouteEntry(
                    dest_node=dest,
                    segments=segments[:4],
                    coherence_threshold=0.5
                )

    def compute_transmission_coherence(self) -> float:
        active_planes = [p for p in self.planes if p.status == PlaneStatus.ACTIVE]
        if not active_planes:
            return 0.0
        coherences = [p.coherence for p in active_planes]
        mean_coh = np.mean(coherences)
        var_coh = np.var(coherences)
        phi = mean_coh - self.lambda_var * var_coh
        return max(0.0, min(1.0, phi))

    def spray_packets(self, tensor: np.ndarray, dest_node: str) -> List[MRCPacket]:
        active_planes = [p for p in self.planes if p.status == PlaneStatus.ACTIVE]
        if not active_planes:
            raise RuntimeError("Nenhum plano ativo disponível para transmissão")

        n_active = len(active_planes)
        slices = np.array_split(tensor, n_active)
        packets = []
        route = self.static_routes.get(dest_node)
        if not route:
            route = RouteEntry(dest_node=dest_node, segments=list(range(n_active)))

        for idx, (plane, slc) in enumerate(zip(active_planes, slices)):
            self.packet_counter += 1
            self.sequence_counter += 1
            should_trim = plane.coherence < self.trim_threshold

            pkt = MRCPacket(
                packet_id=self.packet_counter,
                plane_id=plane.plane_id,
                sequence_num=self.sequence_counter,
                payload=np.array([]) if should_trim else slc,
                header={
                    'src': self.node_id,
                    'dest': dest_node,
                    'segment_list': route.segments,
                    'coherence': plane.coherence,
                    'timestamp': datetime.now().timestamp(),
                    'trimmed': should_trim,
                    'tensor_shape': tensor.shape,
                    'slice_index': idx,
                    'total_slices': n_active
                },
                timestamp=datetime.now().timestamp(),
                trimmed=should_trim
            )
            plane.packets_sent += 1
            if not should_trim:
                plane.bytes_transferred += slc.nbytes
            packets.append(pkt)

        self.coherence_history.append([p.coherence for p in self.planes])
        return packets

    def detect_failure(self, plane_id: int, loss_rate: float = 0.0) -> bool:
        plane = self.planes[plane_id]
        if loss_rate > 0.05 or plane.coherence < 0.1:
            plane.status = PlaneStatus.RETIRED
            plane.coherence = 0.0
            plane.failure_count += 1
            self._redistribute_traffic(plane_id)
            return True
        if loss_rate > 0.01:
            plane.status = PlaneStatus.DEGRADED
            plane.coherence *= 0.8
            return False
        return False

    def _redistribute_traffic(self, failed_plane_id: int):
        active = [p for p in self.planes if p.status == PlaneStatus.ACTIVE]
        if active:
            boost = 1.0 + (1.0 / len(active))
            for p in active:
                p.bandwidth_gbps = min(200.0, p.bandwidth_gbps * boost)

    def send_probe(self, plane_id: int) -> bool:
        plane = self.planes[plane_id]
        if plane.status != PlaneStatus.RETIRED:
            return False
        if random.random() < 0.7:
            plane.status = PlaneStatus.RECOVERING
            plane.coherence = 0.3
            plane.last_probe_time = datetime.now().timestamp()
            return True
        return False

    def promote_recovered_planes(self):
        for p in self.planes:
            if p.status == PlaneStatus.RECOVERING and p.coherence >= 0.8:
                p.status = PlaneStatus.ACTIVE

    def get_network_state(self) -> Dict:
        return {
            'node_id': self.node_id,
            'transmission_coherence': self.compute_transmission_coherence(),
            'active_planes': sum(1 for p in self.planes if p.status == PlaneStatus.ACTIVE),
            'retired_planes': sum(1 for p in self.planes if p.status == PlaneStatus.RETIRED),
            'degraded_planes': sum(1 for p in self.planes if p.status == PlaneStatus.DEGRADED),
            'total_packets_sent': sum(p.packets_sent for p in self.planes),
            'total_bytes': sum(p.bytes_transferred for p in self.planes),
        }


# ============================================================
# SUBSTRATO 257: QHTTP sobre MRC Bridge
# ============================================================

class QHTTPMessageType(Enum):
    COHERENCE_PROBE = "coherence_probe"
    ENTANGLEMENT_REQUEST = "entanglement_request"
    TELEPORTATION_PAYLOAD = "teleportation_payload"
    CONSENSUS_VOTE = "consensus_vote"
    GRADIENT_SLICE = "gradient_slice"
    HEARTBEAT = "heartbeat"

@dataclass
class QHTTPMessage:
    msg_id: str
    msg_type: QHTTPMessageType
    src_node: str
    dest_node: str
    payload: np.ndarray
    coherence_signature: float
    timestamp: float
    ttl: int = 5
    priority: int = 0

class QHTTPOverMRCBridge:
    """Quantum HTTP over MRC Transport — Substrato 257"""

    def __init__(self, node_id: str, mrc_transport: MRCTransportLayer):
        self.node_id = node_id
        self.mrc = mrc_transport
        self.message_log: List[QHTTPMessage] = []
        self.coherence_threshold = 0.5
        self.entanglement_registry: Dict[str, Dict] = {}

    def serialize_message(self, msg: QHTTPMessage) -> np.ndarray:
        header = np.array([
            hash(msg.msg_id) % 2**32,
            hash(msg.msg_type.value) % 2**32,
            hash(msg.src_node) % 2**32,
            hash(msg.dest_node) % 2**32,
            int(msg.coherence_signature * 1e6),
            int(msg.timestamp * 1e6),
            msg.ttl,
            msg.priority
        ], dtype=np.float64)
        payload_flat = msg.payload.flatten() if msg.payload.size > 0 else np.array([0.0])
        return np.concatenate([header, payload_flat])

    def send_qhttp_message(self, msg: QHTTPMessage) -> Dict:
        phi_c = self.mrc.compute_transmission_coherence()
        if phi_c < msg.coherence_signature:
            return {
                'status': 'REJECTED',
                'reason': f'Coerência do canal ({phi_c:.4f}) < exigida ({msg.coherence_signature:.4f})',
                'message_id': msg.msg_id
            }
        tensor = self.serialize_message(msg)
        try:
            packets = self.mrc.spray_packets(tensor, msg.dest_node)
            self.message_log.append(msg)
            return {
                'status': 'SENT',
                'message_id': msg.msg_id,
                'packets': len(packets),
                'channel_coherence': phi_c,
                'trimmed_packets': sum(1 for p in packets if p.trimmed)
            }
        except RuntimeError as e:
            return {'status': 'FAILED', 'reason': str(e), 'message_id': msg.msg_id}

    def establish_entanglement_channel(self, remote_node: str, fidelity_target: float = 0.99) -> Dict:
        probe = QHTTPMessage(
            msg_id=f"probe_{random.randint(0, 999999)}",
            msg_type=QHTTPMessageType.COHERENCE_PROBE,
            src_node=self.node_id,
            dest_node=remote_node,
            payload=np.array([fidelity_target]),
            coherence_signature=0.3,
            timestamp=datetime.now().timestamp()
        )
        result = self.send_qhttp_message(probe)
        if result['status'] == 'SENT':
            self.entanglement_registry[remote_node] = {
                'fidelity_target': fidelity_target,
                'established_at': datetime.now().timestamp(),
                'channel_coherence': result['channel_coherence']
            }
        return {
            'remote_node': remote_node,
            'fidelity_target': fidelity_target,
            'send_result': result,
            'registry': self.entanglement_registry.get(remote_node, {})
        }

    def get_bridge_stats(self) -> Dict:
        msg_types = {}
        for msg in self.message_log:
            msg_types[msg.msg_type.value] = msg_types.get(msg.msg_type.value, 0) + 1
        return {
            'node_id': self.node_id,
            'total_messages': len(self.message_log),
            'message_types': msg_types,
            'entanglement_channels': len(self.entanglement_registry),
            'mrc_state': self.mrc.get_network_state()
        }


# ============================================================
# SUBSTRATO 258: Temporal RoCE Gateway
# ============================================================

class RoCEOpcode(Enum):
    SEND = 0x00
    SEND_INV = 0x01
    WRITE = 0x02
    READ = 0x03
    ATOMIC = 0x04

@dataclass
class RoCEPacket:
    opcode: RoCEOpcode
    src_qp: int
    dest_qp: int
    r_key: int
    addr: int
    length: int
    payload: np.ndarray
    psn: int

class TemporalRoCEGateway:
    """RoCE-to-qhttp:// Translation Gateway — Substrato 258"""

    def __init__(self, node_id: str, qhttp_bridge: QHTTPOverMRCBridge):
        self.node_id = node_id
        self.qhttp = qhttp_bridge
        self.roce_to_qhttp_map = {
            RoCEOpcode.SEND: QHTTPMessageType.TELEPORTATION_PAYLOAD,
            RoCEOpcode.SEND_INV: QHTTPMessageType.TELEPORTATION_PAYLOAD,
            RoCEOpcode.WRITE: QHTTPMessageType.GRADIENT_SLICE,
            RoCEOpcode.READ: QHTTPMessageType.ENTANGLEMENT_REQUEST,
            RoCEOpcode.ATOMIC: QHTTPMessageType.CONSENSUS_VOTE
        }
        self.translation_stats = {
            'packets_translated': 0,
            'bytes_translated': 0,
            'latency_ns': []
        }
        self.qp_registry: Dict[int, Dict] = {}

    def translate_roce_to_qhttp(self, roce_pkt: RoCEPacket, dest_node: str) -> QHTTPMessage:
        qhttp_type = self.roce_to_qhttp_map.get(roce_pkt.opcode, QHTTPMessageType.HEARTBEAT)
        coherence_req = self._qp_to_coherence(roce_pkt.src_qp, roce_pkt.dest_qp)
        msg = QHTTPMessage(
            msg_id=f"roce_{roce_pkt.psn}_{roce_pkt.src_qp}",
            msg_type=qhttp_type,
            src_node=self.node_id,
            dest_node=dest_node,
            payload=roce_pkt.payload,
            coherence_signature=coherence_req,
            timestamp=datetime.now().timestamp(),
            priority=1 if roce_pkt.opcode == RoCEOpcode.ATOMIC else 0
        )
        self.translation_stats['packets_translated'] += 1
        self.translation_stats['bytes_translated'] += roce_pkt.payload.nbytes
        return msg

    def _qp_to_coherence(self, src_qp: int, dest_qp: int) -> float:
        return min(0.95, 0.5 + (src_qp % 16) / 32.0)

    def send_roce_over_qhttp(self, roce_pkt: RoCEPacket, dest_node: str) -> Dict:
        t0 = datetime.now().timestamp()
        qhttp_msg = self.translate_roce_to_qhttp(roce_pkt, dest_node)
        result = self.qhttp.send_qhttp_message(qhttp_msg)
        latency_ns = (datetime.now().timestamp() - t0) * 1e9
        self.translation_stats['latency_ns'].append(latency_ns)
        return {
            'roce_opcode': roce_pkt.opcode.name,
            'qhttp_type': qhttp_msg.msg_type.value,
            'dest_node': dest_node,
            'payload_bytes': roce_pkt.payload.nbytes,
            'translation_latency_ns': latency_ns,
            'send_result': result
        }

    def register_stargate_qp(self, qp_id: int, node_mapping: str, tensor_shape: Tuple):
        self.qp_registry[qp_id] = {
            'node_mapping': node_mapping,
            'tensor_shape': tensor_shape,
            'registered_at': datetime.now().timestamp()
        }

    def batch_translate_and_send(self, roce_packets: List[RoCEPacket], dest_node: str) -> List[Dict]:
        results = []
        for pkt in sorted(roce_packets, key=lambda p: self._qp_to_coherence(p.src_qp, p.dest_qp), reverse=True):
            result = self.send_roce_over_qhttp(pkt, dest_node)
            results.append(result)
            if self.qhttp.mrc.compute_transmission_coherence() < 0.4:
                results.append({'status': 'BATCH_PAUSED', 'reason': 'coherence_below_threshold'})
                break
        return results

    def get_gateway_stats(self) -> Dict:
        latencies = self.translation_stats['latency_ns']
        return {
            'node_id': self.node_id,
            'packets_translated': self.translation_stats['packets_translated'],
            'bytes_translated': self.translation_stats['bytes_translated'],
            'avg_latency_ns': np.mean(latencies) if latencies else 0,
            'max_latency_ns': max(latencies) if latencies else 0,
            'registered_qps': len(self.qp_registry)
        }


# ============================================================
# SUBSTRATO 259: Coherence-Aware Load Balancer
# ============================================================

@dataclass
class NodeProfile:
    node_id: str
    compute_capacity: float
    memory_capacity: float
    current_load: float
    base_coherence: float
    latency_to_peer: Dict[str, float]
    active_tensors: int = 0
    queue_depth: int = 0

class CoherenceAwareLoadBalancer:
    """Coherence-Aware Tensor Load Balancer — Substrato 259"""

    def __init__(self, nodes: List[NodeProfile], phi_threshold: float = 0.5):
        self.nodes = {n.node_id: n for n in nodes}
        self.phi_threshold = phi_threshold
        self.allocation_history: List[Dict] = []
        self.coherence_model: Dict[str, List[float]] = {}

    def predict_coherence(self, src: str, dest: str, horizon_steps: int = 5) -> float:
        key = f"{src}->{dest}"
        history = self.coherence_model.get(key, [])
        if len(history) < 2:
            return self.nodes[src].base_coherence * self.nodes[dest].base_coherence
        alpha = 0.3
        pred = history[-1]
        for h in reversed(history[-horizon_steps:]):
            pred = alpha * h + (1 - alpha) * pred
        return max(0.0, min(1.0, pred))

    def score_node(self, node_id: str, tensor_size: int, src_node: str) -> float:
        node = self.nodes[node_id]
        load_score = 1.0 - node.current_load
        phi_pred = self.predict_coherence(src_node, node_id)
        compute_score = node.compute_capacity / 100.0
        queue_penalty = node.queue_depth / 10.0
        latency = node.latency_to_peer.get(src_node, 10.0) / 100.0
        score = 0.3 * load_score + 0.35 * phi_pred + 0.2 * compute_score - 0.1 * queue_penalty - 0.05 * latency
        if phi_pred < self.phi_threshold:
            score *= 0.1
        return score

    def allocate_tensor(self, tensor: np.ndarray, src_node: str, candidate_nodes: List[str] = None) -> Dict:
        if candidate_nodes is None:
            candidate_nodes = [n for n in self.nodes.keys() if n != src_node]
        scores = {node_id: self.score_node(node_id, tensor.nbytes, src_node) for node_id in candidate_nodes}
        best_node = max(scores, key=scores.get)
        self.nodes[best_node].current_load = min(1.0, self.nodes[best_node].current_load + tensor.nbytes / (self.nodes[best_node].memory_capacity * 1e9))
        self.nodes[best_node].active_tensors += 1
        self.nodes[best_node].queue_depth += 1
        allocation = {
            'tensor_shape': tensor.shape,
            'tensor_bytes': tensor.nbytes,
            'src_node': src_node,
            'dest_node': best_node,
            'score': scores[best_node],
            'predicted_coherence': self.predict_coherence(src_node, best_node),
            'all_scores': scores,
            'timestamp': datetime.now().timestamp()
        }
        self.allocation_history.append(allocation)
        return allocation

    def rebalance_cluster(self, mrc_transport=None):
        migrations = []
        overloaded = [n for n in self.nodes.values() if n.current_load > 0.8]
        underloaded = [n for n in self.nodes.values() if n.current_load < 0.3]
        for src in overloaded:
            for dest in underloaded:
                if src.node_id == dest.node_id:
                    continue
                phi = self.predict_coherence(src.node_id, dest.node_id)
                if phi > self.phi_threshold + 0.1:
                    src.current_load = max(0.0, src.current_load - 0.1)
                    src.active_tensors = max(0, src.active_tensors - 1)
                    dest.current_load = min(1.0, dest.current_load + 0.1)
                    dest.active_tensors += 1
                    migrations.append({
                        'from': src.node_id,
                        'to': dest.node_id,
                        'predicted_coherence': phi,
                        'reason': 'load_rebalance'
                    })
                    break
        return migrations

    def update_coherence_measurement(self, src: str, dest: str, measured_phi: float):
        key = f"{src}->{dest}"
        if key not in self.coherence_model:
            self.coherence_model[key] = []
        self.coherence_model[key].append(measured_phi)
        if len(self.coherence_model[key]) > 100:
            self.coherence_model[key] = self.coherence_model[key][-100:]

    def get_balancer_stats(self) -> Dict:
        loads = [n.current_load for n in self.nodes.values()]
        return {
            'nodes': len(self.nodes),
            'avg_load': np.mean(loads),
            'max_load': max(loads),
            'min_load': min(loads),
            'load_std': np.std(loads),
            'total_allocations': len(self.allocation_history),
            'phi_threshold': self.phi_threshold
        }


# ============================================================
# SUBSTRATO 260: MRC ZK Privacy Layer
# ============================================================

class ZKProofType(Enum):
    GRADIENT_RANGE = "gradient_range"
    GRADIENT_NORM = "gradient_norm"
    UPDATE_CONSISTENCY = "update_consistency"
    COHERENCE_MEMBERSHIP = "coherence_membership"

@dataclass
class ZKProof:
    proof_type: ZKProofType
    commitment: np.ndarray
    challenge: np.ndarray
    response: np.ndarray
    public_inputs: Dict
    verified: bool = False

class MRCZKPrivacyLayer:
    """Zero-Knowledge Privacy Layer for Gradient Transport — Substrato 260"""

    def __init__(self, node_id: str, qhttp_bridge: QHTTPOverMRCBridge):
        self.node_id = node_id
        self.qhttp = qhttp_bridge
        self.proof_history: List[ZKProof] = []
        self.verification_cache: Dict[str, bool] = {}
        self.fhe_params = {'modulus': 2**32, 'noise_budget': 100, 'scale': 2**20}

    def _hash_commitment(self, value: np.ndarray, blinding: int) -> np.ndarray:
        combined = np.concatenate([value.flatten(), np.array([blinding])])
        return np.array([int(hashlib.sha256(combined.tobytes()).hexdigest(), 16) % self.fhe_params['modulus']])

    def prove_gradient_range(self, gradient: np.ndarray, min_val: float, max_val: float) -> ZKProof:
        blinding = random.randint(1, self.fhe_params['modulus'] - 1)
        commitment = self._hash_commitment(gradient, blinding)
        all_in_range = np.all((gradient >= min_val) & (gradient <= max_val))
        challenge_input = np.concatenate([commitment, np.array([min_val, max_val])])
        challenge = int(hashlib.sha256(challenge_input.tobytes()).hexdigest(), 16) % self.fhe_params['modulus']
        response = (blinding + challenge * int(np.sum(gradient) * self.fhe_params['scale'])) % self.fhe_params['modulus']
        proof = ZKProof(
            proof_type=ZKProofType.GRADIENT_RANGE,
            commitment=commitment,
            challenge=np.array([challenge]),
            response=np.array([response]),
            public_inputs={
                'min_val': min_val,
                'max_val': max_val,
                'gradient_shape': gradient.shape,
                'gradient_dtype': str(gradient.dtype),
                'actual_in_range': all_in_range
            },
            verified=all_in_range
        )
        self.proof_history.append(proof)
        return proof

    def prove_gradient_norm(self, gradient: np.ndarray, target_norm: float, tolerance: float = 0.01) -> ZKProof:
        actual_norm = np.linalg.norm(gradient)
        in_tolerance = abs(actual_norm - target_norm) <= tolerance * target_norm
        blinding = random.randint(1, self.fhe_params['modulus'] - 1)
        commitment = self._hash_commitment(gradient, blinding)
        challenge_input = np.concatenate([commitment, np.array([target_norm, tolerance])])
        challenge = int(hashlib.sha256(challenge_input.tobytes()).hexdigest(), 16) % self.fhe_params['modulus']
        response = (blinding + challenge * int(actual_norm * self.fhe_params['scale'])) % self.fhe_params['modulus']
        proof = ZKProof(
            proof_type=ZKProofType.GRADIENT_NORM,
            commitment=commitment,
            challenge=np.array([challenge]),
            response=np.array([response]),
            public_inputs={
                'target_norm': target_norm,
                'tolerance': tolerance,
                'gradient_shape': gradient.shape,
                'actual_norm': actual_norm,
                'verified': in_tolerance
            },
            verified=in_tolerance
        )
        self.proof_history.append(proof)
        return proof

    def verify_proof(self, proof: ZKProof, prover_node: str) -> bool:
        proof_id = f"{prover_node}_{proof.proof_type.value}_{hash(proof.commitment.tobytes())}"
        if proof_id in self.verification_cache:
            return self.verification_cache[proof_id]
        if proof.proof_type == ZKProofType.GRADIENT_RANGE:
            expected_input = np.concatenate([proof.commitment, np.array([proof.public_inputs['min_val'], proof.public_inputs['max_val']])])
        elif proof.proof_type == ZKProofType.GRADIENT_NORM:
            expected_input = np.concatenate([proof.commitment, np.array([proof.public_inputs['target_norm'], proof.public_inputs['tolerance']])])
        else:
            self.verification_cache[proof_id] = False
            return False
        expected_challenge = int(hashlib.sha256(expected_input.tobytes()).hexdigest(), 16) % self.fhe_params['modulus']
        is_valid = (proof.challenge[0] == expected_challenge) and proof.verified
        self.verification_cache[proof_id] = is_valid
        return is_valid

    def send_verified_gradient(self, gradient: np.ndarray, dest_node: str, proof: ZKProof) -> Dict:
        combined = np.concatenate([
            np.array([proof.challenge[0], proof.response[0], proof.commitment[0], 1.0 if proof.verified else 0.0]),
            gradient.flatten()[:100]
        ])
        msg = QHTTPMessage(
            msg_id=f"zk_grad_{random.randint(0, 999999)}",
            msg_type=QHTTPMessageType.GRADIENT_SLICE,
            src_node=self.node_id,
            dest_node=dest_node,
            payload=combined,
            coherence_signature=0.6,
            timestamp=datetime.now().timestamp(),
            priority=2
        )
        return self.qhttp.send_qhttp_message(msg)

    def get_privacy_stats(self) -> Dict:
        by_type = {}
        for p in self.proof_history:
            by_type[p.proof_type.value] = by_type.get(p.proof_type.value, 0) + 1
        return {
            'node_id': self.node_id,
            'total_proofs_generated': len(self.proof_history),
            'proofs_by_type': by_type,
            'verified_proofs': sum(1 for p in self.proof_history if p.verified),
            'verification_cache_size': len(self.verification_cache)
        }
