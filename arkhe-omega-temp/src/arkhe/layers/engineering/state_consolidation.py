# src/arkhe/layers/engineering/state_consolidation.py
from arkhe.state import CompileCache
from arkhe.layers.constraints import TemporalChainClient
import hashlib

class UnifiedState:
    def __init__(self, cache_dir="./arkhe-state", temporal_endpoint=None):
        self.cache = CompileCache(cache_dir)
        self.temporal = TemporalChainClient(temporal_endpoint)

    def get(self, key: str) -> dict:
        # try cache first
        val = self.cache.get(hashlib.sha3_256(key.encode()).hexdigest()[:16])
        if val is not None:
            return val
        # fallback to temporal chain
        return self.temporal.retrieve(key)

    def set(self, key: str, value: dict):
        key_hash = hashlib.sha3_256(key.encode()).hexdigest()[:16]
        self.cache.set(key_hash, value)
        # also anchor in temporal chain
        self.temporal.anchor(key_hash, value)

    def snapshot(self) -> str:
        # return a hash of all keys
        keys = self.cache.cache_dir.glob("*.json")
        hasher = hashlib.sha3_256()
        for k in sorted(keys):
            hasher.update(k.read_bytes())
        return hasher.hexdigest()[:16]
