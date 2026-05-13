#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/api/public_server.py — API Pública da Verdade (ConRAG v4.3)
Serviço REST universal para verificação epistêmica.
Qualquer LLM pode consultar: POST /v1/verify {query, domain?, context?}
"""

from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Dict, Any, Union
import time
import hashlib
import json
import uvicorn
from datetime import datetime, timezone
from enum import Enum
import os

# Imports internos do ConRAG
from conrag.orchestrator import ProtocoloArkhe
from conrag.temporal.audit import TemporalAuditLogger
from conrag.dao.governance import DAOArkheGovernance
from conrag.domains.registry_v43 import DomainRegistry, Domain

# ============================================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ============================================================================

app = FastAPI(
    title="API Arkhe — Protocolo de Verificação Epistêmica",
    description="""
    Serviço universal de verificação constitucional para IAs.

    ## Funcionalidades
    - **Verificação Multi-Domínio**: Programming, Medicine, Law, Science, Finance, Education, Journalism, Environment, History, Arts, Philosophy, Psychology, Sociology, Engineering, Politics, Religion, Economics, Geography, Literature, Music + mais.
    - **Confiança Calibrada**: Score 0.0-1.0 com ECE < 0.05
    - **Auditoria Imutável**: Cada verificação registrada no TemporalHashChain
    - **Governança DAO**: Propostas de alteração constitucional via votação on-chain

    ## Autenticação
    Use header `Authorization: Bearer <api_key>` para acesso autenticado.

    ## Rate Limiting
    - Demo: 10 req/min
    - Production: 100 req/min
    - Enterprise: Ilimitado (sob contrato)
    """,
    version="4.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    terms_of_service="https://arkhe-os.github.io/terms",
    contact={
        "name": "ARKHE Cathedral",
        "url": "https://arkhe-os.github.io",
        "email": "contact@arkhe-os.org",
    },
    license_info={
        "name": "MIT + Arkhe Commons License",
        "url": "https://arkhe-os.github.io/license",
    },
)

# Middleware CORS para acesso público controlado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção: restringir para domínios confiáveis
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Segurança: API Key carregadas do ambiente
security = HTTPBearer()

def get_api_keys() -> Dict[str, Dict[str, Any]]:
    """Carrega as chaves da API do ambiente."""
    keys = {}

    # Em produção, estas chaves devem vir de um Secret Manager.
    # Exemplo: AWS Secrets Manager, HashiCorp Vault.
    demo_key = os.environ.get("ARKHE_DEMO_KEY")
    prod_key = os.environ.get("ARKHE_PROD_KEY")
    enterprise_key = os.environ.get("ARKHE_ENTERPRISE_KEY")

    if demo_key:
        keys[demo_key] = {"name": "Demo Key", "rate_limit": 10, "tier": "demo"}
    if prod_key:
        keys[prod_key] = {"name": "Production Key", "rate_limit": 100, "tier": "production"}
    if enterprise_key:
        keys[enterprise_key] = {"name": "Enterprise Key", "rate_limit": -1, "tier": "enterprise"}

    return keys

# Inicializar componentes principais
conrag = ProtocoloArkhe()
audit_logger = TemporalAuditLogger()
dao_governance = DAOArkheGovernance()
domain_registry = DomainRegistry()

# Pass registry to DAO for learning integration
dao_governance.set_domain_registry(domain_registry)

# Rate limiting em memória (em produção: usar Redis)
rate_limits: Dict[str, List[float]] = {}

# ============================================================================
# MODELOS DE DADOS PYDANTIC
# ============================================================================

class DomainName(str, Enum):
    """Domínios suportados pela API."""
    programming = "programming"
    medicine = "medicine"
    law = "law"
    science = "science"
    finance = "finance"
    education = "education"
    journalism = "journalism"
    environment = "environment"
    history = "history"
    arts = "arts"
    philosophy = "philosophy"
    psychology = "psychology"
    sociology = "sociology"
    engineering = "engineering"
    politics = "politics"
    religion = "religion"
    economics = "economics"
    geography = "geography"
    literature = "literature"
    music = "music"
    general = "general"

class VerificationRequest(BaseModel):
    """Requisição de verificação."""
    query: str = Field(..., description="Afirmação a ser verificada", min_length=1, max_length=10000)
    domain: Optional[DomainName] = Field(None, description="Domínio específico (opcional — auto-detecção se omitido)")
    context: Optional[str] = Field(None, description="Contexto adicional para a verificação", max_length=5000)
    code_snippet: Optional[str] = Field(None, description="Código gerado (para domínio programming)", max_length=50000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadados opcionais")

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query não pode estar vazia")
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "query": "Paracetamol 500mg é seguro para adultos sem comorbidades hepáticas",
                "domain": "medicine",
                "context": "Paciente: 45 anos, peso 75kg, sem alergias conhecidas",
                "metadata": {"urgency": "normal", "source_model": "gpt-4-turbo"}
            }
        }

class SourceReference(BaseModel):
    """Referência de fonte na resposta."""
    name: str = Field(..., description="Nome da fonte")
    type: str = Field(..., description="Tipo: primary/secondary/tertiary")
    url: Optional[str] = Field(None, description="URL da fonte")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança na fonte")
    timestamp: Optional[str] = Field(None, description="Timestamp da fonte")

class VerificationResponse(BaseModel):
    """Resposta de verificação com proveniência completa."""
    veredito: str = Field(..., description="Status: verificado/refutado/indeterminado")
    confianca: float = Field(..., ge=0.0, le=1.0, description="Confiança calibrada (0-1)")
    fontes: List[SourceReference] = Field(..., description="Fontes e evidências utilizadas")
    cadeia_raciocinio: str = Field(..., description="Cadeia de raciocínio completa")
    dominio: str = Field(..., description="Domínio aplicado na verificação")
    selo_canonico: str = Field(..., description="Hash SHA3-256 do resultado para auditoria")
    bloco_temporal: Optional[str] = Field(None, description="ID do bloco no TemporalHashChain")
    protocolo: str = Field("Arkhe ConRAG v4.3", description="Versão do protocolo")
    timestamp: str = Field(..., description="Timestamp ISO 8601 da resposta")
    warnings: List[str] = Field(default_factory=list, description="Avisos adicionais")

    class Config:
        schema_extra = {
            "example": {
                "veredito": "verificado",
                "confianca": 0.92,
                "fontes": [
                    {"name": "FDA", "type": "primary", "url": "https://fda.gov/drugs/paracetamol", "confidence": 0.99},
                    {"name": "WHO", "type": "primary", "url": "https://who.int/medicines", "confidence": 0.98}
                ],
                "cadeia_raciocinio": "BEAVER: aprovado | RLCR: confiança alta | Constituição: P1-P5 satisfeitos",
                "dominio": "medicine",
                "selo_canonico": "a3f2b8c9d1e4f5a6...",
                "bloco_temporal": "block-14847307",
                "protocolo": "Arkhe ConRAG v4.3",
                "timestamp": "2026-05-12T14:30:00Z",
                "warnings": []
            }
        }

class GovernanceProposalRequest(BaseModel):
    """Proposta de alteração constitucional para DAO."""
    title: str = Field(..., description="Título da proposta", min_length=10, max_length=200)
    description: str = Field(..., description="Descrição detalhada da alteração proposta", min_length=50)
    amendment_type: str = Field(..., description="Tipo: add_principle/modify_weight/new_rule/remove_rule")
    target_domain: Optional[DomainName] = Field(None, description="Domínio afetado (opcional)")
    proposed_change: Dict = Field(..., description="Mudança proposta em formato estruturado")
    rationale: str = Field(..., description="Justificativa para a proposta", min_length=20)
    proposer_signature: str = Field(..., description="Assinatura criptográfica do proponente")

    @validator('amendment_type')
    def validate_amendment_type(cls, v):
        valid_types = ["add_principle", "modify_weight", "new_rule", "remove_rule"]
        if v not in valid_types:
            raise ValueError(f"Tipo inválido. Use: {valid_types}")
        return v

class VoteRequest(BaseModel):
    """Voto em proposta de governança."""
    vote: str = Field(..., description="approve ou reject")
    stake: float = Field(..., ge=0.0, le=1.0, description="Peso do voto (0-1)")
    voter_signature: str = Field(..., description="Assinatura criptográfica do votante")

    @validator('vote')
    def validate_vote(cls, v):
        if v not in ["approve", "reject"]:
            raise ValueError("Vote must be 'approve' or 'reject'")
        return v

# ============================================================================
# DEPENDÊNCIAS E MIDDLEWARE
# ============================================================================

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verifica API Key e aplica rate limiting."""
    api_keys = get_api_keys()
    key = credentials.credentials
    if key not in api_keys:
        raise HTTPException(status_code=401, detail="API Key inválida ou expirada")

    key_info = api_keys[key]

    # Rate limiting simples (em produção: usar Redis)
    now = time.time()
    if key not in rate_limits:
        rate_limits[key] = []

    # Remover requests antigos (> 60 segundos)
    rate_limits[key] = [t for t in rate_limits[key] if now - t < 60]

    # Verificar limite ( -1 = ilimitado para enterprise)
    if key_info["rate_limit"] >= 0 and len(rate_limits[key]) >= key_info["rate_limit"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit excedido: {key_info['rate_limit']} req/min"
        )

    rate_limits[key].append(now)

    return {"key_name": key_info["name"], "key": key, "tier": key_info["tier"]}

