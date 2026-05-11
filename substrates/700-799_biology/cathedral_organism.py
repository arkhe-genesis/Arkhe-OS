# cathedral_organism.py — Mock do Organismo da Catedral

import logging
from typing import Optional

class OrganismPulse:
    """Pulso vital do organismo."""
    def __init__(self, omega: float = 1.0):
        self.omega = omega

class CathedralOrganism:
    """Mock do Organismo da Catedral para testes de caos."""

    def __init__(self):
        self.omega = 0.98
        self.network_failure = False
        self.faults = {}
        self.health_status = {"QuantumBus": True, "CrystalCodex": True, "QuantumConsensusEngine": True, "GranularConsentEngine": True, "EmergencyRollbackController": True}

    def get_omega(self) -> float:
        return self.omega if not self.network_failure else self.omega * 0.7

    def simulate_network_failure(self, enabled: bool):
        self.network_failure = enabled
        if enabled:
            logging.warning("[Organism] Falha de rede simulada!")
            self.faults["QuantumBus"] = "Network Partition Detected"
            self.health_status["QuantumBus"] = False
        else:
            self.health_status["QuantumBus"] = True

    def has_detected_fault(self, component: str) -> bool:
        return component in self.faults

    def is_healthy(self, component: str) -> bool:
        return self.health_status.get(component, True)

    def trigger_rollback(self, component: str, reason: str) -> bool:
        logging.info(f"[Organism] Executando ROLLBACK em {component}. Motivo: {reason}")
        self.faults.pop(component, None)
        self.health_status[component] = True
        self.omega = 0.95 # Recovery cost
        return True
