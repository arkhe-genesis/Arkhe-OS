#!/usr/bin/env python3
"""
Substrato 198‑B: MetaAudit Sidecar — Registro Imutável de Loops Evolutivos
Integrado a todos os pipelines (ZapGPT 2D, 3D, BioSim), este sidecar
ancora cada ciclo na TemporalChain e expõe métricas via Phi‑Bus.
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MetaCycleRecord:
    """Registro imutável de um ciclo de aprendizado meta."""
    cycle_id: str
    prompt: str
    prompt_hash: str
    vlm_score: float
    best_individual_hash: str
    population_size: int
    generations: int
    environment_id: str
    engine_version: str
    timestamp: float
    temporal_seal: Optional[str] = None

class MetaAuditSidecar:
    """
    Sidecar de auditoria meta‑aprendizado.

    Funcionalidades:
    • Intercepta ciclos evolutivos (P2I → Simulação → VLM → Evolução)
    • Gera registro imutável com hash do melhor indivíduo
    • Ancora na TemporalChain com assinatura PQC
    • Publica métricas no Phi‑Bus para dashboard unificado
    • API de consulta histórica (filtros por prompt, score, ambiente)
    """

    def __init__(
        self,
        temporal_chain=None,
        phi_bus=None,
        engine_version: str = "zapgpt_2d_v1.0"
    ):
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.engine_version = engine_version
        self._history: List[MetaCycleRecord] = []
        self._on_cycle_callbacks: List[Callable] = []

    def on_cycle_completed(self, callback: Callable):
        """Registra callback para ser chamado após cada ciclo."""
        self._on_cycle_callbacks.append(callback)

    async def record_cycle(
        self,
        prompt: str,
        vlm_score: float,
        best_individual: Any,
        population_size: int,
        generations: int,
        environment_id: str,
        additional_metadata: Optional[Dict] = None
    ) -> MetaCycleRecord:
        """
        Ancora um ciclo de aprendizado meta.

        Args:
            prompt: O prompt linguístico usado
            vlm_score: Score de alinhamento VLM (0‑1)
            best_individual: O melhor campo/rede evoluído
            population_size: Tamanho da população no ES
            generations: Número de gerações executadas
            environment_id: Identificador do ambiente (2D, 3D, bio)
            additional_metadata: Metadados extras para o registro

        Returns:
            MetaCycleRecord com selo temporal
        """
        # Gerar identificadores únicos
        prompt_hash = hashlib.sha3_256(prompt.encode()).hexdigest()[:16]
        individual_hash = hashlib.sha3_256(
            str(best_individual).encode()
        ).hexdigest()[:16]

        cycle_id = hashlib.sha3_256(
            f"{prompt_hash}:{individual_hash}:{time.time()}".encode()
        ).hexdigest()[:12]

        # Criar registro
        record = MetaCycleRecord(
            cycle_id=cycle_id,
            prompt=prompt,
            prompt_hash=prompt_hash,
            vlm_score=vlm_score,
            best_individual_hash=individual_hash,
            population_size=population_size,
            generations=generations,
            environment_id=environment_id,
            engine_version=self.engine_version,
            timestamp=time.time()
        )

        # Ancorar na TemporalChain
        if self.temporal:
            record.temporal_seal = await self.temporal.anchor_event(
                "meta_cycle_audited",
                {
                    "cycle_id": cycle_id,
                    "prompt_hash": prompt_hash,
                    "vlm_score": vlm_score,
                    "best_individual": individual_hash,
                    "population_size": population_size,
                    "generations": generations,
                    "environment_id": environment_id,
                    "engine_version": self.engine_version,
                    "metadata": additional_metadata or {},
                    "timestamp": record.timestamp
                }
            )
            logger.info(f"🔐 Ciclo {cycle_id} ancorado (selo: {record.temporal_seal[:8]}...)")

        # Armazenar localmente
        self._history.append(record)

        # Publicar métrica no Phi‑Bus
        if self.phi_bus:
            await self.phi_bus.publish_metric(
                f"meta_cycle_score_{environment_id}",
                vlm_score,
                {"prompt_hash": prompt_hash}
            )

        # Executar callbacks
        for callback in self._on_cycle_callbacks:
            await callback(record)

        return record

    def get_history(
        self,
        min_score: Optional[float] = None,
        environment_id: Optional[str] = None,
        limit: int = 100
    ) -> List[MetaCycleRecord]:
        """Consulta histórica com filtros."""
        results = self._history

        if min_score is not None:
            results = [r for r in results if r.vlm_score >= min_score]

        if environment_id is not None:
            results = [r for r in results if r.environment_id == environment_id]

        return sorted(results, key=lambda r: r.timestamp, reverse=True)[:limit]

    def get_statistics(self) -> Dict:
        """Retorna estatísticas agregadas dos ciclos."""
        if not self._history:
            return {}

        scores = [r.vlm_score for r in self._history]
        return {
            "total_cycles": len(self._history),
            "avg_score": np.mean(scores),
            "max_score": max(scores),
            "min_score": min(scores),
            "std_score": np.std(scores),
            "best_prompt_hash": max(self._history, key=lambda r: r.vlm_score).prompt_hash,
            "environments": list(set(r.environment_id for r in self._history)),
            "first_cycle": min(r.timestamp for r in self._history),
            "last_cycle": max(r.timestamp for r in self._history)
        }
