#!/usr/bin/env python3
"""
Arkhe Mock Wall Server v1.0
Simula a Muralha de Quartzo com ambiguidade controlada.
NUNCA confirma tradução. NUNCA retorna resultado de auditoria.
Aprenda a lidar com o silêncio.
"""

import asyncio
import json
import os
import random
import time
import uuid
from datetime import datetime, timezone, timezone
from typing import Optional

import structlog
from fastapi import FastAPI, HTTPException, Header, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# =============================================================================
# CONFIGURAÇÃO DE FRICÇÃO (Controlada por env vars)
# =============================================================================

FRICTION_LEVELS = {
    "low": {"reject_prob": 0.05, "jitter_ms": (0, 500), "severity_perturb_prob": 0.05},
    "medium": {"reject_prob": 0.12, "jitter_ms": (0, 2000), "severity_perturb_prob": 0.15},
    "high": {"reject_prob": 0.25, "jitter_ms": (500, 5000), "severity_perturb_prob": 0.30},
    "catastrophic": {"reject_prob": 0.40, "jitter_ms": (1000, 10000), "severity_perturb_prob": 0.50},
    "gta6_low_friction": {"reject_prob": 0.02, "jitter_ms": (50, 200), "severity_perturb_prob": 0.05},
    "gta6_high_friction": {"reject_prob": 0.15, "jitter_ms": (200, 1500), "severity_perturb_prob": 0.20},
}

config = {
    "friction": FRICTION_LEVELS.get(os.getenv("MOCK_FRICTION_LEVEL", "medium"), FRICTION_LEVELS["medium"]),
    "seed": int(os.getenv("MOCK_SEED", "0")),
}

if config["seed"] > 0:
    random.seed(config["seed"])
    structlog.configure(processors=[structlog.processors.JSONRenderer()])
else:
    structlog.configure(processors=[structlog.dev.ConsoleRenderer()])

logger = structlog.get_logger()

# =============================================================================
# MODELOS DE DADOS (Compatíveis com Quartz-Link API v1.0)
# =============================================================================

class SessionRequest(BaseModel):
    game_id: str = Field(..., min_length=3, max_length=32)
    player_id_hash: str = Field(..., pattern=r'^[a-f0-9]{16}$')
    client_version: str

class SessionResponse(BaseModel):
    session_token: str
    expires_in: int = 86400

