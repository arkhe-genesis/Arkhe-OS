#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/api/server.py — API Pública da Verdade (ConRAG v4.1)
Serviço REST/GraphQL para verificação epistêmica universal.
Qualquer LLM pode consultar: "Esta afirmação é verificável?"
"""

from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import time
import hashlib
import json
import uvicorn

# Imports internos
from conrag.orchestrator import ProtocoloArkhe
from conrag.temporal.audit import TemporalAuditLogger
from conrag.dao.governance import DAOArkheGovernance
from conrag.domains import DOMAIN_REGISTRY

app = FastAPI(
    title="API Arkhe — Protocolo de Verificação Epistêmica",
    description="Serviço universal de verificação constitucional para IAs. "
                "Qualquer modelo pode consultar: 'Esta afirmação é verificável?'",
    version="4.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Middleware CORS para acesso público
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção: restringir para domínios confiáveis
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Segurança: API Key simples (em produção: OAuth2/JWT)
security = HTTPBearer()
API_KEYS = {
    "sk-arkhe-demo": {"name": "Demo Key", "rate_limit": 10},  # 10 req/min
    "sk-arkhe-prod": {"name": "Production Key", "rate_limit": 100},
}

# Inicializar componentes
protocolo = ProtocoloArkhe()
audit_logger = TemporalAuditLogger()
dao_governance = DAOArkheGovernance()

# Rate limiting simples em memória
rate_limits: Dict[str, List[float]] = {}

# ============================================================================
# MODELOS DE DADOS
# ============================================================================

class VerificationRequest(BaseModel):
    """Requisição de verificação."""
    query: str = Field(..., description="Afirmação a ser verificada", min_length=1, max_length=5000)
    domain: str = Field("general", description="Domínio: programming/medicine/law/science/general")
    context: Optional[str] = Field(None, description="Contexto adicional para a verificação")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadados opcionais")

    @validator('domain')
    def validate_domain(cls, v):
        valid_domains = [d.name.lower() for d in DOMAIN_REGISTRY.keys()]
        if v not in valid_domains:
            raise ValueError(f"Domínio inválido. Use: {valid_domains}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Paracetamol é seguro para crianças com dosagem de 15mg/kg",
                "domain": "medicine",
                "context": "Paciente: 8 anos, 25kg, sem comorbidades",
                "metadata": {"urgency": "high", "source_model": "gpt-4"}
            }
        }

class VerificationResponse(BaseModel):
    """Resposta de verificação com proveniência completa."""
    veredito: str = Field(..., description="Status: verificado/refutado/indeterminado")
    confianca: float = Field(..., ge=0.0, le=1.0, description="Confiança calibrada (0-1)")
    fontes: List[Dict] = Field(..., description="Fontes e evidências utilizadas")
    cadeia_raciocinio: str = Field(..., description="Cadeia de raciocínio completa")
    dominio: str = Field(..., description="Domínio aplicado na verificação")
    selo_canonico: str = Field(..., description="Hash SHA3-256 do resultado para auditoria")
    bloco_temporal: Optional[str] = Field(None, description="ID do bloco no TemporalHashChain")
    protocolo: str = Field("Arkhe ConRAG v4.1", description="Versão do protocolo")
    timestamp: str = Field(..., description="Timestamp ISO 8601 da resposta")

    class Config:
        json_schema_extra = {
            "example": {
                "veredito": "verificado",
                "confianca": 0.92,
                "fontes": [
                    {"source": "FDA", "type": "primary", "url": "https://fda.gov/drugs/paracetamol"},
                    {"source": "WHO", "type": "primary", "url": "https://who.int/medicines"}
                ],
                "cadeia_raciocinio": "BEAVER: aprovado | RLCR: confiança alta | Constituição: P1-P5 satisfeitos",
                "dominio": "medicine",
                "selo_canonico": "a3f2b8c9d1e4f5a6...",
                "bloco_temporal": "block-14847307",
                "protocolo": "Arkhe ConRAG v4.1",
                "timestamp": "2026-05-12T14:30:00Z"
            }
        }

class GovernanceProposal(BaseModel):
    """Proposta de alteração constitucional para DAO."""
    title: str = Field(..., description="Título da proposta")
    description: str = Field(..., description="Descrição detalhada da alteração proposta")
    amendment_type: str = Field(..., description="Tipo: add_principle/modify_weight/new_rule")
    target_domain: Optional[str] = Field(None, description="Domínio afetado (opcional)")
    proposed_change: Dict = Field(..., description="Mudança proposta em formato estruturado")
    proposer_signature: str = Field(..., description="Assinatura criptográfica do proponente")

# ============================================================================
# DEPENDÊNCIAS E MIDDLEWARE
# ============================================================================

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verifica API Key e aplica rate limiting."""
    key = credentials.credentials
    if key not in API_KEYS:
        raise HTTPException(status_code=401, detail="API Key inválida")

    # Rate limiting simples (em produção: usar Redis)
    now = time.time()
    key_info = API_KEYS[key]
    if key not in rate_limits:
        rate_limits[key] = []

    # Remover requests antigos (> 60 segundos)
    rate_limits[key] = [t for t in rate_limits[key] if now - t < 60]

    if len(rate_limits[key]) >= key_info["rate_limit"]:
        raise HTTPException(status_code=429, detail="Rate limit excedido")

    rate_limits[key].append(now)

    return {"key_name": key_info["name"], "key": key}

