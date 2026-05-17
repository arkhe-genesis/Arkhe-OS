#!/usr/bin/env python3
"""
Substrato 212: Canonical Tool Calling System.
Gerencia o ciclo de vida completo de chamadas de ferramentas por agentes Sentinel,
integrando todos os padrões de resiliência do Substrato 211 e as invariantes ARKHE.
"""

import asyncio, hashlib, json, time, logging, uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum, auto
from collections import deque, defaultdict
import torch
import numpy as np

logger = logging.getLogger(__name__)

# ── Estruturas de Dados ────────────────────────────────────
class ToolCallStatus(Enum):
    PENDING = auto()
    SUCCESS = auto()
    FAILED = auto()
    DEAD_LETTER = auto()
    CIRCUIT_OPEN = auto()
    RATE_LIMITED = auto()
    BULKHEAD_FULL = auto()

@dataclass
class ToolDefinition:
    """Definição canônica de uma ferramenta no registro Arkhe."""
    tool_id: str
    name: str
    description: str
    parameters_schema: Dict
    handler: Callable
    agent_owner: str                          # agente Sentinel responsável
    confidence_required: float = 0.8          # limiar de confiança para chamada
    token_cost_estimate: int = 10             # tokens consumidos por chamada
    max_concurrent: int = 2                   # bulkhead
    failure_threshold: int = 3                # circuit breaker
    idempotent: bool = True                   # se suporta chave idempotente
    pqc_sign_required: bool = True            # assinatura PQC na requisição

@dataclass
class ToolCallRequest:
    """Requisição imutável de chamada de ferramenta."""
    call_id: str
    tool_id: str
    parameters: Dict
    idempotency_key: Optional[str] = None
    agent_id: Optional[str] = None
    context_phi_c: float = 1.0
    pqc_signature: Optional[str] = None

@dataclass
class ToolCallResult:
    """Resultado de uma chamada de ferramenta."""
    call_id: str
    status: ToolCallStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    tokens_consumed: int = 0
    temporal_seal: Optional[str] = None

