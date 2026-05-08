import hashlib

class LedgerSync:
    def __init__(self):
        self.ledger = []

    def sync_octra(self, data):
        self.ledger.append(data)

    def verify_merkle(self):
        if not self.ledger:
            return None
        return hashlib.sha256(str(self.ledger).encode()).hexdigest()

def sync_ledger():
    sync = LedgerSync()
    return sync
