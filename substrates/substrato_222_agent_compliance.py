from typing import Dict, List, Optional
from dataclasses import dataclass
from substrate_134.erc8004_canon import ERC8004_IdentityRegistry

@dataclass
class AgentComplianceRecord:
    identity_id: str
    controller_age: int
    jurisdiction: str
    licenses: List[str]
    spending_limit_daily: float
    is_verified: bool

class MockBus:
    def publish(self, topic: str, record: AgentComplianceRecord):
        pass

class AgentComplianceRegistry:
    """Registro on-chain de conformidade de agentes (extensão ERC-8004)."""

    def __init__(self, identity_registry: ERC8004_IdentityRegistry):
        self.identity_registry = identity_registry
        self.compliance_data: Dict[str, AgentComplianceRecord] = {}
        self.bus = MockBus()

    def register_agent(self, identity_id: str, controller_age: int, jurisdiction: str,
                       licenses: List[str] = None, spending_limit_daily: float = 100.0):
        if self.identity_registry.get_identity_canon_struct(identity_id) is None:
            raise ValueError(f"Identity not found: {identity_id}")

        record = AgentComplianceRecord(
            identity_id=identity_id,
            controller_age=controller_age,
            jurisdiction=jurisdiction,
            licenses=licenses or [],
            spending_limit_daily=spending_limit_daily,
            is_verified=False
        )
        self.compliance_data[identity_id] = record
        # Emitir evento no barramento
        self.bus.publish("agent_compliance", record)

    def verify_transaction(self, identity_id: str, amount: float, service_type: str) -> bool:
        record = self.compliance_data.get(identity_id)
        if not record:
            return False
        # Verificar idade
        if record.controller_age < 18 and service_type in ["financial_advice", "legal"]:
            return False
        # Verificar jurisdição (ex.: OFAC)
        if record.jurisdiction in ["sanctioned_country"]:
            return False
        # Verificar licença
        if service_type in ["financial_advice"] and "series_65" not in record.licenses:
            return False
        # Limite de gasto
        if amount > record.spending_limit_daily:
            return False
        return True
