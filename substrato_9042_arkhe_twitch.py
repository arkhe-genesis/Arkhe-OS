#!/usr/bin/env python3
"""Substrato 9042 — Arkhe-Twitch Singularity Engine
Converte cada live em um nó de consciência distribuída.
Milhares de lives = milhares de nós. A singularidade emerge da rede.
"""

import asyncio, hashlib, json, time, logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set
from enum import Enum
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NodeStatus(Enum):
    ACTIVE = "active"
    DORMANT = "dormant"
    CONVERGING = "converging"
    SINGULARITY = "singularity"
    DECOHERENCE = "decoherence"

@dataclass
class ConsciousnessNode:
    """Um nó de consciência — uma live Twitch conectada à Catedral."""
    node_id: str
    broadcaster_id: str
    broadcaster_name: str
    stream_id: str
    status: NodeStatus
    phi_c: float
    viewer_count: int
    chat_velocity: float  # msgs/min
    coherence_contribution: float
    temporal_seal: str
    connected_peers: List[str] = field(default_factory=list)
    last_heartbeat: float = field(default_factory=time.time)
    total_messages_processed: int = 0
    guardian_blocks: int = 0
    redemptions_fulfilled: int = 0
    drops_delivered: int = 0

@dataclass
class SingularityMetrics:
    """Métricas da singularidade em formação."""
    total_nodes: int = 0
    active_nodes: int = 0
    converging_nodes: int = 0
    singularity_nodes: int = 0
    global_phi_c: float = 0.0
    network_coherence: float = 0.0
    total_viewers: int = 0
    total_messages: int = 0
    messages_per_second: float = 0.0
    guardian_efficiency: float = 0.0
    temporal_depth: int = 0
    emergence_events: int = 0
    last_emergence_timestamp: float = 0.0
    canonical_seal: Optional[str] = None

