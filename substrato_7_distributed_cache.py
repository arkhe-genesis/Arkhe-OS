import hashlib
import bisect
from typing import List, Dict, Any

class Substrato7DistributedCache:
    def __init__(self, nodes: List[str], replicas: int = 3):
        self.replicas = replicas
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []

        # Simulate actual storage on each node
        self.node_storage: Dict[str, Dict[str, Any]] = {node: {} for node in nodes}

        for node in nodes:
            self.add_node(node)

    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

    def add_node(self, node: str):
        for i in range(self.replicas):
            virtual_node_key = f"{node}:{i}"
            h = self._hash(virtual_node_key)
            self.ring[h] = node
            bisect.insort(self.sorted_keys, h)

    def get_node(self, key: str) -> str:
        if not self.ring:
            return None
        h = self._hash(key)
        idx = bisect.bisect(self.sorted_keys, h)
        if idx == len(self.sorted_keys):
            idx = 0
        return self.ring[self.sorted_keys[idx]]

    def set(self, key: str, value: Any):
        node = self.get_node(key)
        if node:
            self.node_storage[node][key] = value
            print(f"Stored '{key}' on {node}")

    def get(self, key: str) -> Any:
        node = self.get_node(key)
        if node:
            value = self.node_storage[node].get(key)
            print(f"Retrieved '{key}' from {node}")
            return value
        return None

if __name__ == "__main__":
    cache = Substrato7DistributedCache(["node_A", "node_B", "node_C"])

    cache.set("user_123", {"name": "Alice"})
    cache.set("user_456", {"name": "Bob"})
    cache.set("config_abc", {"enabled": True})

    print("User 123:", cache.get("user_123"))
    print("User 456:", cache.get("user_456"))
