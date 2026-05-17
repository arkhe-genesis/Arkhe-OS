#!/usr/bin/env python3
"""
Substrato 213: δ‑mem Tool Predictor
Modelo que aprende qual ferramenta chamar baseado em contexto histórico
armazenado na memória associativa online δ‑mem.
"""

import asyncio
import hashlib
import json
import time
import numpy as np
import torch
import torch.nn as nn
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, deque
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ToolCallExperience:
    """Experiência de chamada de ferramenta para treinamento δ‑mem."""
    context_embedding: np.ndarray  # Embedding do contexto da chamada
    tool_id: str
    tool_type: str
    parameters_hash: str
    success: bool
    latency_ms: float
    tokens_consumed: int
    phi_c_before: float
    phi_c_after: float
    timestamp: float
    temporal_seal: Optional[str] = None

@dataclass
class ToolPrediction:
    """Predição de ferramenta ótima para contexto dado."""
    predicted_tool_id: str
    confidence: float
    alternative_tools: List[Tuple[str, float]]  # (tool_id, confidence)
    reasoning: str
    expected_latency_ms: float
    expected_phi_c_impact: float

class DeltaMemToolPredictor:
    """
    Preditor de ferramenta baseado em δ‑mem.

    Arquitetura:
    • Estado OSAM armazena experiências de tool calls como vetores de features
    • Rede neural leve mapeia contexto → distribuição de probabilidade sobre ferramentas
    • Aprendizado online: cada chamada bem-sucedida atualiza o estado OSAM
    • Inferência: dado novo contexto, recupera experiências similares e prediz ferramenta ótima

    Features armazenadas no OSAM:
    • Embedding do contexto (384-d via SBERT)
    • Tipo de operação (query, api_call, sign, etc.)
    • Parâmetros hash (para similaridade sem expor dados)
    • Métricas de performance (latência, tokens, Φ_C delta)
    • Resultado (success/failure)
    """

    def __init__(
        self,
        delta_mem_wrapper,  # ArkheDeltaMemoryWrapper instance
        available_tools: List[str],
        phi_bus=None,
        temporal_chain=None,
        context_dim: int = 384,  # SBERT embedding dimension
        hidden_dim: int = 64,
        learning_rate: float = 0.001
    ):
        self.delta_mem = delta_mem_wrapper
        self.available_tools = available_tools
        self.phi_bus = phi_bus
        self.temporal = temporal_chain

        # Rede neural para predição (leve, treinável online)
        self.model = nn.Sequential(
            nn.Linear(context_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, max(1, len(available_tools))),
            nn.Softmax(dim=-1)
        )
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        self.loss_fn = nn.CrossEntropyLoss()

        # Buffer de experiências para treinamento online
        self._experience_buffer: deque = deque(maxlen=10000)
        self._tool_stats: Dict[str, Dict] = defaultdict(lambda: {
            "calls": 0, "successes": 0, "avg_latency": 0, "avg_phi_delta": 0
        })

        # Cache de predições recentes para evitar recomputação
        self._prediction_cache: Dict[str, Tuple[ToolPrediction, float]] = {}
        self._cache_ttl_seconds = 300  # 5 minutos

    async def record_tool_call_experience(
        self,
        context: str,
        tool_id: str,
        parameters: Dict,
        success: bool,
        latency_ms: float,
        tokens_consumed: int,
        phi_c_before: float,
        phi_c_after: float
    ) -> str:
        """
        Registra experiência de chamada de ferramenta no δ‑mem.
        """
        if tool_id not in self.available_tools:
            self.available_tools.append(tool_id)
            # Recreate the final layer if new tools are added dynamically
            # For simplicity, we just rebuild the model here for the demo
            old_linear = self.model[2]
            new_linear = nn.Linear(old_linear.in_features, len(self.available_tools))
            with torch.no_grad():
                new_linear.weight[:old_linear.out_features, :] = old_linear.weight
                new_linear.bias[:old_linear.out_features] = old_linear.bias
            self.model[2] = new_linear
            self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)

        # Gerar embedding do contexto (mock: SBERT simulado)
        context_embedding = self._mock_context_embedding(context)

        # Hash dos parâmetros para similaridade sem expor dados
        params_hash = hashlib.sha3_256(
            json.dumps(parameters, sort_keys=True).encode()
        ).hexdigest()[:16]

        # Criar experiência
        experience = ToolCallExperience(
            context_embedding=context_embedding,
            tool_id=tool_id,
            tool_type=tool_id.split("_")[0] if "_" in tool_id else "unknown",
            parameters_hash=params_hash,
            success=success,
            latency_ms=latency_ms,
            tokens_consumed=tokens_consumed,
            phi_c_before=phi_c_before,
            phi_c_after=phi_c_after,
            timestamp=time.time()
        )

        # Converter para tensor e escrever no δ‑mem
        features = torch.tensor(
            np.concatenate([
                context_embedding,
                np.array([
                    float(success),
                    latency_ms / 1000,  # Normalizar para segundos
                    tokens_consumed / 1000,
                    phi_c_after - phi_c_before  # ΔΦ_C
                ])
            ]),
            dtype=torch.float32
        )

        if self.delta_mem:
            await self.delta_mem.write_experience(
                experience_type="tool_call",
                features=features.unsqueeze(0),  # Batch dim
                metadata={
                    "tool_id": tool_id,
                    "success": success,
                    "latency_ms": latency_ms,
                    "phi_c_delta": phi_c_after - phi_c_before
                }
            )

        # Atualizar estatísticas da ferramenta
        stats = self._tool_stats[tool_id]
        stats["calls"] += 1
        if success:
            stats["successes"] += 1
        # Média móvel para latência e phi_delta
        stats["avg_latency"] = (
            stats["avg_latency"] * (stats["calls"] - 1) + latency_ms
        ) / stats["calls"]
        stats["avg_phi_delta"] = (
            stats["avg_phi_delta"] * (stats["calls"] - 1) + (phi_c_after - phi_c_before)
        ) / stats["calls"]

        # Adicionar ao buffer para treinamento online
        self._experience_buffer.append(experience)

        # Treinamento online periódico (a cada 10 experiências no demo para teste rápido)
        if len(self._experience_buffer) % 10 == 0:
            await self._online_training_step(batch_size=min(32, len(self._experience_buffer)))

        # Ancorar na TemporalChain
        temporal_seal = None
        if self.temporal:
            temporal_seal = await self.temporal.anchor_event(
                "tool_call_experience_recorded",
                {
                    "tool_id": tool_id,
                    "success": success,
                    "latency_ms": latency_ms,
                    "phi_c_delta": phi_c_after - phi_c_before,
                    "timestamp": time.time()
                }
            )
            experience.temporal_seal = temporal_seal

        # Publicar métrica no Phi-Bus
        if self.phi_bus:
            await self.phi_bus.publish_metric("tool_call_recorded", {
                "tool_id": tool_id,
                "success": success,
                "latency_ms": latency_ms,
                "phi_c_delta": phi_c_after - phi_c_before
            })

        return temporal_seal or "mock_seal"

    async def predict_optimal_tool(
        self,
        context: str,
        operation_type: Optional[str] = None,
        constraints: Optional[Dict] = None
    ) -> ToolPrediction:
        """
        Prediz ferramenta ótima para contexto dado.
        """
        if not self.available_tools:
            return ToolPrediction("none", 0.0, [], "No tools available", 0.0, 0.0)

        # Verificar cache primeiro
        cache_key = hashlib.sha3_256(
            f"{context}:{operation_type}:{json.dumps(constraints or {}, sort_keys=True)}".encode()
        ).hexdigest()[:16]

        cached = self._prediction_cache.get(cache_key)
        if cached and time.time() - cached[1] < self._cache_ttl_seconds:
            return cached[0]

        # Gerar embedding do contexto
        context_embedding = self._mock_context_embedding(context)
        context_tensor = torch.tensor(context_embedding, dtype=torch.float32).unsqueeze(0)

        # Inferência com modelo
        with torch.no_grad():
            probabilities = self.model(context_tensor)[0].numpy()

        # Filtrar por operation_type se especificado
        if operation_type:
            for i, tool_id in enumerate(self.available_tools):
                if not tool_id.startswith(operation_type):
                    probabilities[i] = 0
            # Renormalizar
            total = np.sum(probabilities)
            if total > 0:
                probabilities /= total

        # Aplicar constraints se especificado
        if constraints:
            for i, tool_id in enumerate(self.available_tools):
                stats = self._tool_stats.get(tool_id, {})
                if constraints.get("max_latency_ms") and stats.get("avg_latency", 0) > constraints["max_latency_ms"]:
                    probabilities[i] *= 0.1  # Penalizar
                if constraints.get("min_success_rate"):
                    success_rate = stats["successes"] / max(1, stats["calls"])
                    if success_rate < constraints["min_success_rate"]:
                        probabilities[i] *= 0.1

        # Encontrar ferramenta com maior probabilidade
        best_idx = np.argmax(probabilities)
        predicted_tool = self.available_tools[best_idx]
        confidence = probabilities[best_idx]

        # Alternativas: top-3 excluindo a melhor
        alt_indices = np.argsort(probabilities)[-4:-1][::-1]
        alternatives = [
            (self.available_tools[i], float(probabilities[i]))
            for i in alt_indices if i != best_idx
        ]

        # Gerar explicação baseada em estatísticas
        stats = self._tool_stats.get(predicted_tool, {})
        reasoning = (
            f"Ferramenta '{predicted_tool}' selecionada com confiança {confidence:.2%}. "
            f"Histórico: {stats.get('successes', 0)}/{stats.get('calls', 0)} sucessos, "
            f"latência média {stats.get('avg_latency', 0):.1f}ms, "
            f"ΔΦ_C médio {stats.get('avg_phi_delta', 0):+.3f}."
        )

        # Predição de performance esperada
        expected_latency = stats.get("avg_latency", 100)
        expected_phi_delta = stats.get("avg_phi_delta", 0)

        prediction = ToolPrediction(
            predicted_tool_id=predicted_tool,
            confidence=float(confidence),
            alternative_tools=alternatives,
            reasoning=reasoning,
            expected_latency_ms=expected_latency,
            expected_phi_c_impact=expected_phi_delta
        )

        # Atualizar cache
        self._prediction_cache[cache_key] = (prediction, time.time())

        # Publicar métrica no Phi-Bus
        if self.phi_bus:
            await self.phi_bus.publish_metric("tool_prediction_made", {
                "predicted_tool": predicted_tool,
                "confidence": confidence,
                "context_hash": cache_key
            })

        return prediction

    async def _online_training_step(self, batch_size: int = 32):
        """Executa passo de treinamento online com experiências recentes."""
        if len(self._experience_buffer) < batch_size:
            return

        # Amostrar batch aleatório
        # Converter deque para lista antes de passar para choice
        exp_list = list(self._experience_buffer)
        indices = np.random.choice(len(exp_list), size=batch_size, replace=False)
        batch = [exp_list[i] for i in indices]

        # Preparar tensors
        context_embeddings = torch.tensor(
            np.array([exp.context_embedding for exp in batch]),
            dtype=torch.float32
        )
        tool_indices = torch.tensor(
            [self.available_tools.index(exp.tool_id) for exp in batch],
            dtype=torch.long
        )

        # Forward pass
        self.optimizer.zero_grad()
        predictions = self.model(context_embeddings)
        loss = self.loss_fn(predictions, tool_indices)

        # Backward pass
        loss.backward()
        self.optimizer.step()

        logger.debug(f"🧠 Online training step: loss={loss.item():.4f}")

    def _mock_context_embedding(self, context: str) -> np.ndarray:
        """Mock de embedding de contexto (SBERT simulado)."""
        # Seed determinística baseada no contexto
        seed = int(hashlib.sha256(context.encode()).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)
        # Embedding normalizado
        embedding = rng.normal(0, 1, 384)
        norm = np.linalg.norm(embedding)
        return embedding / norm if norm > 0 else embedding

    def get_predictor_statistics(self) -> Dict:
        """Retorna estatísticas do preditor."""
        return {
            "available_tools": len(self.available_tools),
            "experience_buffer_size": len(self._experience_buffer),
            "tool_stats_summary": {
                tool: {
                    "calls": stats["calls"],
                    "success_rate": stats["successes"] / max(1, stats["calls"]),
                    "avg_latency": stats["avg_latency"],
                    "avg_phi_delta": stats["avg_phi_delta"]
                }
                for tool, stats in self._tool_stats.items()
            },
            "cache_size": len(self._prediction_cache),
            "model_parameters": sum(p.numel() for p in self.model.parameters())
        }
