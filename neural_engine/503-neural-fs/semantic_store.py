# neural_engine/503-neural-fs/semantic_store.py
import numpy as np
from typing import List, Tuple, Optional
import time

try:
    import faiss  # Facebook AI Similarity Search
except ImportError:
    faiss = None

class NeuralFilesystem:
    '''503-NEURAL-FS: Sem ficheiros, apenas embeddings.'''

    def __init__(self, dim: int = 768):
        self.dim = dim
        if faiss:
            self.index = faiss.IndexFlatIP(dim)  # Inner product (cosine apos normalizacao)
        else:
            self.index = None
        self.id_to_data = {}  # embedding_id -> dados originais
        self.id_to_metadata = {}  # embedding_id -> metadados

    def store(self, data: bytes, context: str,
             embedding: Optional[np.ndarray] = None) -> str:
        '''
        Armazena dados como embedding no espaco semantico.
        Se embedding nao fornecido, gera via encoder do 490-NES-v2.
        '''
        if embedding is None:
            embedding = self._encode(data, context)

        # Normalizar para busca por similaridade de cosseno
        embedding = embedding / np.linalg.norm(embedding)

        # Inserir no indice FAISS
        emb_id = len(self.id_to_data)
        if self.index:
            self.index.add(embedding.reshape(1, -1))
        self.id_to_data[emb_id] = data
        self.id_to_metadata[emb_id] = {
            "context": context,
            "timestamp_ns": time.time_ns(),
            "access_count": 0,
            "size_bytes": len(data),
        }

        return "XiM://thought/" + str(emb_id)  # Nao ha caminho, apenas ID

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[bytes, float]]:
        '''Recupera top_k dados mais similares a query semantica.'''
        if not self.index:
            return []

        query_emb = self._encode_text(query)
        query_emb = query_emb / np.linalg.norm(query_emb)

        distances, indices = self.index.search(query_emb.reshape(1, -1), top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx in self.id_to_data:
                self.id_to_metadata[idx]["access_count"] += 1
                results.append((self.id_to_data[idx], float(dist)))

        return results

    def dream(self, thought_id: int) -> bytes:
        '''Recupera memoria de sonho (Domain 4 - NVMe comprimido).'''
        if thought_id in self.id_to_data:
            return self.id_to_data[thought_id]
        # Fallback: descomprimir do Dream Store
        return self._decompress_from_dream_store(thought_id)

    def _encode(self, data: bytes, context: str) -> np.ndarray:
        '''Encoder neural (490-NES-v2 logistic neuron stack).'''
        # Simplificacao: hash -> embedding deterministico
        import hashlib
        h = hashlib.sha3_256(data + context.encode()).digest()
        return np.frombuffer(h, dtype=np.float32)[:self.dim]

    def _encode_text(self, text: str) -> np.ndarray:
        import hashlib
        h = hashlib.sha3_256(text.encode()).digest()
        return np.frombuffer(h, dtype=np.float32)[:self.dim]