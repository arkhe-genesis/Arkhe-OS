import subprocess
import json

class IPFSBridge:
    def __init__(self):
        self.nostr_relays = [
            "wss://relay.damus.io",
            "wss://nos.lol",
            "wss://relay.nostr.band"
        ]

    def get_cid(self, cid):
        # 1. Try IPFS native
        try:
            result = subprocess.run(["ipfs", "cat", cid], capture_output=True, text=True, check=True)
            return result.stdout
        except Exception:
            pass

        # 2. Fallback to Hashtree / Nostr Relays via htree
        try:
            result = subprocess.run(["htree", "get", cid], capture_output=True, text=True, check=True)
            return result.stdout
        except Exception:
            pass

        return None

if __name__ == "__main__":
    bridge = IPFSBridge()
    # test
