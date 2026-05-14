#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core.py — Substrato 9018: TemporalChain Core
Implementação da cadeia de eventos imutável com ancoragem causal e verificação criptográfica.
"""

import hashlib
import json
import time
import asyncio
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union, Set, Tuple
from enum import Enum, auto
from datetime import datetime, timezone
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# TIPOS BASE
# ============================================================================

class EventType(Enum):
    """Tipos de eventos suportados na cadeia temporal."""
    # Segurança e Conformidade
    CVS_SCAN = "cvs_scan"
    APM_PATH = "apm_path"
    INV_SBOM = "inv_sbom"
    ARO_DEPLOY = "aro_deploy"
    MA_S2_ASSESSMENT = "ma_s2_assessment"

    # Processamento de Dados
    DATA_INGESTION = "data_ingestion"
    QNC_EXECUTION = "qnc_execution"
    SPARK_PROCESSING = "spark_processing"

    # Sistema e Auditoria
    PARSE_SUCCESS = "parse_success"
    PARSE_CORRECTED = "parse_corrected"
    GUARDIAN_EXORCISM = "guardian_exorcism"
    MCP_TOOL_CALL = "mcp_tool_call"

    # Genômica e Epigenética
    EPIGENETIC_MARK = "epigenetic_mark"
    SINGLE_CELL_CLUSTER = "single_cell_cluster"
    lncRNA_REGULATION = "lncrna_regulation"

    # Custom
    CUSTOM = "custom"

@dataclass
class CausalLink:
    """Referência causal a um evento anterior."""
    event_id: str
    event_type: str
    seal: str
    timestamp: float

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'CausalLink':
        return cls(**data)

@dataclass
class Event:
    """Evento imutável na cadeia temporal."""
    event_id: str
    event_type: EventType
    payload: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float
    causal_deps: Optional[List[CausalLink]] = None
    seal: str = ""  # Preenchido após ancoragem

    def __post_init__(self):
        if self.causal_deps is None:
            self.causal_deps = []
        if not self.seal:
            self.seal = self._compute_seal()

    def _compute_seal(self) -> str:
        """Computa selo SHA3-256 do evento."""
        seal_data = {
            "event_id": self.event_id,
            "event_type": self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "causal_deps": [d.to_dict() for d in self.causal_deps],
        }
        return hashlib.sha3_256(
            json.dumps(seal_data, sort_keys=True, default=str).encode()
        ).hexdigest()

    def to_dict(self) -> Dict:
        """Serializa evento para dicionário."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "causal_deps": [d.to_dict() for d in self.causal_deps],
            "seal": self.seal,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        """Deserializa evento de dicionário."""
        data["event_type"] = EventType(data["event_type"]) if isinstance(data["event_type"], str) else data["event_type"]
        data["causal_deps"] = [CausalLink.from_dict(d) for d in data.get("causal_deps", [])]
        return cls(**data)

@dataclass
class Anchor:
    """Âncora de um evento na cadeia temporal."""
    event: Event
    previous_seal: str  # Selo do evento anterior (ou "genesis" para o primeiro)
    chain_seal: str  # Selo acumulado da cadeia até este ponto
    position: int  # Posição na cadeia (0-indexed)
    anchored_at: float

    def to_dict(self) -> Dict:
        return {
            "event": self.event.to_dict(),
            "previous_seal": self.previous_seal,
            "chain_seal": self.chain_seal,
            "position": self.position,
            "anchored_at": self.anchored_at,
        }

@dataclass
class MerkleProof:
    """Prova Merkle para verificação de inclusão de evento."""
    event_seal: str
    position: int
    proof_hashes: List[Tuple[str, str]]  # (hash, direction: 'left' or 'right')
    root_hash: str

    def verify(self) -> bool:
        """Verifica a prova Merkle."""
        current = self.event_seal
        for hash_val, direction in self.proof_hashes:
            if direction == 'left':
                current = hashlib.sha3_256((hash_val + current).encode()).hexdigest()
            else:
                current = hashlib.sha3_256((current + hash_val).encode()).hexdigest()
        return current == self.root_hash

