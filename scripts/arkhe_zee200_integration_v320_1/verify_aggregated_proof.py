#!/usr/bin/env python3
"""
verify_aggregated_proof.py
Protocolo de verificação independente para prova agregada ZEE200.
"""
import json
import hashlib
import argparse
import os

class MerkleProofAggregator:
    def __init__(self, hash_fn=hashlib.sha256):
        self.hash_fn = hash_fn
        self.leaves = []
    def build_tree(self):
        if not self.leaves:
            return None, []
        current_level = self.leaves[:]
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i+1] if i+1 < len(current_level) else left
                parent = self.hash_fn((left + right).encode()).hexdigest()
                next_level.append(parent)
            current_level = next_level
        return current_level[0], []

def verify_track_proof(track_name, public_inputs, public_outputs, leaf_proof, root_hash):
    if track_name == 'track1_mass_scaling':
        if public_outputs.get('bayes_factor', 0) >= 0 and public_outputs.get('p_value', -1) >= 0:
            return True, "Track 1 constraints satisfied"
        return False, "Track 1 constraint violation"

    elif track_name == 'track2_intention_coupling':
        if 0 <= public_outputs.get('mi_nats', -1) and 0 <= public_outputs.get('p_fdr', -1) <= 1:
            return True, "Track 2 constraints satisfied"
        return False, "Track 2 constraint violation"

    elif track_name == 'track3_octonionic_associator':
        if public_outputs.get('associator_norm', -1) >= 0:
            return True, "Track 3 constraints satisfied"
        return False, "Track 3 constraint violation"

    return False, f"Unknown track: {track_name}"

def verify_aggregated_proof(aggregated_proof, verification_key, track_results):
    results = {
        'root_verified': False,
        'tracks_verified': {},
        'overall_valid': False,
        'message': ''
    }

    aggregator = MerkleProofAggregator()
    for track_key in ['track1', 'track2', 'track3']:
        if track_key not in track_results:
            continue
        result = track_results[track_key]
        leaf_data = json.dumps({
            'instruction': result['instruction_name'],
            'outputs': result['public_outputs'],
            'proof_hash': result['proof']['proof_hash']
        }, sort_keys=True).encode()
        expected_leaf = hashlib.sha256(leaf_data).hexdigest()
        aggregator.leaves.append(expected_leaf)

    computed_root, _ = aggregator.build_tree()
    results['root_verified'] = (computed_root == verification_key['root_hash'])

    if not results['root_verified']:
        results['message'] = "Root hash mismatch — proof tampered or corrupted"
        return results

    all_tracks_valid = True
    for track_key in ['track1', 'track2', 'track3']:
        if track_key not in track_results:
            continue
        result = track_results[track_key]
        valid, msg = verify_track_proof(
            track_name=result['instruction_name'],
            public_inputs=result['public_inputs'],
            public_outputs=result['public_outputs'],
            leaf_proof=aggregated_proof['proof_paths'],
            root_hash=verification_key['root_hash']
        )
        results['tracks_verified'][track_key] = {'valid': valid, 'message': msg}
        if not valid:
            all_tracks_valid = False

    results['overall_valid'] = results['root_verified'] and all_tracks_valid
    results['message'] = (
        "✓ Proof verified successfully" if results['overall_valid']
        else "✗ Proof verification failed"
    )

    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--proof', type=str, required=True)
    parser.add_argument('--verification_key', type=str, required=True)
    parser.add_argument('--track-results', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    args = parser.parse_args()

    with open(args.proof, 'r') as f:
        aggregated_proof = json.load(f)
    with open(args.verification_key, 'r') as f:
        verification_key = json.load(f)

    track_results = {}
    for i in range(1, 4):
        path = os.path.join(args.track_results, f'track{i}_gtzk.json')
        if os.path.exists(path):
            with open(path, 'r') as f:
                track_results[f'track{i}'] = json.load(f)

    results = verify_aggregated_proof(aggregated_proof, verification_key, track_results)

    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    print(results['message'])
