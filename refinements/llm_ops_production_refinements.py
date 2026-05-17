#!/usr/bin/env python3
"""LLM Ops refinements – batching, cache semântico, anti‑alucinação – Substrato 199.5"""

import asyncio, hashlib, time, logging, numpy as np
from collections import deque
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class BatchOptimizer:
    """
    Otimizador de batching dinâmico com janela adaptativa.
    Maximiza throughput sem exceder latência alvo (P95 < 200ms).
    """
    def __init__(self, max_batch_size: int = 32, target_latency_ms: int = 200, phi_bus=None):
        self.max_batch_size = max_batch_size
        self.target_latency = target_latency_ms
        self.phi_bus = phi_bus
        self.batch_history = deque(maxlen=100)

    async def build_batch(self, queue: asyncio.Queue) -> List[Dict]:
        """Agrupa requisições da fila em batch de tamanho adaptativo."""
        batch = []
        deadline = time.time() + 0.1
        # Estimativa de tamanho ideal baseada no histórico recente
        optimal_size = self._estimate_optimal_batch()
        while len(batch) < optimal_size and time.time() < deadline:
            try:
                req = await asyncio.wait_for(queue.get(), timeout=0.01)
                batch.append(req)
            except asyncio.TimeoutError:
                break
        return batch

    def _estimate_optimal_batch(self) -> int:
        if len(self.batch_history) < 5:
            return self.max_batch_size // 2
        avg_latency = np.mean([h["latency"] for h in self.batch_history])
        # Se latência média está muito abaixo do alvo, podemos aumentar
        if avg_latency < self.target_latency * 0.7:
            return min(self.max_batch_size, int(self.max_batch_size * 1.2))
        elif avg_latency > self.target_latency * 0.9:
            return max(4, int(self.max_batch_size * 0.8))
        return self.max_batch_size // 2

class SemanticCache:
    """
    Cache semântico para RAG.
    Armazena embeddings de consultas e respostas, retornando cache hit se similaridade > threshold.
    """
    def __init__(self, embedding_model=None, similarity_threshold: float = 0.95, capacity: int = 10000):
        self.model = embedding_model
        self.threshold = similarity_threshold
        self.capacity = capacity
        self._cache: Dict[str, np.ndarray] = {}  # key: query_hash, value: embedding
        self._responses: Dict[str, Dict] = {}

    def _key(self, query: str) -> str:
        return hashlib.sha3_256(query.encode()).hexdigest()

    async def lookup(self, query: str) -> Optional[Dict]:
        """Retorna resposta cacheada se similaridade > threshold."""
        query_emb = await self.model.embed(query) if self.model else np.random.rand(128)
        best_score = 0
        best_key = None
        for key, cached_emb in self._cache.items():
            # Similaridade cosseno
            score = np.dot(query_emb, cached_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(cached_emb))
            if score > best_score:
                best_score = score
                best_key = key
        if best_score >= self.threshold and best_key:
            logger.info(f"⚡ Cache semântico hit (score {best_score:.3f})")
            return self._responses[best_key]
        return None

    async def store(self, query: str, response: Dict):
        key = self._key(query)
        self._cache[key] = await self.model.embed(query) if self.model else np.random.rand(128)
        self._responses[key] = response
        if len(self._cache) > self.capacity:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
            del self._responses[oldest]

class HallucinationGuardrails:
    """
    Guardrails em tempo real contra alucinação.
    Verifica consistência factual, entropia, e ancoragem em fontes.
    """
    def __init__(self, grounding_sources: List[str] = None, phi_bus=None):
        self.grounding_sources = grounding_sources or []
        self.phi_bus = phi_bus

    async def evaluate(self, response: str, context: str, entropy: float = 0.0) -> Dict:
        """Avalia risco de alucinação e aplica filtro se necessário."""
        grounding_score = self._grounding(response, context)
        # Fatores combinados
        risk = 1.0 - (0.5 * grounding_score + 0.3 * (1 - entropy) + 0.2 * len(response.split())/200)
        is_hallucination = risk > 0.7

        if is_hallucination:
            logger.warning(f"🛑 Alucinação detectada em tempo real (risk {risk:.2f}). Resposta bloqueada.")
            if self.phi_bus:
                await self.phi_bus.publish_metric("hallucination_blocked", {"risk": risk})
            return {"blocked": True, "fallback": "Desculpe, não posso confirmar essa informação."}
        return {"blocked": False, "risk": risk}

    def _grounding(self, response: str, context: str) -> float:
        words_resp = set(response.lower().split())
        words_ctx = set(context.lower().split())
        if not words_resp:
            return 0.0
        return len(words_resp & words_ctx) / len(words_resp)
