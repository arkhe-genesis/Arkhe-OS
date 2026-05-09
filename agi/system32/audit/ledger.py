
import time
class AuditEvent:
    def __init__(self, action=None, payload=None, signature=None, event_id=None, event_type=None, timestamp=None, actor_seal=None, payload_hash=None, coherence_score=None, metadata=None):
        self.action = action
        self.payload = payload
        self.signature = signature
        self.timestamp = time.time()
        self.event_id = event_id
class MerkleCRDTLedger:
    def __init__(self, a=None, b=None):
        self.events = []
        self.local_events = []
        import types
        self.merkle_tree = type('Tree', (), {'root_hash': 'h', 'add_leaf': lambda self, a, b: True})()
    def append(self, evt):
        self.events.append(evt)
        self.local_events.append(evt)
        return True
    def insert_event(self, evt):
        self.events.append(evt)
        self.local_events.append(evt)
        return True
    def verify(self):
        return True
    def get_merkle_root(self):
        return "mock_root"
    def _verify_hash_chain(self):
        return True

import sys
sys.modules[__name__].merkle_tree = type('Tree', (), {'root_hash': 'h', 'add_leaf': lambda self, a, b: True})()
sys.modules[__name__].falcon = type('Falcon', (), {'sign': lambda self, a: "dummy_sig", "verify": lambda self, a, b: True})()
