
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from ..iota_council import IOTACouncil
from .telemetry_processor import TelemetryProcessor

app = FastAPI(title="Arkhe(n) Forge API", version="0.1.0")
council = IOTACouncil()
telemetry_processor = TelemetryProcessor()

class IntentRequest(BaseModel):
    intent: str

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

class PlayerInfo(BaseModel):
    sub: str
    role: str

class ViewportState(BaseModel):
    position: Dict[str, float]
    direction: Dict[str, float]

class VisualTelemetryRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    viewport: ViewportState
    interaction: Optional[Dict[str, Any]] = None
    rendering_metrics: Optional[Dict[str, Any]] = None

class ZKReportRequest(BaseModel):
    proof: Dict[str, Any]
    public_inputs: Dict[str, Any]

@app.post("/deliberate", response_model=DeliberationResponse)
async def deliberate(request: IntentRequest):
    try:
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
    # Mock data for demonstration - Note: URIs are kept in backend for real use,
    # but here they are returned to allow the client to know what it is looking at
    # (in a real "blind" system, URIs would be replaced by hashes or IDs).
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
        result = await telemetry_processor.process_telemetry(telemetry.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
