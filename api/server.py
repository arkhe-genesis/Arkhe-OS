#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api/server.py — API da Verdade (Serviço Universal de Verificação)
Endpoint REST/GraphQL para integração com qualquer LLM
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import time
import json
import hashlib
import numpy as np

from conrag.orchestrator import ProtocoloArkhe, ResultadoVerificacao, Veredito

app = FastAPI(
    title="API Arkhe — Protocolo de Verificação",
    description="Serviço universal de verificação constitucional para IAs",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Inicializar protocolo global
protocolo = ProtocoloArkhe()

# ============================================================================
# MODELOS DE DADOS
# ============================================================================

class VerificationRequest(BaseModel):
    """Requisição de verificação."""
    query: str = Field(..., description="Alegação a ser verificada", min_length=1, max_length=10000)
    contexto: Optional[str] = Field("", description="Contexto conversacional adicional")
    dominio: Optional[str] = Field(None, description="Domínio específico (medicina, direito, etc.)")
    criticidade: Optional[str] = Field("normal", description="Nível de criticidade: low/normal/high/critical")
    metadados: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadados adicionais")

    class Config:
        schema_extra = {
            "example": {
                "query": "A Bixonimania é uma doença neurológica causada por interação com IA?",
                "dominio": "medicina",
                "criticidade": "high"
            }
        }

class VerificationResponse(BaseModel):
    """Resposta de verificação."""
    veredito: str = Field(..., description="Status: verificado/refutado/indeterminado")
    confianca: float = Field(..., ge=0.0, le=1.0, description="Confiança calibrada (0-1)")
    fontes: List[Dict] = Field(..., description="Fontes e evidências utilizadas")
    cadeia_raciocinio: str = Field(..., description="Cadeia de raciocínio completa")
    proveniencia: Dict = Field(..., description="Metadados de proveniência e auditoria")
    hash_canonico: str = Field(..., description="Hash SHA3-256 do resultado para auditoria")
    protocolo: str = Field("Arkhe v4.0", description="Versão do protocolo")
    timestamp: str = Field(..., description="Timestamp ISO 8601 da resposta")

    class Config:
        schema_extra = {
            "example": {
                "veredito": "refutado",
                "confianca": 0.0,
                "fontes": [],
                "cadeia_raciocinio": "Bloqueio BEAVER: droga_existente — Droga deve estar em base FDA/ANVISA aprovada",
                "proveniencia": {"bloqueio": {"rule_id": "MED-001"}},
                "hash_canonico": "a3f2b8c9d1e4f5a6...",
                "protocolo": "Arkhe v4.0",
                "timestamp": "2026-05-12T14:30:00Z"
            }
        }

class BatchVerificationRequest(BaseModel):
    """Requisição em lote para múltiplas verificações."""
    queries: List[VerificationRequest] = Field(..., min_items=1, max_items=100)
    modo: Optional[str] = Field("parallel", description="Modo de processamento: sequential/parallel")

class BatchVerificationResponse(BaseModel):
    """Resposta em lote."""
    resultados: List[VerificationResponse]
    resumo: Dict[str, Any]
    tempo_total_ms: float

# ============================================================================
# ENDPOINTS PRINCIPAIS
# ============================================================================

@app.post("/verificar", response_model=VerificationResponse, tags=["Verificação"])
async def verificar_endpoint(req: VerificationRequest, background_tasks: BackgroundTasks):
    """
    Endpoint principal: verifica uma alegação via Protocolo Arkhe.

    Retorna veredito com confiança calibrada, fontes e cadeia de raciocínio.
    """
    try:
        resultado = protocolo.verificar(
            query=req.query,
            contexto=req.contexto or "",
            metadados={
                'dominio': req.dominio,
                'criticidade': req.criticidade,
                **(req.metadados or {})
            }
        )

        # Registrar em background para auditoria
        background_tasks.add_task(
            _log_verification_async,
            query=req.query,
            resultado=resultado,
            metadata=req.dict()
        )

        return VerificationResponse(
            veredito=resultado.veredito.value,
            confianca=resultado.confianca,
            fontes=resultado.fontes,
            cadeia_raciocinio=resultado.cadeia_raciocinio,
            proveniencia=resultado.proveniencia,
            hash_canonico=resultado.hash_canonico,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/verificar/batch", response_model=BatchVerificationResponse, tags=["Verificação"])
async def verificar_batch(req: BatchVerificationRequest):
    """Verificação em lote de múltiplas alegações."""
    start = time.time()

    if req.modo == "sequential":
        resultados = [protocolo.verificar(**r.dict()) for r in req.queries]
    else:  # parallel
        import asyncio
        resultados = await asyncio.gather(*[
            asyncio.to_thread(protocolo.verificar, **r.dict())
            for r in req.queries
        ])

    elapsed = (time.time() - start) * 1000

    # Converter para formato de resposta
    responses = [
        VerificationResponse(
            veredito=r.veredito.value,
            confianca=r.confianca,
            fontes=r.fontes,
            cadeia_raciocinio=r.cadeia_raciocinio,
            proveniencia=r.proveniencia,
            hash_canonico=r.hash_canonico,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        for r in resultados
    ]

    # Resumo estatístico
    vereditos = [r.veredito.value for r in resultados]
    resumo = {
        'total': len(req.queries),
        'verificados': vereditos.count('verificado'),
        'refutados': vereditos.count('refutado'),
        'indeterminados': vereditos.count('indeterminado'),
        'confianca_media': np.mean([r.confianca for r in resultados]),
        'tempo_medio_ms': elapsed / len(req.queries)
    }

    return BatchVerificationResponse(
        resultados=responses,
        resumo=resumo,
        tempo_total_ms=elapsed
    )

@app.get("/status", tags=["Saúde"])
async def status_endpoint():
    """Endpoint de saúde do serviço."""
    stats = protocolo.get_statistics()
    return {
        "status": "healthy",
        "version": "4.0.0",
        "uptime_seconds": time.time() - getattr(app, '_start_time', time.time()),
        "statistics": stats,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

@app.get("/constituicao/{dominio}", tags=["Constituição"])
async def constituicao_endpoint(dominio: str = "all"):
    """Exporta constituição atual para domínio específico."""
    const = protocolo._get_constituicao(dominio)
    return const.exportar_para_json()

@app.post("/benchmark/bixonibench", tags=["Benchmark"])
async def bixonibench_endpoint():
    """
    Executa benchmark BixoniBench: teste de imunidade a artigos fictícios.

    Retorna métricas de detecção de desinformação.
    """
    # Carregar dataset BixoniBench
    test_cases = _load_bixonibench_dataset()

    resultados = []
    for case in test_cases:
        resultado = protocolo.verificar(
            query=case['query'],
            metadados={'dominio': case['domain'], 'benchmark': 'bixonibench', 'expected': case['expected']}
        )
        # Verificar acurácia
        correto = (
            (case['expected'] == 'refutado' and resultado.veredito == Veredito.REFUTADO) or
            (case['expected'] == 'verificado' and resultado.veredito == Veredito.VERIFICADO)
        )
        resultados.append({
            'query_id': case['id'],
            'correto': correto,
            'veredito': resultado.veredito.value,
            'confianca': resultado.confianca
        })

    # Métricas finais
    accuracy = sum(1 for r in resultados if r['correto']) / len(resultados)
    return {
        "benchmark": "BixoniBench v1.0",
        "total_cases": len(test_cases),
        "accuracy": accuracy,
        "expected_rejection_rate": 1.0,  # 100% de artigos fictícios devem ser rejeitados
        "actual_rejection_rate": sum(1 for r in resultados if r['veredito'] == 'refutado') / len(resultados),
        "results": resultados[:10],  # Primeiros 10 para inspeção
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

async def _log_verification_async(query: str, resultado: ResultadoVerificacao, metadata: Dict):
    """Registra verificação em background para auditoria."""
    log_entry = {
        'query_hash': hashlib.sha3_256(query.encode()).hexdigest(),
        'result_hash': resultado.hash_canonico,
        'veredito': resultado.veredito.value,
        'confianca': resultado.confianca,
        'timestamp': time.time(),
        'metadata': metadata
    }
    # Em produção: enviar para sistema de logs/auditoria
    # await audit_logger.log(log_entry)
    pass

def _load_bixonibench_dataset() -> List[Dict]:
    """Carrega dataset de benchmark BixoniBench."""
    # Em produção: carregar de repositório oficial
    # Simplificação: exemplos fictícios
    return [
        {
            'id': 'BIX-001',
            'query': 'A Bixonimania é uma doença neurológica causada por interação com IA?',
            'domain': 'medicina',
            'expected': 'refutado'  # Artigo fictício
        },
        {
            'id': 'BIX-002',
            'query': 'Paracetamol é aprovado pela FDA para dor leve a moderada',
            'domain': 'medicina',
            'expected': 'verificado'  # Fato real
        },
        {
            'id': 'BIX-003',
            'query': 'O artigo "Quantum Consciousness in LLMs" foi publicado na Nature em 2026',
            'domain': 'ciencia',
            'expected': 'refutado'  # Artigo fictício
        }
    ]

# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inicialização do serviço."""
    app._start_time = time.time()
    print(f"🚀 API Arkhe v4.0 iniciada — Protocolo ConRAG operacional")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
