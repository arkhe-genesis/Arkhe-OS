import hashlib

def _hash(data):
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).digest()

def compute_merkle_root(leaves):
    if not leaves:
        return {"root": b'', "proof_map": {}}

    nodes = [_hash(leaf) for leaf in leaves]
    levels = [nodes]

    while len(nodes) > 1:
        if len(nodes) % 2 != 0:
            nodes.append(nodes[-1])
        next_level = []
        for i in range(0, len(nodes), 2):
            left = nodes[i]
            right = nodes[i + 1]
            # OpenZeppelin MerkleProof requires sorted sibling nodes before hashing
            if left <= right:
                combined = left + right
            else:
                combined = right + left
            next_level.append(_hash(combined))
        nodes = next_level
        levels.append(nodes)

    proof_map = {"levels": levels, "leaves": leaves}
    return {"root": nodes[0], "proof_map": proof_map}

def generate_proof(proof_map, index):
    levels = proof_map.get("levels", [])
    proof = []

    for level in levels[:-1]:
        is_right_node = index % 2 != 0
        sibling_index = index - 1 if is_right_node else index + 1

        if sibling_index < len(level):
            proof.append(level[sibling_index])

        index = index // 2

    return proof
