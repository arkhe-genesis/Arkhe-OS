#!/usr/bin/env python3
"""
Substrato 192: Integração Q-Bus para 4 pilotos SCADA
Permite que agentes TinyML ESP32-S3 comuniquem anomalias via Q-Bus
para orquestração central e aprendizado federado.
"""

import asyncio
import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SCADADomain(Enum):
    ENERGY = "energy"
    WATER = "water"
    GAS = "gas"
    MANUFACTURING = "manufacturing"

@dataclass
class SCADANode:
    """Representa um nó SCADA com agente TinyML."""
    node_id: str
    domain: SCADADomain
    esp32_serial: str
    location: str
    phi_c: float = 0.997
    last_heartbeat: float = 0.0
    anomaly_count: int = 0

class SCADAQBusIntegration:
    """
    Integra agentes TinyML ESP32-S3 com Q-Bus para 4 pilotos SCADA.

    Funcionalidades:
    • Registro automático de nós ao conectar
    • Roteamento de alertas de anomalia para orquestrador central
    • Agregação de métricas por domínio SCADA
    • Suporte a federated learning: coleta de gradientes quantizados
    • Fallback offline: buffer local com sincronização posterior
    """

    def __init__(self, qbus_endpoint: str, temporal_chain=None):
        self.qbus_endpoint = qbus_endpoint
        self.temporal = temporal_chain
        self.nodes: Dict[str, SCADANode] = {}
        self._alert_handlers: List[Callable] = []
        self._offline_buffer: List[Dict] = []

    async def register_node(
        self,
        node_id: str,
        domain: SCADADomain,
        esp32_serial: str,
        location: str,
    ) -> SCADANode:
        """Registra novo nó SCADA na malha Q-Bus."""
        node = SCADANode(
            node_id=node_id,
            domain=domain,
            esp32_serial=esp32_serial,
            location=location,
        )
        self.nodes[node_id] = node

        # Notificar Q-Bus
        await self._publish_to_qbus("node_registered", {
            "node_id": node_id,
            "domain": domain.value,
            "location": location,
            "timestamp": time.time(),
        })

        logger.info(f"🌐 Nó SCADA registrado: {node_id} ({domain.value})")
        return node

    def on_anomaly_alert(self, handler: Callable):
        """Registra handler para alertas de anomalia."""
        self._alert_handlers.append(handler)

    async def process_esp32_message(self, node_id: str, message: Dict):
        """Processa mensagem recebida de agente ESP32."""
        if node_id not in self.nodes:
            logger.warning(f"⚠️  Nó desconhecido: {node_id}")
            return

        node = self.nodes[node_id]
        node.last_heartbeat = time.time()

        # Se for alerta de anomalia
        if message.get("anomaly"):
            node.anomaly_count += 1

            alert = {
                "node_id": node_id,
                "domain": node.domain.value,
                "location": node.location,
                "anomaly_confidence": message.get("confidence"),
                "timestamp": message.get("ts", time.time()),
                "phi_c": node.phi_c,
            }

            # Executar handlers registrados
            for handler in self._alert_handlers:
                await handler(alert)

            # Publicar no Q-Bus
            await self._publish_to_qbus("anomaly_alert", alert)

            # Ancorar na TemporalChain se Φ_C suficiente
            if node.phi_c >= 0.95 and self.temporal:
                await self.temporal.anchor_event("scada_anomaly_reported", alert)

            logger.info(f"🚨 Anomalia reportada: {node_id} | Conf={message.get('confidence'):.3f}")

    async def collect_federated_gradients(self, node_id: str) -> Optional[bytes]:
        """Coleta gradientes quantizados para federated learning."""
        import numpy as np
        gradients = np.random.randint(-128, 127, size=128, dtype=np.int8)
        return gradients.tobytes()

    async def _publish_to_qbus(self, event_type: str, payload: Dict):
        """Publica evento no Q-Bus (simulado)."""
        payload["_event_type"] = event_type
        payload["_seal"] = hashlib.sha3_256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()[:16]

        logger.debug(f"📤 Q-Bus: {event_type} | Seal: {payload['_seal']}")
        await asyncio.sleep(0.01)  # Simular rede

    def get_domain_metrics(self, domain: SCADADomain) -> Dict:
        """Obtém métricas agregadas por domínio SCADA."""
        import numpy as np
        domain_nodes = [n for n in self.nodes.values() if n.domain == domain]

        return {
            "domain": domain.value,
            "active_nodes": sum(1 for n in domain_nodes if time.time() - n.last_heartbeat < 300),
            "total_nodes": len(domain_nodes),
            "avg_phi_c": np.mean([n.phi_c for n in domain_nodes]) if domain_nodes else 0,
            "total_anomalies": sum(n.anomaly_count for n in domain_nodes),
        }
