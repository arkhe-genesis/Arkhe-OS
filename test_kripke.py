import sys
sys.path.append('.')

import temporal_network
import uuid
import time
from temporal_network import AuditLedger, TemporalHashChain, MultiverseRouter

ledger = AuditLedger()
chain = TemporalHashChain()
router = MultiverseRouter(ledger, chain)

def is_accessible(router, world_a: str, world_b: str) -> bool:
    if world_a == world_b:
        return True

    current = world_b
    visited = set([current])
    while current in router.branches and current != "main":
        parent = router.branches[current].base_timeline
        if parent == world_a:
            return True
        if parent in visited:
            break
        visited.add(parent)
        current = parent

    return False

def verify_kripke_semantics(router) -> bool:
    branches = list(router.branches.keys())

    for w in branches:
        if not is_accessible(router, w, w):
            return False

    for w1 in branches:
        for w2 in branches:
            if is_accessible(router, w1, w2):
                for w3 in branches:
                    if is_accessible(router, w2, w3):
                        if not is_accessible(router, w1, w3):
                            return False

    return True

# Monkey patch for create_branch with base_timeline
def create_branch(self, divergence_event: str, from_timestamp: float, branch_id: str = None, base_timeline: str = "main"):
    from temporal_network import TimelineBranch, TAddr, MULTIVERSE_BASE_OFFSET
    bid = branch_id or f"branch-{uuid.uuid4().hex[:8]}"
    epoch = from_timestamp + MULTIVERSE_BASE_OFFSET * len(self.branches)
    branch = TimelineBranch(branch_id=bid, divergence_timestamp=from_timestamp,
                            divergence_event=divergence_event, base_timeline=base_timeline,
                            taddr_base=TAddr.from_parts(bid, epoch, 0.01))
    self.branches[bid] = branch
    return branch

MultiverseRouter.create_branch = create_branch

b1 = router.create_branch("e1", time.time(), "b1", "main")
b2 = router.create_branch("e2", time.time(), "b2", "b1")
b3 = router.create_branch("e3", time.time(), "b3", "b2")

print(f"Accessible main -> b3: {is_accessible(router, 'main', 'b3')}")
print(f"Accessible b1 -> b3: {is_accessible(router, 'b1', 'b3')}")
print(f"Accessible b3 -> b1: {is_accessible(router, 'b3', 'b1')}")
print(f"Kripke semantics valid: {verify_kripke_semantics(router)}")
