#!/usr/bin/env python3
"""API REST para consulta de audiência por aplicações Ginga (TV 3.0)."""

from fastapi import FastAPI, Query, Path
from fastapi.middleware.cors import CORSMiddleware
import asyncio, time
from .aggregator import AudienceAggregator, BroadcasterMapping

app = FastAPI(title="ARKHE Audience API for TV 3.0", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])

# Injetar aggregator (inicializado no main)
aggregator: AudienceAggregator = None

def set_aggregator(agg: AudienceAggregator):
    global aggregator
    aggregator = agg

@app.get("/api/v1/audience/{broadcaster_id}")
async def get_broadcaster_audience(
    broadcaster_id: str = Path(..., description="ID da emissora: globo, sbt, band, record, cultura"),
):
    """Retorna audiência agregada de uma emissora em todas as plataformas."""
    if not aggregator:
        return {"error": "Aggregator not initialized"}
    snapshot = await aggregator.get_audience(broadcaster_id)
    return {
        "broadcaster_id": snapshot.broadcaster_id,
        "display_name": aggregator.BROADCASTER_MAPPINGS.get(broadcaster_id, BroadcasterMapping(broadcaster_id, "", [], [], [])).display_name,
        "total_viewers": snapshot.total_viewers,
        "platform_breakdown": snapshot.platform_breakdown,
        "channels": [
            {
                "platform": ch["platform"],
                "channel": ch["channel"],
                "viewers": ch["viewer_count"],
                "title": ch.get("title", ""),
            }
            for ch in snapshot.channel_details
        ],
        "phi_c_coherence": snapshot.phi_c_coherence,
        "temporal_seal": snapshot.temporal_seal,
        "timestamp": snapshot.timestamp,
        "share_streaming": aggregator.get_share_of_tv(broadcaster_id, 0),
    }

@app.get("/api/v1/audience")
async def get_all_audiences():
    """Retorna audiência de todas as emissoras."""
    if not aggregator:
        return {"error": "Aggregator not initialized"}
    snapshots = await aggregator.get_all_broadcasters()
    return {
        "broadcasters": {
            bid: {
                "display_name": aggregator.BROADCASTER_MAPPINGS.get(bid, BroadcasterMapping(bid, "", [], [], [])).display_name,
                "total_viewers": snap.total_viewers,
                "platform_breakdown": snap.platform_breakdown,
                "share_streaming": aggregator.get_share_of_tv(bid, 0),
            }
            for bid, snap in snapshots.items()
        },
        "total_streaming_viewers": sum(s.total_viewers for s in snapshots.values()),
        "timestamp": time.time(),
    }

@app.get("/api/v1/audience/{broadcaster_id}/simple")
async def get_simple_audience(broadcaster_id: str):
    """
    Endpoint otimizado para aplicações Ginga (payload mínimo).
    Retorna apenas viewer_count total e por plataforma.
    """
    if not aggregator:
        return {"error": "Aggregator not initialized"}
    snapshot = await aggregator.get_audience(broadcaster_id)
    return {
        "v": snapshot.total_viewers,                    # total viewers
        "tw": snapshot.platform_breakdown.get("twitch", 0),   # twitch viewers
        "yt": snapshot.platform_breakdown.get("youtube", 0),  # youtube viewers
        "tk": snapshot.platform_breakdown.get("tiktok", 0),   # tiktok viewers
        "ts": int(snapshot.timestamp),
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "audience-bridge", "version": "9033-C"}
