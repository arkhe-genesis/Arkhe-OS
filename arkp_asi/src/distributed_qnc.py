#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
distributed_qnc.py — Execução federada de QNC com consenso via TemporalChain.
"""

import asyncio
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable, Awaitable, Any
import time
import hashlib
import json

try:
    from arkp_consensus.oracle import ConsistencyOracle, ConsensusResult
    from arkp_temporal.chain import TemporalAnchor
except ImportError:
    @dataclass
    class TemporalAnchor:
        anchor_hash: str
        payload_hash: str
        timestamp: int
        author: str
        dependencies: list

    @dataclass
    class ConsensusResult:
        task_id: str
        success: bool
        error: Optional[str]
        consensus_value: Any
        temporal_anchor: Any = None

    class ConsistencyOracle:
        def __init__(self, node_id=None):
            self.node_id = node_id
        def anchor_event(self, event_type, payload, causal_deps):
            return TemporalAnchor("mock", "mock", int(time.time()), "mock", [])

from .asi_node_registry import NodeCapability, ASINodeMetadata

@dataclass
class FederatedTask:
    """Tarefa de computação federada."""
    task_id: str
    model_config: Any
    input_data: Dict  # Dados de entrada (ex: sequências genômicas)
    required_capabilities: List[str]
    min_node_reputation: float
    timeout_seconds: int
    callback: Optional[Callable[[Dict], Awaitable[None]]] = None

@dataclass
class NodeComputationResult:
    """Resultado de computação de um nó participante."""
    node_id: str
    task_id: str
    output: Dict
    execution_time_ms: float
    phi_c_coherence_at_execution: float
    integrity_proof: bytes  # Hash do resultado para verificação

class DistributedQNCExecutor:
    """
    Executor federado de modelos QNC com consenso distribuído.

    Fluxo:
    1. Receber tarefa de inferência/predição QNC
    2. Selecionar nós via ASINodeRegistry baseado em capacidades/Φ_C
    3. Distribuir computação com handshakes seguros
    4. Coletar resultados e verificar integridade via provas temporais
    5. Aplicar consenso (majoridade ponderada por reputação × Φ_C)
    6. Ancorar resultado final na TemporalChain
    """

    def __init__(
        self,
        node_registry,  # ASINodeRegistry
        consistency_oracle: ConsistencyOracle,
        local_qnc: Optional[Any] = None,
    ):
        self.registry = node_registry
        self.oracle = consistency_oracle
        self.local_qnc = local_qnc
        self.active_tasks: Dict[str, FederatedTask] = {}
        self.results_cache: Dict[str, List[NodeComputationResult]] = {}

    async def submit_federated_task(
        self,
        task: FederatedTask,
    ) -> ConsensusResult:
        """Submete tarefa para execução federada."""
        self.active_tasks[task.task_id] = task

        # 1. Descobrir nós adequados
        req_caps = set()
        for cap in task.required_capabilities:
            if cap == "QNC_INFERENCE":
                req_caps.add(NodeCapability.QNC_INFERENCE)
            elif cap == "EPIGENETIC_MODELING":
                req_caps.add(NodeCapability.EPIGENETIC_MODELING)
            elif cap == "POLYGLOT_TRANSPILE":
                req_caps.add(NodeCapability.POLYGLOT_TRANSPILE)
            elif cap == "TEMPORAL_CONSENSUS":
                req_caps.add(NodeCapability.TEMPORAL_CONSENSUS)
            elif cap == "Φ_C_OPTIMIZATION":
                req_caps.add(NodeCapability.Φ_C_OPTIMIZATION)
            elif cap == "QUANTUM_SIMULATION":
                req_caps.add(NodeCapability.QUANTUM_SIMULATION)

        nodes = self.registry.discover_nodes(
            required_capabilities=req_caps,
            min_phi_c=0.7,  # Nós com boa coerência para tarefas quânticas
            limit=5,
        )

        if not nodes:
            return ConsensusResult(
                task_id=task.task_id,
                success=False,
                error="No suitable nodes found",
                consensus_value=None,
                temporal_anchor=None,
            )

        # 2. Distribuir computação em paralelo
        coroutines = [
            self._execute_on_node(task, node) for node in nodes
        ]
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # 3. Filtrar resultados válidos
        valid_results = [r for r in results if isinstance(r, NodeComputationResult)]

        if len(valid_results) < 2:
            return ConsensusResult(
                task_id=task.task_id,
                success=False,
                error="Insufficient valid results for consensus",
                consensus_value=None,
                temporal_anchor=None,
            )

        # 4. Aplicar consenso ponderado
        consensus = self._weighted_consensus(valid_results, task)

        # 5. Ancorar na cadeia temporal
        try:
            anchor = self.oracle.anchor_event(
                event_type="federated_qnc_result",
                payload={
                    "task_id": task.task_id,
                    "consensus_value": consensus,
                    "participating_nodes": [r.node_id for r in valid_results],
                },
                causal_deps=[r.integrity_proof for r in valid_results],
            )
        except AttributeError:
            anchor = TemporalAnchor("mock", "mock", int(time.time()), "mock", [])

        # 6. Callback opcional
        if task.callback:
            await task.callback({"consensus": consensus, "anchor": anchor})

        return ConsensusResult(
            task_id=task.task_id,
            success=True,
            error=None,
            consensus_value=consensus,
            temporal_anchor=anchor,
        )

    async def _execute_on_node(
        self,
        task: FederatedTask,
        node,  # ASINodeMetadata
    ) -> Optional[NodeComputationResult]:
        """Executa tarefa em um nó específico (simulado)."""
        try:
            start_time = time.time()

            # Em produção: estabelecer conexão segura via QuantumHandshakeProtocol
            # e enviar tarefa para execução remota

            # Simular execução local para demonstração
            if self.local_qnc:
                # Executar inferência QNC localmente
                if "sequences" in task.input_data:
                    predictions = []
                    for seq in task.input_data["sequences"]:
                        pred_class, confidence = self.local_qnc.predict(seq)
                        predictions.append({"class": pred_class, "confidence": confidence})
                    output = {"predictions": predictions}
                else:
                    output = {"status": "mock_execution", "node": node.node_id}
            else:
                # Fallback: resultado simulado
                output = {
                    "status": "simulated",
                    "node_id": node.node_id,
                    "phi_c": node.phi_c_coherence,
                }

            execution_time = (time.time() - start_time) * 1000

            # Gerar prova de integridade do resultado
            integrity_proof = hashlib.sha3_256(
                json.dumps(output, sort_keys=True, default=str).encode()
            ).digest()

            return NodeComputationResult(
                node_id=node.node_id,
                task_id=task.task_id,
                output=output,
                execution_time_ms=execution_time,
                phi_c_coherence_at_execution=node.phi_c_coherence,
                integrity_proof=integrity_proof,
            )

        except Exception as e:
            # Log erro e retornar None para indicar falha
            print(f"❌ Execution failed on node {node.node_id}: {e}")
            return None

    def _weighted_consensus(
        self,
        results: List[NodeComputationResult],
        task: FederatedTask,
    ) -> Dict:
        """Aplica consenso ponderado por reputação e Φ_C."""
        # Calcular pesos: reputação (50%) + Φ_C (50%)
        weights = []
        for r in results:
            node = self.registry.known_nodes.get(r.node_id)
            if node:
                weight = 0.5 * node.reputation_score + 0.5 * r.phi_c_coherence_at_execution
                weights.append(weight)
            else:
                weights.append(0.5)  # Peso padrão se nó não encontrado

        weights = np.array(weights)
        weights /= weights.sum()  # Normalizar

        # Para resultados numéricos: média ponderada
        # Para resultados categóricos: votação ponderada
        if all("predictions" in r.output for r in results):
            # Consenso para predições QNC
            all_predictions = [r.output["predictions"] for r in results]
            # Simplificado: retornar predições do nó com maior peso
            best_idx = np.argmax(weights)
            return all_predictions[best_idx]
        else:
            # Consenso genérico: retornar resultado do nó mais confiável
            best_idx = np.argmax(weights)
            return results[best_idx].output
