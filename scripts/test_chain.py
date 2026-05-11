import json
import sys

# To force a proof, let's mock the classification_result directly
from scripts.arkhe_homeostasis_v327_1.homeostasis_zee200_bridge import HomeostasisZEE200Bridge
bridge = HomeostasisZEE200Bridge(capture_threshold=0.0)

# Mock some classification results that will trigger generating a proof
classification_result = {'capture_fraction': 0.85}
community_details = {
    0: {'regime': 'CAPTURE', 'rho': 0.9, 'crystals': [1, 2, 3, 4, 5], 'manifold_dim': 3}
}
import numpy as np
binarized_codes = np.random.randn(10, 10)
J_matrix = np.random.randn(10, 10)

proofs = bridge.check_and_prove(classification_result, community_details, binarized_codes, J_matrix, epoch=1, parameter_changes={'kappa': 0.1})

with open('publish/interpretability/coherence_chain.json') as f:
    chain = json.load(f)

for block_id, block in chain.items():
    if block_id.startswith('block_') and block_id != 'block_0':
        print(f"Block: {block_id}")
        print(f"  Proof Type: {block.get('proof_metadata', {}).get('proof_type')}")
        print(f"  Root Hash: {block.get('root_hash')}")
        print(f"  Parent Hash: {block.get('parent_hash')}")
        print(f"  Content Hash: {block.get('content_hash')}")
        print(f"  Entropy Seed: {block.get('entropy_metadata', {}).get('seed')}")