# ============================================================================
# TEMPORAL CHAIN IMPLEMENTATION
# ============================================================================

class TemporalChain:
    """
    Cadeia temporal imutável com ancoragem causal e verificação criptográfica.

    Funcionalidades:
    • Ancoragem de eventos com selo SHA3-256 encadeado
    • Referências causais formando uma DAG de eventos
    • Merkle Tree para verificação eficiente de subconjuntos
    • Múltiplos backends de armazenamento plugáveis
    • API de consulta com filtros avançados
    • Replicação entre nós com consistência eventual
    • Ferramentas de verificação de integridade
    """

    def __init__(
        self,
        storage_backend: str = "in_memory",
        storage_config: Optional[Dict] = None,
        node_id: Optional[str] = None,
        phi_c_resolver: Optional[Any] = None,  # Para resolução de conflitos por Φ_C
    ):
        self.node_id = node_id or hashlib.sha3_256(str(time.time()).encode()).hexdigest()[:16]
        self.phi_c_resolver = phi_c_resolver

        # Inicializar backend de armazenamento
        self.storage = self._init_storage(storage_backend, storage_config or {})

        # Estado da cadeia
        self._genesis_seal = "0" * 64  # Selo inicial (64 zeros para SHA3-256)
        self._current_seal = self._genesis_seal
        self._event_count = 0
        self._merkle_root: Optional[str] = None
        self._merkle_leaves: List[str] = []

        # Cache para consultas frequentes
        self._event_cache: Dict[str, Event] = {}
        self._seal_to_id: Dict[str, str] = {}

        # Load existing chain from storage
        self._load_chain_state()

    def _init_storage(self, backend: str, config: Dict):
        """Inicializa backend de armazenamento."""
        from .storage.base import StorageBackend
        from .storage.in_memory import InMemoryStorage
        from .storage.sqlite import SQLiteStorage
        from .storage.postgresql import PostgreSQLStorage
        from .storage.redis import RedisStorage
        from .storage.decentralized import DecentralizedStorage

        backends = {
            "in_memory": InMemoryStorage,
            "sqlite": SQLiteStorage,
            "postgresql": PostgreSQLStorage,
            "redis": RedisStorage,
            "ipfs": DecentralizedStorage,
            "arweave": DecentralizedStorage,
        }

        backend_class = backends.get(backend, InMemoryStorage)
        return backend_class(config)

    def _load_chain_state(self):
        """Carrega estado da cadeia do storage."""
        state = self.storage.load_chain_state()
        if state:
            self._current_seal = state.get("current_seal", self._genesis_seal)
            self._event_count = state.get("event_count", 0)
            self._merkle_root = state.get("merkle_root")
            self._merkle_leaves = state.get("merkle_leaves", [])
            logger.info(f"📦 Carregada cadeia com {self._event_count} eventos")

    async def anchor_event(
        self,
        event_type: Union[EventType, str],
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        causal_deps: Optional[List[Union[str, CausalLink]]] = None,
        validate_with_guardian: bool = True,
    ) -> Anchor:
        """
        Ancora um novo evento na cadeia temporal.

        Args:
            event_type: Tipo do evento (enum ou string)
            payload: Dados do evento
            metadata: Metadados opcionais (contexto, usuário, etc.)
            causal_deps: Dependências causais (IDs de eventos ou CausalLink objects)
            validate_with_guardian: Se True, valida payload com Guardian Attractor

        Returns:
            Anchor com informações da ancoragem
        """
        # Converter event_type se necessário
        if isinstance(event_type, str):
            event_type = EventType(event_type)

        # Validar com Guardian Attractor se habilitado
        if validate_with_guardian:
            from .guardian_integration import validate_event_payload
            if not await validate_event_payload(event_type, payload):
                raise ValueError("Event payload failed Guardian validation")

        # Gerar ID único para o evento
        event_id = hashlib.sha3_256(
            f"{event_type.value}:{json.dumps(payload, sort_keys=True)}:{time.time()}".encode()
        ).hexdigest()[:16]

        # Resolver dependências causais
        resolved_deps = await self._resolve_causal_deps(causal_deps or [])

        # Criar evento
        event = Event(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            metadata=metadata or {},
            timestamp=time.time(),
            causal_deps=resolved_deps,
        )

        # Computar selo da cadeia até este ponto
        chain_input = f"{self._current_seal}:{event.seal}:{self._event_count}"
        new_chain_seal = hashlib.sha3_256(chain_input.encode()).hexdigest()

        # Criar âncora
        anchor = Anchor(
            event=event,
            previous_seal=self._current_seal,
            chain_seal=new_chain_seal,
            position=self._event_count,
            anchored_at=time.time(),
        )

        # Atualizar Merkle Tree
        self._merkle_leaves.append(event.seal)
        self._merkle_root = self._compute_merkle_root()

        # Persistir no storage
        await self.storage.save_anchor(anchor)
        await self.storage.save_chain_state({
            "current_seal": new_chain_seal,
            "event_count": self._event_count + 1,
            "merkle_root": self._merkle_root,
            "merkle_leaves": self._merkle_leaves[-1000:],  # Manter últimos 1000 para eficiência
        })

        # Atualizar estado em memória
        self._current_seal = new_chain_seal
        self._event_count += 1
        self._event_cache[event_id] = event
        self._seal_to_id[event.seal] = event_id

        # Replicar para outros nós se configurado
        if self.storage.supports_replication:
            asyncio.create_task(self._replicate_anchor(anchor))

        return anchor

    async def _resolve_causal_deps(
        self,
        deps: List[Union[str, CausalLink]],
    ) -> List[CausalLink]:
        """Resolve dependências causais para CausalLink objects."""
        resolved = []
        for dep in deps:
            if isinstance(dep, CausalLink):
                resolved.append(dep)
            elif isinstance(dep, str):
                # Pode ser event_id ou seal
                event = await self.get_event_by_id(dep) or await self.get_event_by_seal(dep)
                if event:
                    resolved.append(CausalLink(
                        event_id=event.event_id,
                        event_type=event.event_type.value,
                        seal=event.seal,
                        timestamp=event.timestamp,
                    ))
        return resolved

    def _compute_merkle_root(self) -> Optional[str]:
        """Computa raiz Merkle dos selos de eventos."""
        if not self._merkle_leaves:
            return None

        # Implementação simplificada de Merkle Tree
        hashes = [hashlib.sha3_256(h.encode()).digest() for h in self._merkle_leaves]

        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])  # Duplicar último se ímpar

            next_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i+1]
                next_level.append(hashlib.sha3_256(combined).digest())
            hashes = next_level

        return hashes[0].hex() if hashes else None

    async def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """Recupera evento por ID."""
        # Verificar cache primeiro
        if event_id in self._event_cache:
            return self._event_cache[event_id]

        # Buscar no storage
        anchor = await self.storage.get_anchor_by_event_id(event_id)
        if anchor:
            self._event_cache[event_id] = anchor.event
            self._seal_to_id[anchor.event.seal] = event_id
            return anchor.event
        return None

    async def get_event_by_seal(self, seal: str) -> Optional[Event]:
        """Recupera evento por selo."""
        if seal in self._seal_to_id:
            return await self.get_event_by_id(self._seal_to_id[seal])

        anchor = await self.storage.get_anchor_by_seal(seal)
        if anchor:
            self._event_cache[anchor.event.event_id] = anchor.event
            self._seal_to_id[seal] = anchor.event.event_id
            return anchor.event
        return None

    async def query_events(
        self,
        event_type: Optional[Union[EventType, str]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        seal_prefix: Optional[str] = None,
        causal_filter: Optional[Dict] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Event]:
        """
        Consulta eventos com filtros avançados.

        Returns:
            Lista de eventos ordenados por timestamp (mais recente primeiro)
        """
        if isinstance(event_type, str):
            event_type = EventType(event_type)

        events = await self.storage.query_events(
            event_type=event_type.value if event_type else None,
            start_time=start_time,
            end_time=end_time,
            seal_prefix=seal_prefix,
            causal_filter=causal_filter,
            limit=limit,
            offset=offset,
        )

        # Atualizar cache
        for event in events:
            self._event_cache[event.event_id] = event
            self._seal_to_id[event.seal] = event.event_id

        return events

    def get_merkle_proof(self, event_seal: str) -> Optional[MerkleProof]:
        """Gera prova Merkle para um evento."""
        if event_seal not in self._merkle_leaves:
            return None

        position = self._merkle_leaves.index(event_seal)
        # Implementação simplificada de geração de prova Merkle
        # Em produção: implementar algoritmo completo de Merkle proof
        proof_hashes = []  # Placeholder
        return MerkleProof(
            event_seal=event_seal,
            position=position,
            proof_hashes=proof_hashes,
            root_hash=self._merkle_root or "",
        )

    async def verify_chain(self, from_position: int = 0) -> bool:
        """
        Verifica integridade da cadeia a partir de uma posição.

        Returns:
            True se a cadeia é íntegra, False caso contrário
        """
        anchors = await self.storage.get_anchors_range(from_position, self._event_count)

        expected_seal = self._genesis_seal if from_position == 0 else anchors[0].previous_seal

        for i, anchor in enumerate(anchors):
            # Verificar selo do evento
            if anchor.event.seal != anchor.event._compute_seal():
                logger.error(f"❌ Evento {anchor.event.event_id} tem selo inválido")
                return False

            # Verificar encadeamento
            chain_input = f"{expected_seal}:{anchor.event.seal}:{from_position + i}"
            expected_chain_seal = hashlib.sha3_256(chain_input.encode()).hexdigest()

            if anchor.chain_seal != expected_chain_seal:
                logger.error(f"❌ Cadeia quebrada na posição {from_position + i}")
                return False

            expected_seal = anchor.chain_seal

        return True

    async def export_chain(
        self,
        start_position: int = 0,
        end_position: Optional[int] = None,
        format: str = "json",
    ) -> Union[str, bytes]:
        """Exporta parte ou toda a cadeia para auditoria externa."""
        if end_position is None:
            end_position = self._event_count

        anchors = await self.storage.get_anchors_range(start_position, end_position)

        if format == "json":
            export_data = {
                "genesis_seal": self._genesis_seal,
                "start_position": start_position,
                "end_position": end_position,
                "merkle_root": self._merkle_root,
                "anchors": [a.to_dict() for a in anchors],
                "exported_at": time.time(),
                "exported_by": self.node_id,
            }
            return json.dumps(export_data, indent=2, default=str)
        elif format == "binary":
            # Formato binário compacto para transferência eficiente
            import struct
            data = b""
            for anchor in anchors:
                data += struct.pack("!Q", int(anchor.anchored_at * 1000))
                data += anchor.event.seal.encode()
                data += json.dumps(anchor.event.to_dict()).encode()
            return data
        else:
            raise ValueError(f"Formato não suportado: {format}")

    @property
    def current_seal(self) -> str:
        """Retorna selo atual da cadeia."""
        return self._current_seal

    @property
    def event_count(self) -> int:
        """Retorna número total de eventos."""
        return self._event_count

    @property
    def merkle_root(self) -> Optional[str]:
        """Retorna raiz Merkle atual."""
        return self._merkle_root

    async def _replicate_anchor(self, anchor: Anchor):
        """Replica âncora para outros nós da malha."""
        # Em produção: implementar protocolo gossip/raft
        # Para demo: log apenas
        logger.debug(f"🔁 Replicando âncora {anchor.event.event_id} para malha")
