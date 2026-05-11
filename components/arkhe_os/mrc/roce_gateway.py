from enum import Enum
from dataclasses import dataclass
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime
from arkhe_os.mrc.qhttp_bridge import QHTTPOverMRCBridge, QHTTPMessage, QHTTPMessageType

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
        self.translation_stats = {'packets_translated': 0, 'bytes_translated': 0, 'latency_ns': []}
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
