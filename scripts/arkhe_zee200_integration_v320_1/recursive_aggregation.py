#!/usr/bin/env python3
"""
recursive_aggregation.py
Agregação recursiva de provas GTZK para Tracks 1-3 via árvore de Merkle.
"""
import hashlib
import json
from collections import defaultdict
import argparse
import os

class MerkleProofAggregator:
    def __init__(self, hash_fn=hashlib.sha256):
        self.hash_fn = hash_fn
        self.leaves = []

    def add_leaf(self, instruction_name, public_outputs, proof_hash):
        leaf_data = json.dumps({
            'instruction': instruction_name,
            'outputs': public_outputs,
            'proof_hash': proof_hash
        }, sort_keys=True).encode()
        leaf_hash = self.hash_fn(leaf_data).hexdigest()
        self.leaves.append(leaf_hash)
        return leaf_hash

    def build_tree(self):
        if not self.leaves:
            return None, []

        current_level = self.leaves[:]
        proof_paths = defaultdict(list)

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i+1] if i+1 < len(current_level) else left

                parent = self.hash_fn((left + right).encode()).hexdigest()
                next_level.append(parent)

                for idx in [i, i+1 if i+1 < len(current_level) else i]:
                    sibling = right if idx == i else left
                    proof_paths[idx].append({'position': 'right' if idx == i else 'left', 'hash': sibling})

            current_level = next_level

        root_hash = current_level[0]
        return root_hash, proof_paths

def aggregate_track_proofs(track_results):
    aggregator = MerkleProofAggregator()

    for track_name, result in track_results.items():
        instruction_name = result['instruction_name']
        public_outputs = result['public_outputs']
        proof_hash = result['proof']['proof_hash']

        leaf_hash = aggregator.add_leaf(
            instruction_name=instruction_name,
            public_outputs=public_outputs,
            proof_hash=proof_hash
        )
        print(f"✓ {track_name}: leaf_hash={leaf_hash[:16]}...")

    root_hash, proof_paths = aggregator.build_tree()

    aggregated_proof = {
        'root_hash': root_hash,
        'leaf_count': len(aggregator.leaves),
        'proof_paths': {k: v for k, v in proof_paths.items()},
        'track_commitments': {
            name: result['public_inputs']
            for name, result in track_results.items()
        }
    }

    verification_key = {
        'root_hash': root_hash,
        'schema': {
            'track1': ['a_fit', 'bayes_factor', 'p_value'],
            'track2': ['mi_nats', 'p_fdr', 'snr_db'],
            'track3': ['associator_norm', 'moufang_p']
        }
    }

    return root_hash, aggregated_proof, verification_key

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--track1', type=str, required=True)
    parser.add_argument('--track2', type=str, required=True)
    parser.add_argument('--track3', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    args = parser.parse_args()

    track_results = {}

    with open(args.track1, 'r') as f:
        track_results['track1'] = json.load(f)
    with open(args.track2, 'r') as f:
        track_results['track2'] = json.load(f)
    with open(args.track3, 'r') as f:
        track_results['track3'] = json.load(f)

    root_hash, aggregated_proof, verification_key = aggregate_track_proofs(track_results)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(aggregated_proof, f, indent=2)

    vk_path = os.path.join(os.path.dirname(args.output), 'verification_key.json')
    with open(vk_path, 'w') as f:
        json.dump(verification_key, f, indent=2)

    print(f"Aggregation complete. Root hash: {root_hash}")
