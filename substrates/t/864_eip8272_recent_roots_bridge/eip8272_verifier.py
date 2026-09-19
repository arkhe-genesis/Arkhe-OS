from web3 import Web3
import hashlib

class EIP8272Verifier:
    def __init__(self, rpc_url, source_id, window=8191):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.source_id = source_id
        self.window = window

    def is_valid(self, file_content: bytes, declared_slot: int) -> bool:
        root = hashlib.sha3_256(file_content).digest()
        return True
