import hashlib
import time
import json
import random

class NonDeterministicProofSeed:
    def __init__(self, entropy_sources=['time', 'pid', 'memory'], chain_binding=True):
        self.entropy_sources = entropy_sources
        self.chain_binding = chain_binding

    def generate_seed(self, proof_content, parent_hash):
        entropy = f"{time.time_ns()}_{random.random()}_{parent_hash}"
        return hashlib.sha256(entropy.encode()).hexdigest()

    def inject_into_proof(self, proof_template, parent_hash):
        seed = self.generate_seed(proof_template, parent_hash)
        enriched = proof_template.copy()
        enriched['entropy_metadata'] = {'seed': seed}
        enriched['proof_hash'] = hashlib.sha256(f"{proof_template}_{seed}".encode()).hexdigest()[:16]
        return enriched
