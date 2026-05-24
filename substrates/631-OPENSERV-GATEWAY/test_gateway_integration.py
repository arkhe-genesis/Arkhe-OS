#!/usr/bin/env python3
"""test_gateway_integration.py — Teste completo do Substrato 631"""

import requests
import base64
import hashlib
import struct
from cryptography.hazmat.primitives.asymmetric import ed25519

URL = "http://localhost:50051"

# 1. Health
r = requests.get(f"{URL}/health")
assert r.json()["status"] == "ok"

# 2. Obter pubkey
r = requests.get(f"{URL}/gateway_pubkey")
pubkey_hex = r.json()["public_key_hex"]
pubkey = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubkey_hex))

# 3. Invocar paper-reviewer
latex = br"\documentclass{article}\begin{document}ARKHE Kernel Test\end{document}"
req = {
    "input": base64.b64encode(latex).decode(),
    "time_direction": "+1"
}
r = requests.post(f"{URL}/serv/paper-reviewer/invoke", json=req)
env = r.json()

# 4. Validar envelope
in_hash = hashlib.sha3_256(latex).digest()
assert in_hash.hex() == env["input_hash"]

out_bytes = base64.b64decode(env["output"])
out_hash = hashlib.sha3_256(out_bytes).digest()
assert out_hash.hex() == env["output_hash"]

phi_int = int(env["phi_score"] * 10000)
msg = (
    in_hash +
    out_hash +
    struct.pack("<I", phi_int) +
    env["timestamp"].encode() +
    env["gateway_id"].encode()
)
sig = bytes.fromhex(env["signature"])
pubkey.verify(sig, msg)

print(f"✅ Envelope válido! Φ = {env['phi_score']:.4f}")
print(out_bytes.decode())
