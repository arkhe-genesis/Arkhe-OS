import hashlib
import time
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

try:
    from arkhe.layers.constraints import TemporalChainClient
except ImportError:
    class TemporalChainClient:
        def __init__(self, endpoint=None):
            pass
        def anchor_content(self, content_hash, metadata):
            return f"anchor_{content_hash}"

@dataclass
class AuditRecord:
    timestamp: float
    function_name: str
    payload: str
    severity: str
    reason: str
    seal: str = ""

class AuditHook:
    def __init__(self):
        self.temporal_client = TemporalChainClient()
        self.blocked_calls = 0
        self.phi_c = 0.998

    def _compute_seal(self, record: AuditRecord) -> str:
        data = {
            "timestamp": record.timestamp,
            "function_name": record.function_name,
            "payload": record.payload,
            "severity": record.severity,
            "reason": record.reason,
            "event_type": "stdlib_blocked"
        }
        return hashlib.sha3_256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def log_blocked_action(self, function_name: str, payload: str, severity: str, reason: str):
        self.blocked_calls += 1
        record = AuditRecord(
            timestamp=time.time(),
            function_name=function_name,
            payload=payload,
            severity=severity,
            reason=reason
        )
        record.seal = self._compute_seal(record)
        metadata = asdict(record)
        metadata["event_type"] = "stdlib_blocked"
        self.temporal_client.anchor_content(record.seal, metadata)
        return record.seal

# Instância global para facilitar importação e uso
auditor = AuditHook()
