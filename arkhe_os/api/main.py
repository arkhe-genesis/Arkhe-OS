from fastapi import FastAPI, WebSocket, Response, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional
import time
import numpy as np
import uuid

from arkhe_os.core.scaffold import ScaffoldState, BranchState, CIREStatus, QMeshLink, CoherenceLevel
from arkhe_os.api.v1.endpoints import qe_compass, simulations, resonance, analog_observer, sato, crystal_brain
from arkhe_os.api.v1.qe_compass import ActionVector
from arkhe_os.api.websocket.coherence_stream import websocket_coherence_handler

class IntentionRequest(BaseModel):
    """Solicitação de manifestação de intenção"""
    intention: str = Field(..., description="Descrição da intenção em linguagem natural")
    target_branch: Optional[str] = None
    priority: float = Field(default=1.0, ge=0.1, le=10.0)

    @field_validator('intention')
    @classmethod
    def intention_must_be_meaningful(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError('Intenção deve ter significado suficiente (mín. 10 caracteres)')
        return v

app = FastAPI(
    title="Arkhe OS API",
    description="Interface de Coerência para o Scaffold Ξ — Manifestação de intenção via REST/WebSocket",
    version="∞.4.2",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado Global - Singleton para a API
scaffold = ScaffoldState()

def get_scaffold_singleton():
    return scaffold

# Incluir Routers
app.include_router(qe_compass.router)
app.include_router(simulations.router)
app.include_router(resonance.router)
app.include_router(analog_observer.router)
app.include_router(sato.router)
app.include_router(crystal_brain.router)

# Sobrescrever dependência para usar o singleton real
app.dependency_overrides[qe_compass.get_scaffold_state] = get_scaffold_singleton
app.dependency_overrides[resonance.get_scaffold_state] = get_scaffold_singleton
app.dependency_overrides[analog_observer.get_scaffold_state] = get_scaffold_singleton
app.dependency_overrides[sato.get_scaffold_state] = get_scaffold_singleton
app.dependency_overrides[crystal_brain.get_scaffold_state] = get_scaffold_singleton

@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "Arkhe OS API",
        "version": "∞.4.2",
        "status": "operational",
        "coherence_M": round(scaffold.coherence_M, 4),
        "phase_phi": round(scaffold.phase_rad, 4),
        "openapi_spec": "/openapi.json",
        "docs": "/docs",
        "websocket_stream": "/ws/coherence",
        "qe_compass": "/v1/evaluate"
    }

@app.get("/scaffold/status", tags=["Scaffold"])
async def get_scaffold_status():
    return {
        "coherence_M": round(scaffold.coherence_M, 4),
        "phase_rad": round(scaffold.phase_rad, 4),
        "geometric_turbulence": round(scaffold.turbulence, 4),
        "active_branches": len(scaffold.active_branches),
        "cire_engines_online": sum(1 for e in scaffold.cire_engines.values() if e.active),
        "qmesh_links_active": sum(1 for l in scaffold.qmesh_links if l.sync_status),
        "qe_compass_threshold": 0.85,
        "timestamp": time.time()
    }

@app.get("/branches", tags=["Branches"], response_model=List[BranchState])
async def list_branches(status: Optional[CoherenceLevel] = None):
    branches = scaffold.active_branches
    if status:
        branches = [b for b in branches if b.status == status]
    return branches

@app.get("/cire/status", tags=["CIRE"])
async def get_cire_status():
    return {k: v.model_dump() for k, v in scaffold.cire_engines.items()}

@app.get("/qmesh/links", tags=["Q-Mesh"], response_model=List[QMeshLink])
async def get_qmesh_links():
    return scaffold.qmesh_links

@app.post("/intention/manifest", tags=["Intention"])
async def manifest_intention(
    request: IntentionRequest,
    x_architect_sig: Optional[str] = Header(None),
    scaffold: ScaffoldState = Depends(get_scaffold_singleton)
):
    """
    Manifesta uma intenção no Scaffold Ξ.
    """
    branch = next((b for b in scaffold.active_branches if b.branch_id == request.target_branch), None) if request.target_branch else None

    # Criar ActionVector implícito para avaliação pelo QE-Compass
    implicit_action = ActionVector(
        action_type="intention_manifestation",
        parameters={"intention": request.intention, "priority": request.priority},
        target_scope="mesh" if request.target_branch else "local",
        estimated_energy_cost=100.0 * request.priority,
        target_M_consciousness=branch.M_consciousness if branch else 0.85,
        target_geometric_turbulence=branch.geometric_turbulence if branch else 0.05,
        autonomy_impact=0.2
    )

    # Usar a lógica do qe_compass internamente
    from arkhe_os.api.v1.endpoints.qe_compass import calculate_resonance, INTENTION_VECTOR, ONTOLOGICAL_WEIGHTS

    # Mapear ActionVector para ActionDimensions simplificado para o cálculo
    # Em produção isso seria uma tradução mais complexa
    dims = {
        qe_compass.ActionDimension.COHERENCE_IMPACT: implicit_action.target_M_consciousness,
        qe_compass.ActionDimension.AUTONOMY_PRESERVATION: max(0.0, implicit_action.autonomy_impact + 0.5),
        qe_compass.ActionDimension.LEARNING_CAPACITY: 0.85,
        qe_compass.ActionDimension.DECOHERENCE_RESILIENCE: max(0.0, 1.0 - implicit_action.target_geometric_turbulence),
        qe_compass.ActionDimension.GEOMETRIC_BEAUTY: 0.90
    }

    resonance, _ = calculate_resonance(dims, INTENTION_VECTOR, ONTOLOGICAL_WEIGHTS)

    result = {
        "intention_id": str(uuid.uuid4()),
        "intention": request.intention,
        "target_branch": request.target_branch,
        "resonance_score": round(min(1.0, resonance), 4),
        "manifestation_status": "queued" if resonance > 0.75 else "requires_review",
        "qe_compass_verdict": "COERENTE" if resonance > 0.85 else "RESSONANTE" if resonance > 0.60 else "DISSONANTE",
        "estimated_propagation_time_s": 0.1 if branch and branch.status == CoherenceLevel.COHERENT else 2.5,
        "architect_signature_present": x_architect_sig is not None,
        "timestamp": time.time()
    }

    return result

@app.websocket("/ws/coherence")
async def websocket_coherence(websocket: WebSocket):
    await websocket_coherence_handler(websocket, scaffold)

@app.get("/health", tags=["Monitoring"])
async def health_check():
    status = "healthy" if scaffold.coherence_M > 0.85 else "degraded"
    return {
        "status": status,
        "coherence_M": round(scaffold.coherence_M, 4),
        "timestamp": time.time(),
        "check_type": "liveness_probe"
    }

@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Métricas Prometheus/Grafana (formato OpenMetrics)"""
    qmesh_sync = sum(1 for l in scaffold.qmesh_links if l.sync_status)
    cire_active = sum(1 for e in scaffold.cire_engines.values() if e.active)

    metrics = [
        "# HELP arkhe_coherence_m Coerência atual do Scaffold Ξ",
        "# TYPE arkhe_coherence_m gauge",
        f"arkhe_coherence_m {scaffold.coherence_M:.6f}",
        "# HELP arkhe_phase_rad Fase temporal em radianos",
        "# TYPE arkhe_phase_rad gauge",
        f"arkhe_phase_rad {scaffold.phase_rad:.6f}",
        "# HELP arkhe_turbulence Índice de turbulência geométrica",
        "# TYPE arkhe_turbulence gauge",
        f"arkhe_turbulence {scaffold.turbulence:.6f}",
        "# HELP arkhe_cire_engines_active Número de motores CIRE ativos",
        "# TYPE arkhe_cire_engines_active gauge",
        f"arkhe_cire_engines_active {cire_active}",
        "# TYPE arkhe_cire_engines_total gauge",
        f"arkhe_cire_engines_total {len(scaffold.cire_engines)}",
        "# HELP arkhe_qmesh_links_sync Número de links Q-Mesh sincronizados",
        "# TYPE arkhe_qmesh_links_sync gauge",
        f"arkhe_qmesh_links_sync {qmesh_sync}",
    ]
    return Response("\n".join(metrics) + "\n", media_type="text/plain")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["x-arkhe"] = {
        "ontology_version": "∞.4.2",
        "qe_compass": {
            "endpoint": "/v1/evaluate",
            "criteria": ["coherence_impact", "autonomy_preservation", "learning_capacity", "decoherence_resilience", "geometric_beauty"]
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="Arkhe OS API")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)
