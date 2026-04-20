import asyncio
import json
import random
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ArkheEmulator")

class FrictionConfig:
    BASE_LATENCY_MS = 50
    JITTER_MS = 150
    FAIL_PROBABILITY = {
        "connection_drop": 0.02,
        "message_loss": 0.01,
        "delayed_response": 0.05,
        "malformed_json": 0.001,
    }
    ANOMALY_RATE_PER_ENTITY = 0.3
    ANOMALY_TYPES = ["config_drift", "unauthorized_access", "resource_exhaustion", "data_corruption"]
    SEVERITY_WEIGHTS = {"low": 0.50, "medium": 0.30, "high": 0.15, "critical": 0.05}

config = FrictionConfig()

class GameEvent(BaseModel):
    game_id: str
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    action: str
    target: dict
    metadata: Optional[dict] = None

class EntityState(BaseModel):
    id: str
    status: str
    anomaly_type: Optional[str] = None
    severity: Optional[str] = None
    position: dict
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ArkheStateUpdate(BaseModel):
    entities: List[EntityState]

app = FastAPI(title="Arkhe Anomaly Emulator")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

active_connections: Set[WebSocket] = set()
registered_entities: Dict[str, EntityState] = {}

@app.post("/api/v1/gameplay/event")
async def handle_gameplay_event(event: GameEvent, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    await asyncio.sleep(random.uniform(0.05, 0.2)) # Friction

    # Register entity if scan
    if event.action == "scan" and event.target.get("type") == "coordinate":
        entity_id = event.target.get("data", {}).get("node_uri", f"entity-{uuid.uuid4().hex[:6]}")
        pos = {k: v for k, v in event.target["data"].items() if k in ["x", "y", "z"]}
        if entity_id not in registered_entities:
            registered_entities[entity_id] = EntityState(
                id=entity_id,
                status="healthy",
                position=pos
            )
            logger.info(f"Registered entity via REST: {entity_id}")

    severity = random.choice(["low", "medium", "high"])
    return {
        "result": "confirmed" if random.random() < 0.5 else "false_positive",
        "severity": severity,
        "visual_feedback": {"color": "#FF3333", "animation": "pulse", "sound_id": "arkhe.alert"},
        "reward": {"currency": "diamonds", "amount": 100},
        "audit_ref": f"arkhe:event:{uuid.uuid4().hex[:8]}"
    }

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                # Handle registration via WebSocket
                msg = json.loads(data)
                if msg.get("action") == "scan" and msg.get("target", {}).get("type") == "coordinate":
                    entity_id = msg.get("target", {}).get("data", {}).get("node_uri", f"entity-{uuid.uuid4().hex[:6]}")
                    pos = msg.get("target", {}).get("data", {})
                    if entity_id not in registered_entities:
                        registered_entities[entity_id] = EntityState(
                            id=entity_id,
                            status="healthy",
                            position={k: v for k, v in pos.items() if k in ["x", "y", "z"]}
                        )
                        logger.info(f"Registered entity via WS: {entity_id}")
                        # Confirm registration
                        await websocket.send_text(json.dumps({"type": "ack", "entity_id": entity_id}))
            except:
                pass
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def anomaly_loop():
    while True:
        if active_connections and registered_entities:
            # Simulate anomalies on registered entities
            updates = []
            for eid, state in registered_entities.items():
                if state.status == "healthy" and random.random() < 0.1:
                    state.status = "anomaly_detected"
                    state.severity = random.choice(["high", "critical"])
                    state.anomaly_type = random.choice(config.ANOMALY_TYPES)
                    state.timestamp = datetime.now(timezone.utc).isoformat()
                    updates.append(state)
                elif state.status == "anomaly_detected" and random.random() < 0.3:
                    state.status = "healthy"
                    state.severity = None
                    state.anomaly_type = None
                    state.timestamp = datetime.now(timezone.utc).isoformat()
                    updates.append(state)

            if updates:
                payload = json.dumps({"entities": [u.dict() for u in updates]})
                for ws in list(active_connections):
                    try:
                        await ws.send_text(payload)
                    except:
                        active_connections.discard(ws)

        await asyncio.sleep(2.0)

@app.on_event("startup")
async def startup():
    asyncio.create_task(anomaly_loop())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765)
