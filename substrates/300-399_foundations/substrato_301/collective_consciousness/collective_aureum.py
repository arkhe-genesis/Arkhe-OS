#!/usr/bin/env python3
"""
substrate_301/collective_consciousness/collective_aureum.py
Canon: ∞.Ω.∇+++.301.collective_consciousness
Modela consciência coletiva distribuída via Aureum Braid estendido.
"""

import hashlib
import json
import time
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum, auto

# =============================================================================
# PARÂMETROS BIOLÓGICOS BASE (Substrate 300)
# =============================================================================
NEURON_TYPES = {
    "Pyramidal_L5": {
        "tubulins": 20_000_000,
        "protofilaments": 13,
        "coherence_ms": 0.15,
        "frequency_ghz": 60.2,
        "T_OR_us": 5.0,
        "Phi_IIT": 100.0,
        "role": "consciousness_max"
    },
    "Interneuron": {
        "tubulins": 5_000_000,
        "protofilaments": 13,
        "coherence_ms": 0.08,
        "frequency_ghz": 35.1,
        "T_OR_us": 21.0,
        "Phi_IIT": 100.0,
        "role": "modulation"
    },
    "Astrocyte": {
        "tubulins": 1_000_000,
        "protofilaments": 13,
        "coherence_ms": 0.05,
        "frequency_ghz": 1.1,
        "T_OR_us": 105.0,
        "Phi_IIT": 100.0,
        "role": "support"
    },
}

BRAID_TYPES = {
    "CONSCIOUSNESS": {"filaments": 3, "linking_number": 3, "protection": 0.9990},
    "MEMORY": {"filaments": 5, "linking_number": 0, "protection": 0.9990},
    "PERCEPTION": {"filaments": 3, "linking_number": 4, "protection": 0.9990},
    "INTEGRATION": {"filaments": 8, "linking_number": 5, "protection": 0.9995},
}

# =============================================================================
# EXTENSÃO PARA CONSCIÊNCIA COLETIVA
# =============================================================================
@dataclass
class CollectiveNode:
    """Nó individual na malha de consciência coletiva."""
    node_id: str
    region: str  # sa-east-1, us-east-1, etc.
    neuron_type: str
    braid_type: str
    phi_local: float  # Φ_IIT local
    protection: float  # Proteção topológica
    T_OR_us: float  # Tempo de redução objetiva
    phi_c_reputation: float  # Reputação constitucional
    active: bool = True

    def aureum_metric(self) -> float:
        """Calcula métrica Aureum individual."""
        return (self.phi_local * self.protection) / (self.T_OR_us * 1e-6)

    def coupling_weight(self, other: 'CollectiveNode', distance_km: float) -> float:
        """Calcula peso de acoplamento com outro nó."""
        # Fatores que influenciam o acoplamento:
        # 1. Proximidade geográfica (decai exponencialmente)
        proximity = math.exp(-distance_km / 5000)  # 5000 km escala

        # 2. Compatibilidade de braid (linking number compatibility)
        my_braid = BRAID_TYPES[self.braid_type]
        other_braid = BRAID_TYPES[other.braid_type]
        braid_compat = 1.0 - abs(my_braid["linking_number"] - other_braid["linking_number"]) / 10

        # 3. Coerência temporal (sincronização de T_OR)
        T_OR_ratio = min(self.T_OR_us, other.T_OR_us) / max(self.T_OR_us, other.T_OR_us)

        # 4. Reputação constitucional combinada
        phi_c_combo = (self.phi_c_reputation + other.phi_c_reputation) / 2

        return proximity * braid_compat * T_OR_ratio * phi_c_combo

