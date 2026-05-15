#!/usr/bin/env python3
"""Interface comum para conectores de plataformas de live streaming."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from enum import Enum

class Platform(Enum):
    TWITCH = "twitch"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"

@dataclass
class LiveStreamInfo:
    platform: Platform
    stream_id: str
    broadcaster_id: str
    broadcaster_name: str
    title: str
    viewer_count: int
    started_at: str
    language: str
    game_name: Optional[str] = None
    phi_c_coherence: float = 0.0
    temporal_seal: Optional[str] = None

@dataclass
class LiveChatMessage:
    platform: Platform
    message_id: str
    stream_id: str
    chatter_id: str
    chatter_name: str
    message: str
    timestamp: float
    phi_c_safe: bool = True
    guardian_reason: Optional[str] = None

class BroadcastConnector(ABC):
    """Interface abstrata para conectores de plataformas de live streaming."""

    @abstractmethod
    async def get_stream_info(self) -> Optional[LiveStreamInfo]: ...
    @abstractmethod
    async def send_chat_message(self, message: str) -> bool: ...
    @abstractmethod
    async def subscribe_events(self, handler: Callable): ...
    @abstractmethod
    def get_metrics(self) -> Dict: ...
    @abstractmethod
    async def close(self): ...
