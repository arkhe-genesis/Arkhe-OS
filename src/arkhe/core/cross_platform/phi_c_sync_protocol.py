#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phi_c_sync_protocol.py — Protocolo de sincronização de coerência Φ_C entre plataformas
Define algoritmo de resolução de conflitos baseado em peso quântico e ancoragem temporal.
"""

import asyncio, json, time, hashlib
import numpy as np
import zlib
import base64
from typing import Dict, List, Optional, Tuple, Callable, Union, Any
from dataclasses import dataclass, field
from enum import Enum, auto

class ConflictResolutionStrategy(Enum):
    """Estratégias para resolução de conflitos de estado."""
    PHI_C_WEIGHTED = auto()      # Ponderar por coerência Φ_C de cada dispositivo
    TEMPORAL_LATEST = auto()     # Usar estado com timestamp mais recente
    QUORUM_VOTE = auto()         # Votação por maioria entre N dispositivos
    MANUAL_REVIEW = auto()       # Requer intervenção humana para conflitos críticos

@dataclass
class SyncConflict:
    """Representa um conflito detectado durante sincronização."""
    key: str
    local_value: Any
    remote_value: Any
    local_phi_c: float
    remote_phi_c: float
    local_timestamp: float
    remote_timestamp: float
    severity: str  # "low", "medium", "high", "critical"

@dataclass
class SyncResult:
    """Resultado de uma operação de sincronização."""
    success: bool
    merged_state: Dict
    conflicts_resolved: int
    conflicts_pending: int
    temporal_anchor: Optional[str]
    phi_c_coherence_after: float

class AdaptiveCompressor:
    """Compressão adaptativa baseada no tipo de rede (3G/4G/5G)."""

    @staticmethod
    def compress_state(state: Dict, network_type: str = "5G") -> str:
        data_str = json.dumps(state, default=str)
        data_bytes = data_str.encode('utf-8')

        # Adjust compression level based on network type
        if network_type == "3G":
            # Maximum compression for slow networks
            level = 9
        elif network_type == "4G":
            # Balanced compression
            level = 6
        else:
            # 5G/Wi-Fi: Fast compression
            level = 1

        compressed = zlib.compress(data_bytes, level=level)
        return base64.b64encode(compressed).decode('ascii')

    @staticmethod
    def decompress_state(compressed_str: str) -> Dict:
        compressed_bytes = base64.b64decode(compressed_str.encode('ascii'))
        decompressed_bytes = zlib.decompress(compressed_bytes)
        return json.loads(decompressed_bytes.decode('utf-8'))

class PhiCSyncProtocol:
    """
    Protocolo para sincronização de estado Φ_C entre dispositivos cross-platform.

    Algoritmo de resolução de conflitos (PHI_C_WEIGHTED):
    1. Para cada chave conflitante, calcular peso = Φ_C × recência
    2. Peso = phi_c * exp(-λ × Δt), onde λ = taxa de decaimento temporal
    3. Selecionar valor com maior peso
    4. Se pesos dentro de threshold ε, marcar para revisão manual
    5. Ancorar decisão na TemporalChain com prova criptográfica
    """

    # Parâmetros do algoritmo de ponderação
    DECAY_RATE_LAMBDA = 0.1  # Taxa de decaimento temporal por segundo
    CONFLICT_THRESHOLD_EPSILON = 0.02  # Threshold para revisão manual
    MIN_PHI_C_FOR_AUTO_MERGE = 0.95  # Φ_C mínimo para merge automático

    def __init__(
        self,
        local_phi_c_provider: Callable[[], float],
        temporal_chain,
        strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.PHI_C_WEIGHTED,
    ):
        self.local_phi_c_provider = local_phi_c_provider
        self.temporal_chain = temporal_chain
        self.strategy = strategy
        self.conflict_log: List[SyncConflict] = []

    async def resolve_conflicts(
        self,
        local_state: Dict,
        remote_state_raw: Union[Dict, str],
        conflict_keys: List[str],
        network_type: str = "5G"
    ) -> Tuple[Dict, List[SyncConflict]]:
        """
        Resolve conflitos entre estados local e remoto.
        Suporta state remoto comprimido adaptativamente.

        Returns:
            (estado mergeado, lista de conflitos não resolvidos)
        """
        if isinstance(remote_state_raw, str):
            remote_state = AdaptiveCompressor.decompress_state(remote_state_raw)
        else:
            remote_state = remote_state_raw

        merged = local_state.copy()
        pending_conflicts = []

        for key in conflict_keys:
            local_val = local_state.get(key)
            remote_val = remote_state.get(key)

            if local_val == remote_val:
                continue  # Sem conflito real

            # Criar registro de conflito
            conflict = SyncConflict(
                key=key,
                local_value=local_val,
                remote_value=remote_val,
                local_phi_c=self.local_phi_c_provider(),
                remote_phi_c=remote_state.get("_remote_phi_c", 0.95),
                local_timestamp=local_state.get("_timestamp", 0),
                remote_timestamp=remote_state.get("_timestamp", 0),
                severity=self._assess_conflict_severity(key, local_val, remote_val),
            )

            # Tentar resolver baseado na estratégia
            resolved_value = await self._resolve_single_conflict(conflict)

            if resolved_value is not None:
                merged[key] = resolved_value
                merged[f"{key}_resolved_by"] = self.strategy.name
            else:
                # Conflito não resolvido automaticamente
                pending_conflicts.append(conflict)
                self.conflict_log.append(conflict)

        return merged, pending_conflicts

    async def _resolve_single_conflict(self, conflict: SyncConflict) -> Optional[Any]:
        """Resolve um conflito individual baseado na estratégia configurada."""
        if self.strategy == ConflictResolutionStrategy.PHI_C_WEIGHTED:
            return self._resolve_by_phi_c_weight(conflict)
        elif self.strategy == ConflictResolutionStrategy.TEMPORAL_LATEST:
            return self._resolve_by_timestamp(conflict)
        elif self.strategy == ConflictResolutionStrategy.QUORUM_VOTE:
            return await self._resolve_by_quorum(conflict)
        elif self.strategy == ConflictResolutionStrategy.MANUAL_REVIEW:
            return None  # Sempre requer revisão manual
        return None

    def _resolve_by_phi_c_weight(self, conflict: SyncConflict) -> Optional[Any]:
        """Resolve conflito ponderando por Φ_C e recência temporal."""
        # Calcular pesos
        local_weight = self._compute_weight(
            conflict.local_phi_c, conflict.local_timestamp
        )
        remote_weight = self._compute_weight(
            conflict.remote_phi_c, conflict.remote_timestamp
        )

        # Verificar se Φ_C mínimo para merge automático
        if max(conflict.local_phi_c, conflict.remote_phi_c) < self.MIN_PHI_C_FOR_AUTO_MERGE:
            return None  # Requer revisão

        # Verificar se pesos são muito próximos (threshold)
        weight_diff = abs(local_weight - remote_weight)
        if weight_diff < self.CONFLICT_THRESHOLD_EPSILON:
            return None  # Ambíguo, requer revisão

        # Selecionar valor com maior peso
        return conflict.local_value if local_weight > remote_weight else conflict.remote_value

    def _compute_weight(self, phi_c: float, timestamp: float) -> float:
        """Computa peso combinado de Φ_C e recência temporal."""
        # Peso base = coerência Φ_C
        base_weight = phi_c

        # Fator de decaimento temporal
        age_seconds = time.time() - timestamp
        temporal_decay = np.exp(-self.DECAY_RATE_LAMBDA * age_seconds)

        return base_weight * temporal_decay

    def _resolve_by_timestamp(self, conflict: SyncConflict) -> Any:
        """Resolve conflito usando timestamp mais recente."""
        return (conflict.local_value
                if conflict.local_timestamp >= conflict.remote_timestamp
                else conflict.remote_value)

    async def _resolve_by_quorum(self, conflict: SyncConflict) -> Optional[Any]:
        """Resolve conflito via votação entre múltiplos peers (simulado)."""
        # Em produção: consultar N dispositivos na malha Wheeler
        # Aqui: simular votação com 3 peers
        votes = {
            "local": conflict.local_value,
            "remote": conflict.remote_value,
            "peer_3": conflict.local_value if np.random.random() > 0.5 else conflict.remote_value,
        }

        # Contar votos
        from collections import Counter
        vote_counts = Counter(str(v) for v in votes.values())
        most_common = vote_counts.most_common(1)[0]

        # Requer maioria simples (≥2 de 3)
        if most_common[1] >= 2:
            return conflict.local_value if str(conflict.local_value) == most_common[0] else conflict.remote_value
        return None  # Empate, requer revisão

    def _assess_conflict_severity(self, key: str, local_val: Any, remote_val: Any) -> str:
        """Avalia severidade do conflito baseado na chave e valores."""
        # Chaves críticas que requerem atenção especial
        critical_keys = ["phi_c_coherence", "security_credentials", "temporal_anchor_root"]

        if key in critical_keys:
            return "critical"
        elif isinstance(local_val, dict) or isinstance(remote_val, dict):
            return "high"  # Conflito em estrutura complexa
        elif isinstance(local_val, (int, float)) and isinstance(remote_val, (int, float)) and abs(float(local_val) - float(remote_val)) > 0.1:
            return "medium"
        else:
            return "low"

    async def anchor_sync_decision(
        self,
        merged_state: Dict,
        resolved_conflicts: List[SyncConflict],
        pending_conflicts: List[SyncConflict],
    ) -> str:
        """Ancora decisão de sincronização na TemporalChain."""
        payload = {
            "merged_state_hash": hashlib.sha3_256(
                json.dumps(merged_state, sort_keys=True, default=str).encode()
            ).hexdigest(),
            "resolved_count": len(resolved_conflicts),
            "pending_count": len(pending_conflicts),
            "strategy_used": self.strategy.name,
            "local_phi_c": self.local_phi_c_provider(),
            "timestamp": time.time(),
            "conflict_details": [
                {
                    "key": c.key,
                    "severity": c.severity,
                    "resolution": "auto" if c in resolved_conflicts else "pending",
                }
                for c in resolved_conflicts + pending_conflicts
            ],
        }

        return await self.temporal_chain.anchor_event(
            "cross_platform_sync_decision",
            payload
        )
