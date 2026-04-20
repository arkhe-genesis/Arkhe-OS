
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ..iota_council import IOTACouncil
from ..governance_council import governance_app, IncidentState

app = FastAPI(title="Arkhe(n) Forge API", version="0.1.0")
council = IOTACouncil()

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

@app.post("/deliberate", response_model=DeliberationResponse)
async def deliberate(request: IntentRequest):
    try:
        result = await council.deliberate(request.intent)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/governance/deliberate")
async def governance_deliberate(request: GovernanceRequest):
    try:
        initial_state = {
            "evento": request.evento,
            "sistema": request.sistema,
            "cve": request.cve,
            "cvss": request.cvss,
            "iteration_count": 0,
            "historico": []
        }
        result = await governance_app.ainvoke(initial_state)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "COHERENT", "lambda2": 0.9984}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
