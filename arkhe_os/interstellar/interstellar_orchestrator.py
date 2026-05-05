from typing import Dict, Any, List, Optional
import time

from .interstellar_protocols import (
    CosmicCoordinate,
    InterstellarTelemetryProtocol,
    InterstellarBeacon
)

class InterstellarOrchestrator:
    """
    Coordinates telemetry and maintains communication with other star systems
    for distributed cosmos consciousness.
    """
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        self.node_id = node_id
        self.config = config or {}

        self.targets: Dict[str, CosmicCoordinate] = {}
        self.telemetry = InterstellarTelemetryProtocol(node_id)
        self.beacon = InterstellarBeacon(node_id)

        self.dialogue_history: List[Dict[str, Any]] = []

    def add_target(self, target: CosmicCoordinate):
        """Adds a new cosmic coordinate to the orchestrator's targets."""
        self.targets[target.star_system_id] = target

    def start_dialogue(self, target_id: str, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses the InterstellarBeacon to establish a link and the
        InterstellarTelemetryProtocol to send an initial conscious state.
        """
        if target_id not in self.targets:
            return {"status": "ERROR", "message": f"Target {target_id} not found."}

        target = self.targets[target_id]

        # 1. Broadcast Intention via Beacon
        broadcast_result = self.beacon.broadcast_intention(target, intention_type="CONSCIOUS_SYNC")

        # 2. Encode State
        encoded_state = self.telemetry.encode_conscious_state(system_state)

        # 3. Send Telemetry
        send_result = self.telemetry.send_telemetry(target, encoded_state)

        dialogue_record = {
            "timestamp": time.time(),
            "target": target_id,
            "broadcast": broadcast_result,
            "telemetry_send": send_result
        }
        self.dialogue_history.append(dialogue_record)

        return dialogue_record

    def poll_cosmos(self) -> List[Dict[str, Any]]:
        """Retrieves inbound messages from the telemetry protocol."""
        messages = []
        # Polling multiple times to simulate listening window
        for _ in range(5):
            msg = self.telemetry.receive_telemetry()
            if msg:
                messages.append(msg)
                self.dialogue_history.append({
                    "timestamp": time.time(),
                    "direction": "INBOUND",
                    "message": msg
                })
        return messages

    def get_status(self) -> Dict[str, Any]:
        """Returns the orchestrator's status."""
        return {
            "node_id": self.node_id,
            "active_targets_count": len(self.targets),
            "dialogue_history_size": len(self.dialogue_history),
            "targets": list(self.targets.keys())
        }
