#!/usr/bin/env python3
"""
Substrato 182: Registro de Agentes Especializados para Domínios Críticos
Expande o ecossistema agêntico para energia, tráfego urbano e sistemas financeiros.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum, auto
import hashlib, time, json, logging

logger = logging.getLogger(__name__)

class AgentDomain(Enum):
    """Domínios especializados para agentes ARKHE."""
    SCADA = "scada"
    ENERGY_GRID = "energy_grid"          # Rede elétrica, smart grid
    URBAN_TRAFFIC = "urban_traffic"       # Semaforização, fluxo veicular
    FINANCIAL_CORE = "financial_core"     # SWIFT, FedWire, PIX, TED
    HEALTHCARE = "healthcare"             # Sistemas hospitalares, IoT médico
    LOGISTICS = "logistics"               # Cadeia de suprimentos, rastreamento

@dataclass
class AgentCapability:
    """Capacidade funcional de um agente."""
    name: str
    description: str
    input_schema: Dict
    output_schema: Dict
    phi_c_requirement: float = 0.95
    requires_consensus: bool = False
    dangerous: bool = False  # Requer MAC se True

@dataclass
class SpecializedAgent:
    """Definição de agente especializado por domínio."""
    agent_id: str
    domain: AgentDomain
    name: str
    description: str
    capabilities: List[AgentCapability]
    memory_config: Dict  # Working, Episodic, Semantic
    guardrail_profile: str  # "standard", "high", "critical"
    phi_c_baseline: float = 0.997
    created_at: float = field(default_factory=time.time)
    temporal_seal: Optional[str] = None

class AgentExpansionRegistry:
    """
    Registra e gerencia expansão de agentes para domínios críticos.

    Funcionalidades:
    • Template de agente por domínio com capacidades pré-definidas
    • Validação de guardrails específicos por domínio
    • Integração com PhiCBus para sincronização de coerência
    • Ancoragem de registro na TemporalChain
    • Suporte a deploy canary com monitoramento Φ_C
    """

    # Templates de agentes por domínio
    DOMAIN_TEMPLATES = {
        AgentDomain.ENERGY_GRID: {
            "name": "Energy Grid Monitor",
            "description": "Monitora rede elétrica, detecta anomalias de carga, coordena resposta a falhas",
            "capabilities": [
                AgentCapability(
                    name="query_grid_status",
                    description="Consulta status de subestações e linhas de transmissão",
                    input_schema={"type": "object", "properties": {"region": {"type": "string"}}},
                    output_schema={"type": "object", "properties": {"load_mw": {"type": "number"}, "status": {"type": "string"}}},
                    phi_c_requirement=0.96,
                ),
                AgentCapability(
                    name="trigger_load_shedding",
                    description="Aciona protocolo de redução de carga em emergência",
                    input_schema={"type": "object", "properties": {"region": {"type": "string"}, "priority": {"type": "string", "enum": ["low", "medium", "high"]}}},
                    output_schema={"type": "object", "properties": {"shed_mw": {"type": "number"}, "affected_customers": {"type": "integer"}}},
                    phi_c_requirement=0.99,
                    requires_consensus=True,
                    dangerous=True,
                ),
            ],
            "guardrail_profile": "critical",
            "phi_c_baseline": 0.998,
        },
        AgentDomain.URBAN_TRAFFIC: {
            "name": "Urban Traffic Optimizer",
            "description": "Otimiza semáforos, gerencia fluxo veicular, responde a incidentes",
            "capabilities": [
                AgentCapability(
                    name="query_traffic_sensors",
                    description="Consulta sensores de fluxo e câmeras de tráfego",
                    input_schema={"type": "object", "properties": {"intersection_id": {"type": "string"}}},
                    output_schema={"type": "object", "properties": {"flow_rate": {"type": "number"}, "congestion_level": {"type": "string"}}},
                    phi_c_requirement=0.95,
                ),
                AgentCapability(
                    name="adjust_signal_timing",
                    description="Ajusta tempos de semáforo para otimizar fluxo",
                    input_schema={"type": "object", "properties": {"intersection_id": {"type": "string"}, "green_time_sec": {"type": "integer"}}},
                    output_schema={"type": "object", "properties": {"new_cycle_time": {"type": "integer"}, "estimated_delay_reduction": {"type": "number"}}},
                    phi_c_requirement=0.97,
                    requires_consensus=False,
                    dangerous=False,
                ),
            ],
            "guardrail_profile": "high",
            "phi_c_baseline": 0.997,
        },
        AgentDomain.FINANCIAL_CORE: {
            "name": "Financial Core Validator",
            "description": "Valida transações interbancárias, detecta fraude, coordena settlement",
            "capabilities": [
                AgentCapability(
                    name="validate_transaction",
                    description="Valida transação financeira contra regras de compliance",
                    input_schema={"type": "object", "properties": {"txn_id": {"type": "string"}, "amount": {"type": "number"}, "currency": {"type": "string"}}},
                    output_schema={"type": "object", "properties": {"valid": {"type": "boolean"}, "risk_score": {"type": "number"}}},
                    phi_c_requirement=0.99,
                ),
                AgentCapability(
                    name="initiate_settlement",
                    description="Inicia processo de settlement interbancário",
                    input_schema={"type": "object", "properties": {"batch_id": {"type": "string"}, "participants": {"type": "array", "items": {"type": "string"}}}},
                    output_schema={"type": "object", "properties": {"settlement_id": {"type": "string"}, "status": {"type": "string"}}},
                    phi_c_requirement=0.999,
                    requires_consensus=True,
                    dangerous=True,
                ),
            ],
            "guardrail_profile": "critical",
            "phi_c_baseline": 0.999,
        },
    }

    def __init__(self, phi_bus=None, temporal_chain=None, guardian=None):
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self.guardian = guardian
        self.registered_agents: Dict[str, SpecializedAgent] = {}

    async def register_agent(
        self,
        domain: AgentDomain,
        custom_config: Optional[Dict] = None,
    ) -> SpecializedAgent:
        """Registra novo agente especializado baseado em template de domínio."""
        if domain not in self.DOMAIN_TEMPLATES:
            raise ValueError(f"Domínio não suportado: {domain}")

        template = self.DOMAIN_TEMPLATES[domain]

        # Mesclar configuração customizada com template
        config = {**template, **(custom_config or {})}

        # Gerar ID único para agente
        agent_id = hashlib.sha3_256(
            f"{domain.value}:{config['name']}:{time.time()}".encode()
        ).hexdigest()[:16]

        agent = SpecializedAgent(
            agent_id=agent_id,
            domain=domain,
            name=config["name"],
            description=config["description"],
            capabilities=config["capabilities"],
            memory_config=config.get("memory_config", {
                "working": "redis",
                "episodic": "chroma",
                "semantic": "neo4j",
            }),
            guardrail_profile=config["guardrail_profile"],
            phi_c_baseline=config["phi_c_baseline"],
        )

        # Validar guardrails específicos do domínio
        guardrail_valid = await self._validate_domain_guardrails(agent)
        if not guardrail_valid:
            raise RuntimeError(f"Guardrails inválidos para domínio {domain.value}")

        # Registrar no registry
        self.registered_agents[agent_id] = agent

        # Ancorar registro na TemporalChain
        if self.temporal:
            agent.temporal_seal = await self.temporal.anchor_event(
                "specialized_agent_registered",
                {
                    "agent_id": agent_id,
                    "domain": domain.value,
                    "name": agent.name,
                    "capabilities_count": len(agent.capabilities),
                    "guardrail_profile": agent.guardrail_profile,
                    "phi_c_baseline": agent.phi_c_baseline,
                    "timestamp": time.time(),
                }
            )

        logger.info(f"✅ Agente registrado: {agent.name} ({agent_id}) | Domínio: {domain.value}")
        return agent

    async def _validate_domain_guardrails(self, agent: SpecializedAgent) -> bool:
        """Valida guardrails específicos por domínio."""
        # Guardrails estáticos: verificar capacidades perigosas
        dangerous_caps = [c for c in agent.capabilities if c.dangerous]
        if dangerous_caps and not all(c.requires_consensus for c in dangerous_caps):
            logger.error(f"❌ Capacidades perigosas sem consenso: {[c.name for c in dangerous_caps]}")
            return False

        # Guardrails dinâmicos: verificar threshold Φ_C adequado ao perfil
        min_phi_c = {"standard": 0.95, "high": 0.97, "critical": 0.99}.get(agent.guardrail_profile, 0.95)
        if agent.phi_c_baseline < min_phi_c:
            logger.error(f"❌ Φ_C baseline {agent.phi_c_baseline} abaixo do mínimo {min_phi_c} para perfil {agent.guardrail_profile}")
            return False

        # Guardrails de consenso: verificar integração com MAC para ações críticas
        if any(c.requires_consensus for c in agent.capabilities):
            if not self.phi_bus:
                logger.error("❌ Agente com capacidades de consenso sem PhiBus configurado")
                return False

        return True

    def get_agent_by_domain(self, domain: AgentDomain) -> List[SpecializedAgent]:
        """Retorna lista de agentes registrados para um domínio."""
        return [a for a in self.registered_agents.values() if a.domain == domain]

    def get_all_agents_summary(self) -> Dict:
        """Retorna resumo de todos os agentes registrados."""
        return {
            "total_agents": len(self.registered_agents),
            "by_domain": {
                domain.value: len([a for a in self.registered_agents.values() if a.domain == domain])
                for domain in AgentDomain
            },
            "by_guardrail_profile": {
                profile: len([a for a in self.registered_agents.values() if a.guardrail_profile == profile])
                for profile in ["standard", "high", "critical"]
            },
            "avg_phi_c_baseline": sum(a.phi_c_baseline for a in self.registered_agents.values()) / max(1, len(self.registered_agents)),
        }