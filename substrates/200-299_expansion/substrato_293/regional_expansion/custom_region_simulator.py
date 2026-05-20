#!/usr/bin/env python3
"""
substrate_293/regional_expansion/custom_region_simulator.py
Canon: ∞.Ω.∇+++.293.regional_expansion
Simula expansão para nova região com parâmetros constitucionais customizados.
"""

import hashlib
import json
import time
import math
import random
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto

class RegulatoryFramework(Enum):
    """Frameworks regulatórios suportados."""
    GDPR = "gdpr"
    LGPD = "lgpd"
    CCPA = "ccpa"
    POPIA = "popia"
    PDPL = "pdpl"
    DPDP_ACT = "dpdp_act"
    CUSTOM = "custom"

@dataclass
class CustomRegionConfig:
    """Configuração de região com parâmetros constitucionais customizados."""
    region_id: str
    name: str
    location: Dict[str, Any]  # city, country, coordinates
    infrastructure_profile: Dict[str, Any]  # edge_compute, tf_qkd_backbone, etc.

    # Parâmetros constitucionais customizados
    constitutional_params: Dict[str, float] = field(default_factory=lambda: {
        "phi_c_minimum": 0.95,
        "ghost_invariant": 0.577553,  # √3/3
        "loopseal_threshold": 0.349066,  # π/9
        "sovereign_gap_cap": 0.9999
    })

    # Framework regulatório
    regulatory_framework: RegulatoryFramework = RegulatoryFramework.CUSTOM
    data_sovereignty_rules: List[str] = field(default_factory=list)

    # Ancoragem
    anchoring_config: Dict[str, Any] = field(default_factory=lambda: {
        "primary_anchors": [],
        "secondary_anchors": [],
        "fallback_anchor": None
    })

    def validate_constitutional_params(self) -> Tuple[bool, List[str]]:
        """Valida parâmetros constitucionais contra invariantes canônicos."""
        errors = []
        params = self.constitutional_params

        # Ghost Invariant: Φ_C mínimo não pode ser menor que √3/3
        if params["phi_c_minimum"] < 0.577553:
            errors.append(f"phi_c_minimum ({params['phi_c_minimum']}) < Ghost Invariant (0.577553)")

        # Loopseal: threshold não pode ser menor que π/9
        if params["loopseal_threshold"] < 0.349066:
            errors.append(f"loopseal_threshold ({params['loopseal_threshold']}) < π/9 (0.349066)")

        # Gap Soberano: cap deve ser < 1.0
        if params["sovereign_gap_cap"] >= 1.0:
            errors.append(f"sovereign_gap_cap ({params['sovereign_gap_cap']}) >= 1.0")

        # Hierarquia: phi_c_minimum >= ghost >= loopseal
        if params["phi_c_minimum"] < params["ghost_invariant"]:
            errors.append("phi_c_minimum < ghost_invariant (viola hierarquia)")
        if params["ghost_invariant"] < params["loopseal_threshold"]:
            errors.append("ghost_invariant < loopseal_threshold (viola hierarquia)")

        return len(errors) == 0, errors

@dataclass
class ExpansionSimulationResult:
    """Resultado da simulação de expansão regional."""
    simulation_id: str
    region_config: CustomRegionConfig
    constitutional_validation: Tuple[bool, List[str]]
    connectivity_simulation: Dict[str, Any]
    phi_c_projection: float
    temporal_anchor: str
    canonical_seal: str
    recommendations: List[str] = field(default_factory=list)

