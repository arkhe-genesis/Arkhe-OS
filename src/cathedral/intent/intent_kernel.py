#!/usr/bin/env python3
"""
src/cathedral/intent/intent_kernel.py
==========================================================
Protótipo do Kernel de Intenção (FS-190 & FS-192.1)
Bypassa HTML/DOM/Click. Compila IntentGraph/JSON-LD → Ação Direta.
Arkhe(n) Framework v3.0 — Catedral Arkhe, 2026.
"""

import hashlib
import time
import json
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum, auto

class ValidationLayer(Enum):
    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    PRAGMATIC = "pragmatic"
    CAUSAL = "causal"

@dataclass(frozen=True)
class IntentPacket:
    intent_id: str
    origin: str
    action_graph: Dict
    context: Dict
    signature: str

# -------------------------------------------
# 1. Validador Semântico (Membrana Dissipativa)
# -------------------------------------------
class SemanticValidator:
    """Valida intenções contra ambiguidade, coerência causal e autoridade."""

    def __init__(self, coherence_field=None, coherence_threshold: float = 0.87):
        self.coherence_field = coherence_field
        self.threshold = coherence_threshold
        self.action_schemas = {
            "ReserveAction": {
                "required": ["target.identifier", "target.departureDate", "parameters.passengers"],
                "coherence_min": 0.80
            },
            "TransferAction": {
                "required": ["target.amount", "target.recipient"],
                "coherence_min": 0.85
            },
            "QueryAction": {
                "required": ["target.query"],
                "coherence_min": 0.70
            },
            "transfer_ownership": {
                "required": ["params.to"],
                "coherence_min": 0.90
            }
        }

    async def validate_all_layers(self, packet: IntentPacket) -> Tuple[bool, List[str]]:
        """Executa as 4 camadas de validação (Léxica, Semântica, Pragmática, Causal)."""
        violations = []

        # 1. Camada Léxica
        if not packet.signature.startswith("ecdsa-"):
            violations.append("lexical_error: invalid signature format")

        # 2. Camada Semântica (Precisão)
        if not self._check_semantic_precision(packet.action_graph):
            violations.append("semantic_ambiguity")

        # 3. Camada Pragmática (Autoridade/Ω)
        if not await self._check_authority(packet):
            violations.append("insufficient_coherence")

        # 4. Camada Causal (Temporal/Consistência)
        if not self._check_causal_consistency(packet):
            violations.append("causal_inconsistency")

        return len(violations) == 0, violations

    def _check_semantic_precision(self, graph: Dict) -> bool:
        # Suporta tanto schema FS-190 (action_graph) quanto FS-192.1 (JSON-LD)
        action_type = graph.get("@type") or graph.get("verb")
        action_data = graph

        if not action_type and "nodes" in graph:
            # Tenta extrair do primeiro nó de ação se for FS-190 nodes/edges
            for node in graph["nodes"]:
                if node["type"] == "action":
                    action_type = node.get("verb")
                    action_data = node
                    break

        schema = self.action_schemas.get(action_type)
        if not schema:
            return False # Ação desconhecida

        required = schema.get("required", [])
        for field in required:
            if not self._resolve_path(action_data, field):
                return False
        return True

    def _resolve_path(self, data: Dict, path: str) -> Any:
        parts = path.split(".")
        val = data
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part)
            else:
                return None
        return val

    async def _check_authority(self, packet: IntentPacket) -> bool:
        required_omega = packet.context.get("coherence_threshold") or packet.context.get("coherenceThreshold") or self.threshold
        if self.coherence_field:
            current_omega = await self.coherence_field.get_current_coherence(packet.origin)
            return current_omega >= required_omega
        # Se não houver campo, validamos apenas se há uma origem definida
        return len(packet.origin) > 0

    def _check_causal_consistency(self, packet: IntentPacket) -> bool:
        validity_ns = packet.context.get("validity_ns")
        if validity_ns and time.time_ns() > validity_ns:
            return False
        return True

