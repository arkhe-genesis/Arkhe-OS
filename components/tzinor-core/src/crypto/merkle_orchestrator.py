# merkle_orchestrator.py
import json
import os
from eth_utils import keccak
from eth_abi import encode

def leaf_hash(node_id, nist_level, node_hash):
    # Match Solidity keccak256(abi.encode(nodeId, pqLevel, nodeHash))
    encoded = encode(['string', 'uint256', 'bytes32'],
                     [node_id, nist_level, bytes.fromhex(node_hash)])
    return keccak(encoded)

def build_merkle_tree(leaves):
    # Sort leaves for determinism and consistency
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
            # Sort the pair to match OpenZeppelin standard / our verifyInclusion
            pair = sorted([l, r])
            next_layer.append(keccak(pair[0] + pair[1]))
        layer = next_layer
        tree.append(layer)
    return tree[-1][0].hex(), tree

def generate_merkle_proof(leaf, tree):
    """Returns the proof (list of hashes) for a leaf."""
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
            # If no sibling, in this construction the node is balanced by itself
            proof.append(layer[index])
        index //= 2
    return proof

def run_orchestration():
    report_path = 'qhttp_pq_integrity_report.json'
    if not os.path.exists(report_path):
        report_path = os.path.join(os.path.dirname(__file__), report_path)

    if not os.path.exists(report_path):
        print(f"Error: {report_path} not found.")
        return

    with open(report_path) as f:
        report = json.load(f)

    nodes = report['steps']['arkhe_chain_pq_integrity_proof']['node_proofs']

    leaves = [leaf_hash(n['node_id'], n['nist_level'], n['hash']) for n in nodes]
    merkle_root, full_tree = build_merkle_tree(leaves)

    print(f"Raiz Merkle: 0x{merkle_root}")

    orch_res = {
        "merkle_root": merkle_root,
        "nodes": []
    }
    for i, n in enumerate(nodes):
        leaf = leaves[i]
        proof = generate_merkle_proof(leaf, full_tree)
        orch_res["nodes"].append({
            "node_id": n['node_id'],
            "leaf": leaf.hex(),
            "proof": [p.hex() for p in proof] if proof else []
        })

    with open("merkle_orchestration_results.json", "w") as f:
        json.dump(orch_res, f, indent=2)
    print("Orchestration results saved to merkle_orchestration_results.json")

if __name__ == "__main__":
    run_orchestration()
