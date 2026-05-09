from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

from core.coherence.engine import coherence_engine
from core.lfir.lfir_parser import LFIRParser
from core.kym.verifier import KYMVerifier

app = FastAPI(title="ARKHE OS Nexus API", version="5003.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev; restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContractRequest(BaseModel):
    code: str

class VerifyRequest(BaseModel):
    did: str
    signature: str
    challenge: str

@app.get("/api/coherence")
def get_coherence():
    phi = coherence_engine.measure()
    return {"phi_c": phi, "timestamp": time.time(), "status": "stable" if phi >= 0.72 else "critical"}

@app.post("/api/contract/deploy")
def deploy_contract(req: ContractRequest):
    result = LFIRParser.deploy_contract(req.code)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.get("/api/kym/challenge")
def get_kym_challenge():
    return {"challenge": KYMVerifier.generate_challenge()}

@app.post("/api/kym/verify")
def verify_kym(req: VerifyRequest):
    return KYMVerifier.verify_identity(req.did, req.signature, req.challenge)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
