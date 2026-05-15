#!/usr/bin/env python3
"""
Substrato 9043 — Cross Platform Mesh
Orquestrador multi‑plataforma: Twitch, YouTube, TikTok e demonstração.
"""

import asyncio, time
from typing import Dict, List, Optional
from arkhe_twitch.broadcast_connector_interface import BroadcastConnector, LiveStreamInfo, LiveChatMessage, Platform
from arkhe_twitch.youtube_live_connector import YouTubeLiveConnector, YouTubeConfig
from arkhe_twitch.tiktok_live_connector import TikTokLiveConnector, TikTokConfig
from arkhe_twitch.twitch_connector import ArkheTwitchConnector, TwitchConfig

class MultiPlatformMesh:
    def __init__(self, phi_bus=None, temporal_chain=None, spark=None):
        self.connectors: Dict[str, BroadcastConnector] = {}
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self.spark = spark
        self._mesh_phi_c = 0.0

    async def add_twitch(self, stream_id: str, twitch_config: TwitchConfig):
        conn = ArkheTwitchConnector(twitch_config, self.temporal, None, self.phi_bus)
        await conn.__aenter__()
        self.connectors[stream_id] = conn
        await conn.subscribe_events(lambda msg: self._handle_message(stream_id, msg))

    async def add_youtube(self, stream_id: str, yt_config: YouTubeConfig):
        conn = YouTubeLiveConnector(yt_config, self.temporal, None, self.phi_bus)
        self.connectors[stream_id] = conn
        await conn.subscribe_events(lambda msg: self._handle_message(stream_id, msg))

    async def add_tiktok(self, stream_id: str, tk_config: TikTokConfig):
        conn = TikTokLiveConnector(tk_config, self.temporal, None, self.phi_bus)
        self.connectors[stream_id] = conn
        await conn.subscribe_events(lambda msg: self._handle_message(stream_id, msg))

    async def _handle_message(self, stream_id: str, msg: LiveChatMessage):
        # Publicar no Kafka para processamento Spark
        if self.spark:
            await self.spark.publish_event("chat_messages", {
                "stream_id": stream_id, "platform": msg.platform.value,
                "message": msg.message, "chatter": msg.chatter_name,
                "safe": msg.phi_c_safe, "timestamp": msg.timestamp,
            })

    async def get_mesh_status(self) -> Dict:
        status = {"streams": {}, "total_viewers": 0, "mesh_phi_c": self._mesh_phi_c}
        for sid, conn in self.connectors.items():
            try:
                info = await conn.get_stream_info()
                if info:
                    status["streams"][sid] = {
                        "platform": info.platform.value,
                        "title": info.title,
                        "viewers": info.viewer_count,
                        "phi_c": info.phi_c_coherence,
                    }
                    status["total_viewers"] += info.viewer_count
            except Exception:
                pass
        return status
