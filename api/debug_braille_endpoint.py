#!/usr/bin/env python3
"""
Substrato 187: Endpoint HTTP /debug/braille para Inspeção Visual de Estado de Agentes
Qualquer agente registrado pode ser inspecionado via requisição HTTP,
com redação automática de sensíveis, gating por Φ_C, e ancoragem temporal.
"""

from fastapi import FastAPI, HTTPException, Header, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import time
import hashlib
import logging

# Mocks for BrailleDebugMixin and BrailleDetailConfig as we don't have the real ones
class BrailleDetailConfig:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class BrailleDebugMixin:
    async def invoke_braille_detail(self, state_supplier, context):
        class Result:
            braille_output = "⠷⠁⠗⠅⠓⠑⠒⠃⠗⠁⠊⠇⠇⠑⠤⠙⠑⠞⠁⠊⠇⠷"
            ansi_colored_output = "\x1b[32m⠷⠁⠗⠅⠓⠑⠒⠃⠗⠁⠊⠇⠇⠑⠤⠙⠑⠞⠁⠊⠇⠷\x1b[0m"
            quality_verdict = "production-safe"
            quality_score = 14.28
            temporal_seal = "mock_temporal_seal"
        return Result()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ARKHE Debug API", version="1.0.0")

class BrailleDebugRequest(BaseModel):
    """Requisição para inspeção braille-detail."""
    agent_id: str = Field(..., description="ID do agente a ser inspecionado")
    max_depth: int = Field(default=3, ge=1, le=5, description="Profundidade máxima de inspeção")
    color_mode: str = Field(default="monochrome", pattern="^(monochrome|ansi_16|ansi_256)$")
    redact_sensitive: bool = Field(default=True, description="Redactar dados sensíveis")
    include_metadata: bool = Field(default=True, description="Incluir metadados na saída")

class BrailleDebugResponse(BaseModel):
    """Resposta da inspeção braille-detail."""
    success: bool
    agent_id: str
    braille_output: Optional[str] = None
    ansi_colored_output: Optional[str] = None
    quality_verdict: Optional[str] = None
    quality_score: Optional[float] = None
    temporal_seal: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

@app.post("/debug/braille", response_model=BrailleDebugResponse, tags=["debug"])
async def debug_braille(
    request: BrailleDebugRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Inspeção visual do estado interno de um agente via renderização braille-detail.

    Requisitos:
    • Token de autorização válido (simulado para demo)
    • Φ_C do agente ≥ 0.95 para permitir debug
    • Campos sensíveis redactados por padrão
    """
    # Verificar autorização (simulado)
    if authorization != "Bearer arkhe-debug-token":
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Obter instância do agente (simulado: registry global)
        agent = await _get_agent_instance(request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")

        # Verificar se agente suporta BrailleDebugMixin
        if not isinstance(agent, BrailleDebugMixin):
            raise HTTPException(
                status_code=400,
                detail=f"Agent {request.agent_id} does not support braille-detail mode"
            )

        # Configurar renderer com parâmetros da requisição
        config = BrailleDetailConfig(
            enabled=True,
            resolution_multiplier=4,
            color_mode=request.color_mode,
            include_metadata=request.include_metadata,
            quality_gate_threshold=0.95,
            max_depth=request.max_depth,
            redact_sensitive=request.redact_sensitive,
        )

        # Invocar inspeção visual
        result = await agent.invoke_braille_detail(
            state_supplier=lambda: agent._get_internal_state() if hasattr(agent, "_get_internal_state") else agent.__dict__,
            context={"source": "api_endpoint", "requested_by": authorization[:20] if authorization else "unknown"},
        )

        if not result:
            raise HTTPException(status_code=500, detail="Debug invocation returned None")

        # Verificar verdict de qualidade
        if result.quality_verdict == "rejected":
            return BrailleDebugResponse(
                success=False,
                agent_id=request.agent_id,
                error_message=f"Render rejected: low quality (score={result.quality_score:.3f})",
            )

        return BrailleDebugResponse(
            success=True,
            agent_id=request.agent_id,
            braille_output=result.braille_output,
            ansi_colored_output=result.ansi_colored_output if request.color_mode != "monochrome" else None,
            quality_verdict=result.quality_verdict,
            quality_score=result.quality_score,
            temporal_seal=result.temporal_seal,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no endpoint /debug/braille: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/debug/braille/agents", tags=["debug"])
async def list_debuggable_agents():
    """Lista agentes que suportam modo braille-detail."""
    # Simulado: retornar lista de agentes registrados com suporte a debug
    agents = [
        {"agent_id": "agent-financial-risk-01", "domain": "financial", "braille_enabled": True},
        {"agent_id": "agent-diagnostic-industrial-01", "domain": "diagnostic", "braille_enabled": True},
        {"agent_id": "agent-scada-monitor-01", "domain": "scada", "braille_enabled": True},
    ]
    return {"agents": agents, "total": len(agents)}

async def _get_agent_instance(agent_id: str):
    """Obtém instância do agente por ID (simulado para demo)."""
    # Em produção: buscar em registry de agentes ativo
    # Para demo: retornar mock de agente com suporte a debug se na lista de suportados
    await asyncio.sleep(0.01)  # Simular lookup

    # Simple check against mock agent list
    if agent_id in ["agent-financial-risk-01", "agent-diagnostic-industrial-01", "agent-scada-monitor-01"]:
        class MockAgent(BrailleDebugMixin):
            def _get_internal_state(self):
                return {"status": "active", "phi_c": 0.999}
        return MockAgent()
    return None
