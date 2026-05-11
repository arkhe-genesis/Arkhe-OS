from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import time
import hashlib
import asyncio
import numpy as np

router = APIRouter(prefix="/api/v1/security")

class ThreatReport(BaseModel):
    attack_type: str = Field(..., pattern="^(bot_flood|credential_stuffing|scraping|injection)$")
    domain: str = Field(..., min_length=3)
    indicators: List[str] = Field(..., min_items=1)
    proof_commitment: Optional[str] = Field(None, pattern=r'^0x[a-f0-9]{64}$')
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    coordinates: Optional[List[float]] = Field(None, min_items=2, max_items=2)
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))

class TPVDesignRequest(BaseModel):
    target_efficiency: float
    temperature_k: float

@router.post("/report")
async def report_threat(report: ThreatReport, background_tasks: BackgroundTasks):
    report_id = hashlib.sha256(f"{report.domain}{report.timestamp}".encode()).hexdigest()[:16]

    # Mock processing
    async def process_report(rid):
        await asyncio.sleep(1)
        print(f"🜏 Enriched report {rid} processed by federated analyzer.")

    background_tasks.add_task(process_report, report_id)

    return {
        "status": "received",
        "report_id": report_id,
        "federated_score": 0.88,
        "action_taken": "flagged_for_review"
    }

@router.get("/dashboard")
async def get_dashboard_data():
    return {
        "threats": [
            {"coordinates": [-43.1729, -22.9068], "intensity": 75, "severity": "high", "type": "bot_flood", "domain": "arkhe.rio"},
            {"coordinates": [-0.1278, 51.5074], "intensity": 30, "severity": "low", "type": "scraping", "domain": "arkhe.uk"}
        ],
        "metrics": {
            "avg_omega": 0.9412,
            "global_humanity_score": 0.982
        },
        "incidents": [
            {"domain": "node-alpha.network", "attack_type": "credential_stuffing", "severity": "medium", "timestamp": int(time.time()*1000) - 3600000}
        ]
    }

@router.post("/tpv/optimize")
async def optimize_tpv(request: TPVDesignRequest):
    # Mock optimization result
    return {
        "status": "optimized",
        "suggested_layers": 20,
        "expected_efficiency": 0.65,
        "design_id": hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    }

@router.websocket("/ws/stream")
async def security_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Send periodic mock updates
            await websocket.send_json({
                "type": "threat_detected",
                "payload": {
                    "coordinates": [float(np.random.uniform(-180, 180)), float(np.random.uniform(-90, 90))],
                    "intensity": int(np.random.randint(10, 100)),
                    "severity": "medium",
                    "timestamp": int(time.time()*1000)
                }
            })
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS Error: {e}")
