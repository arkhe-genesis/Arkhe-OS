
import os
import uuid
import logging
from datetime import datetime, timezone, timezone
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from jose import jwt, JWTError

from ..iota_council import IOTACouncil
from .telemetry_processor import TelemetryProcessor
from .gameplay_handler import GameplayHandler
from .stream_gateway import stream_gateway
from .security_router import router as security_router

# Security Configuration
SECRET_KEY = os.environ.get("ARKHE_CORE_SECRET_KEY", "DEVELOPMENT_SECRET_INSECURE")
ALGORITHM = "HS256"
security = HTTPBearer()

logger = logging.getLogger(__name__)

app = FastAPI(title="Arkhe(n) Forge API", version="0.1.0")
app.include_router(security_router)

council = IOTACouncil()
telemetry_processor = TelemetryProcessor()
gameplay_handler = GameplayHandler()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validates the JWT token and returns the user payload (APTS-HO-001)."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

async def get_current_game(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validates the JWT token and returns the game_id."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("game_id")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

class IntentRequest(BaseModel):
    intent: str

class GovernanceRequest(BaseModel):
    evento: str
    sistema: str
    cve: Optional[str] = None
    cvss: float

class DeliberationResponse(BaseModel):
    intent: str
    perspectives: List[Dict[str, Any]]
    consensus: Dict[str, Any]
    status: str

class OntologyNode(BaseModel):
    uri: str
    position: List[float]
    color: List[float]
    size: float
    type: int
    securityState: int

class OntologyEdge(BaseModel):
    sourceIndex: int
    targetIndex: int
    relationType: int
    strength: float

class VisualizationState(BaseModel):
    nodes: List[OntologyNode]
    edges: List[OntologyEdge]

class ViewportState(BaseModel):
    position: Dict[str, float]
    direction: Dict[str, float]

class VisualTelemetryRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    viewport: ViewportState
    interaction: Optional[Dict[str, Any]] = None
    rendering_metrics: Optional[Dict[str, Any]] = None

class ZKReportRequest(BaseModel):
    proof: Dict[str, Any]
    public_inputs: Dict[str, Any]

class GameplayTarget(BaseModel):
    type: str
    data: Dict[str, Any]

class GameplayEvent(BaseModel):
    game_id: str
    player_id: str
    action: str
    target: GameplayTarget

@app.post("/deliberate", response_model=DeliberationResponse)
async def deliberate(request: IntentRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Sensitive governance endpoint secured via JWT (APTS-HO-001)."""
    try:
        # Audit logs could use 'user' context here if needed
        result = await council.deliberate(request.intent)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/game/zk-challenge/{node_hash}")
async def get_zk_challenge(node_hash: str):
    return await telemetry_processor.generate_zk_challenge(node_hash)

@app.post("/game/zk-report")
async def post_zk_report(report: ZKReportRequest):
    try:
        result = await telemetry_processor.verify_zk_report(report.proof, report.public_inputs)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "COHERENT", "lambda2": 0.9984}

@app.get("/visualization-state", response_model=VisualizationState)
async def get_visualization_state():
    nodes = [
        OntologyNode(uri="arkhe:Core", position=[0, 0, 0], color=[0, 1, 0.6, 1], size=0.5, type=0, securityState=0),
        OntologyNode(uri="arkhe:Sensory", position=[2, 0, 0], color=[0, 0.5, 1, 1], size=0.3, type=1, securityState=0),
        OntologyNode(uri="arkhe:Cognitive", position=[-2, 0, 0], color=[0.7, 0.3, 1, 1], size=0.3, type=1, securityState=1),
        OntologyNode(uri="arkhe:Metabolic", position=[0, 2, 0], color=[1, 0.5, 0, 1], size=0.3, type=1, securityState=2),
        OntologyNode(uri="arkhe:Immune", position=[0, -2, 0], color=[0.1, 0.8, 0.3, 1], size=0.3, type=1, securityState=0),
    ]
    edges = [
        OntologyEdge(sourceIndex=0, targetIndex=1, relationType=0, strength=1.0),
        OntologyEdge(sourceIndex=0, targetIndex=2, relationType=0, strength=1.0),
        OntologyEdge(sourceIndex=0, targetIndex=3, relationType=0, strength=1.0),
        OntologyEdge(sourceIndex=0, targetIndex=4, relationType=0, strength=1.0),
    ]
    return VisualizationState(nodes=nodes, edges=edges)

@app.post("/visual-telemetry")
async def post_visual_telemetry(telemetry: VisualTelemetryRequest):
    try:
        result = await telemetry_processor.process_telemetry(telemetry.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/gameplay/event")
async def gameplay_event(
    event: GameplayEvent,
    x_arkhe_async: Optional[bool] = Header(None, alias="X-Arkhe-Async"),
    game_id: str = Depends(get_current_game)
):
    try:
        if x_arkhe_async:
            task_id = str(uuid.uuid4())
            return JSONResponse(
                status_code=202,
                content={"task_id": task_id, "status": "pending"}
            )

        # Verify event's game_id matches token's game_id
        if event.game_id != game_id:
             raise HTTPException(status_code=403, detail="Token does not match game_id")

        result = await gameplay_handler.process_event(event.model_dump())
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/api/v1/stream")
async def websocket_endpoint(websocket: WebSocket):
    # Verify token from query param or header
    token = websocket.query_params.get("token")
    if not token:
        # Check header if subprotocol or similar mechanism is used
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        await websocket.close(code=4001)
        return

    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        await websocket.close(code=4001)
        return

    await stream_gateway.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received from client: {data}")
    except WebSocketDisconnect:
        stream_gateway.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
