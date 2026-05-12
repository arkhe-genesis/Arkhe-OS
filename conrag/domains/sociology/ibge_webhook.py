#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/sociology/ibge_webhook.py — Webhook Handler para Invalidação de Cache IBGE
Permite que o IBGE notifique automaticamente quando novos dados são publicados,
invalidando entradas de cache relevantes sem necessidade de polling.

Integração:
- IBGE publica webhook para https://arkhe-cathedral.org/api/v1/ibge/webhook
- Payload assinado com chave pública IBGE
- Redis Pub/Sub notifica nós do ConRAG para invalidar cache local
- Audit trail registrado no TemporalHashChain
"""

import json
import hashlib
import hmac
import time
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import aiohttp
from fastapi import FastAPI, Request, HTTPException, Header, BackgroundTasks
from fastapi.responses import JSONResponse

try:
    import redis.asyncio as aioredis
    REDIS_ASYNC_AVAILABLE = True
except ImportError:
    REDIS_ASYNC_AVAILABLE = False
    logging.warning("redis async not installed — webhook notifications will be local-only")

logger = logging.getLogger(__name__)

# ============================================================================
# TIPOS E CONSTANTES
# ============================================================================

class IBGEUpdateType(Enum):
    """Tipos de atualização do IBGE que podem invalidar cache."""
    NEW_DATASET = auto()           # Novo conjunto de dados publicado
    DATASET_UPDATE = auto()        # Dados existentes atualizados
    METADATA_CHANGE = auto()       # Metadados alterados (ex: metodologia)
    REVISION = auto()              # Revisão de dados históricos
    DEPRECATION = auto()           # Dataset marcado como obsoleto

@dataclass
class IBGEWebhookPayload:
    """Payload canônico para webhook do IBGE."""
    event_type: IBGEUpdateType
    dataset_id: str                # ID do dataset (ex: "sidra/1612")
    indicators: List[str]          # Indicadores afetados
    years: List[int]               # Anos afetados
    states: Optional[List[str]]    # Estados afetados (None = nacional)
    update_timestamp: float        # Timestamp da atualização no IBGE
    version: str                   # Versão do payload (ex: "1.0")
    signature: str                 # Assinatura HMAC para verificação

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'IBGEWebhookPayload':
        return cls(
            event_type=IBGEUpdateType[data['event_type']],
            dataset_id=data['dataset_id'],
            indicators=data['indicators'],
            years=data['years'],
            states=data.get('states'),
            update_timestamp=data['update_timestamp'],
            version=data['version'],
            signature=data['signature'],
        )

@dataclass
class CacheInvalidationRule:
    """Regra para determinar quais chaves de cache invalidar."""
    indicators_pattern: Optional[str] = None    # Regex para indicadores
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    states_pattern: Optional[str] = None        # Regex para estados
    dataset_pattern: Optional[str] = None       # Regex para dataset_id

    def matches(self, cache_key: str, cache_metadata: Dict) -> bool:
        """Verifica se uma entrada de cache deve ser invalidada."""
        import re
        # Extrair metadados da chave (simplificado)
        if self.dataset_pattern and cache_metadata.get('dataset'):
            if not re.match(self.dataset_pattern, cache_metadata['dataset']):
                return False
        if self.indicators_pattern:
            indicators = cache_metadata.get('indicators', [])
            if not any(re.match(self.indicators_pattern, ind) for ind in indicators):
                return False
        if self.year_min or self.year_max:
            year = cache_metadata.get('year')
            if year:
                if self.year_min and year < self.year_min:
                    return False
                if self.year_max and year > self.year_max:
                    return False
        if self.states_pattern:
            states = cache_metadata.get('states', [])
            if states and not any(re.match(self.states_pattern, s) for s in states):
                return False
        return True

# ============================================================================
# VERIFICADOR DE ASSINATURA IBGE
# ============================================================================

class IBGESignatureVerifier:
    """Verifica assinaturas HMAC de webhooks do IBGE."""

    # Chave pública IBGE (em produção: buscar via JWK endpoint)
    IBGE_PUBLIC_KEY = "arkhe:ibge:webhook:pubkey:v1:..."

    @staticmethod
    def verify(payload: IBGEWebhookPayload, secret: str) -> bool:
        """
        Verifica assinatura HMAC do payload.

        Args:
            payload: Payload recebido
            secret: Chave secreta compartilhada com IBGE

        Returns:
            True se assinatura válida
        """
        # Reconstruir mensagem para verificação (excluir signature)
        message_data = {
            'event_type': payload.event_type.name,
            'dataset_id': payload.dataset_id,
            'indicators': payload.indicators,
            'years': payload.years,
            'states': payload.states,
            'update_timestamp': payload.update_timestamp,
            'version': payload.version,
        }
        message = json.dumps(message_data, sort_keys=True).encode()

        # Verificar HMAC-SHA3-256
        expected_sig = hmac.new(
            secret.encode(),
            message,
            hashlib.sha3_256
        ).hexdigest()

        return hmac.compare_digest(expected_sig, payload.signature)

# ============================================================================
# GERENCIADOR DE INVALIDAÇÃO DE CACHE
# ============================================================================

class IBGECacheInvalidator:
    """
    Gerencia invalidação de cache baseada em webhooks do IBGE.

    Funcionalidades:
    - Recebe webhooks assinados do IBGE
    - Determina quais chaves de cache invalidar baseado em regras
    - Notifica nós distribuídos via Redis Pub/Sub
    - Registra auditoria no TemporalHashChain
    """

    # Canal Redis para notificações de invalidação
    REDIS_CHANNEL = "arkhe:ibge:cache_invalidation"

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        ibge_webhook_secret: str = "",
        audit_logger=None,
    ):
        self.redis: Optional[aioredis.Redis] = None
        self.ibge_secret = ibge_webhook_secret
        self.audit_logger = audit_logger
        self.invalidation_rules: List[CacheInvalidationRule] = []
        self._stats = {'webhooks_received': 0, 'keys_invalidated': 0, 'errors': 0}

        if REDIS_ASYNC_AVAILABLE:
            self.redis = aioredis.from_url(redis_url, decode_responses=True)

    def register_invalidation_rule(self, rule: CacheInvalidationRule):
        """Registra regra para determinar quais caches invalidar."""
        self.invalidation_rules.append(rule)

    async def process_webhook(
        self,
        payload: IBGEWebhookPayload,
        cache_manager,  # IBGECacheManager instance
    ) -> Dict:
        """
        Processa webhook recebido do IBGE.

        Args:
            payload: Payload verificado do webhook
            cache_manager: Instância do gerenciador de cache

        Returns:
            Dict com resultados da invalidação
        """
        self._stats['webhooks_received'] += 1
        start_time = time.time()

        # 1. Verificar assinatura
        if not IBGESignatureVerifier.verify(payload, self.ibge_secret):
            self._stats['errors'] += 1
            logger.error(f"❌ Assinatura inválida para webhook: {payload.dataset_id}")
            return {'error': 'invalid_signature', 'payload_id': payload.dataset_id}

        # 2. Determinar chaves a invalidar
        keys_to_invalidate = []
        for rule in self.invalidation_rules:
            # Em produção: scan Redis para encontrar chaves matching
            # Aqui: delegar para cache_manager com filtros
            matching_keys = await self._find_matching_keys(
                cache_manager, payload, rule
            )
            keys_to_invalidate.extend(matching_keys)

        # 3. Invalidar chaves localmente
        invalidated_count = 0
        for key in keys_to_invalidate:
            if await cache_manager._async_delete(key):
                invalidated_count += 1

        self._stats['keys_invalidated'] += invalidated_count

        # 4. Notificar outros nós via Redis Pub/Sub
        if self.redis:
            await self._broadcast_invalidation(payload, keys_to_invalidate)

        # 5. Registrar auditoria
        if self.audit_logger:
            self.audit_logger.record({
                'type': 'ibge_cache_invalidation',
                'dataset_id': payload.dataset_id,
                'event_type': payload.event_type.name,
                'indicators': payload.indicators,
                'years': payload.years,
                'keys_invalidated': invalidated_count,
                'processing_time_ms': (time.time() - start_time) * 1000,
                'webhook_signature': payload.signature[:16],
            })

        return {
            'success': True,
            'dataset_id': payload.dataset_id,
            'event_type': payload.event_type.name,
            'keys_invalidated': invalidated_count,
            'processing_time_ms': (time.time() - start_time) * 1000,
        }

    async def _find_matching_keys(
        self,
        cache_manager,
        payload: IBGEWebhookPayload,
        rule: CacheInvalidationRule,
    ) -> List[str]:
        """Encontra chaves de cache que correspondem aos critérios de invalidação."""
        # Em produção: usar Redis SCAN com pattern matching
        # Aqui: delegar para cache_manager com filtros simplificados
        return await cache_manager.find_keys_by_criteria(
            indicators=payload.indicators if rule.indicators_pattern else None,
            years=payload.years if rule.year_min or rule.year_max else None,
            states=payload.states if rule.states_pattern else None,
            dataset=payload.dataset_id if rule.dataset_pattern else None,
        )

    async def _broadcast_invalidation(
        self,
        payload: IBGEWebhookPayload,
        keys: List[str],
    ):
        """Notifica outros nós sobre invalidação de cache."""
        message = {
            'type': 'cache_invalidation',
            'dataset_id': payload.dataset_id,
            'event_type': payload.event_type.name,
            'keys': keys,
            'timestamp': time.time(),
            'source': 'ibge_webhook',
        }
        await self.redis.publish(self.REDIS_CHANNEL, json.dumps(message))

    def get_stats(self) -> Dict:
        """Retorna estatísticas do invalidator."""
        return {
            **self._stats,
            'rules_count': len(self.invalidation_rules),
            'redis_connected': self.redis is not None,
        }

# ============================================================================
# FASTAPI ENDPOINT PARA WEBHOOK
# ============================================================================

def create_ibge_webhook_app(
    invalidator: IBGECacheInvalidator,
    cache_manager,
) -> FastAPI:
    """Cria aplicação FastAPI para receber webhooks do IBGE."""

    app = FastAPI(
        title="ARKHE IBGE Webhook Receiver",
        description="Endpoint para receber notificações de atualização do IBGE",
        version="1.0.0",
    )

    @app.post("/api/v1/ibge/webhook", tags=["IBGE Webhooks"])
    async def ibge_webhook_handler(
        request: Request,
        background_tasks: BackgroundTasks,
        x_ibge_signature: str = Header(..., description="Assinatura HMAC do IBGE"),
    ):
        """
        Endpoint para receber webhooks do IBGE.

        Expected payload:
        {
            "event_type": "DATASET_UPDATE",
            "dataset_id": "sidra/1612",
            "indicators": ["3640", "173"],
            "years": [2023],
            "states": ["SP", "RJ"],
            "update_timestamp": 1234567890.0,
            "version": "1.0",
            "signature": "hmac_sha3_256_hex..."
        }
        """
        try:
            body = await request.json()
            payload = IBGEWebhookPayload.from_dict(body)

            # Verificar assinatura via header
            if not IBGESignatureVerifier.verify(payload, invalidator.ibge_secret):
                raise HTTPException(status_code=401, detail="Invalid signature")

            # Processar em background para não bloquear resposta
            async def process_async():
                result = await invalidator.process_webhook(payload, cache_manager)
                logger.info(f"✅ Webhook processado: {result}")

            background_tasks.add_task(process_async)

            return JSONResponse(
                status_code=202,
                content={'status': 'accepted', 'payload_id': payload.dataset_id}
            )

        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")
        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"Missing field: {e}")
        except Exception as e:
            logger.error(f"❌ Erro ao processar webhook: {e}")
            raise HTTPException(status_code=500, detail="Internal error")

    @app.get("/api/v1/ibge/webhook/stats", tags=["IBGE Webhooks"])
    async def get_webhook_stats():
        """Retorna estatísticas de webhooks recebidos."""
        return invalidator.get_stats()

    return app

# ============================================================================
# INTEGRAÇÃO COM IBGECacheManager
# ============================================================================

class IBGECacheManager:
    # ... métodos existentes ...
    def __init__(self):
        self.redis_client = None
        self.local_cache = {}

    async def _async_delete(self, key: str) -> bool:
        """Deleta entrada de cache de forma assíncrona."""
        success = False
        if self.redis_client:
            try:
                result = await self.redis_client.delete(key)
                success = result > 0
            except Exception as e:
                logger.warning(f"Erro ao deletar Redis: {e}")
        if self.local_cache and key in self.local_cache:
            del self.local_cache[key]
            success = True
        return success

    async def find_keys_by_criteria(
        self,
        indicators: Optional[List[str]] = None,
        years: Optional[List[int]] = None,
        states: Optional[List[str]] = None,
        dataset: Optional[str] = None,
    ) -> List[str]:
        """
        Encontra chaves de cache que correspondem aos critérios.
        Usado pelo webhook handler para invalidação seletiva.
        """
        matching_keys = []
        # Em produção: usar Redis SCAN com pattern matching
        # Aqui: iterar sobre cache local (simplificado para demo)
        if self.local_cache:
            for key, entry in self.local_cache.items():
                meta = entry.metadata
                if indicators and not any(ind in meta.get('indicators', []) for ind in indicators):
                    continue
                if years and meta.get('year') not in years:
                    continue
                if states and not any(s in meta.get('states', []) for s in (states or [])):
                    continue
                if dataset and meta.get('dataset') != dataset:
                    continue
                matching_keys.append(key)
        return matching_keys
