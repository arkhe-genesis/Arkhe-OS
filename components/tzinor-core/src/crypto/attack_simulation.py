# attack_simulation.py
import json
import os
from eth_utils import keccak
from eth_abi import encode

def leaf_hash(node_id, nist_level, node_hash):
    encoded = encode(['string', 'uint256', 'bytes32'],
                     [node_id, nist_level, bytes.fromhex(node_hash)])
    return keccak(encoded)

def build_merkle_tree(leaves):
    leaves = sorted(leaves)
    if not leaves:
        return None, []

    layer = leaves
    tree = [layer]
    while len(layer) > 1:
        next_layer = []
        for i in range(0, len(layer), 2):
            l = layer[i]
            r = layer[i+1] if i+1 < len(layer) else l
            pair = sorted([l, r])
            next_layer.append(keccak(pair[0] + pair[1]))
        layer = next_layer
        tree.append(layer)
    return tree[-1][0].hex(), tree

def generate_merkle_proof(leaf, tree):
    try:
        index = tree[0].index(leaf)
    except ValueError:
        return None
    proof = []
    for layer in tree[:-1]:
        sibling_index = index ^ 1
        if sibling_index < len(layer):
            proof.append(layer[sibling_index])
        else:
            proof.append(layer[index])
        index //= 2
    return proof

def verify_inclusion(leaf, proof, root):
    computed = leaf
    for p in proof:
        if computed <= p:
            computed = keccak(computed + p)
        else:
            computed = keccak(p + computed)
    return computed.hex() == root

def run_attack_simulation():
    report_path = 'qhttp_pq_integrity_report.json'
    if not os.path.exists(report_path):
        report_path = os.path.join(os.path.dirname(__file__), report_path)

    with open(report_path) as f:
        report = json.load(f)

    real_nodes = report['steps']['arkhe_chain_pq_integrity_proof']['node_proofs']
    real_leaves = [leaf_hash(n['node_id'], n['nist_level'], n['hash']) for n in real_nodes]
    merkle_root, tree = build_merkle_tree(real_leaves)

    print(f"Raiz Merkle Validada: 0x{merkle_root}")

    # Fake node
    fake_node = ("arkhe-rio-FAKE", 5, "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff")
    fake_leaf = leaf_hash(*fake_node)

    # Attempt 1: Use a proof from a real leaf
    some_real_leaf = real_leaves[0]
    proof = generate_merkle_proof(some_real_leaf, tree)

    is_valid = verify_inclusion(fake_leaf, proof, merkle_root)
    print(f"Fake leaf with real proof: {is_valid} (Expect: False)")

    # Attempt 2: Random proof
    import secrets
    random_proof = [secrets.token_bytes(32) for _ in range(len(proof))]
    is_valid_random = verify_inclusion(fake_leaf, random_proof, merkle_root)
    print(f"Fake leaf with random proof: {is_valid_random} (Expect: False)")

    if not is_valid and not is_valid_random:
        print("\nSUCCESS: All forged inclusion attempts rejected by Keccak-256 Merkle logic.")
    else:
        print("\nFAILURE: One or more forged inclusion attempts accepted.")

if __name__ == "__main__":
    run_attack_simulation()
