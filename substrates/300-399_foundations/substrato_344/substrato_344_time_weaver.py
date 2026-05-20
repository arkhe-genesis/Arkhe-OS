import hashlib
import json
import time

class TimeWeaverTransceiverV4:
    def __init__(self):
        self.channel_entropy = 0.0

    def generate_temporal_packet(self, gate_id: str, payload: bytes, target_epoch: int) -> dict:
        packet = {
            "gate_id": gate_id,
            "payload": payload.hex(),
            "target_epoch": target_epoch,
            "timestamp": time.time()
        }
        packet["hash"] = hashlib.sha256(json.dumps(packet, sort_keys=True).encode()).hexdigest()
        return packet
