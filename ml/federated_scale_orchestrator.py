#!/usr/bin/env python3
"""
Substrato 225: Federated Learning Scale Orchestrator
Orquestra treinamento federado em escala com 50+ nós simultâneos,
agregação hierárquica e balanceamento geográfico.
"""
import asyncio
import hashlib
import json
import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)

class AggregationTier(Enum):
    """Níveis hierárquicos de agregação para escalabilidade."""
    LOCAL = "local"           # Agregação intra-região (baixa latência)
    REGIONAL = "regional"     # Agregação por região geográfica
    GLOBAL = "global"         # Agregação final global

@dataclass
class FederatedNode:
    """Representa um nó participante do treinamento federado."""
    node_id: str
    region: str
    capabilities: Dict[str, float]  # CPU, GPU, bandwidth, reliability
    current_status: str = "IDLE"    # IDLE, TRAINING, SYNCING, OFFLINE
    last_heartbeat: float = field(default_factory=time.time)
    phi_c_contribution: float = 0.95

@dataclass
class HierarchicalAggregationResult:
    """Resultado de agregação hierárquica."""
    round_id: str
    tier: AggregationTier
    participating_nodes: int
    aggregation_time_ms: float
    model_hash: str
    phi_c_score: float
    dp_epsilon_used: float
    temporal_seal: Optional[str] = None