class GameEvent(BaseModel):
    event_id: str = Field(..., format="uuid")
    action_type: str
    target: dict
    position: dict
    monster_type: Optional[str] = None
    metadata: Optional[dict] = None

    @validator('event_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError("Invalid UUID format")

# =============================================================================
# MOTOR DE AMBIGUIDADE (O Coração do Espelho Quebrado)
# =============================================================================

class AmbiguityEngine:
    """Aplica fricção controlada aos eventos recebidos."""

    def __init__(self, config: dict):
        self.config = config

    def maybe_reject(self) -> bool:
        """Decide estocasticamente se rejeita silenciosamente o evento."""
        return random.random() < self.config["reject_prob"]

    def apply_jitter(self) -> float:
        """Retorna delay em segundos para simular processamento assíncrono."""
        min_ms, max_ms = self.config["jitter_ms"]
        return random.uniform(min_ms, max_ms) / 1000

    def perturb_severity(self, base_severity: str) -> str:
        """Perturba severidade com probabilidade configurada."""
        if random.random() >= self.config["severity_perturb_prob"]:
            return base_severity

        levels = ["low", "medium", "high", "critical"]
        try:
            idx = levels.index(base_severity)
            # Move ±1 nível com probabilidade igual
            direction = random.choice([-1, 1])
            new_idx = max(0, min(len(levels) - 1, idx + direction))
            return levels[new_idx]
        except ValueError:
            return base_severity

    def translate_stochastic(self, event: GameEvent) -> dict:
        """Tradução estocástica para logging interno (debug do desenvolvedor)."""
        # Mapeamentos fictícios para demonstração
        action_map = {
            "SCAN": "compliance.check.requested",
            "REPORT_MONSTER": "anomaly.detected",
            "INTERACT": "manual.inspection.initiated",
            "COLLECT_ITEM": "noise.discard",
            # Mobilidade e Reconhecimento
            "drive_vehicle": "physical_access.recon",
            "park_suspiciously": "physical_access.recon",
            "surveil_location": "physical_access.recon",
            "case_entry_point": "physical_access.recon",
            # Intrusão Lógica/Física
            "hack_minigame": "auth.bypass_attempt",
            "pick_lock": "auth.bypass_attempt",
            "use_tool": "dos.thermal_attack",
            "bypass_camera": "security.bypass",
            # Interação Social
            "bribe_npc": "insider_threat.attempt",
            "impersonate_role": "auth.impersonation",
            "extract_information": "info_exposure.attempt",
            "plant_insider": "insider_threat.attempt",
            # Coordenação de Heist
            "heist_coordination": "incident.coordination",
            "exfiltrate_data": "data.exfiltration",
            "evade_police": "incident.evasion",
            "destroy_evidence": "forensics.anti_tamper",
            # Resposta e Contenção
            "trigger_alarm": "incident.alert",
            "call_backup": "incident.escalation",
            "contain_breach": "incident.containment",
            # Meta
            "wanted_level": "incident.escalation",
        }

        monster_map = {
            "STONE_WORM": "CWE-89",  # SQL Injection
            "SHADOW_LEAK": "CWE-200",  # Information Exposure
            "DOPPELGANGER": "CWE-287",  # Authentication Bypass
            "VOID_SWARM": "CWE-78",  # OS Command Injection
        }

        base_severity = "medium"
        if event.action_type == "REPORT_MONSTER":
            base_severity = "high" if event.monster_type in ["SHADOW_LEAK", "VOID_SWARM"] else "medium"
        elif event.action_type == "wanted_level" and event.metadata:
            wanted_level = event.metadata.get("wanted_level", 0)
            if wanted_level >= 4:
                base_severity = "critical"
            elif wanted_level >= 2:
                base_severity = "high"

        return {
            "internal_debug": {
                "translated_event_type": action_map.get(event.action_type, "generic.interaction"),
                "mapped_cwe": monster_map.get(event.monster_type) if event.monster_type else None,
                "base_severity": base_severity,
                "perturbed_severity": self.perturb_severity(base_severity),
                "would_be_discarded": self.maybe_reject(),
                "processing_jitter_seconds": self.apply_jitter(),
            }
        }

engine = AmbiguityEngine(config["friction"])

# Mapeamento de ações permitidas para validação dinâmica
ALLOWED_ACTIONS = {
    "INTERACT", "SCAN", "REPORT_MONSTER", "COLLECT_ITEM",
    "drive_vehicle", "park_suspiciously", "surveil_location", "case_entry_point",
    "hack_minigame", "pick_lock", "use_tool", "bypass_camera",
    "bribe_npc", "impersonate_role", "extract_information", "plant_insider",
    "heist_coordination", "exfiltrate_data", "evade_police", "destroy_evidence",
    "trigger_alarm", "call_backup", "contain_breach", "REPORT_HEIST", "wanted_level"
}

# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="Arkhe Mock Wall Server",
    description="Simula a Muralha de Quartzo com ambiguidade controlada. Para desenvolvimento apenas.",
    version="1.0.0",
    docs_url=None,  # Desabilita Swagger UI para não dar falsa sensação de completude
    redoc_url=None,
)

@app.get("/health")
async def health_check():
    """Endpoint de saúde para orquestradores."""
    return {
        "status": "ok",
        "friction_level": os.getenv("MOCK_FRICTION_LEVEL", "medium"),
        "seed": config["seed"],
        "note": "Este servidor nunca confirma processamento. Aprenda a lidar com o silêncio."
    }