# Mocks para dependências ausentes
class AgentCircuitBreaker:
    def __init__(self, failure_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.failures: Dict[str, int] = defaultdict(int)

    def is_allowed(self, tool_id: str) -> bool:
        return self.failures[tool_id] < self.failure_threshold

    def record_failure(self, tool_id: str):
        self.failures[tool_id] += 1

class TokenBudgetPerAgent:
    def __init__(self, max_tokens: int = 10000):
        self.max_tokens = max_tokens
        self.used_tokens: Dict[str, int] = defaultdict(int)

    def consume(self, agent_id: str, tokens: int) -> bool:
        if self.used_tokens[agent_id] + tokens > self.max_tokens:
            return False
        self.used_tokens[agent_id] += tokens
        return True

class EscalationQueue:
    def __init__(self):
        self.queue: deque = deque()

    def enqueue(self, item: Dict, reason: str):
        self.queue.append({"item": item, "reason": reason, "timestamp": time.time()})

# ── Sistema Central de Tool Calling ────────────────────────
class CanonicalToolCallingSystem:
    """
    Orquestrador único para chamadas de ferramentas.
    Integra:
    - Circuit Breaker por ferramenta
    - Bulkhead (concurrency limit)
    - Idempotency Key (via δ‑mem e cache)
    - Rate Limiting por agente/ferramenta
    - Dead Letter Queue
    - PQC Signing
    - Auditing via TemporalChain
    - Tracing via ArkheObservability
    - δ‑mem para contexto de ferramenta (ex: última chamada)
    """

    def __init__(self, temporal=None, phi_bus=None, delta_mem=None,
                 observability=None, resilience_patterns=None):
        self.temporal = temporal
        self.phi_bus = phi_bus
        self.delta_mem = delta_mem
        self.observability = observability
        # Registro de ferramentas (Service Discovery)
        self.tool_registry: Dict[str, ToolDefinition] = {}
        # Estado de resiliência por ferramenta
        self.circuit_breakers: Dict[str, AgentCircuitBreaker] = {}
        self.bulkhead_counts: Dict[str, int] = defaultdict(int)
        self.rate_limiter: TokenBudgetPerAgent = TokenBudgetPerAgent()
        # Cache de idempotência (simples, em produção usaria δ‑mem)
        self.idempotency_store: Dict[str, ToolCallResult] = {}
        # Fila de cartas mortas
        self.dead_letter_queue: EscalationQueue = EscalationQueue()
        # Histórico para auditoria
        self.call_history: deque = deque(maxlen=10000)

    def register_tool(self, definition: ToolDefinition):
        """Registra uma ferramenta no sistema."""
        self.tool_registry[definition.tool_id] = definition
        # Inicializar disjuntor e bulkhead
        self.circuit_breakers[definition.tool_id] = AgentCircuitBreaker(
            failure_threshold=definition.failure_threshold)
        logger.info(f"🔧 Ferramenta '{definition.name}' registrada ({definition.tool_id})")

    async def invoke_tool(self, request: ToolCallRequest) -> ToolCallResult:
        """
        Ponto de entrada canônico para chamada de ferramenta.
        Executa todas as verificações de segurança e resiliência.
        """
        tool = self.tool_registry.get(request.tool_id)
        if not tool:
            return ToolCallResult(request.call_id, ToolCallStatus.FAILED, error="Tool not found")

        # 1. Verificação de confiança (Health Check)
        if request.context_phi_c < tool.confidence_required:
            return ToolCallResult(request.call_id, ToolCallStatus.FAILED,
                                  error=f"Confidence too low: {request.context_phi_c:.2f} < {tool.confidence_required}")

        # 2. Verificação de disjuntor
        if not self.circuit_breakers[tool.tool_id].is_allowed(tool.tool_id):
            return ToolCallResult(request.call_id, ToolCallStatus.CIRCUIT_OPEN,
                                  error="Circuit breaker open")

        # 3. Verificação de rate limiting (token budget do agente)
        agent_id = request.agent_id or "system"
        if not self.rate_limiter.consume(agent_id, tool.token_cost_estimate):
            return ToolCallResult(request.call_id, ToolCallStatus.RATE_LIMITED,
                                  error="Agent token budget exhausted")

        # 4. Bulkhead: controle de concorrência
        if self.bulkhead_counts[tool.tool_id] >= tool.max_concurrent:
            return ToolCallResult(request.call_id, ToolCallStatus.BULKHEAD_FULL,
                                  error="Bulkhead capacity reached")
        self.bulkhead_counts[tool.tool_id] += 1

        # 5. Verificação de idempotência (se fornecida chave)
        if tool.idempotent and request.idempotency_key:
            if request.idempotency_key in self.idempotency_store:
                logger.info(f"🔁 Idempotent hit: {request.idempotency_key}")
                self.bulkhead_counts[tool.tool_id] -= 1
                return self.idempotency_store[request.idempotency_key]

        # 6. Assinatura PQC (simulada)
        if tool.pqc_sign_required:
            # Gerar assinatura do payload (em produção usaria HSM)
            payload = json.dumps(request.parameters, sort_keys=True)
            request.pqc_signature = hashlib.sha3_256(payload.encode()).hexdigest()

        # 7. Execução real com tracing
        start = time.time()
        trace_span = None
        if self.observability:
            trace = self.observability.start_trace(request.call_id, "tool_call",
                                                   {"tool": tool.tool_id, "agent": agent_id})
            trace_span = True

        try:
            result = await tool.handler(request.parameters) if asyncio.iscoroutinefunction(tool.handler) else tool.handler(request.parameters)
            status = ToolCallStatus.SUCCESS
            error = None
            # Registrar sucesso no disjuntor (reset falhas)
            self.circuit_breakers[tool.tool_id].failures[tool.tool_id] = 0
        except Exception as e:
            result = None
            status = ToolCallStatus.FAILED
            error = str(e)
            # Registrar falha no disjuntor
            self.circuit_breakers[tool.tool_id].record_failure(tool.tool_id)
            # Se circuito abrir, enviar para Dead Letter Queue
            if not self.circuit_breakers[tool.tool_id].is_allowed(tool.tool_id):
                self.dead_letter_queue.enqueue({
                    "call_id": request.call_id,
                    "tool_id": tool.tool_id,
                    "parameters": request.parameters,
                    "error": error
                }, "circuit_open")
                status = ToolCallStatus.DEAD_LETTER

        latency = (time.time() - start) * 1000
        tokens = tool.token_cost_estimate
        self.bulkhead_counts[tool.tool_id] -= 1

        call_result = ToolCallResult(
            call_id=request.call_id,
            status=status,
            result=result,
            error=error,
            latency_ms=latency,
            tokens_consumed=tokens
        )

        # 8. Auditoria e armazenamento
        self.call_history.append(call_result)
        if self.temporal:
            seal = await self.temporal.anchor_event("tool_call_executed", {
                "call_id": request.call_id,
                "tool": tool.tool_id,
                "status": status.name,
                "latency_ms": latency
            })
            call_result.temporal_seal = seal

        # 9. Cache idempotente
        if tool.idempotent and request.idempotency_key:
            self.idempotency_store[request.idempotency_key] = call_result

        # 10. Escrita em δ‑mem (se disponível) para contexto da ferramenta
        if self.delta_mem and status == ToolCallStatus.SUCCESS:
            # Armazena um vetor de features simples no OSAM
            features = torch.tensor([hash(str(result)) % 1000, latency / 10, tokens], dtype=torch.float32)
            if hasattr(self.delta_mem, 'write_experience'):
                if asyncio.iscoroutinefunction(self.delta_mem.write_experience):
                    await self.delta_mem.write_experience("tool_use", features.unsqueeze(0))
                else:
                    self.delta_mem.write_experience("tool_use", features.unsqueeze(0))

        # 11. Métricas
        if self.phi_bus:
            await self.phi_bus.publish_metric("tool_call", {
                "tool": tool.tool_id,
                "status": status.name,
                "latency_ms": latency,
                "tokens": tokens
            })

        return call_result

    def get_tool_stats(self) -> Dict:
        """Estatísticas consolidadas das ferramentas."""
        return {
            "registered_tools": len(self.tool_registry),
            "circuit_open": sum(1 for cb in self.circuit_breakers.values() if not cb.is_allowed("irrelevant")),
            "dead_letters": len(self.dead_letter_queue.queue),
            "idempotent_keys_cached": len(self.idempotency_store),
            "bulkhead_usage": dict(self.bulkhead_counts)
        }