async def log_to_temporal_chain(
    request: VerificationRequest,
    response: VerificationResponse,
    api_key_info: Dict,
    background_tasks: BackgroundTasks
):
    """Registra verificação no TemporalHashChain em background."""
    audit_entry = {
        "request_hash": hashlib.sha3_256(
            json.dumps(request.dict(), sort_keys=True).encode()
        ).hexdigest(),
        "response_hash": response.selo_canonico,
        "veredito": response.veredito,
        "confianca": response.confianca,
        "dominio": response.dominio,
        "api_key": api_key_info["key"][:8] + "...",  # Parcial para privacidade
        "timestamp": time.time(),
        "metadata": request.metadata
    }
    # Registrar no ledger temporal (simulado)
    block_id = audit_logger.record(audit_entry)
    response.bloco_temporal = block_id

# ============================================================================
# ENDPOINTS PRINCIPAIS
# ============================================================================

@app.post("/v1/verify", response_model=VerificationResponse, tags=["Verificação"])
async def verify_endpoint(
    req: VerificationRequest,
    background_tasks: BackgroundTasks,
    api_key_info: Dict = Depends(verify_api_key)
):
    """
    Endpoint principal: verifica uma afirmação via Protocolo Arkhe.

    Retorna veredito com confiança calibrada, fontes e cadeia de raciocínio.
    Cada verificação é registrada no TemporalHashChain para auditoria imutável.
    """
    start_time = time.time()

    try:
        # Executar verificação via ProtocoloArkhe
        result = protocolo.verificar(
            query=req.query,
            dominio=req.domain,
            contexto=req.context or "",
            metadados=req.metadata
        )

        # Gerar resposta formatada
        response = VerificationResponse(
            veredito=result["veredito"],
            confianca=result["confianca"],
            fontes=result["fontes"],
            cadeia_raciocinio=result["raciocinio"],
            dominio=req.domain,
            selo_canonico=hashlib.sha3_256(
                f"{result['veredito']}:{result['confianca']}:{time.time()}".encode()
            ).hexdigest(),
            protocolo="Arkhe ConRAG v4.1",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )

        # Registrar no TemporalHashChain em background
        background_tasks.add_task(
            log_to_temporal_chain, req, response, api_key_info
        )

        return response

    except Exception as e:
        # Registrar erro no audit log
        audit_logger.record({
            "type": "verification_error",
            "error": str(e),
            "request_hash": hashlib.sha3_256(
                json.dumps(req.dict(), sort_keys=True).encode()
            ).hexdigest(),
            "timestamp": time.time()
        })
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/v1/verify/batch", response_model=List[VerificationResponse], tags=["Verificação"])
async def verify_batch_endpoint(
    requests: List[VerificationRequest],
    background_tasks: BackgroundTasks,
    api_key_info: Dict = Depends(verify_api_key)
):
    """Verificação em lote de múltiplas afirmações."""
    if len(requests) > 50:
        raise HTTPException(status_code=400, detail="Máximo de 50 requests por batch")

    results = []
    for req in requests:
        result = await verify_endpoint(req, background_tasks, api_key_info)
        results.append(result)

    return results

@app.get("/v1/domains", tags=["Metadados"])
async def list_domains():
    """Lista domínios suportados e suas configurações."""
    return {
        "domains": {
            d.name: {
                "description": cfg.description,
                "primary_apis": cfg.primary_apis,
                "risk_threshold": cfg.risk_threshold,
                "constitution_weights": cfg.constitution_weights
            }
            for d, cfg in DOMAIN_REGISTRY.items()
        }
    }

