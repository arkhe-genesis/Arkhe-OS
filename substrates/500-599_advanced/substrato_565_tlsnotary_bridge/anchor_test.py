import sys
import os
import json
import time
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from temporalchain.anchor_asi_owl_eth import AsiOwlEthAnchor

class MockRegistry:
    def __init__(self):
        self.store = {}

    def set(self, key, value):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key)

def main():
    print("Testing TemporalChain Anchoring for TLSNotary...")
    registry = MockRegistry()
    anchor = AsiOwlEthAnchor(registry)

    # Simulate a TLSNotary proof
    proof = {
        "session_id": "test_session_999",
        "timestamp": int(time.time()),
        "server_cert": "mock_cert_data"
    }

    proof_str = json.dumps(proof)
    proof_hash = "mock_hash_" + str(proof["timestamp"])

    # Save the proof to the expected directory
    proofs_dir = Path("substrates/500-599_advanced/substrato_565_tlsnotary_bridge/proofs")
    proofs_dir.mkdir(parents=True, exist_ok=True)

    proof_file = proofs_dir / f"565_{proof['session_id']}_{proof['timestamp']}.json"
    with open(proof_file, "w") as f:
        f.write(proof_str)

    print(f"Saved mock proof to {proof_file}")

    # Anchor the proof
    block = anchor.anchor_constitution("ipfs_cid_dummy", proof_hash)

    print(f"Verification block ID: {block['block_id']}")
    print("Anchoring completed successfully.")

if __name__ == "__main__":
    main()
