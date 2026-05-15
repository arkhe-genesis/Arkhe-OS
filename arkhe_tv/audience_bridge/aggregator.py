#!/usr/bin/env python3
"""
Substrato 9033-C — Audience Bridge: TV 3.0 ↔ Twitch
Agrega viewer counts de plataformas de streaming para emissoras de TV aberta,
fornece API para aplicações Ginga e ancora métricas na TemporalChain.
"""

import asyncio
import hashlib
import json
import time
import aiohttp
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

class Platform(Enum):
    TWITCH = "twitch"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"

@dataclass
class BroadcasterMapping:
    """Mapeamento: emissora de TV aberta → canais nas plataformas de streaming."""
    broadcaster_id: str          # ID da emissora (ex: "globo", "sbt", "band")
    display_name: str            # Nome de exibição
    twitch_channels: List[str]   # Lista de canais Twitch que retransmitem
    youtube_channels: List[str]  # IDs de canal YouTube
    tiktok_rooms: List[str]      # IDs de sala TikTok
    auto_discover: bool = True   # Descobrir automaticamente novos canais

@dataclass
class AudienceSnapshot:
    """Snapshot de audiência agregada para uma emissora."""
    broadcaster_id: str
    timestamp: float
    total_viewers: int
    platform_breakdown: Dict[str, int]  # platform → viewers
    channel_details: List[Dict]          # detalhes por canal
    phi_c_coherence: float = 0.0
    temporal_seal: Optional[str] = None

