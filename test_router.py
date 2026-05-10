import sys
sys.path.append('.')

import temporal_network
import uuid
import time
from temporal_network import AuditLedger, TemporalHashChain, MultiverseRouter

ledger = AuditLedger()
chain = TemporalHashChain()
router = MultiverseRouter(ledger, chain)

b1 = router.create_branch("e1", time.time(), "b1", "main")
b2 = router.create_branch("e2", time.time(), "b2", "b1")
b3 = router.create_branch("e3", time.time(), "b3", "b2")

print(f"verify_kripke_semantics (expected True): {router.verify_kripke_semantics()}")
print(f"is_accessible main -> b3 (expected True): {router.is_accessible('main', 'b3')}")
print(f"is_accessible b1 -> b3 (expected True): {router.is_accessible('b1', 'b3')}")
print(f"is_accessible b3 -> b1 (expected False): {router.is_accessible('b3', 'b1')}")

router.create_branch("e4", time.time(), "b4", "b3")
print(f"verify_kripke_semantics (expected True): {router.verify_kripke_semantics()}")
