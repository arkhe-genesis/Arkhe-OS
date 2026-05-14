#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
redis.py — Stub Redis Backend.
"""
from typing import Dict, List, Optional, Any
from .base import StorageBackend
from ..core import Anchor, Event

class RedisStorage(StorageBackend):
    def __init__(self, config: Dict):
        pass
    async def save_anchor(self, anchor: Anchor) -> bool: return True
    async def get_anchor_by_event_id(self, event_id: str) -> Optional[Anchor]: return None
    async def get_anchor_by_seal(self, seal: str) -> Optional[Anchor]: return None
    async def query_events(self, **kwargs) -> List[Event]: return []
    async def get_anchors_range(self, start: int, end: int) -> List[Anchor]: return []
    async def save_chain_state(self, state: Dict[str, Any]) -> bool: return True
    def load_chain_state(self) -> Optional[Dict[str, Any]]: return None
    @property
    def supports_replication(self) -> bool: return True
