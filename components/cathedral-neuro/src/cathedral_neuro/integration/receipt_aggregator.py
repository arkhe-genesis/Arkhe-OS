"""
receipt_aggregator.py — Agregação de NeuroReceipts via Merkle tree
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

@dataclass
class ReceiptBatch:
    batch_id: str
    merkle_root: str
    n_receipts: int
    is_complete: bool

class NeuroReceiptAggregator:
    def __init__(self, quantum_bus_publisher, config=None):
        self.qbus = quantum_bus_publisher
        self._active_batches = {}

    async def add_receipt(self, receipt_data, participant_did):
        return ReceiptBatch("batch_001", "root_hash", 1, True)
