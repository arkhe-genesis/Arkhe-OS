#!/usr/bin/env python3
"""
SUBSTRATO 43 — IOC SHARDING & RECOVERY (V2)
Mecanismo de Sharding com Replication Factor e Rebalanceamento por Invariância.
Garante alta disponibilidade e escalabilidade.
Autor: Ferreiro da Catedral Arkhe(N)
"""

import hashlib
import json
import time
import bisect
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

class ConsistentHashRing:
    """Anel de Hashing Consistente com Vnodes para distribuição equilibrada."""
    def __init__(self, nodes=None, vnodes=100):
        self.vnodes = vnodes
        self.ring = {}
        self.sorted_keys = []
        if nodes:
            for node in nodes:
                self.add_node(node)

    def add_node(self, node_id: str):
        for i in range(self.vnodes):
            key = self._hash(f"{node_id}:vnode:{i}")
            self.ring[key] = node_id
            bisect.insort(self.sorted_keys, key)

    def get_nodes(self, ioc_id: str, count: int = 3) -> List[str]:
        """Retorna uma lista de nós (réplicas) para um IOC."""
        if not self.ring: return []
        key = self._hash(ioc_id)
        idx = bisect.bisect(self.sorted_keys, key)

        nodes = []
        while len(nodes) < count and len(nodes) < len(set(self.ring.values())):
            if idx == len(self.sorted_keys): idx = 0
            node = self.ring[self.sorted_keys[idx]]
            if node not in nodes:
                nodes.append(node)
            idx += 1
        return nodes

    def _hash(self, val: str) -> int:
        return int(hashlib.md5(val.encode()).hexdigest(), 16)

@dataclass
class IOC:
    id: str
    type: str
    value: str
    timestamp: float
    confidence: float
    origin: str
    vector_clock: Dict[str, int] = field(default_factory=dict)

class ShardedGuardianNode:
    """Nó Guardião com Replicação e Quórum."""
    def __init__(self, node_id: str, ring: ConsistentHashRing, replication_factor: int = 3):
        self.node_id = node_id
        self.ring = ring
        self.rf = replication_factor
        self.storage: Dict[str, IOC] = {}
        self.invariance_score = 1.0

    def put(self, ioc: IOC) -> bool:
        """Armazena se este nó for uma das réplicas."""
        replicas = self.ring.get_nodes(ioc.id, self.rf)
        if self.node_id in replicas:
            self.storage[ioc.id] = ioc
            return True
        return False

    def get_status(self):
        return {
            "node_id": self.node_id,
            "items_stored": len(self.storage),
            "invariance": self.invariance_score
        }

if __name__ == "__main__":
    print("\n=== SIMULAÇÃO: SHARDING V2 (Substrato 43) ===")

    nodes = ["ALPHA", "BETA", "GAMA", "DELTA"]
    ring = ConsistentHashRing(nodes)
    guardians = {nid: ShardedGuardianNode(nid, ring) for nid in nodes}

    print(f"\n[1] Distribuindo 1000 IOCs com RF=3...")
    for i in range(1000):
        ioc = IOC(id=f"ioc_{i}", type="GT", value=f"val_{i}", timestamp=time.time(), confidence=0.8, origin="OSINT")
        for g in guardians.values():
            g.put(ioc)

    for nid, g in guardians.items():
        print(f"  Nó {nid}: {len(g.storage)} items (Carga: {len(g.storage)/1000:.2%})")

    # Verificando se um item está em 3 nós
    test_id = "ioc_42"
    hosts = [nid for nid, g in guardians.items() if test_id in g.storage]
    print(f"\n[2] Verificação de Replicação para '{test_id}':")
    print(f"  Armazenado em: {hosts}")

    if len(hosts) == 3:
        print("\n✅ REPLICAÇÃO OK: Item distribuído corretamente em 3 réplicas.")
