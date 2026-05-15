#!/usr/bin/env python3
"""Conector para TikTok Live via TikTok Live API (REST + WebSocket)."""

import asyncio, hashlib, json, time, logging, aiohttp
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from .broadcast_connector_interface import BroadcastConnector, LiveStreamInfo, LiveChatMessage, Platform

logger = logging.getLogger(__name__)

@dataclass
class TikTokConfig:
    client_key: str
    client_secret: str
    access_token: str
    open_id: str
    room_id: Optional[str] = None

class TikTokLiveConnector(BroadcastConnector):
    """Conector para TikTok Live."""

    BASE_URL = "https://open.tiktokapis.com/v2"

    def __init__(self, config: TikTokConfig, temporal_chain=None, guardian=None, phi_bus=None):
        self.config = config
        self.temporal = temporal_chain
        self.guardian = guardian
        self.phi_bus = phi_bus
        self._metrics = {"api_requests": 0, "api_errors": 0, "chat_messages": 0, "chat_blocks": 0}
        self._session: Optional[aiohttp.ClientSession] = None

    def _headers(self):
        return {"Authorization": f"Bearer {self.config.access_token}", "Content-Type": "application/json"}

    async def _api_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._headers()
        if not self._session:
            self._session = aiohttp.ClientSession()
        self._metrics["api_requests"] += 1
        try:
            async with self._session.request(method, url, headers=headers, **kwargs) as resp:
                if resp.status == 200:
                    return await resp.json()
                self._metrics["api_errors"] += 1
                return {"error": f"HTTP {resp.status}"}
        except Exception as e:
            self._metrics["api_errors"] += 1
            return {"error": str(e)}

    async def get_stream_info(self) -> Optional[LiveStreamInfo]:
        data = await self._api_request("GET", f"/live/room/info/?open_id={self.config.open_id}")
        room = data.get("data", {}).get("room", {})
        if not room or room.get("status") != "LIVE":
            return None
        phi_c = self.phi_bus.get_mesh_coherence() if self.phi_bus else 0.997
        info = LiveStreamInfo(
            platform=Platform.TIKTOK,
            stream_id=room.get("id", ""),
            broadcaster_id=self.config.open_id,
            broadcaster_name=room.get("owner", {}).get("display_id", ""),
            title=room.get("title", ""),
            viewer_count=room.get("user_count", 0),
            started_at=room.get("start_time", ""),
            language=room.get("language", "en"),
            phi_c_coherence=phi_c,
        )
        if self.temporal:
            info.temporal_seal = await self.temporal.anchor_event("tiktok_stream_info", {
                "stream_id": info.stream_id, "title": info.title, "viewers": info.viewer_count, "phi_c": phi_c,
                "timestamp": time.time(),
            })
        return info

    async def send_chat_message(self, message: str) -> bool:
        if self.guardian:
            safe, _ = self.guardian.exorcise(message)
            if not safe:
                self._metrics["chat_blocks"] += 1
                return False
        await self._api_request("POST", "/live/room/chat/", json={
            "open_id": self.config.open_id, "message": message
        })
        return True

    async def subscribe_events(self, handler: Callable):
        # TikTok usa WebSocket; simulamos com polling simplificado
        asyncio.create_task(self._poll_chat(handler))

    async def _poll_chat(self, handler: Callable):
        while True:
            data = await self._api_request("GET", f"/live/room/chat/?open_id={self.config.open_id}&room_id={self.config.room_id}")
            for msg in data.get("data", {}).get("messages", []):
                text = msg.get("content", "")
                safe = True
                reason = None
                if self.guardian:
                    safe, report = self.guardian.exorcise(text)
                    if not safe:
                        reason = getattr(report, "reason", "unsafe")
                        self._metrics["chat_blocks"] += 1
                chat_msg = LiveChatMessage(
                    platform=Platform.TIKTOK,
                    message_id=msg.get("id", ""),
                    stream_id=self.config.room_id or "",
                    chatter_id=msg.get("user_id", ""),
                    chatter_name=msg.get("nickname", ""),
                    message=text,
                    timestamp=time.time(),
                    phi_c_safe=safe,
                    guardian_reason=reason,
                )
                self._metrics["chat_messages"] += 1
                await handler(chat_msg)
            await asyncio.sleep(5)

    def get_metrics(self) -> Dict:
        self._metrics["phi_c"] = self.phi_bus.get_mesh_coherence() if self.phi_bus else 0.997
        return self._metrics

    async def close(self):
        if self._session:
            await self._session.close()