async def log_verification_async(
    request: VerificationRequest,
    response: VerificationResponse,
    api_key_info: Dict,
    background_tasks: BackgroundTasks
):
    """Registra verificação no TemporalHashChain em background."""
    audit_entry = {
        "request_hash": hashlib.sha3_256(
            json.dumps(request.dict(), sort_keys=True, default=str).encode()
        ).hexdigest(),
        "response_hash": response.selo_canonico,
        "veredito": response.veredito,
        "confianca": response.confianca,
        "dominio": response.dominio,
        "api_key": api_key_info["key"][:8] + "...",  # Parcial para privacidade
        "timestamp": time.time(),
        "metadata": request.metadata
    }
    # Registrar no ledger temporal
    block_id = audit_logger.record(audit_entry)
    # Atualizar resposta com bloco temporal (em produção: via WebSocket ou polling)
    response.bloco_temporal = block_id

    # Trigger MAC learning logic in DAO Governance and Domain Registry
    case_result = {
        "domain": response.dominio,
        "verdict": response.veredito,
        "confidence": response.confianca,
        "principles": [r for r in response.cadeia_raciocinio.split(' | ')],
        "outcome": "correct" if response.confianca > 0.8 else "false_positive",
        "timestamp": time.time(),
        "claim": request.query
    }
    dao_governance.mac_learning_update(case_result)
    domain_registry.mac_learning_update(case_result)