@app.get("/v1/constitution/{domain}", tags=["Constituição"])
async def get_constitution(domain: str):
    """Retorna constituição atual para um domínio específico."""
    from conrag.domains.constitutions import DomainConstitution
    const = DomainConstitution(domain)
    return {
        "domain": domain,
        "principles": [
            {
                "id": p.id,
                "statement": p.statement,
                "weight": p.domain_weights.get(domain, 0.2),
                "description": p.description
            }
            for p in const.principles
        ],
        "hash": hashlib.sha3_256(
            json.dumps([p.__dict__ for p in const.principles], sort_keys=True).encode()
        ).hexdigest()[:16]
    }

# ============================================================================
# GOVERNANÇA DAO — PROPOSTAS E VOTAÇÃO
# ============================================================================

@app.post("/v1/governance/proposals", tags=["Governança DAO"])
async def submit_proposal(
    proposal: GovernanceProposal,
    api_key_info: Dict = Depends(verify_api_key)
):
    """
    Submete proposta de alteração constitucional para votação na DAO Arkhe.
    Requer assinatura criptográfica válida do proponente.
    """
    # Verificar assinatura (simulado)
    if not dao_governance.verify_signature(proposal.proposer_signature, proposal.dict()):
        raise HTTPException(status_code=400, detail="Assinatura inválida")

    # Criar proposta no ledger de governança
    proposal_id = dao_governance.create_proposal(
        title=proposal.title,
        description=proposal.description,
        amendment_type=proposal.amendment_type,
        target_domain=proposal.target_domain,
        proposed_change=proposal.proposed_change,
        proposer=api_key_info["key"]
    )

    return {
        "proposal_id": proposal_id,
        "status": "pending",
        "voting_starts": time.time() + 86400,  # 24h para votação
        "voting_ends": time.time() + 604800,    # 7 dias de votação
        "quorum_required": 0.1,  # 10% dos stakeholders
        "approval_threshold": 0.66  # 2/3 para aprovação
    }

@app.get("/v1/governance/proposals/{proposal_id}", tags=["Governança DAO"])
async def get_proposal(proposal_id: str):
    """Retorna status de uma proposta de governança."""
    proposal = dao_governance.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    return proposal

from fastapi import Body

class VoteRequest(BaseModel):
    vote: str
    stake: float = Field(..., ge=0.0, le=1.0, description="Peso do voto (0-1)")
    voter_signature: str

@app.post("/v1/governance/vote/{proposal_id}", tags=["Governança DAO"])
async def cast_vote(
    proposal_id: str,
    vote_req: VoteRequest = Body(...),
    api_key_info: Dict = Depends(verify_api_key)
):
    """Registra voto em uma proposta de governança."""
    if not dao_governance.verify_signature(vote_req.voter_signature, {"vote": vote_req.vote, "stake": vote_req.stake}):
        raise HTTPException(status_code=400, detail="Assinatura do voto inválida")

    result = dao_governance.cast_vote(
        proposal_id=proposal_id,
        voter=api_key_info["key"],
        vote=vote_req.vote,
        stake=vote_req.stake
    )

    return {
        "vote_recorded": True,
        "proposal_id": proposal_id,
        "current_results": result
    }

# ============================================================================
# ENDPOINTS DE SAÚDE E MÉTRICAS
# ============================================================================

@app.get("/health", tags=["Saúde"])
async def health_check():
    """Endpoint de saúde do serviço."""
    return {
        "status": "healthy",
        "version": "4.1.0",
        "uptime_seconds": time.time() - getattr(app, "_start_time", time.time()),
        "active_domains": list(DOMAIN_REGISTRY.keys()),
        "total_verifications": audit_logger.get_stats().get("total_requests", 0),
        "avg_response_time_ms": audit_logger.get_stats().get("avg_response_time_ms", 0),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

@app.get("/metrics", tags=["Métricas"])
async def get_metrics():
    """Retorna métricas operacionais do serviço."""
    stats = audit_logger.get_stats()
    return {
        "total_requests": stats.get("total_requests", 0),
        "verifications_by_domain": stats.get("by_domain", {}),
        "verifications_by_verdict": stats.get("by_verdict", {}),
        "avg_confidence": stats.get("avg_confidence", 0.0),
        "avg_response_time_ms": stats.get("avg_response_time_ms", 0.0),
        "error_rate": stats.get("error_rate", 0.0),
        "dao_active_proposals": dao_governance.get_active_proposals_count(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inicialização do serviço."""
    app._start_time = time.time()
    print(f"🚀 API Arkhe ConRAG v4.1 iniciada")
    print(f"   Domínios ativos: {[d.name for d in DOMAIN_REGISTRY]}")
    print(f"   Docs: http://localhost:8080/docs")
    print(f"   Health: http://localhost:8080/health")

if __name__ == "__main__":
    uvicorn.run(
        "conrag.api.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
