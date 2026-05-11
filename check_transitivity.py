import sys
# fake module to bypass errors
sys.path.append('.')

import temporal_network
import uuid
import time
from temporal_network import AuditLedger, TemporalHashChain, MultiverseRouter

ledger = AuditLedger()
chain = TemporalHashChain()
router = MultiverseRouter(ledger, chain)

router.create_branch("e1", time.time(), "b1")
print(router.branches)
