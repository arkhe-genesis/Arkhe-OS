import numpy as np
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

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
