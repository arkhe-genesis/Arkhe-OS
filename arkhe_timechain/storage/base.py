#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
base.py — Interface abstrata para backends de armazenamento do TemporalChain.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from ..core import Anchor, Event, EventType

class StorageBackend(ABC):
    """Interface base para backends de armazenamento."""

    @abstractmethod
    async def save_anchor(self, anchor: Anchor) -> bool:
        """Salva uma âncora no storage."""
        pass

    @abstractmethod
    async def get_anchor_by_event_id(self, event_id: str) -> Optional[Anchor]:
        """Recupera âncora por ID do evento."""
        pass

    @abstractmethod
    async def get_anchor_by_seal(self, seal: str) -> Optional[Anchor]:
        """Recupera âncora por selo do evento."""
        pass

    @abstractmethod
    async def query_events(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        seal_prefix: Optional[str] = None,
        causal_filter: Optional[Dict] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Event]:
        """Consulta eventos com filtros."""
        pass

    @abstractmethod
    async def get_anchors_range(self, start: int, end: int) -> List[Anchor]:
        """Recupera âncoras em um intervalo de posições."""
        pass

    @abstractmethod
    async def save_chain_state(self, state: Dict[str, Any]) -> bool:
        """Salva estado da cadeia (seal atual, count, merkle root)."""
        pass

    @abstractmethod
    def load_chain_state(self) -> Optional[Dict[str, Any]]:
        """Carrega estado da cadeia do storage."""
        pass

    @property
    @abstractmethod
    def supports_replication(self) -> bool:
        """Indica se o backend suporta replicação entre nós."""
        pass
