#!/usr/bin/env python3
"""
Integration script to apply Hybrid Signatures (Substrato 191)
to TemporalChain blocks.
"""

import sys
import os

# Add parent directory to path to import security module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.hybrid_pqc_quantum_signer import HybridPQCQuantumSigner, SignatureMode
import asyncio
import hashlib
import time

class TemporalChainHybridSigner:
    def __init__(self):
        self.signer = HybridPQCQuantumSigner(pqc_algorithm="ML-DSA-65")

    async def sign_block(self, block_data: dict) -> dict:
        """Sign a TemporalChain block using hybrid signature."""

        # Serialize block data
        # For a simple demo, we just use a string representation
        block_bytes = str(block_data).encode('utf-8')

        metadata = {
            "block_index": block_data.get("index", 0),
            "timestamp": time.time(),
            "context": "temporal_chain_block"
        }

        print(f"Signing block {block_data.get('index', 0)} with Hybrid PQC+Quantum Signature...")

        result = await self.signer.sign_message(
            message=block_bytes,
            metadata=metadata,
            mode=SignatureMode.HYBRID_PARALLEL
        )

        if result.success:
            block_data["hybrid_signature"] = {
                "pqc_hex": result.pqc_signature_hex,
                "quantum_witness": result.quantum_witness_hash,
                "combined_hash": result.combined_signature_hash,
                "mode": result.mode.value
            }
            print(f"✅ Block signed successfully. Combined Hash: {result.combined_signature_hash}")
        else:
            print(f"❌ Failed to sign block: {result.error_message}")

        return block_data

async def demo_temporal_chain_signing():
    signer = TemporalChainHybridSigner()

    # Create a dummy block
    block = {
        "index": 42,
        "previous_hash": "a1b2c3d4e5f6g7h8i9j0",
        "timestamp": time.time(),
        "data": "Quantum event recorded",
        "nonce": 12345
    }

    signed_block = await signer.sign_block(block)

    print("\nSigned Block Details:")
    for k, v in signed_block.items():
        if k == "hybrid_signature":
            print(f"  {k}:")
            for sub_k, sub_v in v.items():
                # Truncate long hex strings for display
                display_v = f"{sub_v[:20]}..." if isinstance(sub_v, str) and len(sub_v) > 20 else sub_v
                print(f"    {sub_k}: {display_v}")
        else:
            print(f"  {k}: {v}")

if __name__ == "__main__":
    asyncio.run(demo_temporal_chain_signing())
