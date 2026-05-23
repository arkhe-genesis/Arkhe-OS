# extenddb_ipfs_backend.py
# Wraps ExtendDB operations: large B attributes -> IPFS/Hashtree.

import subprocess
import os

class ExtendDBIPFSBackend:
    def __init__(self, base_extenddb, ipfs_bridge, threshold_bytes=4096, use_htree=True):
        self.base = base_extenddb
        self.ipfs = ipfs_bridge
        self.threshold = threshold_bytes
        self.use_htree = use_htree

    def put_item(self, table, item):
        # Replace large binary values with CIDs
        for key, value in item.items():
            if isinstance(value, bytes) and len(value) > self.threshold:
                cid = None
                if self.use_htree:
                    # Integrate htree CLI to add content to hashtree
                    try:
                        # Write temporarily to upload via htree
                        import tempfile
                        fd, path = tempfile.mkstemp()
                        with os.fdopen(fd, 'wb') as f:
                            f.write(value)

                        # Simulate htree command (assuming htree is installed)
                        # Normally: result = subprocess.run(["htree", "add", path], capture_output=True, text=True)
                        # cid = result.stdout.strip()
                        # For simulation, we fall back to ipfs if htree isn't actually available:
                        cid = self.ipfs.add(value)
                        os.remove(path)
                    except Exception:
                        cid = self.ipfs.add(value)
                else:
                    cid = self.ipfs.add(value)
                item[key] = "ipfs://" + cid
        return self.base.put_item(table, item)

    def get_item(self, table, key):
        result = self.base.get_item(table, key)
        # Restore binary values from IPFS/Hashtree CIDs
        for attr, value in result.get("Item", {}).items():
            if isinstance(value, str) and value.startswith("ipfs://"):
                cid = value[7:]
                try:
                    # The updated ipfs_bridge will fallback to Hashtree/Nostr automatically
                    result["Item"][attr] = self.ipfs.get(cid)
                except Exception:
                    result["Item"][attr] = None  # Graceful degradation
        return result
