import faiss
import numpy as np
from typing import List, Dict, Tuple
import time

class SemanticVectorIndex:
    """Indexação vetorial de embeddings LFIR com ponderação por coerência."""

    def __init__(self, dim: int = 768):
        self.dim = dim
        self.index = faiss.IndexFlatIP(self.dim)  # Inner product para similaridade
        self.metadata = {}  # id → metadata (coherence, timestamp, etc.)

    def add(self, state_id: str, embedding: np.ndarray, coherence: float):
        """Adiciona embedding ao índice com metadados."""
        embedding = embedding / np.linalg.norm(embedding)  # Normalizar
        self.index.add(embedding.reshape(1, -1))
        self.metadata[self.index.ntotal - 1] = {
            "state_id": state_id,
            "coherence": coherence,
            "timestamp": time.time()
        }

    def search(self, query_embedding: np.ndarray, k: int = 5,
               min_coherence: float = 0.6) -> List[Dict]:
        """Busca por similaridade semântica + peso de coerência."""
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        D, I = self.index.search(query_embedding.reshape(1, -1), k * 2)

        results = []
        for idx in range(len(D[0])):
            if I[0][idx] == -1:
                continue
            meta = self.metadata.get(I[0][idx], {})
            if meta.get("coherence", 0) >= min_coherence:
                # Score combinado: similaridade * (1 + coerência)
                score = D[0][idx] * (1 + meta["coherence"])
                results.append({
                    "state_id": meta["state_id"],
                    "similarity": D[0][idx],
                    "coherence": meta["coherence"],
                    "score": score,
                    "timestamp": meta.get("timestamp", 0)
                })

        return sorted(results, key=lambda x: x["score"], reverse=True)[:k]
