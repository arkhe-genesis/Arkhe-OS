import os
import asyncio
import structlog
from fastapi import FastAPI
from prometheus_client import start_http_server, Gauge
from arkhe_brain.subagents import SquadronAgent

# Configure logging
log = structlog.get_logger()

# Prometheus metrics
COHERENCE = Gauge('squadron_coherence_lambda2', 'Current coherence index λ2')
OPCODES_PROCESSED = Gauge('squadron_opcodes_total', 'Total opcodes processed by this squadron')

app = FastAPI(title="Arkhe(n) Squadron Agent")

@app.on_event("startup")
async def startup_event():
    squadron_name = os.getenv("SQUADRON_NAME", "unnamed-squadron")
    squadron_role = os.getenv("SQUADRON_ROLE", "generic-agent")
    allowed_opcodes = os.getenv("ALLOWED_OPCODES", "").split(",")
    metrics_port = int(os.getenv("METRICS_PORT", "9090"))

    # Start metrics server
    start_http_server(metrics_port)

    log.info("squadron_starting", name=squadron_name, role=squadron_role)

    # Initialize agent
    app.state.agent = SquadronAgent(
        agent_id=squadron_name,
        role=squadron_role,
        allowed_opcodes=allowed_opcodes
    )

    # Run agent loop in background
    asyncio.create_task(update_metrics(app.state.agent))
    asyncio.create_task(app.state.agent.run_loop())

async def update_metrics(agent):
    while True:
        COHERENCE.set(agent.lambda2)
        await asyncio.sleep(1)

@app.get("/health")
async def health():
    return {
        "status": "COHERENT" if app.state.agent.lambda2 > 0.9 else "DECOHERENT",
        "lambda2": app.state.agent.lambda2
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=50052)