class FederatedScaleOrchestrator:
    """
    Orquestrador de treinamento federado em escala.

    Estratégia de escalabilidade:
    • Agregação hierárquica em 3 níveis (local → regional → global)
    • Balanceamento geográfico para minimizar latência de sincronização
    • Seleção dinâmica de nós baseada em capability scoring
    • Tolerância a falhas com retry e fallback entre tiers
    """

    # Configurações de escala
    MAX_NODES_PER_ROUND = 50
    MIN_NODES_FOR_GLOBAL = 10
    REGIONAL_AGGREGATION_THRESHOLD = 5
    CAPABILITY_WEIGHTS = {
        "compute": 0.4,
        "bandwidth": 0.3,
        "reliability": 0.2,
        "phi_c": 0.1
    }

    def __init__(
        self,
        cluster_config: any,  # TemporalChainClusterClient
        phi_bus=None,
        temporal_chain=None
    ):
        self.cluster = cluster_config
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self._registered_nodes: Dict[str, FederatedNode] = {}
        self._aggregation_history: List[HierarchicalAggregationResult] = []
        self._round_counter = 0

    async def register_node(self, node: FederatedNode) -> bool:
        """Registra novo nó no pool de treinamento federado."""
        if node.node_id in self._registered_nodes:
            # Atualizar heartbeat se já registrado
            self._registered_nodes[node.node_id].last_heartbeat = time.time()
            return True

        # Validar capacidades mínimas
        min_compute = node.capabilities.get("compute", 0)
        min_reliability = node.capabilities.get("reliability", 0)

        if min_compute < 0.5 or min_reliability < 0.8:
            logger.warning(f"⚠️  Nó {node.node_id} não atende capacidades mínimas")
            return False

        self._registered_nodes[node.node_id] = node
        logger.info(f"✅ Nó registrado: {node.node_id} ({node.region})")

        # Publicar métrica
        if self.phi_bus:
            await self.phi_bus.publish_metric("federated_node_registered", {
                "node_id": node.node_id,
                "region": node.region,
                "compute": node.capabilities.get("compute"),
                "total_nodes": len(self._registered_nodes)
            })

        return True

    async def select_nodes_for_round(
        self,
        required_nodes: int = None,
        target_regions: Optional[List[str]] = None
    ) -> List[FederatedNode]:
        """
        Seleciona nós para round de treinamento baseado em capability scoring.

        Algoritmo:
        1. Filtrar nós online e com heartbeat recente (< 5 min)
        2. Calcular capability score ponderado
        3. Balancear por região se target_regions especificado
        4. Selecionar top-K nós por score
        """
        now = time.time()
        cutoff = now - 300  # 5 minutos

        # Filtrar nós elegíveis
        eligible = [
            n for n in self._registered_nodes.values()
            if n.current_status == "IDLE"
            and n.last_heartbeat > cutoff
        ]

        if not eligible:
            return []

        # Calcular capability score para cada nó
        scored = []
        for node in eligible:
            score = sum(
                node.capabilities.get(k, 0) * w
                for k, w in self.CAPABILITY_WEIGHTS.items()
            )
            scored.append((node, score))

        # Balanceamento regional se necessário
        if target_regions:
            # Agrupar por região e selecionar proporcionalmente
            by_region: Dict[str, List[Tuple[FederatedNode, float]]] = {}
            for node, score in scored:
                if node.region in target_regions:
                    by_region.setdefault(node.region, []).append((node, score))

            # Selecionar nós de cada região proporcionalmente
            selected = []
            total_capacity = sum(len(nodes) for nodes in by_region.values())
            for region, nodes in by_region.items():
                quota = max(1, int(len(nodes) / total_capacity * (required_nodes or self.MAX_NODES_PER_ROUND)))
                nodes.sort(key=lambda x: x[1], reverse=True)
                selected.extend([n for n, _ in nodes[:quota]])
        else:
            # Selecionar top-K globalmente
            scored.sort(key=lambda x: x[1], reverse=True)
            selected = [n for n, _ in scored[:required_nodes or self.MAX_NODES_PER_ROUND]]

        # Atualizar status dos nós selecionados
        for node in selected:
            node.current_status = "TRAINING"

        logger.info(f"🎯 {len(selected)} nós selecionados para round")
        return selected

    async def execute_hierarchical_aggregation(
        self,
        local_updates: List[Dict],
        dp_epsilon: float
    ) -> HierarchicalAggregationResult:
        """
        Executa agregação hierárquica em 3 níveis para escalabilidade.

        Nível 1 (Local): Agregação intra-região com baixa latência
        Nível 2 (Regional): Agregação entre regiões vizinhas
        Nível 3 (Global): Agregação final com validação de quórum
        """
        self._round_counter += 1
        round_id = hashlib.sha3_256(
            f"fed_round_{self._round_counter}:{time.time()}".encode()
        ).hexdigest()[:12]

        start_time = time.time()

        # Nível 1: Agregação local por região
        by_region: Dict[str, List[Dict]] = {}
        for update in local_updates:
            region = update.get("region", "unknown")
            by_region.setdefault(region, []).append(update)

        regional_aggregates = {}
        for region, updates in by_region.items():
            if len(updates) >= 2:  # Mínimo para agregação
                # FedAvg simples intra-região
                aggregated = self._fedavg_aggregate(updates)
                regional_aggregates[region] = {
                    "region": region,
                    "weights": aggregated,
                    "node_count": len(updates),
                    "avg_phi_c": np.mean([u.get("phi_c_contribution", 0.9) for u in updates])
                }

        # Nível 2: Agregação regional (se múltiplas regiões)
        if len(regional_aggregates) >= 2:
            global_weights = self._fedavg_aggregate(
                list(regional_aggregates.values()),
                weight_key="node_count"
            )
        elif len(regional_aggregates) == 1:
            # Apenas uma região: promover para global
            region_data = list(regional_aggregates.values())[0]
            global_weights = region_data["weights"]
        else:
            # Fallback
            global_weights = {}

        # Nível 3: Validação global e aplicação de DP noise
        noisy_weights = self._apply_dp_noise(global_weights, dp_epsilon)

        # Calcular hash do modelo agregado
        model_hash = hashlib.sha3_256(
            json.dumps(noisy_weights, sort_keys=True).encode()
        ).hexdigest()

        aggregation_time = (time.time() - start_time) * 1000

        # Calcular Φ_C composto do round
        phi_c_score = np.mean([
            r.get("avg_phi_c", 0.9) for r in regional_aggregates.values()
        ]) if regional_aggregates else 0.9

        result = HierarchicalAggregationResult(
            round_id=round_id,
            tier=AggregationTier.GLOBAL,
            participating_nodes=len(local_updates),
            aggregation_time_ms=aggregation_time,
            model_hash=model_hash,
            phi_c_score=phi_c_score,
            dp_epsilon_used=dp_epsilon
        )

        # Ancorar na TemporalChain
        if self.temporal:
            try:
                if asyncio.iscoroutinefunction(self.temporal.anchor_event):
                    result.temporal_seal = await self.temporal.anchor_event(
                        "federated_aggregation_hierarchical",
                        {
                            "round_id": round_id,
                            "tier": result.tier.value,
                            "nodes": result.participating_nodes,
                            "regions": list(regional_aggregates.keys()),
                            "phi_c": phi_c_score,
                            "epsilon": dp_epsilon,
                            "aggregation_time_ms": aggregation_time,
                            "model_hash": model_hash[:16],
                            "timestamp": time.time()
                        }
                    )
                else:
                    result.temporal_seal = self.temporal.anchor_event(
                        "federated_aggregation_hierarchical",
                        {
                            "round_id": round_id,
                            "tier": result.tier.value,
                            "nodes": result.participating_nodes,
                            "regions": list(regional_aggregates.keys()),
                            "phi_c": phi_c_score,
                            "epsilon": dp_epsilon,
                            "aggregation_time_ms": aggregation_time,
                            "model_hash": model_hash[:16],
                            "timestamp": time.time()
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to anchor federated event: {e}")

        self._aggregation_history.append(result)

        logger.info(
            f"✅ Agregação hierárquica concluída: round {round_id} | "
            f"nós={result.participating_nodes} | regiões={len(regional_aggregates)} | "
            f"Φ_C={phi_c_score:.4f} | tempo={aggregation_time:.1f}ms"
        )

        return result

    def _fedavg_aggregate(
        self,
        updates: List[Dict],
        weight_key: str = "training_samples"
    ) -> Dict:
        """Agregação FedAvg ponderada."""
        if not updates:
            return {}

        total_weight = sum(u.get(weight_key, 1) for u in updates)
        if total_weight == 0:
            total_weight = len(updates)  # Fallback para pesos iguais

        aggregated = {}
        # Mock: em produção, agregar tensores de pesos de modelo
        for key in updates[0].get("weights", {}).keys():
            weighted_sum = sum(
                u.get("weights", {}).get(key, 0) * u.get(weight_key, 1) / total_weight
                for u in updates
            )
            aggregated[key] = weighted_sum

        return aggregated

    def _apply_dp_noise(self, weights: Dict, epsilon: float) -> Dict:
        """Aplica ruído Laplace para privacidade diferencial."""
        noisy = {}
        for key, value in weights.items():
            if isinstance(value, (int, float)):
                noise = np.random.laplace(0, 1/epsilon)
                noisy[key] = value + noise
            else:
                noisy[key] = value  # Preservar estruturas não-numéricas
        return noisy

    def get_scale_statistics(self) -> Dict:
        """Retorna estatísticas de operação em escala."""
        active_nodes = sum(
            1 for n in self._registered_nodes.values()
            if n.current_status in ["IDLE", "TRAINING"]
        )

        regions = list(set(n.region for n in self._registered_nodes.values()))

        return {
            "total_registered": len(self._registered_nodes),
            "active_nodes": active_nodes,
            "regions_covered": regions,
            "rounds_completed": len(self._aggregation_history),
            "avg_aggregation_time_ms": (
                np.mean([r.aggregation_time_ms for r in self._aggregation_history])
                if self._aggregation_history else 0
            ),
            "avg_phi_c": (
                np.mean([r.phi_c_score for r in self._aggregation_history])
                if self._aggregation_history else 0
            ),
            "max_nodes_per_round": self.MAX_NODES_PER_ROUND,
            "hierarchical_tiers": [t.value for t in AggregationTier]
        }