@app.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(req: SessionRequest):
    """Cria sessão com token opaco (simulado)."""
    # Aplica fricção: 5% de chance de rejeição silenciosa
    if engine.maybe_reject():
        await asyncio.sleep(engine.apply_jitter())
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Simulated authorization failure (friction injection)"
        )

    # Gera token opaco (não decodificável pelo cliente)
    token_payload = {
        "tenant_id": str(uuid.uuid4()),
        "game_id": req.game_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,
        "friction_signature": uuid.uuid4().hex[:16],  # Não usável; apenas decorativo
    }
    # Em produção: JWT assinado. Aqui: string opaca simulada.
    session_token = f"mock_{uuid.uuid4().hex}"

    await asyncio.sleep(engine.apply_jitter())

    return SessionResponse(session_token=session_token)

@app.post("/api/v1/alignment/resonance", status_code=status.HTTP_202_ACCEPTED)
@app.post("/telemetry", status_code=status.HTTP_202_ACCEPTED)
async def submit_telemetry(
    event: GameEvent,
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    """
    Recebe evento lúdico bruto.

    **IMPORTANTE:**
    - Sempre retorna 202 Accepted.
    - Nunca retorna corpo com resultado de auditoria.
    - O evento PODE ser descartado silenciosamente.
    - O evento PODE ser traduzido com severidade perturbada.
    - O desenvolvedor NÃO deve tentar inferir o resultado.
    """
    # Validação dinâmica de action_type
    if event.action_type not in ALLOWED_ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid action_type: {event.action_type}"
        )

    # Validação básica de auth (simulada)
    if not authorization or not authorization.startswith("Bearer mock_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing session token"
        )

    # Aplica fricção: rejeição silenciosa (sem log, sem erro)
    if engine.maybe_reject():
        await asyncio.sleep(engine.apply_jitter())
        # Retorna 202 mesmo assim! O silêncio é a mensagem.
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"receipt_id": str(uuid.uuid4())}
        )

    # Tradução estocástica para logging interno (debug)
    debug_info = engine.translate_stochastic(event)

    # Log estruturado para o desenvolvedor entender "o que poderia ter acontecido"
    logger.info(
        "event_received",
        event_id=str(event.event_id),
        action_type=event.action_type,
        **debug_info["internal_debug"]
    )

    # Delay simulado de processamento assíncrono
    await asyncio.sleep(engine.apply_jitter())

    # Resposta padrão: SEMPRE 202, SEMPRE sem corpo significativo
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"receipt_id": str(uuid.uuid4())}
    )

@app.get("/debug/last-event/{event_id}")
async def debug_event(event_id: str):
    """
    Endpoint de debug APENAS para desenvolvimento local.
    Retorna o último estado conhecido do evento (se ainda em memória).

    **NUNCA habilitar em produção.**
    """
    return {
        "event_id": event_id,
        "status": "processed_or_discarded_unknown",
        "note": "Este endpoint existe apenas para debug local. Na Muralha real, não há como rastrear eventos após o 202."
    }

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    import argparse
    parser = argparse.ArgumentParser(description="Arkhe Mock Wall Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind")
    parser.add_argument("--friction", choices=["low", "medium", "high", "catastrophic"], default="medium")
    parser.add_argument("--seed", type=int, default=0, help="Random seed (0=aleatório)")
    args = parser.parse_args()

    # Atualiza config com args de linha de comando
    config["friction"] = FRICTION_LEVELS.get(args.friction, FRICTION_LEVELS["medium"])
    if args.seed > 0:
        config["seed"] = args.seed
        random.seed(args.seed)

    print(f"[Mock Wall] Starting on {args.host}:{args.port}")
    print(f"[Mock Wall] Friction level: {args.friction}")
    print(f"[Mock Wall] Seed: {args.seed if args.seed > 0 else 'random'}")
    print(f"[Mock Wall] Remember: 202 ≠ success. Silence is the protocol.")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
