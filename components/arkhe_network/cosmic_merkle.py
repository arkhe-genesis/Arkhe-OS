# arkhe_network/cosmic_merkle.py
import hashlib

class CosmicMerkleTree:
    """
    Constrói uma Merkle Tree de profundidade 1 (Árvore de Estrela)
    onde as folhas são as Raízes Merkle dos sinais locais de cada nó.
    """
    @staticmethod
    def hash_node_state(node_id: str, local_merkle_root: str, timestamp_tdb: float) -> str:
        """Hash do estado relatado por um nó individual"""
        state_str = f"{node_id}:{local_merkle_root}:{timestamp_tdb:.9f}"
        return hashlib.sha256(state_str.encode()).hexdigest()

    @classmethod
    def compute_global_root(cls, node_states: list) -> str:
        """
        Calcula a Raiz Merkle Global para uma fatia de tempo sincronizada.
        node_states: lista de (node_id, local_root, tdb_timestamp)
        """
        if not node_states:
            return "0" * 64

        leaf_hashes = [cls.hash_node_state(n_id, root, tdb) for n_id, root, tdb in node_states]

        level = leaf_hashes
        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i+1] if i+1 < len(level) else level[i]
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                next_level.append(combined)
            level = next_level

        return level[0]