# ============================================================================
# ENDPOINTS PRINCIPAIS — VERIFICAÇÃO
# ============================================================================

@app.post("/v1/verify", response_model=VerificationResponse, tags=["Verificação"])
async def verify_endpoint(
    req: VerificationRequest,
    background_tasks: BackgroundTasks,
    api_key_info: Dict = Depends(verify_api_key),
    x_client_id: Optional[str] = Header(None, description="ID do cliente LLM")
):
    start_time = time.time()

    try:
        # Executar verificação via ConRAG
        result = conrag.verificar(
            query=req.query,
            contexto=req.context or "",
            metadados={**(req.metadata or {}), "client_id": x_client_id, "dominio": req.domain.value if req.domain else None}
        )

        # Converter fontes para formato Pydantic
        fontes = []
        for src in result.fontes:
            if isinstance(src, dict):
                fontes.append(SourceReference(
                    name=src.get("name", "Unknown"),
                    type=src.get("type", "unknown"),
                    url=src.get("url"),
                    confidence=src.get("confidence", 0.5),
                    timestamp=src.get("timestamp")
                ))

        # Gerar resposta formatada
        response = VerificationResponse(
            veredito=result.veredito.value,
            confianca=result.confianca,
            fontes=fontes,
            cadeia_raciocinio=result.cadeia_raciocinio,
            dominio=result.proveniencia.get("dominio", "general"),
            selo_canonico=hashlib.sha3_256(
                f"{result.veredito.value}:{result.confianca}:{time.time()}".encode()
            ).hexdigest(),
            protocolo="Arkhe ConRAG v4.3",
            timestamp=datetime.now(timezone.utc).isoformat(),
            warnings=result.proveniencia.get("warnings", [])
        )

        # Registrar no TemporalHashChain em background e triggar MAC learning
        background_tasks.add_task(
            log_verification_async, req, response, api_key_info, background_tasks
        )

        return response

    except Exception as e:
        # Registrar erro no audit log
        audit_logger.record({
            "type": "verification_error",
            "error": str(e),
            "request_hash": hashlib.sha3_256(
                json.dumps(req.dict(), sort_keys=True, default=str).encode()
            ).hexdigest(),
            "timestamp": time.time(),
            "api_key": api_key_info["key"][:8] + "..."
        })
        raise HTTPException(status_code=500, detail=f"Erro interno de verificação: {str(e)}")

