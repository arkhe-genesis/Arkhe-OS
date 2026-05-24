#!/usr/bin/env python3
"""
ARKHE Cathedral - OpenServ Gateway FastAPI Daemon (Substrate 631-OPENSERV-SERV)
"""
import struct
import hashlib
from cryptography.hazmat.primitives.asymmetric import ed25519

PRIVATE_KEY = ed25519.Ed25519PrivateKey.generate()
PUBLIC_KEY = PRIVATE_KEY.public_key()
GATEWAY_ID = "arkhe-openserv-gw-1"

def sign_envelope(input_hash: bytes, output_hash: bytes, phi_score: float, timestamp: str) -> str:
    phi_int = int(phi_score * 10000)
    message = (
        input_hash +
        output_hash +
        struct.pack("<I", phi_int) +
        timestamp.encode("utf-8") +
        GATEWAY_ID.encode("utf-8")
    )
    signature = PRIVATE_KEY.sign(message)       # Ed25519 real
    return signature.hex()
