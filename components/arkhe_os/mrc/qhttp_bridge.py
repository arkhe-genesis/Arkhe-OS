from enum import Enum
from dataclasses import dataclass
import numpy as np
import random
from typing import List, Dict
from datetime import datetime
from arkhe_os.network.mrc_transport import MRCTransportLayer, Packet

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
    def __init__(self, node_id: str, mrc_transport: MRCTransportLayer):
        self.node_id = node_id
        self.mrc = mrc_transport
        self.message_log: List[QHTTPMessage] = []
        self.coherence_threshold = 0.5
        self.entanglement_registry: Dict[str, Dict] = {}

    def serialize_message(self, msg: QHTTPMessage) -> np.ndarray:
        header = np.array([hash(msg.msg_id) % 2**32, hash(msg.msg_type.value) % 2**32,
                           hash(msg.src_node) % 2**32, hash(msg.dest_node) % 2**32,
                           int(msg.coherence_signature * 1e6), int(msg.timestamp * 1e6), msg.ttl, msg.priority], dtype=np.float64)
        payload_flat = msg.payload.flatten() if msg.payload.size > 0 else np.array([0.0])
        return np.concatenate([header, payload_flat])

    def send_qhttp_message(self, msg: QHTTPMessage) -> Dict:
        phi_c = self.mrc.compute_transmission_coherence()
        if phi_c < msg.coherence_signature:
            return {'status': 'REJECTED', 'reason': f'Coerência do canal ({phi_c:.4f}) < exigida ({msg.coherence_signature:.4f})', 'message_id': msg.msg_id}
        tensor = self.serialize_message(msg)
        try:
            packets = self.mrc.spray_packets(tensor, msg.dest_node)
            self.message_log.append(msg)
            return {'status': 'SENT', 'message_id': msg.msg_id, 'packets': len(packets), 'channel_coherence': phi_c, 'trimmed_packets': sum(1 for p in packets if p.trimmed)}
        except RuntimeError as e:
            return {'status': 'FAILED', 'reason': str(e), 'message_id': msg.msg_id}

    def establish_entanglement_channel(self, remote_node: str, fidelity_target: float = 0.99) -> Dict:
        probe = QHTTPMessage(msg_id=f"probe_{random.randint(0, 999999)}", msg_type=QHTTPMessageType.COHERENCE_PROBE,
                             src_node=self.node_id, dest_node=remote_node, payload=np.array([fidelity_target]),
                             coherence_signature=0.3, timestamp=datetime.now().timestamp())
        result = self.send_qhttp_message(probe)
        if result['status'] == 'SENT':
            self.entanglement_registry[remote_node] = {'fidelity_target': fidelity_target, 'established_at': datetime.now().timestamp(), 'channel_coherence': result['channel_coherence']}
        return {'remote_node': remote_node, 'fidelity_target': fidelity_target, 'send_result': result, 'registry': self.entanglement_registry.get(remote_node, {})}

    def get_bridge_stats(self) -> Dict:
        msg_types = {}
        for msg in self.message_log:
            msg_types[msg.msg_type.value] = msg_types.get(msg.msg_type.value, 0) + 1
        return {'node_id': self.node_id, 'total_messages': len(self.message_log), 'message_types': msg_types,
                'entanglement_channels': len(self.entanglement_registry), 'mrc_state': self.mrc.get_network_state()}
