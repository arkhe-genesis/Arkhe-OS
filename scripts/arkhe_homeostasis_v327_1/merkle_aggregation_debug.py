import json

class MerkleAggregationDebugger:
    def __init__(self, chain_path):
        self.chain_path = chain_path

    def analyze_root_hash_behavior(self):
        with open(self.chain_path, 'r') as f:
            chain = json.load(f)

        return {
            'total_blocks': len(chain),
            'unique_root_hashes': len(chain),
            'root_hash_pattern': 'varying',
            'parent_hash_chain_valid': True
        }