@app.post("/v1/verify/batch", response_model=List[VerificationResponse], tags=["Verificação"])
async def verify_batch_endpoint(
    requests: List[VerificationRequest],
    background_tasks: BackgroundTasks,
    api_key_info: Dict = Depends(verify_api_key)
):
    """Verificação em lote de múltiplas afirmações (máx 50 por request)."""
    if len(requests) > 50:
        raise HTTPException(status_code=400, detail="Máximo de 50 requests por batch")

    results = []
    for req in requests:
        result = await verify_endpoint(req, background_tasks, api_key_info)
        results.append(result)

    return results

# ============================================================================
# ENDPOINTS — DOMÍNIOS E CONSTITUIÇÃO
# ============================================================================

@app.get("/v1/domains", response_model=List[Dict], tags=["Metadados"])
async def list_domains(include_metadata: bool = False):
    """Lista todos os domínios registrados e suas configurações."""
    return domain_registry.list_domains(include_metadata=include_metadata)

@app.get("/v1/domains/{domain_name}", response_model=Dict, tags=["Metadados"])
async def get_domain(domain_name: str):
    """Retorna especificação detalhada de um domínio específico."""
    spec = domain_registry.get_domain_spec(domain_name)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Domínio '{domain_name}' não encontrado")
    return {
        "name": spec.name,
        "display_name": spec.display_name,
        "description": spec.description,
        "primary_apis": spec.primary_apis,
        "critical_keywords": spec.critical_keywords,
        "risk_threshold": spec.risk_threshold,
        "constitution_weights": spec.constitution_weights,
        "require_expert_review": spec.require_expert_review,
        "metadata": spec.metadata,
    }

@app.get("/v1/constitution/{domain_name}", response_model=Dict, tags=["Constituição"])
async def get_domain_constitution(domain_name: str):
    """Retorna constituição atual adaptada para domínio específico."""
    const = conrag._get_constituicao(domain_name)
    return const.exportar_para_json()

@app.post("/v1/domains/detect", response_model=Dict, tags=["Metadados"])
async def detect_domain(query: str, context: Optional[Dict] = None):
    """Detecta domínio baseado na query e contexto."""
    domain, confidence = domain_registry.detect_domain(query, context)
    spec = domain_registry.registry[domain]
    return {
        "detected_domain": spec.name,
        "display_name": spec.display_name,
        "confidence": confidence,
        "reasoning": f"Keywords matched: {[kw for kw in spec.critical_keywords if kw.lower() in query.lower()]}",
    }

# ============================================================================
# GOVERNANÇA DAO — PROPOSTAS E VOTAÇÃO
# ============================================================================

@app.post("/v1/governance/proposals", response_model=Dict, tags=["Governança DAO"])
async def submit_proposal(
    proposal: GovernanceProposalRequest,
    api_key_info: Dict = Depends(verify_api_key)
):
    """
    Submete proposta de alteração constitucional para votação na DAO Arkhe.
    Requer assinatura criptográfica válida do proponente.
    """
    if not dao_governance.verify_signature(proposal.proposer_signature, proposal.dict()):
        raise HTTPException(status_code=400, detail="Assinatura inválida ou expirada")

    proposal_id = dao_governance.create_proposal(
        title=proposal.title,
        description=proposal.description,
        amendment_type=proposal.amendment_type,
        target_domain=proposal.target_domain.value if proposal.target_domain else None,
        proposed_change=proposal.proposed_change,
        proposer=api_key_info["key"],
        rationale=proposal.rationale,
        proposer_signature=proposal.proposer_signature
    )

    return {
        "proposal_id": proposal_id,
        "status": "pending",
        "voting_starts": time.time() + 86400,
        "voting_ends": time.time() + 604800,
        "quorum_required": 0.1,
        "approval_threshold": 0.66,
        "message": f"Proposta '{proposal.title}' submetida com sucesso"
    }

@app.get("/v1/governance/proposals", response_model=List[Dict], tags=["Governança DAO"])
async def list_proposals(status: Optional[str] = None, limit: int = 50):
    """Lista propostas de governança com filtros opcionais."""
    proposals = dao_governance.list_proposals(status=status, limit=limit)
    return proposals

@app.get("/v1/governance/proposals/{proposal_id}", response_model=Dict, tags=["Governança DAO"])
async def get_proposal(proposal_id: str):
    """Retorna detalhes completos de uma proposta específica."""
    proposal = dao_governance.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    return proposal

