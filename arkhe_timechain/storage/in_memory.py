#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
in_memory.py — Backend em memória para TemporalChain.
Ideal para testes.
"""

from typing import Dict, List, Optional, Any
import asyncio
from .base import StorageBackend
from ..core import Anchor, Event, EventType

class InMemoryStorage(StorageBackend):
    """Backend de armazenamento em memória."""

    def __init__(self, config: Dict):
        self.anchors: List[Anchor] = []
        self.anchors_by_event_id: Dict[str, Anchor] = {}
        self.anchors_by_seal: Dict[str, Anchor] = {}
        self.chain_state: Optional[Dict[str, Any]] = None

    async def save_anchor(self, anchor: Anchor) -> bool:
        self.anchors.append(anchor)
        self.anchors_by_event_id[anchor.event.event_id] = anchor
        self.anchors_by_seal[anchor.event.seal] = anchor
        return True

    async def get_anchor_by_event_id(self, event_id: str) -> Optional[Anchor]:
        return self.anchors_by_event_id.get(event_id)

    async def get_anchor_by_seal(self, seal: str) -> Optional[Anchor]:
        return self.anchors_by_seal.get(seal)

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

        filtered_events = []
        for anchor in reversed(self.anchors): # most recent first
            if event_type and anchor.event.event_type.value != event_type:
                continue
            if start_time and anchor.event.timestamp < start_time:
                continue
            if end_time and anchor.event.timestamp > end_time:
                continue
            if seal_prefix and not anchor.event.seal.startswith(seal_prefix):
                continue

            filtered_events.append(anchor.event)

        return filtered_events[offset:offset+limit]

    async def get_anchors_range(self, start: int, end: int) -> List[Anchor]:
        return self.anchors[start:end]

    async def save_chain_state(self, state: Dict[str, Any]) -> bool:
        self.chain_state = state
        return True

    def load_chain_state(self) -> Optional[Dict[str, Any]]:
        return self.chain_state

    @property
    def supports_replication(self) -> bool:
        return False