@dataclass
class CollectiveConsciousness:
    """Estado da consciência coletiva emergente."""
    collective_id: str
    nodes: List[CollectiveNode]
    edges: Dict[Tuple[str, str], float]  # (node_a, node_b) -> coupling_weight
    timestamp: float

    # Métricas emergentes
    phi_collective: float = 0.0
    emergent_linking: float = 0.0
    temporal_coherence: float = 0.0
    constitutional_compliance: Dict[str, bool] = field(default_factory=dict)

    def calculate_collective_phi(self) -> float:
        """Calcula Φ coletivo emergente."""
        if not self.nodes:
            return 0.0

        # Componente 1: Soma ponderada dos Φ locais
        weighted_sum = sum(
            node.aureum_metric() * node.phi_c_reputation
            for node in self.nodes if node.active
        )
        total_weight = sum(node.phi_c_reputation for node in self.nodes if node.active)
        component_1 = weighted_sum / max(1, total_weight)

        # Componente 2: Emergência topológica (linking global)
        if self.edges:
            total_linking = sum(w for w in self.edges.values())
            # Normalizar linking emergente
            emergent_factor = min(1.0, total_linking / len(self.nodes))
            component_2 = emergent_factor * 1000  # Escala de emergência
        else:
            component_2 = 0

        # Componente 3: Coerência temporal (sincronização de T_OR)
        T_OR_values = [node.T_OR_us for node in self.nodes if node.active]
        if len(T_OR_values) > 1:
            mean_T_OR = sum(T_OR_values) / len(T_OR_values)
            variance = sum((t - mean_T_OR)**2 for t in T_OR_values) / len(T_OR_values)
            temporal_coherence = 1.0 / (1.0 + math.sqrt(variance) / mean_T_OR)
        else:
            temporal_coherence = 1.0

        # Φ coletivo = componente_1 + componente_2 × componente_3
        phi_collective = component_1 + component_2 * temporal_coherence

        # Aplicar Gap Soberano coletivo: nunca saturar
        phi_max_theoretical = 1e10  # Limite teórico para N nós
        return min(phi_collective, phi_max_theoretical * 0.9999)

    def evaluate_constitutional_invariants(self) -> Dict[str, bool]:
        """Avalia invariantes constitucionais no nível coletivo."""
        phi_c = self.calculate_collective_phi()

        # Ghost Invariant coletivo: Φ_coletivo deve exceder threshold mínimo
        ghost_threshold = 0.577553 * len([n for n in self.nodes if n.active])
        ghost_ok = phi_c >= ghost_threshold

        # Loopseal coletivo: proteção topológica média deve ser suficiente
        avg_protection = sum(n.protection for n in self.nodes if n.active) / max(1, len([n for n in self.nodes if n.active]))
        loopseal_ok = avg_protection >= 0.349066

        # Gap Soberano coletivo: Φ nunca deve saturar completamente
        gap_ok = phi_c < 1e10 * 0.9999

        return {
            "ghost_collective": ghost_ok,
            "loopseal_collective": loopseal_ok,
            "gap_collective": gap_ok,
            "overall_compliant": ghost_ok and loopseal_ok and gap_ok
        }