# -------------------------------------------
# 2. Executor de Ações
# -------------------------------------------
class ActionExecutor:
    """Executa uma intenção validada, bypassando UI."""

    def __init__(self, codex=None):
        self.codex = codex
        self.execution_handlers: Dict[str, Callable] = {
            "ReserveAction": self._execute_reservation,
            "TransferAction": self._execute_transfer,
            "QueryAction": self._execute_query,
            "transfer_ownership": self._execute_transfer_ownership # FS-190 verb
        }

    async def execute(self, packet: IntentPacket) -> Dict:
        """Pipeline: Compilação → Execução → Âncora"""
        # Compilação simplificada (Neo-Assembly mockup)
        instructions = self._compile(packet.action_graph)

        results = []
        for instr in instructions:
            handler = self.execution_handlers.get(instr["op"])
            if handler:
                res = await handler(instr["params"])
                results.append(res)

        # Gerar recibo
        status = "success" if results else "no_op"
        data = results[0] if len(results) == 1 else results

        receipt = {
            "status": status,
            "data": data,
            "intent_id": packet.intent_id,
            "timestamp_ns": time.time_ns()
        }

        # Ancoragem no Códice
        if self.codex:
            causal_hash = self._compute_causal_hash(packet, receipt)
            receipt["causal_hash"] = causal_hash
            await self.codex.store_artifact(
                artifact_id=f"intent_execution_{packet.intent_id}",
                content_hash=causal_hash,
                metadata={"type": "intent_execution", "status": status}
            )

        return receipt

    def _compile(self, graph: Dict) -> List[Dict]:
        instructions = []
        # Suporte FS-192.1 JSON-LD
        if "@type" in graph:
            instructions.append({"op": graph["@type"], "params": graph})
        # Suporte FS-190 Graph
        elif "nodes" in graph:
            for node in graph["nodes"]:
                if node["type"] == "action":
                    instructions.append({"op": node["verb"], "params": node.get("params", {})})
        return instructions

    async def _execute_reservation(self, params: Dict) -> Dict:
        return {"action": "reservation_completed", "status": "executed"}

    async def _execute_transfer(self, params: Dict) -> Dict:
        return {"action": "transfer_completed", "status": "executed"}

    async def _execute_query(self, params: Dict) -> Dict:
        return {"action": "query_completed", "results": []}

    async def _execute_transfer_ownership(self, params: Dict) -> Dict:
        return {"action": "ownership_transferred", "to": params.get("to")}

    def _compute_causal_hash(self, packet: IntentPacket, receipt: Dict) -> str:
        payload = f"{packet.intent_id}:{receipt['status']}:{receipt['timestamp_ns']}"
        return hashlib.sha256(payload.encode()).hexdigest()

# -------------------------------------------
# 3. Kernel Principal
# -------------------------------------------
class IntentKernel:
    def __init__(self, codex=None, reticulum_mesh=None, coherence_field=None):
        self.validator = SemanticValidator(coherence_field)
        self.executor = ActionExecutor(codex)
        self.mesh = reticulum_mesh

    async def execute_intent(self, packet: IntentPacket) -> Dict:
        # 1. Validação
        is_valid, violations = await self.validator.validate_all_layers(packet)
        if not is_valid:
            return {"status": "error", "reason": f"validation_failed: {violations}"}

        # 2. Resolução Semântica (via Reticulum Mesh se disponível)
        if self.mesh:
            # Simula resolução de URIs
            pass

        # 3. Execução Direta
        return await self.executor.execute(packet)

class ArkheIntentKernel(IntentKernel):
    """Alias para compatibilidade FS-192.1"""

    async def process_intent_json(self, intent_json: str) -> Dict:
        data = json.loads(intent_json)
        # Converte JSON-LD para IntentPacket
        packet = IntentPacket(
            intent_id=data.get("id", "unknown"),
            origin=data.get("issuer", {}).get("did", "anonymous"),
            action_graph=data.get("action", data),
            context=data.get("validation", {}),
            signature="ecdsa-mock-sig" # Em prod viria do envelope
        )
        return await self.execute_intent(packet)
