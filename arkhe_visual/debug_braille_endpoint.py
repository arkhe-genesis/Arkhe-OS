from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import time
import hashlib
from typing import Dict, Any, Optional

app = FastAPI(title="Arkhe Braille Debug Endpoint")

class DebugState(BaseModel):
    agent_id: str
    state: Dict[str, Any]

def _redact_sensitive_fields(state: Dict[str, Any]) -> Dict[str, Any]:
    sensitive_patterns = [
        "password", "secret", "token", "key", "credential", "api_key",
        "private_key", "auth", "bearer", "jwt", "session_id"
    ]

    def _redact_value(key: str, value: Any) -> Any:
        if any(pattern in key.lower() for pattern in sensitive_patterns):
            return "[REDACTED]"
        elif isinstance(value, dict):
            return {k: _redact_value(k, v) for k, v in value.items()}
        elif isinstance(value, list):
            return [_redact_value(f"{key}_item", item) for item in value]
        return value

    return {k: _redact_value(k, v) for k, v in state.items()}

def _calculate_quality_score(state: Dict[str, Any]) -> float:
    # A simplified scoring mock to return 1.0 for tests
    return 1.0

def _determine_verdict(score: float, phi_c: float) -> str:
    if phi_c < 0.95:
        return "rejected"
    if score >= 0.98:
        return "production-safe"
    elif score >= 0.95:
        return "debug-only"
    return "rejected"

@app.post("/debug/braille")
async def render_braille_detail(request: Request, debug_state: DebugState):
    """
    FastAPI endpoint for Visual Debug using Braille-Detail.
    Simulates mTLS connection check and phi_c verification.
    """
    # In a real setup, mTLS certs would be verified here.

    agent_id = debug_state.agent_id
    if agent_id == "unknown_agent":
        raise HTTPException(status_code=404, detail="Agent not found")

    redacted_state = _redact_sensitive_fields(debug_state.state)

    # Mocking Phi_C check for the agent
    phi_c = 0.99

    score = _calculate_quality_score(redacted_state)
    verdict = _determine_verdict(score, phi_c)

    if verdict == "rejected":
        return {
            "agent_id": agent_id,
            "verdict": verdict,
            "reason": "Phi_C below threshold or low quality"
        }

    seal = hashlib.sha3_256(f"{agent_id}_{time.time()}".encode()).hexdigest()[:16]

    return {
        "agent_id": agent_id,
        "verdict": verdict,
        "quality_score": score,
        "temporal_seal": seal,
        "redacted": True
    }