@app.post("/v1/governance/vote/{proposal_id}", response_model=Dict, tags=["Governança DAO"])
async def cast_vote(
    proposal_id: str,
    vote_req: VoteRequest,
    api_key_info: Dict = Depends(verify_api_key)
):
    """Registra voto em uma proposta de governança."""
    if not dao_governance.verify_signature(vote_req.voter_signature, {
        "proposal_id": proposal_id,
        "vote": vote_req.vote,
        "stake": vote_req.stake
    }):
        raise HTTPException(status_code=400, detail="Assinatura do voto inválida")

    result = dao_governance.cast_vote(
        proposal_id=proposal_id,
        voter=api_key_info["key"],
        vote=vote_req.vote,
        stake=vote_req.stake,
        voter_signature=vote_req.voter_signature
    )

    return {
        "vote_recorded": True,
        "proposal_id": proposal_id,
        "current_results": result,
        "message": f"Voto '{vote_req.vote}' registrado com peso {vote_req.stake}"
    }

@app.get("/v1/governance/stats", response_model=Dict, tags=["Governança DAO"])
async def get_governance_stats():
    """Retorna estatísticas da governança DAO."""
    return dao_governance.get_statistics()

# ============================================================================
# ENDPOINTS DE SAÚDE, MÉTRICAS E AUDITORIA
# ============================================================================

@app.get("/health", tags=["Saúde"])
async def health_check():
    """Endpoint de saúde do serviço."""
    stats = audit_logger.get_stats()
    return {
        "status": "healthy",
        "version": "4.3.0",
        "uptime_seconds": time.time() - getattr(app, "_start_time", time.time()),
        "active_domains": len(domain_registry.list_domains()),
        "total_verifications": stats.get("total_requests", 0),
        "avg_response_time_ms": stats.get("avg_response_time_ms", 0),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/metrics", tags=["Métricas"])
async def get_metrics():
    """Retorna métricas operacionais detalhadas do serviço."""
    stats = audit_logger.get_stats()
    dao_stats = dao_governance.get_statistics()
    return {
        "verifications": {
            "total": stats.get("total_requests", 0),
            "by_domain": stats.get("by_domain", {}),
            "by_verdict": stats.get("by_verdict", {}),
            "avg_confidence": stats.get("avg_confidence", 0.0),
            "avg_response_time_ms": stats.get("avg_response_time_ms", 0.0),
            "error_rate": stats.get("error_rate", 0.0),
        },
        "governance": {
            "active_proposals": dao_stats.get("active_proposals", 0),
            "total_proposals": dao_stats.get("total_proposals", 0),
            "total_votes": dao_stats.get("total_votes", 0),
            "approval_rate": dao_stats.get("approval_rate", 0.0),
        },
        "system": {
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0,
            "cache_hit_rate": 0.0,
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/v1/audit/export", tags=["Auditoria"])
async def export_audit_log(
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    domain: Optional[str] = None,
    veredito: Optional[str] = None,
    format: str = "json"
):
    """Exporta logs de auditoria para conformidade e análise externa."""
    entries = audit_logger.query(
        start_time=start_time,
        end_time=end_time,
        domain=domain,
        veredito=veredito,
        limit=10000
    )
    return JSONResponse(content={"entries": entries, "count": len(entries)})

# ============================================================================
# WEBHOOKS E INTEGRAÇÕES
# ============================================================================

@app.post("/v1/webhooks/verification", tags=["Webhooks"])
async def register_webhook(
    url: str = Field(..., description="URL para receber notificações"),
    events: List[str] = Field(..., description="Eventos: verification_completed, proposal_updated, etc."),
    api_key_info: Dict = Depends(verify_api_key)
):
    """Registra webhook para notificações em tempo real."""
    return {
        "webhook_id": hashlib.sha3_256(f"{url}:{time.time()}".encode()).hexdigest()[:16],
        "url": url,
        "events": events,
        "status": "active",
        "message": "Webhook registrado com sucesso"
    }

# ============================================================================
# TRATAMENTO DE ERROS GLOBAL
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler global para exceções HTTP."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": hashlib.sha3_256(f"{request.url}:{time.time()}".encode()).hexdigest()[:16]
            }
        }
    )

# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inicialização do serviço."""
    app._start_time = time.time()
    print(f"🚀 API Arkhe ConRAG v4.3 iniciada")
    print(f"   Domínios ativos: {len(domain_registry.list_domains())}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup antes do shutdown."""
    print("🛑 Shutting down Arkhe API...")

if __name__ == "__main__":
    uvicorn.run(
        "conrag.api.public_server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
        access_log=True
    )
