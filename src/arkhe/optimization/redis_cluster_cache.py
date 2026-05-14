#!/usr/bin/env python3
"""
redis_cluster_cache.py — Cache distribuído com Redis Cluster.
Escala horizontal do exorcismo e scan para equipes globais.
"""

import redis, hashlib, json, time
from typing import Optional, Dict

class RedisClusterCache:
    """
    Cache distribuído sobre Redis Cluster.
    - Sharding automático para evitar hotspots
    - TTL configurável por tipo de dado
    - Fallback para cache local se Redis indisponível
    """
    def __init__(self, nodes: list, ttl_seconds: int = 300):
        try:
            self.client = redis.RedisCluster(
                startup_nodes=[{"host": h, "port": p} for h, p in nodes],
                decode_responses=True,
                skip_full_coverage_check=True
            )
            self.connected = True
        except Exception:
            self.connected = False
            self._local_cache = {}
        self.ttl = ttl_seconds

    def get(self, key: str) -> Optional[Dict]:
        if self.connected:
            data = self.client.get(key)
            return json.loads(data) if data else None
        return self._local_cache.get(key)

    def set(self, key: str, value: Dict):
        if self.connected:
            self.client.setex(key, self.ttl, json.dumps(value))
        else:
            self._local_cache[key] = value
            if len(self._local_cache) > 10000:
                oldest = min(self._local_cache, key=lambda k: self._local_cache[k].get("t", 0))
                del self._local_cache[oldest]

    def invalidate_by_pattern(self, pattern: str):
        if self.connected:
            for key in self.client.scan_iter(match=pattern):
                self.client.delete(key)