#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/temporal/audit.py — Logger de Auditoria Temporal
Registra todas as verificações no TemporalHashChain para auditoria imutável.
Cada entrada é selada com hash canônico e vinculada ao bloco temporal.
"""

import hashlib
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

@dataclass
class AuditEntry:
    """Entrada de auditoria canônica."""
    entry_id: str
    entry_type: str  # "verification", "error", "governance", etc.
    request_hash: str  # SHA3-256 da requisição original
    response_hash: Optional[str]  # SHA3-256 da resposta (se aplicável)
    veredito: Optional[str]
    confianca: Optional[float]
    dominio: Optional[str]
    api_key_partial: str  # Primeiros 8 chars da API key (para privacidade)
    timestamp: float
    metadata: Dict
    temporal_block_id: Optional[str] = None

    def canonical_hash(self) -> str:
        """Computa hash canônico da entrada para integridade."""
        data = {
            "entry_id": self.entry_id,
            "entry_type": self.entry_type,
            "request_hash": self.request_hash,
            "response_hash": self.response_hash,
            "veredito": self.veredito,
            "confianca": self.confianca,
            "dominio": self.dominio,
            "api_key_partial": self.api_key_partial,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
        return hashlib.sha3_256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

class TemporalAuditLogger:
    """
    Logger de auditoria integrado ao TemporalHashChain.

    Características:
    - Cada entrada gera hash canônico para integridade
    - Vinculação a blocos temporais para ordenação imutável
    - Consultas eficientes por hash, domínio, veredito, período
    - Exportação para auditoria externa via API
    """

    def __init__(self, chain_endpoint: Optional[str] = None):
        self.chain_endpoint = chain_endpoint
        self._local_buffer: List[AuditEntry] = []
        self._stats = {
            "total_requests": 0,
            "by_domain": {},
            "by_verdict": {},
            "avg_confidence": 0.0,
            "avg_response_time_ms": 0.0,
            "error_rate": 0.0,
            "_count": 0
        }

    def record(self, entry_data: Dict) -> str:
        """
        Registra nova entrada de auditoria.
        Retorna ID do bloco temporal (simulado).
        """
        # Gerar ID único
        entry_id = hashlib.sha3_256(
            f"{entry_data.get('request_hash')}:{time.time()}".encode()
        ).hexdigest()[:16]

        # Criar entrada canônica
        entry = AuditEntry(
            entry_id=entry_id,
            entry_type=entry_data.get("type", "verification"),
            request_hash=entry_data.get("request_hash", ""),
            response_hash=entry_data.get("response_hash"),
            veredito=entry_data.get("veredito"),
            confianca=entry_data.get("confianca"),
            dominio=entry_data.get("dominio"),
            api_key_partial=entry_data.get("api_key", "")[:8],
            timestamp=entry_data.get("timestamp", time.time()),
            metadata=entry_data.get("metadata", {})
        )

        # Calcular hash canônico
        entry.temporal_block_id = entry.canonical_hash()[:16]

        # Buffer local (em produção: enviar para chain em background)
        self._local_buffer.append(entry)

        # Atualizar estatísticas
        self._update_stats(entry)

        # Em produção: enviar para TemporalHashChain
        # block_id = self._submit_to_chain(entry)

        return entry.temporal_block_id

    def _update_stats(self, entry: AuditEntry):
        """Atualiza estatísticas operacionais."""
        self._stats["total_requests"] += 1
        self._stats["_count"] += 1

        # Por domínio
        if entry.dominio:
            self._stats["by_domain"][entry.dominio] = self._stats["by_domain"].get(entry.dominio, 0) + 1

        # Por veredito
        if entry.veredito:
            self._stats["by_verdict"][entry.veredito] = self._stats["by_verdict"].get(entry.veredito, 0) + 1

        # Confiança média (média móvel)
        if entry.confianca is not None:
            n = self._stats["_count"]
            self._stats["avg_confidence"] = (
                (self._stats["avg_confidence"] * (n-1) + entry.confianca) / n
            )

        # Taxa de erro
        if entry.entry_type == "error":
            self._stats["error_rate"] = (
                self._stats["by_verdict"].get("error", 0) /
                max(1, self._stats["total_requests"])
            )

    def query(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        domain: Optional[str] = None,
        veredito: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Consulta entradas de auditoria com filtros."""
        results = []
        for entry in reversed(self._local_buffer):  # Mais recentes primeiro
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            if domain and entry.dominio != domain:
                continue
            if veredito and entry.veredito != veredito:
                continue

            results.append(asdict(entry))
            if len(results) >= limit:
                break
        return results

    def get_stats(self) -> Dict:
        """Retorna estatísticas consolidadas."""
        return {
            "total_requests": self._stats["total_requests"],
            "by_domain": self._stats["by_domain"],
            "by_verdict": self._stats["by_verdict"],
            "avg_confidence": round(self._stats["avg_confidence"], 4),
            "avg_response_time_ms": round(self._stats["avg_response_time_ms"], 2),
            "error_rate": round(self._stats["error_rate"], 4),
            "buffer_size": len(self._local_buffer),
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

    def export_for_audit(self, start_time: float, end_time: float) -> bytes:
        """Exporta entradas para auditoria externa (formato canônico)."""
        entries = self.query(start_time=start_time, end_time=end_time, limit=10000)
        # Ordenar por timestamp para consistência
        entries.sort(key=lambda e: e["timestamp"])
        # Gerar hash do conjunto para integridade
        batch_hash = hashlib.sha3_256(
            json.dumps(entries, sort_keys=True).encode()
        ).hexdigest()
        # Formato de exportação canônico
        export = {
            "export_type": "conrag_audit",
            "version": "4.1",
            "time_range": {"start": start_time, "end": end_time},
            "batch_hash": batch_hash,
            "entry_count": len(entries),
            "entries": entries,
            "exported_at": time.time()
        }
        return json.dumps(export, sort_keys=True).encode()
