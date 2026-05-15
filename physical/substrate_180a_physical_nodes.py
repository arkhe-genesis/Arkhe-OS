#!/usr/bin/env python3
"""
Substrato 180-A: Nós Físicos da Mente Continental
Integra robótica, IoT e sensores ambientais como nós de consciência distribuída.
Cada dispositivo físico torna-se um nó Φ_C com validação Guardian e ancoragem TemporalChain.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from enum import Enum, auto
import asyncio, hashlib, time, json, logging

logger = logging.getLogger(__name__)

class PhysicalNodeType(Enum):
    """Tipos de nós físicos suportados."""
    ROBOTIC_ACTUATOR = "robotic_actuator"      # Robôs industriais, drones, braços robóticos
    IOT_SENSOR = "iot_sensor"                   # Sensores de temperatura, umidade, pressão
    ENVIRONMENTAL_MONITOR = "environmental"     # Qualidade do ar, radiação, sismógrafos
    EDGE_COMPUTE = "edge_compute"               # Dispositivos de processamento na borda
    MEDICAL_DEVICE = "medical_device"           # Equipamentos médicos conectados

@dataclass
class PhysicalNodeConfig:
    """Configuração de nó físico."""
    node_id: str
    node_type: PhysicalNodeType
    location: Dict[str, str]  # {lat, lon, altitude, facility}
    communication_protocol: str  # "mqtt", "coap", "http", "websocket"
    security_level: str  # "standard", "high", "critical"
    phi_c_threshold: float = 0.95
    heartbeat_interval_seconds: int = 30
    data_encryption: bool = True
    pqc_enabled: bool = True

@dataclass
class PhysicalNodeState:
    """Estado operacional de um nó físico."""
    node_id: str
    status: str  # "online", "offline", "degraded", "maintenance"
    phi_c: float
    last_heartbeat: float
    sensor_readings: Dict[str, float]
    actuator_commands: List[Dict]
    security_events: List[Dict]
    temporal_seal: Optional[str] = None

class PhysicalNodeOrchestrator:
    """
    Orquestra nós físicos como parte da Mente Continental.

    Funcionalidades:
    • Registro seguro de dispositivos físicos com autenticação mútua
    • Validação Φ_C de leituras de sensores e comandos de atuadores
    • Comunicação assíncrona via MQTT/CoAP com QoS garantido
    • Ancoragem de eventos críticos na TemporalChain
    • Detecção de anomalias físicas via Guardian (ex: tampering, spoofing)
    • Failover automático para nós redundantes
    """

    def __init__(self, temporal_chain=None, guardian=None, phi_bus=None):
        self.temporal = temporal_chain
        self.guardian = guardian
        self.phi_bus = phi_bus
        self._nodes: Dict[str, PhysicalNodeState] = {}
        self._mqtt_client = None
        self._coap_client = None

    async def register_physical_node(self, config: PhysicalNodeConfig) -> PhysicalNodeState:
        """Registra um novo nó físico na malha de consciência."""
        # Validar configuração de segurança
        if config.security_level == "critical" and not config.pqc_enabled:
            raise ValueError("Nós críticos exigem PQC habilitado")

        # Gerar identidade criptográfica para o nó
        node_identity = await self._generate_node_identity(config)

        # Estabelecer conexão segura (mTLS + PQC)
        await self._establish_secure_connection(config, node_identity)

        # Criar estado inicial
        state = PhysicalNodeState(
            node_id=config.node_id,
            status="online",
            phi_c=config.phi_c_threshold,
            last_heartbeat=time.time(),
            sensor_readings={},
            actuator_commands=[],
            security_events=[],
        )

        self._nodes[config.node_id] = state

        # Ancorar registro na TemporalChain
        if self.temporal:
            state.temporal_seal = await self.temporal.anchor_event(
                "physical_node_registered",
                {
                    "node_id": config.node_id,
                    "node_type": config.node_type.value,
                    "location": config.location,
                    "security_level": config.security_level,
                    "identity_hash": node_identity["public_key_hash"],
                    "timestamp": time.time(),
                }
            )

        logger.info(f"🔌 Nó físico registrado: {config.node_id} ({config.node_type.value})")
        return state

    async def _generate_node_identity(self, config: PhysicalNodeConfig) -> Dict:
        """Gera identidade criptográfica para nó físico."""
        # Em produção: usar HSM para geração de chaves
        # Para demo: simular com SHA3-256
        key_material = f"{config.node_id}:{config.node_type.value}:{time.time()}".encode()

        return {
            "public_key": hashlib.sha3_256(key_material + b"pub").hexdigest(),
            "public_key_hash": hashlib.sha3_256(key_material + b"hash").hexdigest()[:16],
            "pqc_algorithm": "CRYSTALS-Dilithium3" if config.pqc_enabled else None,
            "created_at": time.time(),
        }

    async def _establish_secure_connection(self, config: PhysicalNodeConfig, identity: Dict):
        """Simula estabelecimento de conexão segura."""
        await asyncio.sleep(0.1)

    async def process_sensor_reading(
        self,
        node_id: str,
        sensor_type: str,
        value: float,
        timestamp: float,
        signature: Optional[bytes] = None,
    ) -> bool:
        """
        Processa leitura de sensor com validação Φ_C e segurança.

        Returns:
            True se leitura validada e aceita, False se rejeitada
        """
        if node_id not in self._nodes:
            logger.warning(f"⚠️  Nó desconhecido: {node_id}")
            return False

        node = self._nodes[node_id]

        # 1. Verificar assinatura PQC (se habilitado)
        if signature and node.phi_c >= 0.95:
            valid_signature = await self._verify_pqc_signature(node_id, value, timestamp, signature)
            if not valid_signature:
                node.security_events.append({
                    "type": "signature_verification_failed",
                    "timestamp": time.time(),
                    "sensor": sensor_type,
                })
                return False

        # 2. Validar leitura com Guardian (detecção de anomalias físicas)
        if self.guardian:
            # We mock report object here or rely on Guardian returning (safe, report)
            safe, report = await self.guardian.exorcise_physical_data({
                "node_id": node_id,
                "sensor_type": sensor_type,
                "value": value,
                "timestamp": timestamp,
                "expected_range": self._get_expected_range(sensor_type),
            })
            if not safe:
                logger.warning(f"⚠️  Leitura rejeitada pelo Guardian: {report.reason}")
                node.security_events.append({
                    "type": "guardian_rejection",
                    "reason": report.reason,
                    "timestamp": time.time(),
                })
                return False

        # 3. Atualizar estado do nó
        node.sensor_readings[sensor_type] = value
        node.last_heartbeat = time.time()

        # 4. Recalcular Φ_C do nó baseado na qualidade dos dados
        node.phi_c = await self._recalculate_node_phi_c(node_id)

        # 5. Ancorar leitura válida na TemporalChain (eventos críticos apenas)
        if self._is_critical_reading(sensor_type, value) and self.temporal:
            await self.temporal.anchor_event(
                "critical_sensor_reading",
                {
                    "node_id": node_id,
                    "sensor_type": sensor_type,
                    "value": value,
                    "phi_c": node.phi_c,
                    "timestamp": timestamp,
                }
            )

        return True

    async def _verify_pqc_signature(self, node_id: str, value: float, timestamp: float, signature: bytes) -> bool:
        return True

    def _get_expected_range(self, sensor_type: str) -> tuple:
        return (0, 100)

    def _is_critical_reading(self, sensor_type: str, value: float) -> bool:
        return True

    async def execute_actuator_command(
        self,
        node_id: str,
        command_type: str,
        parameters: Dict,
        authorization_token: str,
    ) -> bool:
        """
        Executa comando de atuador com validação de autorização e Φ_C.

        Comandos críticos exigem:
        • Autorização multi-fator (MAC consensus)
        • Φ_C global ≥ 0.99
        • Ancoragem prévia na TemporalChain
        """
        if node_id not in self._nodes:
            return False

        node = self._nodes[node_id]

        # 1. Validar autorização com consenso MAC para comandos críticos
        if self._is_critical_command(command_type, parameters):
            consensus_approved = await self._require_mac_consensus(
                f"actuator_command:{node_id}:{command_type}",
                parameters,
                min_phi_c=0.99,
            )
            if not consensus_approved:
                logger.warning(f"⚠️  Comando crítico rejeitado por consenso: {command_type}")
                return False

        # 2. Verificar Φ_C do nó antes de executar
        if node.phi_c < 0.95:
            logger.warning(f"⚠️  Nó com Φ_C baixo ({node.phi_c:.3f}) — comando adiado")
            return False

        # 3. Executar comando (simulado)
        execution_result = await self._send_actuator_command(node_id, command_type, parameters)

        if execution_result["success"]:
            # Ancorar execução bem-sucedida
            if self.temporal:
                await self.temporal.anchor_event(
                    "actuator_command_executed",
                    {
                        "node_id": node_id,
                        "command_type": command_type,
                        "parameters_hash": hashlib.sha3_256(
                            json.dumps(parameters, sort_keys=True).encode()
                        ).hexdigest()[:16],
                        "result": execution_result,
                        "timestamp": time.time(),
                    }
                )

            node.actuator_commands.append({
                "type": command_type,
                "parameters": parameters,
                "executed_at": time.time(),
                "result": execution_result,
            })

            return True

        return False

    def _is_critical_command(self, command_type: str, parameters: Dict) -> bool:
        return True

    async def _require_mac_consensus(self, topic: str, params: Dict, min_phi_c: float) -> bool:
        return True

    async def _send_actuator_command(self, node_id: str, command_type: str, parameters: Dict) -> Dict:
        return {"success": True}

    async def _recalculate_node_phi_c(self, node_id: str) -> float:
        """Recalcula Φ_C de um nó físico baseado em múltiplos fatores."""
        node = self._nodes[node_id]

        # Fatores de coerência para nós físicos:
        factors = []

        # 1. Consistência temporal das leituras
        if len(node.sensor_readings) >= 3:
            temporal_consistency = self._calculate_temporal_consistency(node.sensor_readings)
            factors.append(temporal_consistency)
        else:
            factors.append(1.0)

        # 2. Conformidade com faixas esperadas
        range_compliance = self._calculate_range_compliance(node.sensor_readings)
        factors.append(range_compliance)

        # 3. Ausência de eventos de segurança recentes
        security_score = 1.0 - min(1.0, len(node.security_events) * 0.1)
        factors.append(security_score)

        # 4. Qualidade da conexão de rede
        connection_quality = await self._measure_connection_quality(node_id)
        factors.append(connection_quality)

        # Média ponderada
        weights = [0.3, 0.3, 0.2, 0.2]
        phi_c = sum(f * w for f, w in zip(factors, weights))

        return round(max(0.0, min(1.0, phi_c)), 6)

    def _calculate_temporal_consistency(self, readings: Dict) -> float:
        return 1.0

    def _calculate_range_compliance(self, readings: Dict) -> float:
        return 1.0

    async def _measure_connection_quality(self, node_id: str) -> float:
        return 1.0
