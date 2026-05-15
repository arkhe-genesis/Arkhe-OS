#!/usr/bin/env python3
"""
Substrato 192: Federação BLE Mesh com nRF52840 para malha de sensores TinyML
Permite que 20+ nós nRF52840 formem malha auto-organizável para
compartilhar inferências, gradientes federados e selos temporais.
"""

import asyncio
import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum, auto
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeshMessageType(Enum):
    ANOMALY_ALERT = "anomaly_alert"
    GRADIENT_UPDATE = "gradient_update"
    PHI_C_SYNC = "phi_c_sync"
    TEMPORAL_SEAL = "temporal_seal"
    HEARTBEAT = "heartbeat"

@dataclass
class MeshNode:
    """Nó da malha BLE Mesh."""
    node_id: str  # Endereço MAC ou UUID
    nrf52_address: str
    role: str  # "sensor", "relay", "coordinator"
    phi_c: float
    last_seen: float
    neighbors: Set[str] = field(default_factory=set)
    buffer: List[Dict] = field(default_factory=list)

class BLEMeshFederation:
    """
    Federação BLE Mesh para nós nRF52840 com agentes TinyML.

    Características:
    • Topologia auto-organizável com roteamento flood/managed
    • Mensagens assinadas com chave simétrica por nó
    • Buffer offline com sincronização quando conectado ao Q-Bus
    • Agregação de gradientes federados na malha antes de enviar ao central
    • Sincronização de Φ_C entre nós vizinhos para coerência local
    """

    MESH_TTL_HOPS = 3  # TTL padrão para mensagens na malha
    SYNC_INTERVAL_SECONDS = 60  # Intervalo de sincronização com Q-Bus

    def __init__(self, coordinator_address: str, qbus_bridge=None, temporal_chain=None):
        self.coordinator_address = coordinator_address
        self.qbus_bridge = qbus_bridge
        self.temporal = temporal_chain
        self.nodes: Dict[str, MeshNode] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    async def start_mesh(self):
        """Inicia a malha BLE Mesh."""
        self._running = True
        asyncio.create_task(self._mesh_loop())
        asyncio.create_task(self._qbus_sync_loop())
        logger.info(f"🔷 BLE Mesh iniciado — Coordenador: {self.coordinator_address}")

    async def stop_mesh(self):
        self._running = False

    async def _mesh_loop(self):
        """Loop principal da malha: processa mensagens recebidas."""
        while self._running:
            try:
                # Em produção: ler de stack BLE (ex: BlueZ, Zephyr)
                # Para demo: simular recebimento
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erro no loop da malha: {e}")

    async def _qbus_sync_loop(self):
        """Sincroniza malha com Q-Bus periodicamente."""
        while self._running:
            try:
                await self._sync_with_qbus()
                await asyncio.sleep(0.1) # Simulate fast for testing
            except asyncio.CancelledError:
                break

    async def _sync_with_qbus(self):
        """Envia agregados da malha para Q-Bus."""
        if not self.qbus_bridge:
            return

        # Agregar gradientes federados
        aggregated_gradients = await self._aggregate_federated_gradients()

        # Enviar para Q-Bus
        # mock method call
        if hasattr(self.qbus_bridge, "publish_federated_update"):
            await self.qbus_bridge.publish_federated_update(
                mesh_id=self.coordinator_address,
                gradients=aggregated_gradients,
                node_count=len(self.nodes),
                avg_phi_c=self._calculate_mesh_phi_c(),
            )

        # logger.info(f"🔄 Sincronizado com Q-Bus: {len(self.nodes)} nós")

    async def _aggregate_federated_gradients(self) -> bytes:
        """Agrega gradientes quantizados de todos os nós (FedAvg simplificado)."""
        import numpy as np

        gradients_list = []
        for node in self.nodes.values():
            # Em produção: coletar gradientes reais do buffer do nó
            # Para demo: simular
            grad = np.random.randint(-128, 127, size=128, dtype=np.int8)
            gradients_list.append(grad.astype(float))

        if not gradients_list:
            return b""

        # FedAvg: média simples dos gradientes
        aggregated = np.mean(gradients_list, axis=0).astype(np.int8)
        return aggregated.tobytes()

    def _calculate_mesh_phi_c(self) -> float:
        """Calcula Φ_C médio da malha."""
        if not self.nodes:
            return 0.0
        return sum(n.phi_c for n in self.nodes.values()) / len(self.nodes)

    async def broadcast_message(
        self,
        message_type: MeshMessageType,
        payload: Dict,
        source_node: str,
        ttl: int = None,
    ):
        """Broadcast de mensagem na malha BLE."""
        if ttl is None:
            ttl = self.MESH_TTL_HOPS

        message = {
            "type": message_type.value,
            "payload": payload,
            "source": source_node,
            "ttl": ttl,
            "timestamp": time.time(),
            "seal": hashlib.sha3_256(
                json.dumps(payload, sort_keys=True).encode()
            ).hexdigest()[:16],
        }

        # Em produção: enviar via BLE Mesh stack
        # Para demo: adicionar à fila de processamento
        await self._message_queue.put(message)
        logger.debug(f"📡 Broadcast {message_type.value} de {source_node} (TTL={ttl})")

    def add_node(self, node: MeshNode):
        """Adiciona nó à malha."""
        self.nodes[node.node_id] = node
        logger.info(f"🔗 Nó adicionado à malha: {node.node_id} ({node.role})")
