#!/usr/bin/env python3
"""
ARKHE OS EVM Bridge — Python Backend
Canon: ∞.Ω.∇+++.evm.bridge.python

Python equivalent of ethers.js calldata encoding for ARKHE backend integration.
Uses eth_abi and eth_utils for ABI encoding.
"""

from eth_abi import encode
from eth_utils import keccak, to_hex, to_bytes, is_hexstr
import json
import time
from typing import Dict, Tuple, Optional

class ArkheEVMBridge:
    """
    Bridge Python backend → EVM calldata encoding.
    Mirrors the JavaScript ArkheBadgeAnchor class.
    """

    # Function selector for anchorBadge(bytes32,bytes)
    # keccak256("anchorBadge(bytes32,bytes)")[:4]
    ANCHOR_SELECTOR = "0x8a1b4b7e"  # Example selector

    @staticmethod
    def encode_anchor_calldata(badge_key: str, signature: str) -> str:
        """
        Encode calldata for anchorBadge(bytes32,bytes).

        Args:
            badge_key: 32-byte hex string (0x + 64 chars)
            signature: Variable-length hex string

        Returns:
            Complete calldata hex string
        """
        if not is_hexstr(badge_key) or len(badge_key) != 66:  # 0x + 64
            raise ValueError(f"badge_key must be bytes32 hex string, got {badge_key}")

        if not is_hexstr(signature):
            raise ValueError(f"signature must be hex string, got {signature}")

        # Encode arguments: bytes32, bytes
        # bytes32 is padded to 32 bytes
        # bytes is encoded as offset (32 bytes) + length (32 bytes) + data (padded)
        badge_key_bytes = to_bytes(hexstr=badge_key)
        signature_bytes = to_bytes(hexstr=signature)

        encoded = encode(['bytes32', 'bytes'], [badge_key_bytes, signature_bytes])

        # Prepend function selector
        selector = keccak(text="anchorBadge(bytes32,bytes)")[:4]
        calldata = to_hex(selector) + encoded.hex()

        return calldata

    @staticmethod
    def generate_badge_key(substrate_id: str, canonical_seal: str, timestamp: int) -> str:
        """Generate deterministic badge key from ARKHE substrate data."""
        payload = encode(
            ['string', 'bytes32', 'uint256'],
            [substrate_id, to_bytes(hexstr=canonical_seal), timestamp]
        )
        return to_hex(keccak(payload))

    @staticmethod
    def decode_anchor_calldata(calldata: str) -> Dict:
        """Decode anchorBadge calldata for verification."""
        if len(calldata) < 10:
            raise ValueError("Invalid calldata: too short")

        selector = calldata[:10]
        params = calldata[10:]

        # Decode bytes32 (first 32 bytes after selector)
        badge_key = "0x" + params[0:64]  # First word is 32 bytes (64 hex chars)

        # Decode bytes offset and length
        offset = int(params[64:128], 16) * 2  # Convert to hex chars
        length = int(params[128:192], 16) * 2

        # Extract signature data
        sig_start = 192
        signature = "0x" + params[sig_start:sig_start + length]

        return {
            "selector": selector,
            "badge_key": badge_key,
            "signature": signature,
            "signature_length_bytes": length // 2
        }

    @classmethod
    def create_arkhe_transaction(cls,
                                  substrate_id: str,
                                  canonical_seal: str,
                                  signature: str,
                                  contract_address: str,
                                  chain_id: int = 1) -> Dict:
        """
        Create complete EVM transaction for anchoring ARKHE substrate seal.

        Returns transaction dict ready for signing.
        """
        timestamp = int(time.time())
        badge_key = cls.generate_badge_key(substrate_id, canonical_seal, timestamp)
        calldata = cls.encode_anchor_calldata(badge_key, signature)

        return {
            "to": contract_address,
            "data": calldata,
            "value": "0x0",
            "gasLimit": "0x186a0",  # 100k gas
            "chainId": chain_id,
            "badgeKey": badge_key,
            "substrateId": substrate_id,
            "canonicalSeal": canonical_seal,
            "timestamp": timestamp
        }

# Example: Encode Substrate 241 seal
if __name__ == "__main__":
    bridge = ArkheEVMBridge()

    # Substrate 241 data
    substrate_id = "241+∞"
    canonical_seal = "0x4b854d6a61dab3a5dd8d5ede402d72eac201409d6ee478f767083da3515621b5"
    dummy_signature = "0x" + "00" * 65  # 65-byte ECDSA placeholder

    # Generate badge key
    badge_key = bridge.generate_badge_key(substrate_id, canonical_seal, int(time.time()))
    print(f"Badge Key: {badge_key}")

    # Encode calldata
    calldata = bridge.encode_anchor_calldata(badge_key, dummy_signature)
    print(f"\nCalldata: {calldata}")
    print(f"Selector: {calldata[:10]}")
    print(f"Length: {(len(calldata) - 2) // 2} bytes")

    # Decode to verify
    decoded = bridge.decode_anchor_calldata(calldata)
    print(f"\nDecoded badgeKey: {decoded['badge_key']}")
    print(f"Decoded signature length: {decoded['signature_length_bytes']} bytes")

    # Create full transaction
    tx = bridge.create_arkhe_transaction(
        substrate_id=substrate_id,
        canonical_seal=canonical_seal,
        signature=dummy_signature,
        contract_address="0xArkheBadgeRegistry...",
        chain_id=1
    )
    print(f"\nTransaction ready for signing:")
    print(json.dumps(tx, indent=2))
