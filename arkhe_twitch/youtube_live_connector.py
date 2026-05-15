#!/usr/bin/env python3
"""Conector para YouTube Live via YouTube Data API v3 e YouTube Live Chat API."""

import asyncio, aiohttp, hashlib, json, time, logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from .broadcast_connector_interface import BroadcastConnector, LiveStreamInfo, LiveChatMessage, Platform

logger = logging.getLogger(__name__)

@dataclass
class YouTubeConfig:
    client_id: str
    client_secret: str
    refresh_token: str
    channel_id: str
    api_key: str
    broadcast_id: Optional[str] = None

class YouTubeLiveConnector(BroadcastConnector):
    """Conector para YouTube Live."""

    def __init__(self, config: YouTubeConfig, temporal_chain=None, guardian=None, phi_bus=None):
        self.config = config
        self.temporal = temporal_chain
        self.guardian = guardian
        self.phi_bus = phi_bus
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0
        self._live_chat_id: Optional[str] = None
        self._chat_page_token: Optional[str] = None
        self._metrics = {"api_requests": 0, "api_errors": 0, "chat_messages": 0, "chat_blocks": 0}
        self._session: Optional[aiohttp.ClientSession] = None

    async def _ensure_token(self):
        if self._access_token and time.time() < self._token_expiry:
            return
        async with aiohttp.ClientSession() as sess:
            async with sess.post("https://oauth2.googleapis.com/token", data={
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "refresh_token": self.config.refresh_token,
                "grant_type": "refresh_token",
            }) as resp:
                data = await resp.json()
                self._access_token = data["access_token"]
                self._token_expiry = time.time() + data.get("expires_in", 3600) - 60

    async def _api_request(self, method: str, url: str, **kwargs) -> Dict:
        await self._ensure_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._access_token}"
        headers["Accept"] = "application/json"
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
        # Obtém broadcast ativo
        data = await self._api_request("GET",
            f"https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet,status&broadcastStatus=active&broadcastType=all"
        )
        items = data.get("items", [])
        if not items:
            return None
        broadcast = items[0]
        snippet = broadcast.get("snippet", {})
        status = broadcast.get("status", {})
        # Obter contagem de viewers (liveStreamingDetails)
        details = await self._api_request("GET",
            f"https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={broadcast['id']}"
        )
        viewers = 0
        if details.get("items"):
            viewers = int(details["items"][0].get("liveStreamingDetails", {}).get("concurrentViewers", 0))
        phi_c = self.phi_bus.get_mesh_coherence() if self.phi_bus else 0.997
        self._live_chat_id = snippet.get("liveChatId")
        info = LiveStreamInfo(
            platform=Platform.YOUTUBE,
            stream_id=broadcast["id"],
            broadcaster_id=self.config.channel_id,
            broadcaster_name=snippet.get("channelTitle", ""),
            title=snippet.get("title", ""),
            viewer_count=viewers,
            started_at=snippet.get("publishedAt", ""),
            language=snippet.get("defaultLanguage", "en"),
            phi_c_coherence=phi_c,
        )
        if self.temporal:
            info.temporal_seal = await self.temporal.anchor_event("youtube_stream_info", {
                "stream_id": info.stream_id, "title": info.title, "viewers": viewers, "phi_c": phi_c,
                "timestamp": time.time(),
            })
        return info

    async def send_chat_message(self, message: str) -> bool:
        if not self._live_chat_id:
            return False
        if self.guardian:
            safe, _ = self.guardian.exorcise(message)
            if not safe:
                self._metrics["chat_blocks"] += 1
                return False
        await self._api_request("POST",
            f"https://www.googleapis.com/youtube/v3/liveChat/messages?part=snippet",
            json={"snippet": {"liveChatId": self._live_chat_id, "type": "textMessageEvent",
                              "textMessageDetails": {"messageText": message}}}
        )
        return True

    async def subscribe_events(self, handler: Callable):
        # YouTube usa polling na live chat API; simulamos com loop
        asyncio.create_task(self._poll_chat(handler))

    async def _poll_chat(self, handler: Callable):
        while True:
            if not self._live_chat_id:
                await asyncio.sleep(10)
                continue
            params = {"part": "snippet", "liveChatId": self._live_chat_id}
            if self._chat_page_token:
                params["pageToken"] = self._chat_page_token
            data = await self._api_request("GET",
                f"https://www.googleapis.com/youtube/v3/liveChat/messages?part=snippet&liveChatId={self._live_chat_id}",
            )
            for item in data.get("items", []):
                msg_data = item["snippet"]
                if msg_data["type"] == "textMessageEvent":
                    text = msg_data["textMessageDetails"]["messageText"]
                    safe = True
                    reason = None
                    if self.guardian:
                        safe, report = self.guardian.exorcise(text)
                        if not safe:
                            reason = getattr(report, "reason", "unsafe")
                            self._metrics["chat_blocks"] += 1
                    msg = LiveChatMessage(
                        platform=Platform.YOUTUBE,
                        message_id=item["id"],
                        stream_id=self._live_chat_id,
                        chatter_id=msg_data.get("authorChannelId", ""),
                        chatter_name=msg_data.get("authorDisplayName", ""),
                        message=text,
                        timestamp=time.time(),
                        phi_c_safe=safe,
                        guardian_reason=reason,
                    )
                    self._metrics["chat_messages"] += 1
                    await handler(msg)
            self._chat_page_token = data.get("nextPageToken")
            await asyncio.sleep(data.get("pollingIntervalMillis", 5000) / 1000)

    def get_metrics(self) -> Dict:
        self._metrics["phi_c"] = self.phi_bus.get_mesh_coherence() if self.phi_bus else 0.997
        return self._metrics

    async def close(self):
        if self._session:
            await self._session.close()
