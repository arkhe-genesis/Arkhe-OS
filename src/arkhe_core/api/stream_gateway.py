import asyncio
import json
import random
import time
import uuid
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class EntityState(BaseModel):
    id: str
    status: str
    anomaly_type: Optional[str] = None
    severity: Optional[str] = None
    position: Dict[str, float]
    timestamp: str

class StreamGateway:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.registered_entities: Dict[str, EntityState] = {}
        # Pre-populate some entities
        self._add_entity("node-alpha", {"x": 10, "y": 0, "z": 10})
        self._add_entity("node-beta", {"x": -10, "y": 0, "z": -10})
        self._add_entity("firewall-01", {"x": 0, "y": 5, "z": 0})

    def _add_entity(self, id: str, pos: Dict[str, float]):
        self.registered_entities[id] = EntityState(
            id=id,
            status="healthy",
            position=pos,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def run_simulation(self):
        """Simulates periodic state updates and random anomalies with friction."""
        while True:
            updates = []
            for entity_id, entity in self.registered_entities.items():
                changed = False
                # Random anomaly
                if entity.status == "healthy" and random.random() < 0.1:
                    entity.status = "anomaly_detected"
                    entity.anomaly_type = random.choice(["config_drift", "unauthorized_access", "resource_exhaustion"])
                    entity.severity = random.choice(["low", "medium", "high", "critical"])
                    changed = True
                # Random remediation
                elif entity.status == "anomaly_detected" and random.random() < 0.2:
                    entity.status = "healthy"
                    entity.anomaly_type = None
                    entity.severity = None
                    changed = True

                if changed:
                    entity.timestamp = datetime.now(timezone.utc).isoformat()
                    updates.append(entity.dict())

            if updates:
                payload = {"entities": updates}
                await self.broadcast(json.dumps(payload))

            await asyncio.sleep(random.uniform(1.0, 3.0))

stream_gateway = StreamGateway()
