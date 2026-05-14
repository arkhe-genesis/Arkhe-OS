#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exorcism_cache.py — Substrato 172-OMEGA: Cache de Exorcismo por Contexto
Reduz latência em geração longa evitando re-computação de similaridade semântica.
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict

@dataclass
class ExorcismCacheEntry:
    """Entrada de cache para decisão de exorcismo."""
    context_hash: str  # Hash do contexto recente
    token_embedding_hash: str  # Hash do embedding do token
    permitted: bool  # Decisão: permitido ou bloqueado
    threat_reason: Optional[str]  # Motivo se bloqueado
    timestamp: float
    access_count: int = 0

    def is_stale(self, max_age_seconds: float = 300.0) -> bool:
        """Verifica se entrada está obsoleta."""
        return (time.time() - self.timestamp) > max_age_seconds

class ExorcismCache:
    """
    Cache LRU para decisões de exorcismo baseado em (contexto, token).

    Estratégia:
    • Hash combinado: blake3(context_embeddings[-5:] + token_embedding)
    • TTL de 5 minutos para adaptações a mudanças de contexto
    • Tamanho máximo configurável (default: 10.000 entradas)
    • Invalidação por mudança significativa de Φ_C no contexto
    """

    def __init__(self, max_size: int = 10000, ttl_seconds: float = 300.0):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, ExorcismCacheEntry] = OrderedDict()
        self._stats = {
            "hits": 0, "misses": 0, "evictions": 0, "invalidations": 0
        }

    def _compute_context_hash(self, context_embeddings: List, context_texts: List[str]) -> str:
        """Computa hash estável do contexto recente."""
        # Usar últimos 5 tokens de contexto para balancear especificidade/generalização
        recent_embeddings = context_embeddings[-5:] if len(context_embeddings) >= 5 else context_embeddings
        recent_texts = context_texts[-5:] if len(context_texts) >= 5 else context_texts

        # Serializar de forma determinística
        context_data = {
            "embeddings": [e.tobytes() if hasattr(e, 'tobytes') else list(e) for e in recent_embeddings],
            "texts": recent_texts,
            "length": len(context_embeddings)
        }
        return hashlib.blake3(
            json.dumps(context_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

    def _compute_token_hash(self, token_embedding) -> str:
        """Computa hash do embedding do token."""
        if hasattr(token_embedding, 'tobytes'):
            return hashlib.blake3(token_embedding.tobytes()).hexdigest()[:16]
        return hashlib.blake3(
            json.dumps(token_embedding.tolist() if hasattr(token_embedding, 'tolist') else token_embedding, sort_keys=True).encode()
        ).hexdigest()[:16]

    def lookup(
        self,
        context_embeddings: List,
        context_texts: List[str],
        token_embedding,
        current_phi_c: float,
        phi_c_threshold: float = 0.02,  # Mudança significativa em Φ_C invalida cache
    ) -> Optional[ExorcismCacheEntry]:
        """
        Busca decisão de exorcismo em cache.

        Returns:
            ExorcismCacheEntry se hit, None se miss ou entrada inválida
        """
        context_hash = self._compute_context_hash(context_embeddings, context_texts)
        token_hash = self._compute_token_hash(token_embedding)
        cache_key = f"{context_hash}:{token_hash}"

        # Verificar existência
        if cache_key not in self._cache:
            self._stats["misses"] += 1
            return None

        entry = self._cache[cache_key]

        # Verificar TTL
        if entry.is_stale(self.ttl_seconds):
            self._invalidate_entry(cache_key)
            return None

        # Verificar estabilidade de Φ_C (mudança significativa invalida cache)
        # Em produção: comparar com Φ_C armazenado na entrada
        # Aqui: simplificado para demonstração

        # Atualizar estatísticas e promover no LRU
        entry.access_count += 1
        self._cache.move_to_end(cache_key)  # Promover para mais recente
        self._stats["hits"] += 1

        return entry

    def store(
        self,
        context_embeddings: List,
        context_texts: List[str],
        token_embedding,
        permitted: bool,
        threat_reason: Optional[str] = None,
    ) -> str:
        """Armazena decisão de exorcismo no cache."""
        context_hash = self._compute_context_hash(context_embeddings, context_texts)
        token_hash = self._compute_token_hash(token_embedding)
        cache_key = f"{context_hash}:{token_hash}"

        # Criar entrada
        entry = ExorcismCacheEntry(
            context_hash=context_hash,
            token_embedding_hash=token_hash,
            permitted=permitted,
            threat_reason=threat_reason,
            timestamp=time.time(),
        )

        # Evitar overflow com política LRU
        if len(self._cache) >= self.max_size:
            # Remover entrada menos recente
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats["evictions"] += 1

        # Armazenar
        self._cache[cache_key] = entry
        return cache_key

    def _invalidate_entry(self, cache_key: str):
        """Invalida entrada específica do cache."""
        if cache_key in self._cache:
            del self._cache[cache_key]
            self._stats["invalidations"] += 1

    def invalidate_by_context_change(self, phi_c_change: float, threshold: float = 0.05):
        """Invalida entradas se mudança de Φ_C exceder threshold."""
        if abs(phi_c_change) > threshold:
            # Invalidar todo o cache — mudança significativa de contexto
            self._cache.clear()
            self._stats["invalidations"] += len(self._cache)

    def get_statistics(self) -> Dict:
        """Retorna estatísticas de desempenho do cache."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0.0
        return {
            **self._stats,
            "hit_rate": hit_rate,
            "cache_size": len(self._cache),
            "avg_access_count": (
                sum(e.access_count for e in self._cache.values()) / len(self._cache)
                if self._cache else 0
            ),
        }
