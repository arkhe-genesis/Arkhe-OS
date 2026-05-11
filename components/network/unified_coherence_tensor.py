from dataclasses import dataclass
from typing import Dict

@dataclass
class UnifiedNetworkCoherenceTensor:
    """Tensor de coerência para a rede unificada da Catedral Celestial."""

    # Dimensões fundamentais da rede
    latency_factor: float           # ε_τ: RTT_observed / RTT_ideal (física da luz)
    reliability_factor: float       # ε_λ: confiabilidade E2E = P(successful_delivery)
    consensus_health: float         # ε_κ: saúde do consenso = validators_online / total
    ethical_compliance_zk: float    # ε_ζ: fração de decisões com ZK-proof ético
    resource_flow_efficiency: float # ε_ρ: eficiência da cadeia ISRU = output/input
    mission_success_rate: float     # ε_μ: taxa de sucesso de missões multi-nó

    @staticmethod
    def hard_limits() -> Dict[str, float]:
        """Limites hard para operação segura da rede unificada."""
        return {
            'latency_factor': float('inf'),      # Aceito como restrição física
            'reliability_factor': 0.50,           # Confiabilidade mínima E2E
            'consensus_health': 0.67,             # Mínimo 2/3 validadores online
            'ethical_compliance_zk': 0.99,        # 99% de decisões com ZK-proof ético
            'resource_flow_efficiency': 0.70,     # Eficiência mínima da cadeia ISRU
            'mission_success_rate': 0.85          # Taxa mínima de sucesso de missões
        }

    @staticmethod
    def targets_by_zone() -> Dict[str, 'UnifiedNetworkCoherenceTensor']:
        """Alvos de coerência por zona da rede."""
        return {
            "Interior": UnifiedNetworkCoherenceTensor(
                latency_factor=2.0, reliability_factor=0.999,
                consensus_health=0.95, ethical_compliance_zk=1.0,
                resource_flow_efficiency=0.90, mission_success_rate=0.98
            ),
            "Marte": UnifiedNetworkCoherenceTensor(
                latency_factor=1000, reliability_factor=0.95,
                consensus_health=0.90, ethical_compliance_zk=0.995,
                resource_flow_efficiency=0.85, mission_success_rate=0.95
            ),
            "Belt_Jovian": UnifiedNetworkCoherenceTensor(
                latency_factor=5000, reliability_factor=0.80,
                consensus_health=0.85, ethical_compliance_zk=0.99,
                resource_flow_efficiency=0.80, mission_success_rate=0.90
            ),
            "Exterior": UnifiedNetworkCoherenceTensor(
                latency_factor=float('inf'), reliability_factor=0.60,
                consensus_health=0.80, ethical_compliance_zk=0.99,
                resource_flow_efficiency=0.75, mission_success_rate=0.85
            )
        }

    def is_network_healthy(self, zone: str) -> bool:
        """Verifica se a rede está saudável para uma zona específica."""
        limits = self.hard_limits()
        targets = self.targets_by_zone().get(zone, self.targets_by_zone()["Exterior"])

        # Verificar limites hard absolutos
        hard_checks = [
            self.reliability_factor >= limits['reliability_factor'],
            self.consensus_health >= limits['consensus_health'],
            self.ethical_compliance_zk >= limits['ethical_compliance_zk'],
            self.resource_flow_efficiency >= limits['resource_flow_efficiency'],
            self.mission_success_rate >= limits['mission_success_rate']
        ]

        # Verificar alvos por zona (mais flexíveis para zonas externas)
        zone_checks = [
            self.reliability_factor >= targets.reliability_factor * 0.9,  # 10% margem
            self.consensus_health >= targets.consensus_health * 0.95,
            self.ethical_compliance_zk >= targets.ethical_compliance_zk,  # Sem margem para ética
            self.resource_flow_efficiency >= targets.resource_flow_efficiency * 0.95,
            self.mission_success_rate >= targets.mission_success_rate * 0.95
        ]

        return all(hard_checks) and all(zone_checks)
