import hashlib
import json
from typing import List

from arkhe_os.parser.frontends.ping_frontend_async import PingResult

class PingAuditLedger:
    def __init__(self):
        self.ledger: List[dict] = []
        self.node_key = "MOCK_NODE_PRIVATE_KEY_FOR_TESTS" # Mocking cryptographic signature setup for simplicity.

    def _compute_proof_hash(self, result: PingResult, session_id: str) -> str:
        data = f"{session_id}:{result.target}:{result.rtt_avg_ms}:{result.loss_rate}:{result.jitter_ms}:{result.timestamp}:{self.node_key}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def log_session(self, result: PingResult, session_id: str):
        entry = {
            "session_id": session_id,
            "target": result.target,
            "coherence": result.coherence,
            "metrics": {
                "rtt_avg": result.rtt_avg_ms,
                "loss": result.loss_rate,
                "jitter": result.jitter_ms
            },
            "timestamp": result.timestamp,
            "proof_hash": self._compute_proof_hash(result, session_id)
        }
        self.ledger.append(entry)
        # Em produção: assinar com chave do nó e propagar para Hyper-Mesh
        return entry
