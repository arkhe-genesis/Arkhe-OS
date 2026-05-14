#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rest.py — API REST para TemporalChain usando FastAPI.
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import time

from ..core import TemporalChain, EventType

app = FastAPI(title="ARKHE Timechain API", version="1.0.0")

# Dependency injection para TemporalChain
async def get_timechain() -> TemporalChain:
    # Em produção: injetar instância configurada
    return TemporalChain(storage_backend="sqlite")

# Modelos Pydantic para request/response
class AnchorEventRequest(BaseModel):
    event_type: str
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    causal_deps: Optional[List[str]] = None
    validate: bool = True

class AnchorEventResponse(BaseModel):
    event_id: str
    seal: str
    chain_seal: str
    position: int
    anchored_at: float

class QueryEventsRequest(BaseModel):
    event_type: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    seal_prefix: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

@app.post("/events", response_model=AnchorEventResponse)
async def anchor_event(
    request: AnchorEventRequest,
    timechain: TemporalChain = Depends(get_timechain),
):
    """Ancora um novo evento na cadeia temporal."""
    try:
        anchor = await timechain.anchor_event(
            event_type=request.event_type,
            payload=request.payload,
            metadata=request.metadata,
            causal_deps=request.causal_deps,
            validate_with_guardian=request.validate,
        )
        return AnchorEventResponse(
            event_id=anchor.event.event_id,
            seal=anchor.event.seal,
            chain_seal=anchor.chain_seal,
            position=anchor.position,
            anchored_at=anchor.anchored_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/events/{event_id}")
async def get_event(
    event_id: str,
    timechain: TemporalChain = Depends(get_timechain),
):
    """Recupera evento por ID."""
    event = await timechain.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.to_dict()

@app.get("/events")
async def query_events(
    request: QueryEventsRequest = Depends(),
    timechain: TemporalChain = Depends(get_timechain),
):
    """Consulta eventos com filtros."""
    events = await timechain.query_events(
        event_type=request.event_type,
        start_time=request.start_time,
        end_time=request.end_time,
        seal_prefix=request.seal_prefix,
        limit=request.limit,
        offset=request.offset,
    )
    return {
        "events": [e.to_dict() for e in events],
        "count": len(events),
        "has_more": len(events) == request.limit,
    }

@app.get("/verify")
async def verify_chain(
    from_position: int = Query(default=0, ge=0),
    timechain: TemporalChain = Depends(get_timechain),
):
    """Verifica integridade da cadeia."""
    is_valid = await timechain.verify_chain(from_position)
    return {
        "valid": is_valid,
        "current_seal": timechain.current_seal,
        "event_count": timechain.event_count,
        "merkle_root": timechain.merkle_root,
    }

@app.get("/export")
async def export_chain(
    start: int = Query(default=0, ge=0),
    end: Optional[int] = Query(default=None, ge=0),
    format: str = Query(default="json", regex="^(json|binary)$"),
    timechain: TemporalChain = Depends(get_timechain),
):
    """Exporta cadeia para auditoria externa."""
    content = await timechain.export_chain(start, end, format)
    media_type = "application/json" if format == "json" else "application/octet-stream"
    return Response(content=content, media_type=media_type)

@app.get("/health")
async def health_check(timechain: TemporalChain = Depends(get_timechain)):
    """Health check da API."""
    return {
        "status": "healthy",
        "node_id": timechain.node_id,
        "event_count": timechain.event_count,
        "current_seal": timechain.current_seal[:16] + "...",
        "timestamp": time.time(),
    }