class AudienceAggregator:
    """
    Agregador de audiência cross-platform para TV aberta.

    Funcionalidades:
    • Consulta periódica de viewer_count via APIs das plataformas
    • Mapeamento de emissoras para canais de streaming
    • API REST para consulta por aplicações Ginga
    • Ancoragem de métricas na TemporalChain
    • Validação Φ_C dos dados agregados
    """

    # Mapeamento de emissoras brasileiras para canais de streaming
    BROADCASTER_MAPPINGS = {
        "globo": BroadcasterMapping(
            broadcaster_id="globo",
            display_name="TV Globo",
            twitch_channels=["tvglobo", "globotv", "globoplay"],
            youtube_channels=["UCe7HwIfKwJdiH4JfLkLkKjA"],
            tiktok_rooms=[],
        ),
        "sbt": BroadcasterMapping(
            broadcaster_id="sbt",
            display_name="SBT",
            twitch_channels=["sbt", "sbtonline"],
            youtube_channels=["UCpG4LQJK2D5YJLClQhAWsTw"],
            tiktok_rooms=[],
        ),
        "band": BroadcasterMapping(
            broadcaster_id="band",
            display_name="Band",
            twitch_channels=["bandtv", "bandesportes"],
            youtube_channels=["UCiUWFXN6Ai0I86M3Kn3Jkvg"],
            tiktok_rooms=[],
        ),
        "record": BroadcasterMapping(
            broadcaster_id="record",
            display_name="Record TV",
            twitch_channels=["recordtv", "recordtvoficial"],
            youtube_channels=["UCqFqYIfXgGqM8KkLkLkLkL"],
            tiktok_rooms=[],
        ),
        "cultura": BroadcasterMapping(
            broadcaster_id="cultura",
            display_name="TV Cultura",
            twitch_channels=["tvcultura"],
            youtube_channels=["UCcNvQrJkLkLkLkLkLkLkLk"],
            tiktok_rooms=[],
        ),
    }

    # Configurações de polling
    POLL_INTERVAL_SECONDS = 60       # Consultar a cada 1 minuto
    TWITCH_RATE_LIMIT = 800           # Requisições por minuto (Helix API)
    CACHE_TTL_SECONDS = 45            # TTL do cache (menor que polling)

    def __init__(self, twitch_client_id: str, twitch_token: str,
                 yt_api_key: str = "",
                 temporal_chain=None, phi_bus=None):
        self.twitch_client_id = twitch_client_id
        self.twitch_token = twitch_token
        self.yt_api_key = yt_api_key
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self._cache: Dict[str, AudienceSnapshot] = {}
        self._last_poll: float = 0
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_twitch_viewers(self, channels: List[str]) -> List[Dict]:
        """Consulta viewer_count de canais Twitch via Helix API."""
        if not channels:
            return []

        headers = {
            "Client-Id": self.twitch_client_id,
            "Authorization": f"Bearer {self.twitch_token}",
        }

        # Construir query com user_login (nomes dos canais)
        query_params = "&".join(f"user_login={ch}" for ch in channels)
        url = f"https://api.twitch.tv/helix/streams?{query_params}"

        if not self._session:
            self._session = aiohttp.ClientSession()

        try:
            async with self._session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [
                        {
                            "channel": s["user_name"],
                            "viewer_count": s["viewer_count"],
                            "game_name": s.get("game_name", ""),
                            "title": s.get("title", ""),
                            "started_at": s.get("started_at", ""),
                            "platform": "twitch",
                        }
                        for s in data.get("data", [])
                    ]
        except Exception as e:
            print(f"⚠️ Twitch API error: {e}")

        return []

    async def _get_youtube_viewers(self, channel_ids: List[str]) -> List[Dict]:
        """Consulta concurrentViewers de canais YouTube via YouTube Data API v3."""
        results = []

        if not channel_ids or not self.yt_api_key:
            return []

        if not self._session:
            self._session = aiohttp.ClientSession()

        for channel_id in channel_ids:
            # Primeiro, obter broadcast ativo
            search_url = (
                f"https://www.googleapis.com/youtube/v3/search"
                f"?part=snippet&channelId={channel_id}&eventType=live&type=video"
                f"&key={self.yt_api_key}"
            )

            try:
                async with self._session.get(search_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("items", []):
                            video_id = item["id"]["videoId"]

                            # Obter liveStreamingDetails
                            details_url = (
                                f"https://www.googleapis.com/youtube/v3/videos"
                                f"?part=liveStreamingDetails&id={video_id}"
                                f"&key={self.yt_api_key}"
                            )
                            async with self._session.get(details_url) as details_resp:
                                if details_resp.status == 200:
                                    details = await details_resp.json()
                                    for video in details.get("items", []):
                                        live = video.get("liveStreamingDetails", {})
                                        viewers = int(live.get("concurrentViewers", 0))
                                        results.append({
                                            "channel": item["snippet"]["channelTitle"],
                                            "viewer_count": viewers,
                                            "title": item["snippet"]["title"],
                                            "platform": "youtube",
                                        })
            except Exception as e:
                print(f"⚠️ YouTube API error: {e}")

        return results

    async def get_audience(self, broadcaster_id: str) -> AudienceSnapshot:
        """Obtém audiência agregada para uma emissora."""
        mapping = self.BROADCASTER_MAPPINGS.get(broadcaster_id)
        if not mapping:
            return AudienceSnapshot(
                broadcaster_id=broadcaster_id,
                timestamp=time.time(),
                total_viewers=0,
                platform_breakdown={},
                channel_details=[],
            )

        # Verificar cache
        cache_key = f"audience_{broadcaster_id}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached.timestamp < self.CACHE_TTL_SECONDS:
                return cached

        # Consultar todas as plataformas
        twitch_data = await self._get_twitch_viewers(mapping.twitch_channels)
        youtube_data = await self._get_youtube_viewers(mapping.youtube_channels)

        all_channels = twitch_data + youtube_data

        # Agregar
        total_viewers = sum(c["viewer_count"] for c in all_channels)
        platform_breakdown = {}
        for c in all_channels:
            plat = c["platform"]
            platform_breakdown[plat] = platform_breakdown.get(plat, 0) + c["viewer_count"]

        # Φ_C — qualidade do dado
        phi_c = self.phi_bus.get_mesh_coherence() if hasattr(self.phi_bus, 'get_mesh_coherence') else 0.99

        snapshot = AudienceSnapshot(
            broadcaster_id=broadcaster_id,
            timestamp=time.time(),
            total_viewers=total_viewers,
            platform_breakdown=platform_breakdown,
            channel_details=all_channels,
            phi_c_coherence=phi_c,
        )

        # Ancorar na TemporalChain
        if self.temporal and hasattr(self.temporal, 'anchor_event'):
            # Handling both async and sync mock anchor events
            anchor_result = self.temporal.anchor_event(
                "audience_snapshot", {
                    "broadcaster": broadcaster_id,
                    "total_viewers": total_viewers,
                    "platforms": platform_breakdown,
                    "phi_c": phi_c,
                    "timestamp": time.time(),
                }
            )
            if asyncio.iscoroutine(anchor_result):
                snapshot.temporal_seal = await anchor_result
            else:
                snapshot.temporal_seal = anchor_result

        # Atualizar cache
        self._cache[cache_key] = snapshot
        return snapshot

    async def get_all_broadcasters(self) -> Dict[str, AudienceSnapshot]:
        """Obtém audiência de todas as emissoras mapeadas."""
        tasks = [self.get_audience(bid) for bid in self.BROADCASTER_MAPPINGS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            bid: (result if not isinstance(result, Exception) else AudienceSnapshot(
                broadcaster_id=bid, timestamp=time.time(), total_viewers=0,
                platform_breakdown={}, channel_details=[],
            ))
            for bid, result in zip(self.BROADCASTER_MAPPINGS, results)
        }

    def get_share_of_tv(self, broadcaster_id: str, total_tv_viewers: int) -> float:
        """
        Calcula o share estimado na TV aberta com base nos viewers do Twitch.

        Fórmula de equivalência:
        Share_TV(%) = (Viewers_Twitch / Total_Viewers_Twitch) * 100

        Para projeção na TV aberta (opcional):
        Audiência_Projetada = Viewers_Twitch * Fator_Conversão

        Onde Fator_Conversão é calibrado com dados da Kantar Ibope Media.
        """
        snapshot = self._cache.get(f"audience_{broadcaster_id}")
        if not snapshot or snapshot.total_viewers == 0:
            return 0.0

        # Calcular share entre as plataformas de streaming
        all_snapshots = self._cache
        total_streaming_viewers = sum(
            s.total_viewers for s in all_snapshots.values()
        )

        if total_streaming_viewers == 0:
            return 0.0

        return (snapshot.total_viewers / total_streaming_viewers) * 100

    async def close(self):
        if self._session:
            await self._session.close()
