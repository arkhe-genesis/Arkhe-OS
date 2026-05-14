"""
TemporalChain – SBOM imutável + âncora de eventos de conformidade
"""
import hashlib
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class TemporalAnchor:
    event_type: str
    payload: Dict
    timestamp: float
    seal: str

    def to_dict(self) -> Dict:
        return {
            "event": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "seal": self.seal
        }

class TemporalChain:
    """
    Cadeia temporal imutável para auditoria MA‑S2.
    Cada evento é selado com SHA3‑256.
    """

    def __init__(self):
        self.anchors: List[TemporalAnchor] = []
        self.current_seal = "0" * 64
        self.sbom_registry: Dict[str, str] = {}  # release_id -> hash

    async def anchor_event(self, event_type: str, payload: Dict) -> str:
        """Ancora evento na cadeia temporal com hash encadeado."""
        ts = time.time()
        data = json.dumps({
            "prev_seal": self.current_seal,
            "event": event_type,
            "payload": payload,
            "timestamp": ts
        }, sort_keys=True)
        seal = hashlib.sha3_256(data.encode()).hexdigest()

        anchor = TemporalAnchor(
            event_type=event_type,
            payload=payload,
            timestamp=ts,
            seal=seal
        )
        self.anchors.append(anchor)
        self.current_seal = seal
        return seal

    def get_sbom(self, release_id: str) -> Optional[str]:
        return self.sbom_registry.get(release_id)

    def verify_chain(self) -> bool:
        """Verifica integridade da cadeia temporal."""
        prev = "0" * 64
        for anchor in self.anchors:
            data = json.dumps({
                "prev_seal": prev,
                "event": anchor.event_type,
                "payload": anchor.payload,
                "timestamp": anchor.timestamp
            }, sort_keys=True)
            expected = hashlib.sha3_256(data.encode()).hexdigest()
            if expected != anchor.seal:
                return False
            prev = anchor.seal
        return True

    def export_chain(self) -> List[Dict]:
        return [a.to_dict() for a in self.anchors]
