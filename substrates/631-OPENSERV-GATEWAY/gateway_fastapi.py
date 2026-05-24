#!/usr/bin/env python3
"""
openserv-gateway-fastapi — OpenServ Gateway HTTP (FastAPI)
Substrate 631-OPENSERV-GATEWAY
Routes: /health, /gateway_pubkey, /serv/{serv_id}/invoke
Produces Signed Result Envelopes with Ed25519.
"""

import base64
import hashlib
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════════════════

class InvokeRequest(BaseModel):
    input: str = Field(..., description="Base64-encoded input data")
    time_direction: str = Field(default="+1", pattern=r"^[+-]1$")

class SignedEnvelope(BaseModel):
    input_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    output_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    output: str = Field(..., description="Base64-encoded output")
    phi_score: float = Field(..., ge=0.0, le=1.0)
    timestamp: str
    gateway_id: str
    signature: str = Field(..., pattern=r"^[a-f0-9]{128}$")

class PubkeyResponse(BaseModel):
    gateway_id: str
    public_key_hex: str

class HealthResponse(BaseModel):
    status: str
    gateway_id: str

# ═══════════════════════════════════════════════════════════════════════════════
# Key Management
# ═══════════════════════════════════════════════════════════════════════════════

KEY_PATH = Path("/etc/arkhe/gateway_ed25519.key")

def load_or_generate_key() -> ed25519.Ed25519PrivateKey:
    try:
        if KEY_PATH.exists():
            return ed25519.Ed25519PrivateKey.from_private_bytes(KEY_PATH.read_bytes())
    except PermissionError:
        pass

    # Use a local path if we can't write to /etc/arkhe
    local_key_path = Path("gateway_ed25519.key")
    if local_key_path.exists():
        return ed25519.Ed25519PrivateKey.from_private_bytes(local_key_path.read_bytes())

    key = ed25519.Ed25519PrivateKey.generate()

    try:
        KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        KEY_PATH.write_bytes(key.private_bytes_raw())
    except PermissionError:
        local_key_path.write_bytes(key.private_bytes_raw())

    return key

PRIVATE_KEY = load_or_generate_key()
PUBLIC_KEY = PRIVATE_KEY.public_key()
GATEWAY_ID = "openserv-gateway-01"

def public_key_hex() -> str:
    return PUBLIC_KEY.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()

def sha3_256(data: bytes) -> bytes:
    return hashlib.sha3_256(data).digest()

def sign_envelope(input_hash: bytes, output_hash: bytes, phi_score: float, timestamp: str) -> str:
    phi_int = int(phi_score * 10000)
    message = (
        input_hash +
        output_hash +
        struct.pack("<I", phi_int) +
        timestamp.encode("utf-8") +
        GATEWAY_ID.encode("utf-8")
    )
    return PRIVATE_KEY.sign(message).hex()

# ═══════════════════════════════════════════════════════════════════════════════
# Mock Servs
# ═══════════════════════════════════════════════════════════════════════════════

def mock_reviewer(input_data: bytes) -> Tuple[bytes, float]:
    text = input_data.decode("utf-8", errors="replace")
    critique = f"""## Reviewer Report (AAAI Style)

**Originality**: The submission shows adequate novelty.
**Clarity**: The text of {len(text)} characters requires minor revision.
**Significance**: Potentially impactful.

**Recommendation**: Accept with minor revisions (score: 6/10)
"""
    return critique.encode("utf-8"), 0.72

SERV_HANDLERS: Dict[str, callable] = {
    "paper-reviewer": mock_reviewer,
}

# ═══════════════════════════════════════════════════════════════════════════════
# FastAPI App
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="OpenServ Gateway",
    version="1.0.0",
    description="Substrate 631-OPENSERV-GATEWAY — Signed Result Envelope API",
)

@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok", "gateway_id": GATEWAY_ID}

@app.get("/gateway_pubkey", response_model=PubkeyResponse)
async def get_pubkey():
    return {"gateway_id": GATEWAY_ID, "public_key_hex": public_key_hex()}

@app.post("/serv/{serv_id}/invoke", response_model=SignedEnvelope)
async def invoke_serv(serv_id: str, req: InvokeRequest):
    if serv_id not in SERV_HANDLERS:
        raise HTTPException(status_code=404, detail=f"Unknown serv: {serv_id}")

    try:
        input_data = base64.b64decode(req.input)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 input")

    handler = SERV_HANDLERS[serv_id]
    output_data, phi_score = handler(input_data)

    if req.time_direction == "-1":
        output_data = output_data[::-1]
        phi_score = 1.0 - phi_score

    timestamp = datetime.now(timezone.utc).isoformat()
    input_hash = sha3_256(input_data)
    output_hash = sha3_256(output_data)
    signature = sign_envelope(input_hash, output_hash, phi_score, timestamp)

    return SignedEnvelope(
        input_hash=input_hash.hex(),
        output_hash=output_hash.hex(),
        output=base64.b64encode(output_data).decode("ascii"),
        phi_score=phi_score,
        timestamp=timestamp,
        gateway_id=GATEWAY_ID,
        signature=signature,
    )

if __name__ == "__main__":
    import uvicorn
    print(f"[631] FastAPI Gateway starting on :50051")
    print(f"[631] Public key: {public_key_hex()}")
    uvicorn.run(app, host="0.0.0.0", port=50051)
