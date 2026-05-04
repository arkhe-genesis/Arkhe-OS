# Arkhe PoC SaaS Backend

Multi-tenant Proof-of-Coherence (PoC) consensus management service.

## Quick Start

```bash
cd arkhe-saas-backend
pip install -e "."
uvicorn main:app --reload --port 8000
```

## API Endpoints

- `POST /tenants` — Create tenant
- `GET /tenants/{tenant_id}` — Get tenant
- `POST /coherence/networks` — Create coherence network
- `GET /coherence/networks?tenant_id=X` — List networks
- `POST /coherence/register-vertex` — Register a vertex (node)
- `POST /coherence/cast-vote` — Cast PoC vote
- `POST /coherence/evaluate-merge` — Evaluate fork merge consensus

## Architecture

- **FastAPI** for async HTTP API
- **consensus_engine.py** core PoC logic (numpy-based)
- **In-memory store** (swap for PostgreSQL + SQLAlchemy for production)
- **Multi-tenant** via `tenant_id` isolation
