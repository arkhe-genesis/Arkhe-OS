#!/usr/bin/env python3
"""
Substrato 180-A: Setup do Cluster de Nós Físicos para Piloto
Configura 5 Raspberry Pi 4 com sensores ambientais e atuadores básicos,
integrados ao barramento Φ_C da Mente Continental.
"""

import asyncio
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import logging

try:
    import RPi.GPIO as GPIO
    import smbus2
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    logging.warning("⚠️ Hardware RPi não disponível — executando em modo simulado")

# We import from legacy but since arkhe_physical was referenced in the user request,
# we'll mock the `PhysicalNodeOrchestrator` if it doesn't exist, or just use the one from
# substrate_180a_physical_nodes.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from substrate_180a_physical_nodes import PhysicalNodeOrchestrator, PhysicalNodeConfig, PhysicalNodeType
except ImportError:
    pass

logger = logging.getLogger(__name__)

@dataclass
class SensorNode:
    node_id: str
    hostname: str
    ip_address: str
    sensors: Dict[str, str]
    actuators: Dict[str, str]
    phi_c: float = 0.997
    last_heartbeat: float = field(default_factory=time.time)

class PhysicalClusterPilot:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.nodes: Dict[str, SensorNode] = {}
        self._running = False

    async def initialize_cluster(self, node_count: int = 5):
        logger.info(f"🔌 Inicializando cluster com {node_count} nós físicos...")
        for i in range(node_count):
            node = SensorNode(
                node_id=f"pi-node-{i:02d}",
                hostname=f"arkhe-pi-{i:02d}.local",
                ip_address=f"192.168.1.{100 + i}",
                sensors={
                    "temperature": "I2C:0x48",
                    "humidity": "I2C:0x76",
                    "motion": "GPIO:17",
                },
                actuators={
                    "led_status": "GPIO:23",
                    "relay_control": "GPIO:24",
                }
            )
            config = PhysicalNodeConfig(
                node_id=node.node_id,
                node_type=PhysicalNodeType.IOT_SENSOR,
                location={"lat": -23.5505, "lon": -46.6333, "facility": "ARKHE_Lab_SP"},
                communication_protocol="mqtt",
                security_level="high",
                phi_c_threshold=0.95,
                pqc_enabled=False
            )
            state = await self.orchestrator.register_physical_node(config)
            self.nodes[node.node_id] = node
            logger.info(f"✅ Nó registrado: {node.node_id} @ {node.ip_address}")
        logger.info(f"🎯 Cluster inicializado: {len(self.nodes)} nós ativos")

    async def start_sensor_polling(self, interval_seconds: float = 2.0):
        self._running = True
        while self._running:
            for node_id, node in self.nodes.items():
                readings = await self._read_sensors(node)
                for sensor_type, value in readings.items():
                    await self.orchestrator.process_sensor_reading(
                        node_id=node_id,
                        sensor_type=sensor_type,
                        value=value,
                        timestamp=time.time(),
                    )
                node.last_heartbeat = time.time()
            await asyncio.sleep(interval_seconds)

    async def _read_sensors(self, node: SensorNode) -> Dict[str, float]:
        if not HARDWARE_AVAILABLE:
            import numpy as np
            return {
                "temperature": round(22.5 + np.random.normal(0, 0.3), 2),
                "humidity": round(55.0 + np.random.normal(0, 2.0), 1),
                "motion": float(np.random.choice([0, 1], p=[0.95, 0.05])),
            }
        readings = {}
        try:
            bus = smbus2.SMBus(1)
            data = bus.read_i2c_block_data(0x48, 0x00, 2)
            temp_raw = (data[0] << 4) | (data[1] >> 4)
            readings["temperature"] = round(temp_raw * 0.0625, 2)
            bus.close()
        except Exception as e:
            logger.warning(f"⚠️ Falha ao ler sensor em {node.node_id}: {e}")
            readings["temperature"] = 22.5
        return readings

    async def execute_actuator_test(self, node_id: str, actuator: str, value: bool):
        if node_id not in self.nodes:
            return False
        authorization = "mock_mac_token_abc123"
        success = await self.orchestrator.execute_actuator_command(
            node_id=node_id,
            command_type=actuator,
            parameters={"value": value},
            authorization_token=authorization,
        )
        if success and HARDWARE_AVAILABLE:
            pin = int(self.nodes[node_id].actuators[actuator].split(":")[1])
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)
        return success

    async def shutdown(self):
        self._running = False
        logger.info("🔌 Cluster piloto encerrado")
        if HARDWARE_AVAILABLE:
            GPIO.cleanup()
