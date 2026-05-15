from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, generate_latest
from .sidecar import ArkheSidecar
from .security import HybridSigner
from .config import load_config
import time, logging

logger = logging.getLogger(__name__)

# Sidecar global
sidecar: ArkheSidecar = None
hybrid_signer: HybridSigner = None

# Métricas
REQUEST_COUNT = Counter('arkhe_requests_total', 'Total requests', ['endpoint'])
REQUEST_LATENCY = Histogram('arkhe_request_latency_seconds', 'Request latency')

@asynccontextmanager
async def lifespan(app: FastAPI):
    global sidecar, hybrid_signer
    config = load_config()
    sidecar = ArkheSidecar(
        service_name=config.service_name,
        phi_bus_endpoint=config.phi_bus_endpoint,
        temporal_endpoint=config.temporal_endpoint,
        qbus_endpoint=config.qbus_endpoint,
        quantum_enabled=config.quantum_enabled,
    )
    await sidecar.connect()
    hybrid_signer = HybridSigner(
        pqc_algorithm=config.pqc_algorithm,
        quantum_witness_photons=config.quantum_witness_photons,
        temporal_chain=sidecar.temporal,
    )
    logger.info(f"✅ Serviço {config.service_name} iniciado")
    yield
    await sidecar.close()

app = FastAPI(title="Arkhe Service", version="v∞.Ω.196.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "ok", "phi_c": sidecar.get_local_phi_c() if sidecar else 0}

@app.get("/metrics")
async def metrics():
    return generate_latest()

@app.post("/action")
async def perform_action(request: Request):
    """Exemplo de endpoint de negócio com guardrails e ancoragem temporal."""
    start = time.time()
    data = await request.json()
    # Validar com Guardian local
    safe, reason = await sidecar.guardian.validate_action(data)
    if not safe:
        raise HTTPException(status_code=403, detail=reason)
    # Assinar ação com híbrido
    signature = await hybrid_signer.sign_message(
        message=str(data).encode(),
        metadata={"action": data.get("type", "unknown")}
    )
    # Ancorar na TemporalChain
    seal = await sidecar.temporal.anchor_event("service_action", {
        "payload_hash": hybrid_signer.hash_data(data),
        "signature": signature.combined_signature_hash[:16],
        "phi_c": sidecar.get_local_phi_c(),
    })
    REQUEST_COUNT.labels(endpoint="/action").inc()
    REQUEST_LATENCY.observe(time.time() - start)
    return {"status": "executed", "seal": seal}