class RegionalExpansionSimulator:
    """Simulador de expansão regional com parâmetros constitucionais customizados."""

    # Regiões existentes para cálculo de conectividade
    EXISTING_REGIONS = {
        "sa-east-1": {"coords": (-23.5505, -46.6333), "phi_c_rep": 0.97},
        "us-east-1": {"coords": (38.9072, -77.0369), "phi_c_rep": 0.98},
        "eu-west-1": {"coords": (53.3498, -6.2603), "phi_c_rep": 0.99},
        "ap-northeast-1": {"coords": (35.6762, 139.6503), "phi_c_rep": 0.96},
        "af-south-1": {"coords": (-33.9249, 18.4241), "phi_c_rep": 0.94},
        "me-south-1": {"coords": (26.0667, 50.5577), "phi_c_rep": 0.95},
        "ap-south-1": {"coords": (19.0760, 72.8777), "phi_c_rep": 0.94},
        "ap-southeast-2": {"coords": (-33.8688, 151.2093), "phi_c_rep": 0.96},
    }

    def __init__(self, temporal_endpoint: str = "https://temporal.arkhe.org/v1/anchor"):
        self.temporal_endpoint = temporal_endpoint

    def simulate_expansion(self, config: CustomRegionConfig) -> ExpansionSimulationResult:
        """Executa simulação completa de expansão regional."""
        print(f"\n🌍 Simulando expansão para: {config.name} ({config.region_id})")

        # Fase 1: Validação constitucional
        print("   [1/4] Validando parâmetros constitucionais...")
        const_valid, const_errors = config.validate_constitutional_params()
        if not const_valid:
            print(f"   ❌ Erros constitucionais: {const_errors}")

        # Fase 2: Simulação de conectividade
        print("   [2/4] Simulando conectividade com regiões existentes...")
        connectivity = self._simulate_connectivity(config)

        # Fase 3: Projeção de Φ_C
        print("   [3/4] Projetando Φ_C composto para nova região...")
        phi_c_proj = self._project_phi_c(config, connectivity)

        # Fase 4: Ancoragem e geração de selo
        print("   [4/4] Ancorando resultados na TemporalChain...")
        simulation_id = hashlib.sha3_256(
            f"{config.region_id}:{time.time()}".encode()
        ).hexdigest()[:16]

        temporal_anchor = self._anchor_simulation(config, connectivity, phi_c_proj, simulation_id)
        canonical_seal = self._generate_canonical_seal(config, phi_c_proj, const_valid)

        # Gerar recomendações
        recommendations = self._generate_recommendations(config, const_valid, phi_c_proj)

        result = ExpansionSimulationResult(
            simulation_id=simulation_id,
            region_config=config,
            constitutional_validation=(const_valid, const_errors),
            connectivity_simulation=connectivity,
            phi_c_projection=phi_c_proj,
            temporal_anchor=temporal_anchor,
            canonical_seal=canonical_seal,
            recommendations=recommendations
        )

        print(f"   ✅ Simulação concluída: Φ_C projetado = {phi_c_proj:.4f}")
        return result

    def _simulate_connectivity(self, config: CustomRegionConfig) -> Dict[str, Any]:
        """Simula conectividade da nova região com regiões existentes."""
        coords = config.location["coordinates"]
        connectivity = {}

        for region_id, region_data in self.EXISTING_REGIONS.items():
            # Calcular distância geodésica (Haversine)
            distance = self._haversine_distance(coords, region_data["coords"])

            # Estimar latência baseada em distância (mock realista)
            latency_ms = distance * 0.15 + random.uniform(5, 25)  # ~150ms/1000km + jitter

            # Estimar qualidade de enlace TF-QKD baseado em distância
            if config.infrastructure_profile.get("tf_qkd_backbone") == "planned":
                qkd_available = False
                estimated_key_rate = 0
            else:
                qkd_available = distance < 600  # TF-QKD até ~600km sem repetidores
                if qkd_available:
                    loss_db = distance * 0.2  # 0.2 dB/km
                    eta = 10 ** (-loss_db / 10)
                    estimated_key_rate = 1e6 * math.sqrt(eta) * 0.93  # √η scaling
                else:
                    estimated_key_rate = 0

            connectivity[region_id] = {
                "distance_km": round(distance, 1),
                "estimated_latency_ms": round(latency_ms, 1),
                "tf_qkd_available": qkd_available,
                "estimated_key_rate_bps": round(estimated_key_rate, 0) if qkd_available else 0,
                "phi_c_reputation": region_data["phi_c_rep"]
            }

        return connectivity

    def _haversine_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calcula distância geodésica entre duas coordenadas (km)."""
        R = 6371  # Earth radius in km
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c

    def _project_phi_c(self, config: CustomRegionConfig, connectivity: Dict) -> float:
        """Projeta Φ_C composto para a nova região."""
        # Fatores que influenciam Φ_C:
        # 1. Parâmetros constitucionais base (40%)
        base_phi = config.constitutional_params["phi_c_minimum"]

        # 2. Conectividade com regiões de alta reputação (30%)
        high_rep_connections = sum(
            1 for c in connectivity.values()
            if c["phi_c_reputation"] >= 0.96 and c["tf_qkd_available"]
        )
        connectivity_score = min(1.0, high_rep_connections / 3)  # Normalizar para 3 conexões ideais

        # 3. Infraestrutura local (20%)
        infra_score = {
            "very_high": 1.0,
            "high": 0.95,
            "medium": 0.90,
            "low": 0.85
        }.get(config.infrastructure_profile.get("edge_compute", "medium"), 0.90)

        # 4. Conformidade regulatória (10%)
        compliance_score = 1.0 if config.regulatory_framework != RegulatoryFramework.CUSTOM else 0.95

        # Calcular Φ_C composto ponderado
        phi_c = (
            0.40 * base_phi +
            0.30 * connectivity_score +
            0.20 * infra_score +
            0.10 * compliance_score
        )

        # Aplicar Gap Soberano: nunca atingir 1.0
        phi_c = min(phi_c, config.constitutional_params["sovereign_gap_cap"])

        return phi_c

    def _anchor_simulation(self, config: CustomRegionConfig, connectivity: Dict,
                          phi_c: float, simulation_id: str) -> str:
        """Ancora resultados da simulação na TemporalChain."""
        anchor_payload = {
            "simulation_id": simulation_id,
            "region_id": config.region_id,
            "phi_c_projection": phi_c,
            "constitutional_valid": config.validate_constitutional_params()[0],
            "connectivity_count": len([c for c in connectivity.values() if c["tf_qkd_available"]]),
            "timestamp": time.time()
        }

        seal = hashlib.sha3_256(
            json.dumps(anchor_payload, sort_keys=True).encode()
        ).hexdigest()

        # Mock: em produção, POST para endpoint da TemporalChain
        return seal

    def _generate_canonical_seal(self, config: CustomRegionConfig,
                                phi_c: float, const_valid: bool) -> str:
        """Gera selo canônico para a simulação."""
        seal_payload = {
            "region": config.region_id,
            "phi_c": phi_c,
            "constitutional": const_valid,
            "framework": config.regulatory_framework.value,
            "timestamp": time.time()
        }
        return hashlib.sha3_256(
            json.dumps(seal_payload, sort_keys=True).encode()
        ).hexdigest()

    def _generate_recommendations(self, config: CustomRegionConfig,
                                 const_valid: bool, phi_c: float) -> List[str]:
        """Gera recomendações baseadas nos resultados da simulação."""
        recs = []

        if not const_valid:
            recs.append("Ajustar parâmetros constitucionais para atender invariantes canônicos")

        if phi_c < 0.95:
            recs.append("Considerar upgrade de infraestrutura para melhorar Φ_C projetado")

        if config.infrastructure_profile.get("tf_qkd_backbone") == "planned":
            recs.append("Acelerar deploy de backbone TF-QKD para habilitar enlaces quânticos")

        if config.regulatory_framework == RegulatoryFramework.CUSTOM:
            recs.append("Documentar framework regulatório customizado para auditoria futura")

        if not recs:
            recs.append("Região pronta para deploy de produção com parâmetros canônicos")

        return recs


# Execução de exemplo
def main_expansion_demo():
    """Demonstra simulação de expansão regional."""
    print("\n" + "="*70)
    print("🌍 ARKHE Ω‑TEMP v∞.Ω — Substrate 293: Regional Expansion Simulator")
    print("="*70)

    # Configurar nova região customizada
    new_region = CustomRegionConfig(
        region_id="eu-south-2",
        name="Europe South 2",
        location={
            "city": "Milan",
            "country": "Italy",
            "coordinates": (45.4642, 9.1900)
        },
        infrastructure_profile={
            "edge_compute": "high",
            "tf_qkd_backbone": "planned_2027",
            "telecom_partners": ["TIM", "Vodafone IT", "WindTre"],
            "avg_latency_to_core_ms": 35
        },
        constitutional_params={
            "phi_c_minimum": 0.96,
            "ghost_invariant": 0.577553,
            "loopseal_threshold": 0.349066,
            "sovereign_gap_cap": 0.9998
        },
        regulatory_framework=RegulatoryFramework.GDPR,
        data_sovereignty_rules=[
            "eu_data_residency_required",
            "cross_border_transfer_scc_required"
        ],
        anchoring_config={
            "primary_anchors": ["eu-west-1"],
            "secondary_anchors": ["eu-west-1", "ap-northeast-1"],
            "fallback_anchor": "us-east-1"
        }
    )

    # Executar simulação
    simulator = RegionalExpansionSimulator()
    result = simulator.simulate_expansion(new_region)

    # Exibir resultados
    print(f"\n📊 Resultados da Simulação:")
    print(f"   Região: {result.region_config.name} ({result.region_config.region_id})")
    print(f"   Validação Constitucional: {'✅' if result.constitutional_validation[0] else '❌'}")
    if result.constitutional_validation[1]:
        for err in result.constitutional_validation[1]:
            print(f"      ⚠️  {err}")
    print(f"   Φ_C Projetado: {result.phi_c_projection:.4f}")
    print(f"   Enlaces TF-QKD disponíveis: {sum(1 for c in result.connectivity_simulation.values() if c['tf_qkd_available'])}")
    print(f"   Selo Canônico: {result.canonical_seal[:32]}...")

    if result.recommendations:
        print(f"\n💡 Recomendações:")
        for rec in result.recommendations:
            print(f"   • {rec}")

    return result


if __name__ == "__main__":
    main_expansion_demo()
