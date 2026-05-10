import pytest
import time
import math
import hashlib
import random
import sys
import os

sys.path.append('arkhe-omega-temp')

from arkhe.substrate_6041_v2.substrate_6041_v2 import (
    Substrate6041v2,
    TemporalEdgeV2,
    AtomicNode
)

def test_v433_v2_complete():
    substrate = Substrate6041v2("CATHEDRAL-MAIN")

    nodes = []
    for i in range(10):
        name = f"NODE-{i:04d}"
        cost = random.uniform(0.1, 50.0)
        cons = random.uniform(0.5, 0.99)
        edge = TemporalEdgeV2(
            dest=name, next_hop=name, cost=cost,
            consistency=cons, expires=time.time() + 86400,
        )
        edge.zk_proof_hash = hashlib.sha3_256(f"zk-{i}".encode()).hexdigest()
        edge.ledger_hash = hashlib.sha3_256(f"led-{i}".encode()).hexdigest()
        edge.solar_phase = random.uniform(0, 2 * math.pi)
        edge.galactic_index = random.randint(0, 1000)
        edge.created_at = time.time()

        nodes.append((name, cost, cons))
        substrate.add_route(edge)

    # Test 1: Oracle-in-the-Loop
    targets = ["NODE-0000", "NODE-0005"]
    routes = substrate.find_best_routes_batch(targets, use_oracle=True)
    assert len(routes) == 2

    # Test 2: Steiner Broadcast
    multicast_targets = [n[0] for n in random.sample(nodes, 3)]
    steiner_tree = substrate.optimal_multicast_tree(multicast_targets)
    assert steiner_tree is not None

    # Test 3: Multiverse Atomic
    for i in range(10):
        node = AtomicNode(
            name=f"ATOM-{i:06d}",
            shard_id=-1,
            node_type="relay",
            position_au=(0, 0, 0),
            consistency=0.9,
            created_at=time.time(),
            expires=time.time() + 86400,
            metadata_hash="hash",
            is_border=True,
            neighbor_count=1,
        )
        substrate.register_multiverse_node(node)

    substrate._multiverse.add_route("ATOM-000000", "ATOM-000005", 1.0)

    mv_route = substrate.find_multiverse_route("ATOM-000000", "ATOM-000005")
    assert mv_route is not None
