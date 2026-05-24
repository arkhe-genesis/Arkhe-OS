#!/usr/bin/env python3
"""
openserv-gateway — OpenServ Gateway HTTP (Python)
Substrate 631-OPENSERV-GATEWAY
Produces Signed Result Envelopes with Ed25519.
Author: ORCID 0009-0005-2697-4668
"""

import base64
import hashlib
import json
import os
import struct
import time
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from flask import Flask, request, jsonify

app = Flask(__name__)

# ── Key Management ──────────────────────────────────────────────────────────
KEY_PATH = Path("/etc/arkhe/gateway_ed25519.key")

def load_or_generate_key():
    if KEY_PATH.exists():
        private_bytes = KEY_PATH.read_bytes()
        return ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
    else:
        private_key = ed25519.Ed25519PrivateKey.generate()
        KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        KEY_PATH.write_bytes(private_key.private_bytes_raw())
        return private_key

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

def sign_message(input_hash: bytes, output_hash: bytes, phi_score: float, timestamp: str) -> str:
    """Sign the canonical message and return hex-encoded signature."""
    phi_int = int(phi_score * 10000)
    message = (
        input_hash +
        output_hash +
        struct.pack("<I", phi_int) +
        timestamp.encode("utf-8") +
        GATEWAY_ID.encode("utf-8")
    )
    signature = PRIVATE_KEY.sign(message)
    return signature.hex()

def build_signed_envelope(input_data: bytes, output_data: bytes, phi_score: float) -> dict:
    """Build a complete Signed Result Envelope."""
    timestamp = datetime.now(timezone.utc).isoformat()
    input_hash = sha3_256(input_data)
    output_hash = sha3_256(output_data)
    signature = sign_message(input_hash, output_hash, phi_score, timestamp)

    return {
        "input_hash": input_hash.hex(),
        "output_hash": output_hash.hex(),
        "output": base64.b64encode(output_data).decode("ascii"),
        "phi_score": phi_score,
        "timestamp": timestamp,
        "gateway_id": GATEWAY_ID,
        "signature": signature,
    }

# ── Mock Servs ──────────────────────────────────────────────────────────────
def mock_reviewer_serv(input_data: bytes) -> tuple[bytes, float]:
    """Mock Reviewer Serv: returns a fake critique."""
    text = input_data.decode("utf-8", errors="replace")
    critique = "## Reviewer Report (AAAI Style)\n\n"
    critique += "**Originality**: The submission shows adequate novelty.\n"
    critique += "**Clarity**: The text of " + str(len(text)) + " characters requires minor revision.\n"
    critique += "**Soundness**: Methodology appears rigorous.\n"
    critique += "**Significance**: Potentially impactful.\n\n"
    critique += "**Recommendation**: Accept with minor revisions (score: 6/10)\n"
    phi = 0.72
    return critique.encode("utf-8"), phi

SERV_HANDLERS = {
    "paper-reviewer": mock_reviewer_serv,
    # Outros Servs seriam registrados aqui
}

# ── HTTP API ────────────────────────────────────────────────────────────────
@app.route("/serv/<serv_id>/invoke", methods=["POST"])
def invoke_serv(serv_id):
    if serv_id not in SERV_HANDLERS:
        return jsonify({"error": "Unknown serv: " + serv_id}), 404

    body = request.get_json(force=True)
    input_b64 = body.get("input", "")
    time_direction = body.get("time_direction", "+1")

    try:
        input_data = base64.b64decode(input_b64)
    except Exception:
        return jsonify({"error": "Invalid base64 input"}), 400

    # Executa o Serv (mock)
    handler = SERV_HANDLERS[serv_id]
    output_data, phi_score = handler(input_data)

    # Se time_direction == "-1", inverte o output (simulação de espelho temporal)
    if time_direction == "-1":
        output_data = output_data[::-1]
        phi_score = 1.0 - phi_score

    envelope = build_signed_envelope(input_data, output_data, phi_score)
    return jsonify(envelope)

@app.route("/gateway_pubkey", methods=["GET"])
def get_pubkey():
    return jsonify({
        "gateway_id": GATEWAY_ID,
        "public_key_hex": public_key_hex(),
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "gateway_id": GATEWAY_ID})

if __name__ == "__main__":
    print("[631] OpenServ Gateway starting...")
    print("[631] Gateway ID: " + GATEWAY_ID)
    print("[631] Public key: " + public_key_hex())
    app.run(host="0.0.0.0", port=50051, debug=False)
