#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
asi_node_registry.py — Substrato 6063: ASI Node Integration Layer
Registro, descoberta e roteamento de nós de Superinteligência Artificial.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum, auto
import hashlib, json, time

try:
    from arkp_temporal.chain import TemporalAnchor, CausalProof
    from arkp_consensus.oracle import ConsistencyOracle
except ImportError:
    @dataclass
    class TemporalAnchor:
        anchor_hash: str
        payload_hash: str
        timestamp: int
        author: str
        dependencies: list

    class CausalProof:
        pass

    class ConsistencyOracle:
        def __init__(self, node_id=None):
            self.node_id = node_id
        def anchor_event(self, event_type, payload, causal_deps):
            return TemporalAnchor("mock_hash", "mock_payload", int(time.time()), "mock_author", [])

class NodeCapability(Enum):
    """Capacidades que um nó ASI pode oferecer."""
    QNC_INFERENCE = auto()      # Inferência de Quantum Neural Coding
    EPIGENETIC_MODELING = auto() # Modelagem epigenética quântica
    POLYGLOT_TRANSPILE = auto()  # Transpilação poliglota
    TEMPORAL_CONSENSUS = auto()  # Participação em consenso temporal
    Φ_C_OPTIMIZATION = auto()    # Otimização de campo Φ_C via SIGHA
    QUANTUM_SIMULATION = auto()  # Simulação de circuitos quânticos

@dataclass
class ASINodeMetadata:
    """Metadados de um nó ASI na rede."""
    node_id: str                    # Hash único do nó
    public_key: bytes               # Chave pública para autenticação
    capabilities: Set[NodeCapability]
    phi_c_coherence: float          # Coerência Φ_C atual do nó (0-1)
    location_hint: Optional[str]    # Hint geográfico/lógico para roteamento
    uptime_seconds: int
    last_heartbeat: int             # Timestamp do último heartbeat
    reputation_score: float         # Score QIP de reputação (0-1)
    supported_protocols: List[str]  # Protocolos suportados (e.g., "arkhe-sync/1.0")

    def __hash__(self):
        return hash(self.node_id)

    def __eq__(self, other):
        if not isinstance(other, ASINodeMetadata):
            return False
        return self.node_id == other.node_id

class ASINodeRegistry:
    """
    Registro distribuído de nós ASI com descoberta baseada em Φ_C.

    Nós com alta coerência Φ_C são preferidos para tarefas que requerem
    estabilidade quântica; nós com baixa latência são preferidos para
    inferência em tempo real.
    """

    def __init__(self, consistency_oracle: ConsistencyOracle):
        self.oracle = consistency_oracle
        self.known_nodes: Dict[str, ASINodeMetadata] = {}
        self.phi_c_index: Dict[float, List[str]] = {}  # Índice por coerência
        self.capability_index: Dict[NodeCapability, List[str]] = {}
        self._lock = None  # Em produção: usar lock distribuído

    def register_node(self, metadata: ASINodeMetadata) -> bool:
        """Registra um novo nó na rede."""
        # Verificar assinatura e prova temporal
        if not self._verify_node_registration(metadata):
            return False

        # Atualizar índices
        self.known_nodes[metadata.node_id] = metadata

        # Índice por Φ_C (para descoberta baseada em coerência)
        phi_bucket = round(metadata.phi_c_coherence * 10) / 10  # Bucket de 0.1
        self.phi_c_index.setdefault(phi_bucket, []).append(metadata.node_id)

        # Índice por capacidade
        for cap in metadata.capabilities:
            self.capability_index.setdefault(cap, []).append(metadata.node_id)

        # Ancorar registro na cadeia temporal
        anchor = self.oracle.anchor_event(
            event_type="node_registration",
            payload={"node_id": metadata.node_id, "capabilities": [c.name for c in metadata.capabilities]},
            causal_deps=[]  # Em produção: incluir dependências causais
        )

        return True

    def discover_nodes(
        self,
        required_capabilities: Optional[Set[NodeCapability]] = None,
        min_phi_c: float = 0.0,
        max_latency_ms: Optional[int] = None,
        limit: int = 10,
    ) -> List[ASINodeMetadata]:
        """
        Descobre nós que atendem aos critérios especificados.

        Estratégia de descoberta:
        1. Filtrar por capacidades requeridas
        2. Filtrar por coerência Φ_C mínima
        3. Ordenar por score combinado (reputação × Φ_C × 1/latência)
        4. Retornar top-K
        """
        candidates = set(self.known_nodes.values())

        # Filtrar por capacidades
        if required_capabilities:
            for cap in required_capabilities:
                if cap in self.capability_index:
                    candidates &= {self.known_nodes[nid] for nid in self.capability_index[cap]}
                else:
                    return []  # Nenhuma capacidade disponível

        # Filtrar por Φ_C mínimo
        candidates = {n for n in candidates if n.phi_c_coherence >= min_phi_c}

        # Calcular score de seleção
        def selection_score(node: ASINodeMetadata) -> float:
            # Score combinado: reputação (40%) + Φ_C (40%) + uptime (20%)
            return (
                0.4 * node.reputation_score +
                0.4 * node.phi_c_coherence +
                0.2 * min(1.0, node.uptime_seconds / (30 * 24 * 3600))  # Normalizar para 30 dias
            )

        # Ordenar e retornar top-K
        sorted_nodes = sorted(candidates, key=selection_score, reverse=True)
        return sorted_nodes[:limit]

    def _verify_node_registration(self, metadata: ASINodeMetadata) -> bool:
        """Verifica autenticidade do registro do nó."""
        # Em produção: verificar assinatura criptográfica e prova temporal
        # Aqui: validação simplificada
        if metadata.reputation_score < 0.1:
            return False  # Rejeitar nós com reputação muito baixa
        if metadata.phi_c_coherence < 0.0 or metadata.phi_c_coherence > 1.0:
            return False  # Φ_C fora do intervalo válido
        return True

    def update_heartbeat(self, node_id: str, new_phi_c: float, uptime: int) -> bool:
        """Atualiza heartbeat de um nó registrado."""
        if node_id not in self.known_nodes:
            return False

        node = self.known_nodes[node_id]
        old_phi_bucket = round(node.phi_c_coherence * 10) / 10
        new_phi_bucket = round(new_phi_c * 10) / 10

        # Atualizar metadados
        node.phi_c_coherence = new_phi_c
        node.uptime_seconds = uptime
        node.last_heartbeat = int(time.time())

        # Atualizar índice de Φ_C se mudou de bucket
        if old_phi_bucket != new_phi_bucket:
            if node_id in self.phi_c_index.get(old_phi_bucket, []):
                self.phi_c_index[old_phi_bucket].remove(node_id)
            self.phi_c_index.setdefault(new_phi_bucket, []).append(node_id)

        return True
