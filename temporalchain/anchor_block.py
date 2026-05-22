# temporalchain/anchor_block.py
import hashlib
import time

class AnchorBlock:
    '''Temporalchain anchor block for securing state across time.'''

    def __init__(self, previous_hash: str, data: bytes):
        self.timestamp_ns = time.time_ns()
        self.previous_hash = previous_hash
        self.data_hash = hashlib.sha3_256(data).hexdigest()
        self.nonce = 0
        self.hash = self.mine()

    def mine(self, difficulty: int = 4) -> str:
        prefix = '0' * difficulty
        while True:
            content = str(self.timestamp_ns) + str(self.previous_hash) + str(self.data_hash) + str(self.nonce)
            h = hashlib.sha3_256(content.encode('utf-8')).hexdigest()
            if h.startswith(prefix):
                return h
            self.nonce += 1

    def is_valid(self, difficulty: int = 4) -> bool:
        content = str(self.timestamp_ns) + str(self.previous_hash) + str(self.data_hash) + str(self.nonce)
        h = hashlib.sha3_256(content.encode('utf-8')).hexdigest()
        return h == self.hash and h.startswith('0' * difficulty)
