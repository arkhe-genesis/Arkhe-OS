# arkhe-saas-backend/main.py
"""Arkhe PoC SaaS Backend — FastAPI entrypoint."""
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent dir for consensus_engine.py import
sys.path.insert(0, sys.path.append(sys.path[0] + "/..") or "")

from routers import coherence, tenants


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🜏 Arkhe PoC SaaS starting up...")
    yield
    print("🜏 Shutting down Arkhe PoC SaaS...")


app = FastAPI(
    title="Arkhe PoC SaaS API",
    description="Proof-of-Coherence network management for multi-tenant Arkhe deployments",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenants.router)
app.include_router(coherence.router)


@app.get("/health")
def health_check():
    return {"status": "coherent", "version": "1.0.0"}
