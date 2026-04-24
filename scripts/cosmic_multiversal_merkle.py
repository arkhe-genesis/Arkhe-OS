# cosmic_multiversal_merkle.py — Árvore de Merkle quântica para testemunho universal

import hashlib

class CosmicMultiversalMerkleTree:
    """
    Árvore de Merkle quântica para testemunho universal.
    """
    def __init__(self):
        self.leaves = []

    def add_leaf(self, data: str):
        h = hashlib.sha3_256(data.encode()).hexdigest()
        self.leaves.append(h)
        return h

    def build_root(self):
        if not self.leaves: return None
        current = self.leaves
        while len(current) > 1:
            next_lvl = []
            for i in range(0, len(current), 2):
                l = current[i]
                r = current[i+1] if i+1 < len(current) else l
                next_lvl.append(hashlib.sha3_256((l + r).encode()).hexdigest())
            current = next_lvl
        return current[0]

if __name__ == "__main__":
    tree = CosmicMultiversalMerkleTree()
    tree.add_leaf("CosmicEcho:Andromeda")
    tree.add_leaf("MultiversalHandshake:BranchB")
    root = tree.build_root()
    print(f"Cosmic-Multiversal Merkle Root: {root[:16]}...")
