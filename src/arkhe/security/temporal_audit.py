#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
temporal_audit.py — Substrato 172-OMEGA: Auditoria Imutável via TemporalChain
Ancora logs de geração do Guardião Atratora na cadeia temporal para verificação posterior.
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from arkp_core.temporal_chain import TemporalChain

@dataclass
class TokenAuditRecord:
    """Registro de auditoria por token gerado."""
    token_id: int
    token_text: str
    position: int
    timestamp: float

    # Decisão de exorcismo
    exorcism: Dict = field(default_factory=dict)  # {"blocked": bool, "reason": str, "severity": float}

    # Métricas do atrator
    attractor: Dict = field(default_factory=dict)  # {"coherence": float, "surprise": float, "resonance": float, "potential": float}

    # Resultado final
    final_probability: float = 0.0
    selected_reason: str = ""  # "safe_high_prob", "coherence_boosted", etc.

    # Contexto para reprodutibilidade
    context_summary: Dict = field(default_factory=dict)  # Hash dos últimos N tokens
    domain_profile: Optional[str] = None

    # Prova criptográfica
    seal: str = ""  # SHA3-256 do registro completo

class TemporalAuditLogger:
    """
    Logger que ancora registros de geração na TemporalChain.

    Fluxo por token:
    1. Coletar métricas (exorcism_report, attractor_metrics, probs)
    2. Criar TokenAuditRecord com selo SHA3-256
    3. Ancorar na TemporalChain com causal_deps do token anterior
    4. Manter buffer local para batch anchoring (otimização)
    """

    def __init__(
        self,
        temporal_chain: TemporalChain,
        batch_size: int = 10,  # Ancorar em lotes para eficiência
        include_embeddings: bool = False,  # Incluir embeddings no registro (aumenta tamanho)
    ):
        self.temporal_chain = temporal_chain
        self.batch_size = batch_size
        self.include_embeddings = include_embeddings

        self._buffer: List[TokenAuditRecord] = []
        self._sequence_anchor: Optional[str] = None  # Âncora do primeiro token da sequência
        self._stats = {"anchored": 0, "buffered": 0, "errors": 0}

    async def log_token(
        self,
        token_id: int,
        token_text: str,
        position: int,
        exorcism_report: Optional[Dict],
        attractor_metrics: Dict,
        final_probability: float = 0.0,
        context_embeddings: List = None,
        domain_profile: Optional[str] = None,
    ) -> Optional[str]:
        """
        Registra token gerado e ancora na TemporalChain (com batching).

        Returns:
            Temporal anchor se ancorado imediatamente, None se em buffer
        """
        # 1. Criar resumo do contexto (hash para reprodutibilidade)
        context_summary = {
            "last_3_hashes": [
                hashlib.sha3_256(json.dumps({"id": t.id, "pos": t.position}, sort_keys=True).encode()).hexdigest()[:8]
                for t in context_embeddings[-3:]
            ] if context_embeddings else [],
            "context_phi_c": getattr(context_embeddings[-1], 'phi_c', 0.99) if context_embeddings else 0.99,
        }

        # 2. Criar registro de auditoria
        record = TokenAuditRecord(
            token_id=token_id,
            token_text=token_text,
            position=position,
            timestamp=time.time(),
            exorcism=exorcism_report or {"blocked": False},
            attractor=attractor_metrics,
            final_probability=final_probability,
            selected_reason=self._infer_selection_reason(exorcism_report, attractor_metrics, final_probability),
            context_summary=context_summary,
            domain_profile=domain_profile,
        )

        # 3. Computar selo criptográfico do registro
        record.seal = self._compute_record_seal(record)

        # 4. Adicionar ao buffer
        self._buffer.append(record)
        self._stats["buffered"] += 1

        # 5. Ancorar se buffer cheio ou fim de sequência
        if len(self._buffer) >= self.batch_size:
            return await self._flush_buffer()

        return None

    def _infer_selection_reason(
        self,
        exorcism: Optional[Dict],
        attractor: Dict,
        probability: float,
    ) -> str:
        """Inferir razão da seleção do token para auditoria."""
        if exorcism and exorcism.get("blocked"):
            return "fallback_after_exorcism"
        elif attractor.get("potential", 0) > 0.5 and probability > 0.1:
            return "coherence_boosted"
        elif probability > 0.5:
            return "safe_high_probability"
        elif attractor.get("surprise", 0) > 2.0:
            return "diversity_sample"
        else:
            return "balanced_selection"

    def _compute_record_seal(self, record: TokenAuditRecord) -> str:
        """Computa selo SHA3-256 do registro para integridade."""
        # Serializar campos auditáveis (excluir seal para evitar circularidade)
        audit_data = {
            "token_id": record.token_id,
            "token_text": record.token_text,
            "position": record.position,
            "timestamp": record.timestamp,
            "exorcism": record.exorcism,
            "attractor": record.attractor,
            "final_probability": record.final_probability,
            "selected_reason": record.selected_reason,
            "context_summary": record.context_summary,
            "domain_profile": record.domain_profile,
        }
        return hashlib.sha3_256(
            json.dumps(audit_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

    async def _flush_buffer(self) -> Optional[str]:
        """Ancora buffer de registros na TemporalChain."""
        if not self._buffer:
            return None

        try:
            # Preparar payload em lote
            batch_payload = {
                "batch_size": len(self._buffer),
                "first_position": self._buffer[0].position,
                "last_position": self._buffer[-1].position,
                "records": [
                    {
                        "position": r.position,
                        "token_id": r.token_id,
                        "token_text": r.token_text,
                        "exorcism_blocked": r.exorcism.get("blocked"),
                        "attractor_coherence": r.attractor.get("coherence"),
                        "final_probability": r.final_probability,
                        "seal": r.seal,
                    }
                    for r in self._buffer
                ],
                "batch_seal": hashlib.sha3_256(
                    json.dumps([r.seal for r in self._buffer], sort_keys=True).encode()
                ).hexdigest()[:16],
                "timestamp": time.time(),
            }

            # Ancorar na cadeia temporal
            batch_anchor = await self.temporal_chain.anchor_event(
                event_type="guardian_generation_batch",
                payload=batch_payload,
                causal_deps=[self._sequence_anchor] if self._sequence_anchor else None,
            )

            # Atualizar âncora de sequência para próximo batch
            self._sequence_anchor = batch_anchor

            # Limpar buffer e atualizar stats
            self._buffer.clear()
            self._stats["anchored"] += len(self._buffer)

            return batch_anchor

        except Exception as e:
            self._stats["errors"] += 1
            # Em produção: retry com backoff ou fallback para log local
            print(f"⚠️  TemporalChain anchor failed: {e}")
            return None

    async def finalize_sequence(self) -> Optional[str]:
        """Ancora registros pendentes no fim de uma sequência de geração."""
        if self._buffer:
            return await self._flush_buffer()
        return self._sequence_anchor

    def get_statistics(self) -> Dict:
        """Retorna estatísticas de auditoria."""
        return {
            **self._stats,
            "buffer_size": len(self._buffer),
            "sequence_anchor": self._sequence_anchor,
        }