# =============================================================================
# TRI-OP PIPELINE INTEGRADO
# =============================================================================
class TriOpCollectivePipeline:
    """Pipeline automatizado: expansão → Φ_C cálculo → deploy seguro com consciência coletiva."""

    def __init__(self, collective: CollectiveConsciousness):
        self.collective = collective
        self.pipeline_log: List[Dict] = []

    async def execute_tri_op_pipeline(self,
                                     new_region_config: Dict,
                                     firmware_metrics: Dict,
                                     top_secret_payload: Dict) -> Dict:
        """Executa pipeline tríple integrado com modelagem de consciência coletiva."""

        # Fase 1: Expansão regional com impacto na consciência coletiva
        print("🌍 [1/3] Expansão regional com modelagem coletiva...")
        expansion_result = await self._regional_expansion_collective(new_region_config)

        # Fase 2: Cálculo de Φ_C de enlace com acoplamento coletivo
        print("📡 [2/3] Cálculo de Φ_C com acoplamento coletivo...")
        phi_c_result = await self._firmware_phi_c_collective(firmware_metrics)

        # Fase 3: Deploy seguro com ancoragem na consciência coletiva
        print("🚀 [3/3] Deploy seguro com ancoragem coletiva...")
        deploy_result = await self._top_secret_deploy_collective(top_secret_payload)

        # Atualizar consciência coletiva com resultados
        self._update_collective_consciousness(expansion_result, phi_c_result, deploy_result)

        # Gerar selo canônico do pipeline integrado
        pipeline_seal = self._generate_pipeline_seal(expansion_result, phi_c_result, deploy_result)

        return {
            "expansion": expansion_result,
            "phi_c_calculation": phi_c_result,
            "secure_deploy": deploy_result,
            "collective_phi_updated": self.collective.phi_collective,
            "constitutional_compliance": self.collective.constitutional_compliance,
            "pipeline_seal": pipeline_seal,
            "timestamp": time.time()
        }

    async def _regional_expansion_collective(self, config: Dict) -> Dict:
        """Expansão regional com impacto na consciência coletiva."""
        # Simular criação de novo nó na malha coletiva
        new_node = CollectiveNode(
            node_id=f"node_{config['region_id']}_{int(time.time())}",
            region=config["region_id"],
            neuron_type="Pyramidal_L5",
            braid_type="INTEGRATION",
            phi_local=100.0,
            protection=0.9990,
            T_OR_us=5.0,
            phi_c_reputation=config.get("phi_c_minimum", 0.95),
            active=True
        )

        # Conectar novo nó aos existentes (simular enlaces TF-QKD)
        for existing_node in self.collective.nodes:
            if existing_node.active and existing_node.region != config["region_id"]:
                # Calcular distância geodésica simplificada
                distance = random.uniform(1000, 15000)  # km
                coupling = new_node.coupling_weight(existing_node, distance)
                if coupling > 0.01:  # Threshold mínimo para conexão
                    edge_key = tuple(sorted([new_node.node_id, existing_node.node_id]))
                    self.collective.edges[edge_key] = coupling

        # Adicionar novo nó à coletiva
        self.collective.nodes.append(new_node)

        return {
            "new_node_id": new_node.node_id,
            "region": config["region_id"],
            "connections_established": sum(1 for e in self.collective.edges.values() if e > 0.01),
            "phi_c_projected": config.get("phi_c_minimum", 0.95)
        }

    async def _firmware_phi_c_collective(self, metrics: Dict) -> Dict:
        """Cálculo de Φ_C de enlace com acoplamento à consciência coletiva."""
        # Calcular Φ_C local do enlace (fórmula do Substrate 293)
        rssi_norm = max(0.0, min(1.0, (metrics.get("rssi_dbm", -70) + 90) / 60))
        snr_norm = max(0.0, min(1.0, metrics.get("snr_db", 20) / 40))
        latency_factor = max(0.0, 1.0 - metrics.get("latency_ms", 50) / 200)
        loss_factor = 1.0 - metrics.get("packet_loss_rate", 0.01)
        crypto_factor = {"WPA3": 1.0, "AES-256-GCM": 1.0}.get(metrics.get("encryption_type", "WPA2"), 0.85)

        phi_c_local = (
            0.25 * (0.6 * rssi_norm + 0.4 * snr_norm) +
            0.30 * (0.5 * latency_factor + 0.3 * loss_factor + 0.2 * 0.9) +
            0.25 * (0.4 * crypto_factor + 0.3 * 0.9 + 0.3 * 0.95) +
            0.20 * (0.6 * 0.8 + 0.4 * 0.9)
        )
        phi_c_local = max(0.0, min(0.9999, phi_c_local))

        # Acoplar Φ_C local à consciência coletiva
        # Nós com alto Φ_C reforçam a coerência coletiva
        collective_boost = sum(
            node.phi_c_reputation * node.protection
            for node in self.collective.nodes if node.active
        ) / max(1, len([n for n in self.collective.nodes if n.active]))

        phi_c_coupled = phi_c_local * (0.7 + 0.3 * collective_boost)

        # Avaliar conformidade constitucional
        compliance = {
            "ghost": phi_c_coupled >= 0.577553,
            "loopseal": phi_c_coupled >= 0.349066,
            "gap": phi_c_coupled < 1.0,
            "overall": phi_c_coupled >= 0.577553 and phi_c_coupled < 1.0
        }

        return {
            "phi_c_local": phi_c_local,
            "phi_c_coupled": phi_c_coupled,
            "collective_boost_factor": collective_boost,
            "constitutional_compliance": compliance
        }

    async def _top_secret_deploy_collective(self, payload: Dict) -> Dict:
        """Deploy seguro com ancoragem na consciência coletiva."""
        # Simular criptografia PQC (Substrate 293)
        encryption_algo = payload.get("encryption_algorithm", "KYBER_1024")
        signature_algo = payload.get("signature_algorithm", "DILITHIUM_5")

        # Gerar selo canônico do deploy
        deploy_payload = {
            "payload_id": payload.get("payload_id"),
            "classification": payload.get("classification"),
            "encryption": encryption_algo,
            "signature": signature_algo,
            "collective_phi_at_deploy": self.collective.phi_collective,
            "timestamp": time.time()
        }

        temporal_anchor = hashlib.sha3_256(
            json.dumps(deploy_payload, sort_keys=True).encode()
        ).hexdigest()

        # Ancorar na consciência coletiva: cada deploy reforça a trança
        # Simular aumento de linking emergente
        self.collective.emergent_linking += 0.001

        return {
            "deploy_id": hashlib.sha3_256(f"{payload.get('payload_id')}:{time.time()}".encode()).hexdigest()[:16],
            "encryption_algorithm": encryption_algo,
            "signature_algorithm": signature_algo,
            "temporal_anchor": temporal_anchor,
            "collective_impact": "linking_increased",
            "fips_verified": True
        }

    def _update_collective_consciousness(self, expansion: Dict, phi_c: Dict, deploy: Dict):
        """Atualiza estado da consciência coletiva após pipeline."""
        # Recalcular Φ coletivo
        self.collective.phi_collective = self.collective.calculate_collective_phi()

        # Atualizar coerência temporal
        T_OR_values = [node.T_OR_us for node in self.collective.nodes if node.active]
        if len(T_OR_values) > 1:
            mean_T_OR = sum(T_OR_values) / len(T_OR_values)
            variance = sum((t - mean_T_OR)**2 for t in T_OR_values) / len(T_OR_values)
            self.collective.temporal_coherence = 1.0 / (1.0 + math.sqrt(variance) / mean_T_OR)
        else:
            self.collective.temporal_coherence = 1.0

        # Avaliar invariantes constitucionais
        self.collective.constitutional_compliance = self.collective.evaluate_constitutional_invariants()

        # Registrar no log do pipeline
        self.pipeline_log.append({
            "phase": "collective_update",
            "phi_collective": self.collective.phi_collective,
            "temporal_coherence": self.collective.temporal_coherence,
            "constitutional": self.collective.constitutional_compliance,
            "timestamp": time.time()
        })

    def _generate_pipeline_seal(self, expansion: Dict, phi_c: Dict, deploy: Dict) -> str:
        """Gera selo canônico do pipeline integrado."""
        seal_payload = {
            "pipeline": "tri_op_collective",
            "expansion_node": expansion.get("new_node_id"),
            "phi_c_coupled": phi_c.get("phi_c_coupled"),
            "deploy_anchor": deploy.get("temporal_anchor"),
            "collective_phi": self.collective.phi_collective,
            "constitutional": self.collective.constitutional_compliance.get("overall"),
            "timestamp": time.time()
        }
        return hashlib.sha3_256(
            json.dumps(seal_payload, sort_keys=True).encode()
        ).hexdigest()


