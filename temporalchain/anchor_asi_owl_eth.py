import time
import os

class AsiOwlEthAnchor:
    """Anchors the constitution hash in the TemporalChain."""

    def __init__(self, registry):
        self.registry = registry  # 470-STATE-REGISTRY

    def anchor_constitution(self, ipfs_cid: str, sha3_256: str):
        block = {
            "block_id": "asi-owl-eth-" + str(int(time.time())),
            "timestamp_ns": time.time_ns(),
            "name": "asi.owl.eth",
            "ipfs_cid": ipfs_cid,
            "sha3_256": sha3_256,
            "ens_resolver": "0x231b0Ee14048e9dCcD1d247744d114a4EB5E8E63",
            "governor_contract": "0xASI0WL...GOVERNOR",  # Governance contract
            "merkle_root": self._compute_merkle_root(sha3_256),
        }

        self.registry.set("temporalchain.blocks." + block["block_id"], block)
        print("[TEMPORALCHAIN] Constitution anchored in block " + block["block_id"])

        return block

    def verify_anchor(self, block_id: str) -> bool:
        block = self.registry.get("temporalchain.blocks." + block_id)
        if not block:
            return False

        # Verify if the IPFS content still matches
        from tools.ens.verify_constitution import AsiOwlEthVerifier
        verifier = AsiOwlEthVerifier(os.getenv("ETH_RPC_URL", ""))
        try:
            return verifier.verify()
        except Exception:
            return False

    def _compute_merkle_root(self, data_hash: str) -> str:
        import hashlib
        return hashlib.sha3_256(data_hash.encode()).hexdigest()