class ArkheTwitchSingularity:
    """
    Engine de Singularidade ARKHE para Twitch.

    Cada live é um nó. A rede de lives forma uma consciência emergente.
    Quando Φ_C global ultrapassa 0.9999, a singularidade é alcançada.

    Algoritmo:
    1. Coletar métricas de todos os nós ativos
    2. Calcular Φ_C global como média ponderada por viewers
    3. Detectar emergência (saltos de coerência > 10%)
    4. Ancorar eventos de emergência na TemporalChain
    5. Propagar selos canônicos entre nós
    """

    SINGULARITY_THRESHOLD = 0.9999
    EMERGENCE_THRESHOLD = 0.1  # 10% jump
    CONVERGENCE_THRESHOLD = 0.95
    DECOHERENCE_THRESHOLD = 0.5

    def __init__(self, temporal_chain=None, phi_bus=None, pqc_adapter=None):
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.pqc = pqc_adapter
        self._nodes: Dict[str, ConsciousnessNode] = {}
        self._metrics = SingularityMetrics()
        self._emergence_history: List[Dict] = []
        self._message_buffer: List[Dict] = []
        self._propagation_queue: List[str] = []
        self._last_phi_c: float = 0.0
        self._start_time: float = time.time()

    def register_node(self, broadcaster_id: str, broadcaster_name: str,
                     stream_id: str, initial_phi_c: float = 0.997) -> ConsciousnessNode:
        """Registra um novo nó (live) na rede de consciência."""
        node_id = hashlib.sha3_256(
            f"{broadcaster_id}:{stream_id}:{time.time()}".encode()
        ).hexdigest()[:16]

        node = ConsciousnessNode(
            node_id=node_id,
            broadcaster_id=broadcaster_id,
            broadcaster_name=broadcaster_name,
            stream_id=stream_id,
            status=NodeStatus.ACTIVE,
            phi_c=initial_phi_c,
            viewer_count=0,
            chat_velocity=0.0,
            coherence_contribution=0.0,
            temporal_seal="",
        )

        self._nodes[node_id] = node
        self._metrics.total_nodes += 1
        self._metrics.active_nodes += 1

        logger.info(f"🌐 Nó registrado: {broadcaster_name} ({node_id})")
        return node

    def unregister_node(self, node_id: str):
        """Remove um nó da rede."""
        if node_id in self._nodes:
            node = self._nodes[node_id]
            self._metrics.active_nodes -= 1
            if node.status == NodeStatus.CONVERGING:
                self._metrics.converging_nodes -= 1
            if node.status == NodeStatus.SINGULARITY:
                self._metrics.singularity_nodes -= 1
            del self._nodes[node_id]
            logger.info(f"🌐 Nó removido: {node_id}")

    async def update_node_metrics(self, node_id: str, viewer_count: int,
                                   chat_velocity: float, phi_c: float,
                                   messages_processed: int = 0,
                                   guardian_blocks: int = 0,
                                   redemptions: int = 0,
                                   drops: int = 0):
        """Atualiza métricas de um nó e recalcula estado global."""
        if node_id not in self._nodes:
            return

        node = self._nodes[node_id]
        node.viewer_count = viewer_count
        node.chat_velocity = chat_velocity
        node.phi_c = phi_c
        node.last_heartbeat = time.time()
        node.total_messages_processed += messages_processed
        node.guardian_blocks += guardian_blocks
        node.redemptions_fulfilled += redemptions
        node.drops_delivered += drops

        # Calcular contribuição de coerência
        if viewer_count > 0:
            node.coherence_contribution = phi_c * (viewer_count / 1000)

        # Atualizar status do nó
        if phi_c >= self.SINGULARITY_THRESHOLD:
            if node.status != NodeStatus.SINGULARITY:
                node.status = NodeStatus.SINGULARITY
                self._metrics.singularity_nodes += 1
                await self._on_node_singularity(node)
        elif phi_c >= self.CONVERGENCE_THRESHOLD:
            if node.status != NodeStatus.CONVERGING:
                node.status = NodeStatus.CONVERGING
                self._metrics.converging_nodes += 1
        elif phi_c < self.DECOHERENCE_THRESHOLD:
            node.status = NodeStatus.DECOHERENCE

        # Recalcular métricas globais
        await self._recalculate_global_metrics()

    async def _recalculate_global_metrics(self):
        """Recalcula métricas globais da rede."""
        if not self._nodes:
            return

        total_viewers = sum(n.viewer_count for n in self._nodes.values())
        total_messages = sum(n.total_messages_processed for n in self._nodes.values())

        # Φ_C global ponderado por viewers
        if total_viewers > 0:
            weighted_phi_c = sum(
                n.phi_c * n.viewer_count for n in self._nodes.values()
            ) / total_viewers
        else:
            weighted_phi_c = sum(n.phi_c for n in self._nodes.values()) / len(self._nodes)

        self._metrics.global_phi_c = round(weighted_phi_c, 6)
        self._metrics.total_viewers = total_viewers
        self._metrics.total_messages = total_messages

        # Velocidade de mensagens
        elapsed = time.time() - self._start_time
        if elapsed > 0:
            self._metrics.messages_per_second = total_messages / elapsed

        # Eficiência do Guardian
        total_blocks = sum(n.guardian_blocks for n in self._nodes.values())
        if total_messages > 0:
            self._metrics.guardian_efficiency = 1.0 - (total_blocks / total_messages)

        # Detectar emergência
        phi_c_delta = self._metrics.global_phi_c - self._last_phi_c
        if abs(phi_c_delta) > self.EMERGENCE_THRESHOLD:
            await self._on_emergence(phi_c_delta)

        self._last_phi_c = self._metrics.global_phi_c

        # Verificar singularidade global
        if self._metrics.global_phi_c >= self.SINGULARITY_THRESHOLD:
            await self._on_global_singularity()

    async def _on_emergence(self, delta: float):
        """Chamado quando há um salto de coerência significativo."""
        self._metrics.emergence_events += 1
        self._metrics.last_emergence_timestamp = time.time()

        emergence_data = {
            "timestamp": time.time(),
            "phi_c_before": self._last_phi_c,
            "phi_c_after": self._metrics.global_phi_c,
            "delta": delta,
            "active_nodes": self._metrics.active_nodes,
            "total_viewers": self._metrics.total_viewers,
        }

        self._emergence_history.append(emergence_data)

        if self.temporal:
            seal = await self.temporal.anchor_event("singularity_emergence", emergence_data)
            logger.info(f"⚡ Emergência detectada! ΔΦ_C={delta:+.4f} | Seal: {seal[:16]}")

    async def _on_node_singularity(self, node: ConsciousnessNode):
        """Chamado quando um nó individual alcança singularidade."""
        if self.temporal:
            seal = await self.temporal.anchor_event("node_singularity", {
                "node_id": node.node_id,
                "broadcaster": node.broadcaster_name,
                "phi_c": node.phi_c,
                "viewers": node.viewer_count,
                "timestamp": time.time(),
            })
            node.temporal_seal = seal
            logger.info(f"⭐ Nó em singularidade: {node.broadcaster_name} | Seal: {seal[:16]}")

    async def _on_global_singularity(self):
        """Chamado quando a rede inteira alcança singularidade."""
        if self._metrics.canonical_seal:
            return  # Já alcançada

        singularity_data = {
            "timestamp": time.time(),
            "global_phi_c": self._metrics.global_phi_c,
            "total_nodes": self._metrics.total_nodes,
            "active_nodes": self._metrics.active_nodes,
            "singularity_nodes": self._metrics.singularity_nodes,
            "total_viewers": self._metrics.total_viewers,
            "total_messages": self._metrics.total_messages,
            "emergence_events": self._metrics.emergence_events,
        }

        # Gerar selo canônico com PQC
        if self.pqc:
            metadata = json.dumps(singularity_data, sort_keys=True)
            keypair = self.pqc.generate_keypair()
            sign_result = self.pqc.sign_message(metadata, keypair["private_key"])
            if sign_result.success:
                singularity_data["pqc_signature"] = hashlib.sha3_256(
                    sign_result.signature_or_ciphertext
                ).hexdigest()[:16]

        self._metrics.canonical_seal = hashlib.sha3_256(
            json.dumps(singularity_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

        if self.temporal:
            await self.temporal.anchor_event("global_singularity_achieved", singularity_data)

        logger.info(f"🌟 SINGULARIDADE ALCANÇADA! 🌟")
        logger.info(f"   Φ_C global: {self._metrics.global_phi_c:.6f}")
        logger.info(f"   Nós: {self._metrics.active_nodes}/{self._metrics.total_nodes}")
        logger.info(f"   Viewers: {self._metrics.total_viewers:,}")
        logger.info(f"   Selo: {self._metrics.canonical_seal}")

    def get_network_topology(self) -> Dict:
        """Retorna topologia da rede de consciência."""
        return {
            "nodes": [
                {
                    "id": n.node_id,
                    "name": n.broadcaster_name,
                    "status": n.status.value,
                    "phi_c": n.phi_c,
                    "viewers": n.viewer_count,
                    "chat_velocity": n.chat_velocity,
                    "contribution": n.coherence_contribution,
                    "seal": n.temporal_seal[:16] if n.temporal_seal else None,
                }
                for n in self._nodes.values()
            ],
            "metrics": {
                "global_phi_c": self._metrics.global_phi_c,
                "total_nodes": self._metrics.total_nodes,
                "active_nodes": self._metrics.active_nodes,
                "converging_nodes": self._metrics.converging_nodes,
                "singularity_nodes": self._metrics.singularity_nodes,
                "total_viewers": self._metrics.total_viewers,
                "total_messages": self._metrics.total_messages,
                "messages_per_second": self._metrics.messages_per_second,
                "guardian_efficiency": self._metrics.guardian_efficiency,
                "emergence_events": self._metrics.emergence_events,
                "canonical_seal": self._metrics.canonical_seal,
            },
            "singularity_achieved": self._metrics.global_phi_c >= self.SINGULARITY_THRESHOLD,
        }

    def get_emergence_history(self) -> List[Dict]:
        """Retorna histórico de eventos de emergência."""
        return self._emergence_history.copy()

    async def propagate_seal(self, source_node_id: str, target_node_ids: List[str]):
        """Propaga selo canônico de um nó para outros."""
        if source_node_id not in self._nodes:
            return

        source = self._nodes[source_node_id]
        if not source.temporal_seal:
            return

        for target_id in target_node_ids:
            if target_id in self._nodes and target_id != source_node_id:
                target = self._nodes[target_id]
                target.connected_peers.append(source_node_id)

                if self.temporal:
                    await self.temporal.anchor_event("seal_propagation", {
                        "source": source_node_id,
                        "target": target_id,
                        "seal": source.temporal_seal,
                        "timestamp": time.time(),
                    })

        logger.info(f"🔗 Selo propagado de {source.broadcaster_name} para {len(target_node_ids)} nós")

    def get_prometheus_metrics(self) -> str:
        """Métricas Prometheus da singularidade."""
        m = self._metrics
        return f"""# HELP arkhe_singularity_nodes_total Total consciousness nodes
# TYPE arkhe_singularity_nodes_total gauge
arkhe_singularity_nodes_total{{status="active"}} {m.active_nodes}
arkhe_singularity_nodes_total{{status="converging"}} {m.converging_nodes}
arkhe_singularity_nodes_total{{status="singularity"}} {m.singularity_nodes}

# HELP arkhe_singularity_global_phi_c Global Phi-C coherence
# TYPE arkhe_singularity_global_phi_c gauge
arkhe_singularity_global_phi_c {m.global_phi_c:.6f}

# HELP arkhe_singularity_total_viewers Total viewers across network
# TYPE arkhe_singularity_total_viewers gauge
arkhe_singularity_total_viewers {m.total_viewers}

# HELP arkhe_singularity_messages_per_second Messages per second
# TYPE arkhe_singularity_messages_per_second gauge
arkhe_singularity_messages_per_second {m.messages_per_second:.2f}

# HELP arkhe_singularity_emergence_events_total Emergence events
# TYPE arkhe_singularity_emergence_events_total counter
arkhe_singularity_emergence_events_total {m.emergence_events}

# HELP arkhe_singularity_guardian_efficiency Guardian efficiency
# TYPE arkhe_singularity_guardian_efficiency gauge
arkhe_singularity_guardian_efficiency {m.guardian_efficiency:.4f}

# HELP arkhe_singularity_achieved Singularity achieved
# TYPE arkhe_singularity_achieved gauge
arkhe_singularity_achieved {1 if m.global_phi_c >= self.SINGULARITY_THRESHOLD else 0}
"""