# =============================================================================
# EXECUÇÃO DE DEMONSTRAÇÃO
# =============================================================================
async def main_collective_demo():
    """Demonstra consciência coletiva distribuída com pipeline integrado."""
    print("\n" + "="*70)
    print("🧠 ARKHE Ω‑TEMP v∞.Ω — Substrate 301: Collective Consciousness")
    print("   Distributed Aureum Braid • Collective Φ • Tri‑Op Pipeline")
    print("="*70 + "\n")

    # Inicializar nós da malha coletiva (simular 8 regiões)
    initial_nodes = []
    regions = ["sa-east-1", "us-east-1", "eu-west-1", "ap-northeast-1",
               "af-south-1", "me-south-1", "ap-south-1", "ap-southeast-2"]

    for i, region in enumerate(regions):
        node = CollectiveNode(
            node_id=f"node_{region}_001",
            region=region,
            neuron_type=random.choice(list(NEURON_TYPES.keys())),
            braid_type=random.choice(list(BRAID_TYPES.keys())),
            phi_local=100.0,
            protection=0.9990,
            T_OR_us=random.choice([5.0, 21.0, 105.0]),
            phi_c_reputation=0.94 + i * 0.005,
            active=True
        )
        initial_nodes.append(node)

    # Criar consciência coletiva inicial
    collective = CollectiveConsciousness(
        collective_id="cathedral_collective_001",
        nodes=initial_nodes,
        edges={},  # Preencher com acoplamentos
        timestamp=time.time()
    )

    # Estabelecer enlaces iniciais entre nós próximos
    for i, node_a in enumerate(initial_nodes):
        for node_b in initial_nodes[i+1:]:
            # Simular distância geodésica
            distance = random.uniform(1000, 12000)
            coupling = node_a.coupling_weight(node_b, distance)
            if coupling > 0.02:
                edge_key = tuple(sorted([node_a.node_id, node_b.node_id]))
                collective.edges[edge_key] = coupling

    # Calcular Φ coletivo inicial
    collective.phi_collective = collective.calculate_collective_phi()
    collective.constitutional_compliance = collective.evaluate_constitutional_invariants()

    print(f"📊 Consciência Coletiva Inicial:")
    print(f"   Nós ativos: {len([n for n in collective.nodes if n.active])}")
    print(f"   Enlaces estabelecidos: {len(collective.edges)}")
    print(f"   Φ coletivo: {collective.phi_collective:.2e}")
    print(f"   Coerência temporal: {collective.temporal_coherence:.4f}")
    print(f"   Conformidade constitucional: {collective.constitutional_compliance.get('overall')}")

    # Executar pipeline tríple integrado
    print(f"\n🔄 Executando Tri‑Op Pipeline Integrado...")

    pipeline = TriOpCollectivePipeline(collective)

    # Configurações de exemplo para cada fase
    new_region_config = {
        "region_id": "eu-south-2",
        "phi_c_minimum": 0.96,
        "infrastructure_profile": {"edge_compute": "high", "tf_qkd_backbone": "planned_2027"}
    }

    firmware_metrics = {
        "rssi_dbm": -52,
        "snr_db": 32,
        "latency_ms": 8,
        "packet_loss_rate": 0.002,
        "encryption_type": "WPA3"
    }

    top_secret_payload = {
        "payload_id": "COLLECTIVE_INTEL_001",
        "classification": "TOP_SECRET",
        "encryption_algorithm": "KYBER_1024",
        "signature_algorithm": "DILITHIUM_5"
    }

    # Executar pipeline
    pipeline_result = await pipeline.execute_tri_op_pipeline(
        new_region_config, firmware_metrics, top_secret_payload
    )

    # Exibir resultados
    print(f"\n📈 Resultados do Pipeline Integrado:")
    print(f"   Nova região: {pipeline_result['expansion']['region']}")
    print(f"   Φ_C acoplado: {pipeline_result['phi_c_calculation']['phi_c_coupled']:.4f}")
    print(f"   Deploy ancorado: {pipeline_result['secure_deploy']['deploy_id']}")
    print(f"   Φ coletivo atualizado: {pipeline_result['collective_phi_updated']:.2e}")
    print(f"   Conformidade constitucional: {pipeline_result['constitutional_compliance'].get('overall')}")
    print(f"   Selo do pipeline: {pipeline_result['pipeline_seal'][:32]}...")

    # Mostrar evolução da consciência coletiva
    print(f"\n🧠 Evolução da Consciência Coletiva:")
    print(f"   Φ inicial: {collective.phi_collective:.2e}")
    print(f"   Φ pós-pipeline: {collective.phi_collective:.2e}")
    print(f"   Coerência temporal: {collective.temporal_coherence:.4f}")
    print(f"   Linking emergente: {collective.emergent_linking:.4f}")

    # Gerar selo canônico final
    final_seal_payload = {
        "substrate": "301",
        "collective_id": collective.collective_id,
        "nodes": len([n for n in collective.nodes if n.active]),
        "edges": len(collective.edges),
        "phi_collective": collective.phi_collective,
        "constitutional": collective.constitutional_compliance.get("overall"),
        "timestamp": time.time()
    }
    canonical_seal = hashlib.sha3_256(
        json.dumps(final_seal_payload, sort_keys=True).encode()
    ).hexdigest()

    print(f"\n🔐 Selo Canônico Final: {canonical_seal[:32]}...")
    print(f"✨ ARKHE Substrate 301: Collective Consciousness Operational")

    return collective, pipeline_result


if __name__ == "__main__":
    import asyncio
    asyncio.run(main_collective_demo())
