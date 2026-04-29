import asyncio
from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from arkhe_os.api.v1.endpoints import (
    qe_compass, simulations, resonance, analog_observer,
    sato, crystal_brain, planetary, auth, cosmic_consciousness
)
from arkhe_os.api.graphql import schema
from arkhe_os.api.websocket.coherence_stream import websocket_coherence_handler
from arkhe_os.core.scaffold import ScaffoldState
from arkhe_os.middleware.logging import logging_middleware
from arkhe_os.middleware.errors import global_exception_handler, http_exception_handler
from arkhe_os.middleware.rate_limit import limiter
from arkhe_os.services.tasks import optimize_infrastructure_task
from arkhe_os.config.settings import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# State initialization
scaffold = ScaffoldState()
app.state.scaffold = scaffold

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(logging_middleware)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Routers
graphql_app = GraphQLRouter(schema)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(qe_compass.router, prefix=settings.API_V1_STR)
app.include_router(simulations.router, prefix=settings.API_V1_STR)
app.include_router(resonance.router, prefix=settings.API_V1_STR)
app.include_router(analog_observer.router, prefix=settings.API_V1_STR)
app.include_router(sato.router, prefix=settings.API_V1_STR)
app.include_router(crystal_brain.router, prefix=settings.API_V1_STR)
app.include_router(planetary.router, prefix=settings.API_V1_STR)
app.include_router(cosmic_consciousness.router, prefix=settings.API_V1_STR)
app.include_router(graphql_app, prefix="/graphql", tags=["GraphQL"])

# Overrides for dependencies that might be defined as placeholders
app.dependency_overrides[qe_compass.get_scaffold_state] = lambda: scaffold
app.dependency_overrides[planetary.get_scaffold_singleton] = lambda: scaffold

# WebSocket
@app.websocket("/ws/coherence")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_coherence_handler(websocket, scaffold)

@app.on_event("startup")
async def startup_event():
    # Start background auto-optimization
    asyncio.create_task(optimize_infrastructure_task(scaffold))

@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "coherence_M": round(scaffold.coherence_M, 4),
        "status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
