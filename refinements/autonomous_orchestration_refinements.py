#!/usr/bin/env python3
"""Orquestração autônoma refinada – consenso, healing multi‑agente, circuit breakers – Substrato 199.5"""

import asyncio, logging, time, random
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class ConsensusPolicy(Enum):
    MAJORITY = "majority"
    UNANIMOUS = "unanimous"
    WEIGHTED_PHI = "weighted_phi"

@dataclass
class SentinelAgent:
    agent_id: str
    role: str  # detection, compliance, healing, llm_ops
    phi_c: float
    vote_weight: float = 1.0

class ConsensusPolicyEngine:
    """Define políticas de consenso entre módulos Sentinel."""
    def __init__(self, policy: ConsensusPolicy = ConsensusPolicy.WEIGHTED_PHI):
        self.policy = policy
        self.agents: Dict[str, SentinelAgent] = {}

    def register_agent(self, agent: SentinelAgent):
        self.agents[agent.agent_id] = agent

    def reach_decision(self, proposal: Dict, votes: Dict[str, bool]) -> bool:
        """Retorna True se consenso atingido segundo a política."""
        if self.policy == ConsensusPolicy.MAJORITY:
            return sum(votes.values()) > len(votes) / 2
        elif self.policy == ConsensusPolicy.UNANIMOUS:
            return all(votes.values())
        elif self.policy == ConsensusPolicy.WEIGHTED_PHI:
            total_weight = sum(a.phi_c for a in self.agents.values() if a.agent_id in votes)
            approval_weight = sum(self.agents[aid].phi_c for aid, v in votes.items() if v)
            return approval_weight / total_weight >= 0.7
        return False

class MultiAgentHealingCoordinator:
    """Coordena auto‑healing envolvendo múltiplos agentes (detecção → compliance → healing)."""
    def __init__(self, healing_orchestrator, consensus_engine):
        self.healing = healing_orchestrator
        self.consensus = consensus_engine

    async def coordinate_healing(self, anomaly_alert: Dict):
        # 1. Detection Agent propõe ação
        proposed_action = anomaly_alert.get("suggested_healing")
        # 2. Compliance Agent valida conformidade
        compliance_vote = True  # Mock
        # 3. Healing Agent confirma viabilidade
        healing_vote = True
        votes = {"detection": True, "compliance": compliance_vote, "healing": healing_vote}
        if self.consensus.reach_decision(anomaly_alert, votes):
            logger.info(f"✅ Consenso alcançado para healing: {proposed_action}")
            await self.healing.execute_action(proposed_action, anomaly_alert)
        else:
            logger.warning(f"❌ Consenso rejeitado para ação {proposed_action}")

class CrossServiceCircuitBreaker:
    """Circuit breakers cross‑serviço baseados em métricas Φ_C."""
    def __init__(self, phi_bus=None):
        self.phi_bus = phi_bus
        self.circuits: Dict[str, Dict] = {}

    async def check(self, service_id: str, phi_c_threshold: float = 0.85) -> bool:
        """Retorna False se circuito aberto (serviço deve ser isolado)."""
        circuit = self.circuits.setdefault(service_id, {"failures": 0, "state": "closed", "last_failure": 0})
        # Simulação de verificação de saúde via Φ‑Bus
        if self.phi_bus:
            health = await self.phi_bus.get_service_health(service_id)
            if health.get("phi_c", 1.0) < phi_c_threshold:
                circuit["failures"] += 1
                circuit["last_failure"] = time.time()
                if circuit["failures"] >= 3:
                    circuit["state"] = "open"
                    logger.error(f"🔴 Circuit breaker ABERTO para {service_id}")
                    return False
        return True

    async def reset(self, service_id: str):
        if service_id in self.circuits:
            self.circuits[service_id]["failures"] = 0
            self.circuits[service_id]["state"] = "closed"
