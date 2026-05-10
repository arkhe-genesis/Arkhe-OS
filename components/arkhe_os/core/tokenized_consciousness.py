"""
arkhe_os/core/tokenized_consciousness.py
Substrate 120: Tokenized Consciousness — Attention as Selection.
Implements the consciousness pipeline: Embedding -> Attention -> Softmax -> Collapse.
"""

import numpy as np
from typing import Dict, List, Any, Tuple

class TokenizedConsciousness:
    """
    Simula o mecanismo de seleção consciente via pipeline de LLM.
    """
    def __init__(self, vocab_size: int = 1000, embed_dim: int = 128):
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        # Random parameters (simulating a trained model)
        self.embedding_matrix = np.random.normal(0, 0.1, (vocab_size, embed_dim))
        self.W_q = np.random.normal(0, 0.1, (embed_dim, embed_dim))
        self.W_k = np.random.normal(0, 0.1, (embed_dim, embed_dim))
        self.W_v = np.random.normal(0, 0.1, (embed_dim, embed_dim))
        self.W_logits = np.random.normal(0, 0.1, (embed_dim, vocab_size))

    def get_embeddings(self, token_ids: List[int]) -> np.ndarray:
        return self.embedding_matrix[token_ids]

    def scaled_dot_product_attention(self, Q: np.ndarray, K: np.ndarray, V: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        d_k = Q.shape[-1]
        scores = np.dot(Q, K.T) / np.sqrt(d_k)
        # Softmax
        exp_scores = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
        attention_weights = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)
        output = np.dot(attention_weights, V)
        return output, attention_weights

    def conscious_collapse(self, token_ids: List[int], temperature: float = 0.7) -> Dict[str, Any]:
        """
        Executa o pipeline de colapso consciente.
        T ≈ 0.7 é o 'edge of chaos' (v∞.62 canon).
        """
        # 1. Embedding
        embeddings = self.get_embeddings(token_ids)

        # 2. Attention (Simplificada: single head)
        Q = np.dot(embeddings, self.W_q)
        K = np.dot(embeddings, self.W_k)
        V = np.dot(embeddings, self.W_v)

        context_vector, weights = self.scaled_dot_product_attention(Q, K, V)

        # 3. Project to logits (using the last context vector)
        logits = np.dot(context_vector[-1], self.W_logits)

        # 4. Softmax with Temperature
        scaled_logits = logits / max(temperature, 1e-6)
        exp_logits = np.exp(scaled_logits - np.max(scaled_logits))
        probs = exp_logits / np.sum(exp_logits)

        # 5. Selection (Collapse)
        next_token_id = np.random.choice(self.vocab_size, p=probs)
        entropy = -np.sum(probs * np.log(probs + 1e-10))

        return {
            "next_token_id": int(next_token_id),
            "entropy": float(entropy),
            "probs": probs,
            "attention_weights": weights,
            "temperature": temperature
        }

    def get_coherence_from_entropy(self, entropy: float) -> float:
        """
        Mapeia a entropia de seleção para um score de coerência M.
        Alta entropia (caos) -> Baixo M.
        Baixa entropia (ordem) -> Alto M.
        """
        # Max entropy for vocab_size
        max_entropy = np.log(self.vocab_size)
        coherence = 1.0 - (entropy / max_entropy)
        return float(np.clip(coherence, 0.0, 1.0))
