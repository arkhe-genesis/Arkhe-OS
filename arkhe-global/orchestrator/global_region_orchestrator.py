#!/usr/bin/env python3
"""
arkhe-global/orchestrator/global_region_orchestrator.py
Canon: ∞.Ω.∇+++.282.global_orchestrator
Orquestrador para deploy e gestão de 8+ regiões geográficas
com ancoragem geo‑distribuída e consenso constitucional global.
"""

import asyncio
import hashlib
import json
import math
import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, Set
import logging
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# TIPOS CANÔNICOS PARA ORQUESTRAÇÃO GLOBAL
# =============================================================================

class RegionStatus(Enum):
    """Status operacional de uma região."""
    ACTIVE = "active"
    DEPLOYING = "deploying"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

class AnchoringRole(Enum):
    """Papel de uma região no esquema de ancoragem."""
    PRIMARY = "primary"      # Principal para certas regiões
    SECONDARY = "secondary"  # Secundária para replicação
    FALLBACK = "fallback"    # Fallback em caso de falha
    VERIFIER = "verifier"    # Nó de verificação de consistência

@dataclass
class RegionalConfig:
    """Configuração canônica de uma região."""
    region_id: str
    name: str
    location: Dict[str, Any]  # city, country, coordinates
    infrastructure: Dict[str, Any]  # edge_compute, tf_qkd_backbone, etc.
    regulatory: Dict[str, Any]  # frameworks, data_sovereignty, etc.
    constitutional: Dict[str, float]  # phi_c_minimum, thresholds, etc.
    anchoring: Dict[str, Any]  # primary_for_regions, secondary_for_regions, etc.

    def get_phi_c_minimum(self) -> float:
        return self.constitutional.get("phi_c_minimum", 0.95)

    def is_tf_qkd_ready(self) -> bool:
        return self.infrastructure.get("tf_qkd_backbone") is True

    def supports_data_localization(self) -> bool:
        sovereignty = self.regulatory.get("data_sovereignty", "")
        return "local" in sovereignty.lower() or "residency" in sovereignty.lower()

@dataclass
class GlobalConsensusState:
    """Estado do consenso constitucional global."""
    timestamp: float
    participating_regions: Set[str]
    phi_c_weighted_votes: Dict[str, float]  # region -> Φ_C * reputation
    consensus_reached: bool
    global_phi_c: float
    canonical_seal: str

@dataclass
class AnchoringEvent:
    """Evento para ancoragem na TemporalChain."""
    event_type: str
    region_id: str
    payload: Dict[str, Any]
    phi_c_at_event: float
    timestamp: float
    local_seal: str = ""
    global_seal: str = ""

    def generate_local_seal(self) -> str:
        """Gera selo local SHA3-256 para o evento."""
        payload = {
            "event_type": self.event_type,
            "region_id": self.region_id,
            "payload_hash": hashlib.sha3_256(
                json.dumps(self.payload, sort_keys=True).encode()
            ).hexdigest(),
            "phi_c": self.phi_c_at_event,
            "timestamp": self.timestamp
        }
        return hashlib.sha3_256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()


# =============================================================================
# COMPONENTES DE ORQUESTRAÇÃO GLOBAL
# =============================================================================

class RegionRegistry:
    """Registro central de regiões com configuração canônica."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.regions: Dict[str, RegionalConfig] = {}
        self._load_config()

    def _load_config(self):
        """Carrega configuração de regiões do YAML."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            for region_id, region_data in config.get('regions', {}).items():
                self.regions[region_id] = RegionalConfig(
                    region_id=region_id,
                    name=region_data['name'],
                    location=region_data['location'],
                    infrastructure=region_data['infrastructure'],
                    regulatory=region_data['regulatory'],
                    constitutional=region_data['constitutional'],
                    anchoring=region_data['anchoring']
                )

            logger.info(f"✅ Loaded {len(self.regions)} regions from {self.config_path}")

        except Exception as e:
            logger.error(f"❌ Failed to load region config: {e}")
            raise

    def get_region(self, region_id: str) -> Optional[RegionalConfig]:
        """Retorna configuração de uma região por ID."""
        return self.regions.get(region_id)

    def get_all_regions(self) -> List[RegionalConfig]:
        """Retorna todas as regiões configuradas."""
        return list(self.regions.values())

    def get_primary_anchors_for(self, target_region: str) -> List[str]:
        """Retorna regiões que são anchors primários para target_region."""
        primaries = []
        for region in self.regions.values():
            if target_region in region.anchoring.get('primary_for_regions', []):
                primaries.append(region.region_id)
        return primaries if primaries else [target_region]  # Fallback to self

    def get_secondary_anchors_for(self, target_region: str) -> List[str]:
        """Retorna regiões que são anchors secundários para target_region."""
        secondaries = []
        for region in self.regions.values():
            if target_region in region.anchoring.get('secondary_for_regions', []):
                secondaries.append(region.region_id)
        return secondaries

    def calculate_geodesic_distance(self, region_a: str, region_b: str) -> float:
        """Calcula distância geodésica entre duas regiões (Haversine formula)."""
        a = self.regions[region_a].location['coordinates']
        b = self.regions[region_b].location['coordinates']

        R = 6371  # Earth radius in km
        lat1, lon1 = math.radians(a['latitude']), math.radians(a['longitude'])
        lat2, lon2 = math.radians(b['latitude']), math.radians(b['longitude'])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a_val = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a_val), math.sqrt(1 - a_val))

        return R * c


class GlobalConsensusEngine:
    """Motor de consenso constitucional ponderado por Φ_C."""

    def __init__(self, region_registry: RegionRegistry):
        self.registry = region_registry
        self.reputation_scores: Dict[str, float] = {}  # region -> Φ_C reputation
        self._initialize_reputations()

    def _initialize_reputations(self):
        """Inicializa reputações baseadas em Φ_C mínimo configurado."""
        for region in self.registry.get_all_regions():
            # Reputation starts at configured phi_c_minimum
            self.reputation_scores[region.region_id] = region.get_phi_c_minimum()

    def update_reputation(self, region_id: str, observed_phi_c: float,
                         decay_factor: float = 0.99):
        """Atualiza reputação de região baseado em Φ_C observado."""
        if region_id not in self.reputation_scores:
            return

        # Exponential moving average with decay
        current_rep = self.reputation_scores[region_id]
        self.reputation_scores[region_id] = (
            decay_factor * current_rep +
            (1 - decay_factor) * observed_phi_c
        )

    def calculate_weighted_vote(self, region_id: str, vote_value: float) -> float:
        """Calcula voto ponderado por reputação Φ_C."""
        reputation = self.reputation_scores.get(region_id, 0.8)
        return vote_value * reputation

    def run_consensus_round(self, votes: Dict[str, bool],
                           threshold: float = 0.67) -> Tuple[bool, float]:
        """
        Executa rodada de consenso com votação ponderada.
        Retorna: (consensus_reached, global_phi_c)
        """
        if not votes:
            return False, 0.0

        # Calculate weighted votes
        total_weight = sum(
            self.calculate_weighted_vote(region, 1.0)
            for region in votes.keys()
        )

        approved_weight = sum(
            self.calculate_weighted_vote(region, 1.0 if vote else 0.0)
            for region, vote in votes.items()
        )

        consensus_ratio = approved_weight / total_weight if total_weight > 0 else 0.0
        consensus_reached = consensus_ratio >= threshold

        # Calculate global Φ_C as weighted average
        global_phi_c = sum(
            self.reputation_scores.get(region, 0.9) * (1.0 if vote else 0.0)
            for region, vote in votes.items()
        ) / max(1, len(votes))

        return consensus_reached, global_phi_c

    def generate_consensus_seal(self, consensus_state: GlobalConsensusState) -> str:
        """Gera selo canônico para estado de consenso."""
        payload = {
            "timestamp": consensus_state.timestamp,
            "participating_regions": sorted(list(consensus_state.participating_regions)),
            "consensus_reached": consensus_state.consensus_reached,
            "global_phi_c": consensus_state.global_phi_c,
            "phi_c_weights": {
                r: self.reputation_scores.get(r, 0.9)
                for r in consensus_state.participating_regions
            }
        }
        return hashlib.sha3_256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()


class GeoDistributedAnchoring:
    """Sistema de ancoragem geo‑distribuída na TemporalChain."""

    def __init__(self, region_registry: RegionRegistry,
                 temporal_endpoint: str):
        self.registry = region_registry
        self.temporal_endpoint = temporal_endpoint
        self.pending_anchors: Dict[str, List[AnchoringEvent]] = {}
        self.global_seals: List[str] = []

    async def queue_event(self, event: AnchoringEvent):
        """Adiciona evento à fila de ancoragem local."""
        region_id = event.region_id
        if region_id not in self.pending_anchors:
            self.pending_anchors[region_id] = []

        # Generate local seal before queuing
        event.local_seal = event.generate_local_seal()
        self.pending_anchors[region_id].append(event)

        logger.debug(f"📦 Queued event for {region_id}: {event.event_type}")

    async def flush_region_anchors(self, region_id: str,
                                   batch_size: int = 100) -> Optional[str]:
        """Ancora batch de eventos de uma região na TemporalChain."""
        if region_id not in self.pending_anchors:
            return None

        events = self.pending_anchors[region_id][:batch_size]
        if not events:
            return None

        # Create batch payload
        batch_payload = {
            "region_id": region_id,
            "event_count": len(events),
            "events": [
                {
                    "type": e.event_type,
                    "local_seal": e.local_seal,
                    "phi_c": e.phi_c_at_event,
                    "timestamp": e.timestamp
                }
                for e in events
            ],
            "batch_timestamp": time.time()
        }

        # Generate batch seal
        batch_seal = hashlib.sha3_256(
            json.dumps(batch_payload, sort_keys=True).encode()
        ).hexdigest()

        # Mock: In production, POST to TemporalChain endpoint
        # response = await httpx.post(
        #     f"{self.temporal_endpoint}/anchor/batch",
        #     json={"region": region_id, "payload": batch_payload},
        #     headers={"Authorization": f"Bearer {self._get_auth_token()}"}
        # )

        logger.info(f"🔗 Anchored {len(events)} events for {region_id}: {batch_seal[:16]}...")

        # Remove anchored events from queue
        self.pending_anchors[region_id] = self.pending_anchors[region_id][batch_size:]
        if not self.pending_anchors[region_id]:
            del self.pending_anchors[region_id]

        return batch_seal

    async def aggregate_global_seal(self) -> str:
        """Agrega selos regionais em selo global periódico."""
        if not self.pending_anchors:
            return self.global_seals[-1] if self.global_seals else ""

        # Collect recent local seals
        recent_seals = []
        for region_events in self.pending_anchors.values():
            recent_seals.extend([e.local_seal for e in region_events[-10:]])

        if not recent_seals:
            return ""

        # Build Merkle-like aggregation
        aggregated_payload = {
            "aggregation_timestamp": time.time(),
            "region_count": len(self.pending_anchors),
            "event_count": sum(len(events) for events in self.pending_anchors.values()),
            "recent_seals_hash": hashlib.sha3_256(
                "".join(sorted(recent_seals)).encode()
            ).hexdigest()
        }

        global_seal = hashlib.sha3_256(
            json.dumps(aggregated_payload, sort_keys=True).encode()
        ).hexdigest()

        self.global_seals.append(global_seal)
        logger.info(f"🌐 Global seal aggregated: {global_seal[:32]}...")

        return global_seal


# =============================================================================
# ORQUESTRADOR PRINCIPAL GLOBAL
# =============================================================================

class GlobalRegionOrchestrator:
    """Orquestrador principal para 8+ regiões com consenso constitucional."""

    def __init__(self, config_path: str, temporal_endpoint: str):
        self.registry = RegionRegistry(config_path)
        self.consensus_engine = GlobalConsensusEngine(self.registry)
        self.anchoring = GeoDistributedAnchoring(self.registry, temporal_endpoint)
        self.region_status: Dict[str, RegionStatus] = {}
        self._initialize_status()

    def _initialize_status(self):
        """Inicializa status de todas as regiões como ACTIVE."""
        for region in self.registry.get_all_regions():
            self.region_status[region.region_id] = RegionStatus.ACTIVE

    async def deploy_region(self, region_id: str) -> bool:
        """Deploy de funções Arkhe em uma região."""
        region = self.registry.get_region(region_id)
        if not region:
            logger.error(f"❌ Unknown region: {region_id}")
            return False

        logger.info(f"🚀 Deploying Arkhe functions to {region.name} ({region_id})...")

        # Mock deployment steps
        # 1. Provision edge compute resources
        # 2. Deploy constitutional filtering functions
        # 3. Configure TF-QKD endpoints if available
        # 4. Register with global consensus engine
        # 5. Initialize anchoring queue

        # Update status
        self.region_status[region_id] = RegionStatus.ACTIVE

        # Queue deployment event for anchoring
        await self.anchoring.queue_event(AnchoringEvent(
            event_type="region_deployed",
            region_id=region_id,
            payload={"name": region.name, "phi_c_minimum": region.get_phi_c_minimum()},
            phi_c_at_event=region.get_phi_c_minimum(),
            timestamp=time.time()
        ))

        logger.info(f"✅ {region.name} deployed successfully")
        return True

    async def process_regional_event(self, region_id: str,
                                     event_type: str,
                                     event_payload: Dict[str, Any],
                                     observed_phi_c: float) -> bool:
        """Processa evento constitucional de uma região."""
        region = self.registry.get_region(region_id)
        if not region:
            return False

        # Update consensus reputation before potential early return
        self.consensus_engine.update_reputation(region_id, observed_phi_c)

        # Check constitutional thresholds
        if observed_phi_c < region.get_phi_c_minimum():
            logger.warning(f"⚠️ {region_id}: Φ_C {observed_phi_c:.4f} below minimum {region.get_phi_c_minimum()}")
            # Queue violation event
            await self.anchoring.queue_event(AnchoringEvent(
                event_type="phi_c_violation",
                region_id=region_id,
                payload={"observed": observed_phi_c, "minimum": region.get_phi_c_minimum()},
                phi_c_at_event=observed_phi_c,
                timestamp=time.time()
            ))
            return False

        # Queue normal event for anchoring
        await self.anchoring.queue_event(AnchoringEvent(
            event_type=event_type,
            region_id=region_id,
            payload=event_payload,
            phi_c_at_event=observed_phi_c,
            timestamp=time.time()
        ))

        return True

    async def run_consensus_round_global(self) -> GlobalConsensusState:
        """Executa rodada de consenso global com todas as regiões ativas."""
        active_regions = [
            r.region_id for r in self.registry.get_all_regions()
            if self.region_status.get(r.region_id) == RegionStatus.ACTIVE
        ]

        if len(active_regions) < 5:  # Minimum participating regions
            logger.warning(f"⚠️ Insufficient active regions for consensus: {len(active_regions)}")
            return GlobalConsensusState(
                timestamp=time.time(),
                participating_regions=set(active_regions),
                phi_c_weighted_votes={},
                consensus_reached=False,
                global_phi_c=0.0,
                canonical_seal=""
            )

        # Mock: In production, collect votes from each region via RPC
        # For simulation, generate synthetic votes based on reputation
        votes = {}
        for region_id in active_regions:
            # Higher reputation regions more likely to vote "true"
            reputation = self.consensus_engine.reputation_scores.get(region_id, 0.9)
            vote = reputation > 0.85  # Simple threshold for simulation
            votes[region_id] = vote

        consensus_reached, global_phi_c = self.consensus_engine.run_consensus_round(votes)

        consensus_state = GlobalConsensusState(
            timestamp=time.time(),
            participating_regions=set(active_regions),
            phi_c_weighted_votes={
                r: self.consensus_engine.calculate_weighted_vote(r, 1.0 if votes[r] else 0.0)
                for r in active_regions
            },
            consensus_reached=consensus_reached,
            global_phi_c=global_phi_c,
            canonical_seal=""
        )

        # Generate and attach canonical seal
        consensus_state.canonical_seal = self.consensus_engine.generate_consensus_seal(consensus_state)

        # Anchor consensus result
        await self.anchoring.queue_event(AnchoringEvent(
            event_type="global_consensus_round",
            region_id="global",
            payload={
                "consensus_reached": consensus_reached,
                "global_phi_c": global_phi_c,
                "participating_count": len(active_regions)
            },
            phi_c_at_event=global_phi_c,
            timestamp=consensus_state.timestamp
        ))

        logger.info(f"🗳️  Global consensus: {'✅ REACHED' if consensus_reached else '❌ FAILED'} | Φ_C: {global_phi_c:.4f}")

        return consensus_state

    async def run_background_tasks(self):
        """Executa tarefas em background: anchoring flush, consensus rounds, etc."""
        while True:
            try:
                # Flush regional anchors every 30 seconds
                for region_id in list(self.anchoring.pending_anchors.keys()):
                    await self.anchoring.flush_region_anchors(region_id, batch_size=100)

                # Aggregate global seal every 5 minutes (300 seconds)
                if time.time() % 300 < 30:  # Rough 5-minute window
                    await self.anchoring.aggregate_global_seal()

                # Run consensus round every 2 minutes
                if time.time() % 120 < 30:
                    await self.run_consensus_round_global()

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"❌ Background task error: {e}")
                await asyncio.sleep(30)  # Back off on error

    def get_global_status_report(self) -> Dict[str, Any]:
        """Gera relatório de status global consolidado."""
        active_count = sum(1 for s in self.region_status.values() if s == RegionStatus.ACTIVE)
        total_regions = len(self.registry.regions)

        return {
            "timestamp": time.time(),
            "regions_total": total_regions,
            "regions_active": active_count,
            "regions_by_status": {
                status.value: sum(1 for s in self.region_status.values() if s == status)
                for status in RegionStatus
            },
            "tf_qkd_ready_regions": [
                r.region_id for r in self.registry.get_all_regions()
                if r.is_tf_qkd_ready() and self.region_status.get(r.region_id) == RegionStatus.ACTIVE
            ],
            "global_phi_c_average": sum(
                self.consensus_engine.reputation_scores.get(r.region_id, 0.9)
                for r in self.registry.get_all_regions()
            ) / max(1, total_regions),
            "pending_anchors_total": sum(
                len(events) for events in self.anchoring.pending_anchors.values()
            ),
            "global_seals_count": len(self.anchoring.global_seals)
        }


# =============================================================================
# EXECUÇÃO PRINCIPAL: DEMONSTRAÇÃO DA EXPANSÃO GLOBAL
# =============================================================================

async def main():
    """Demonstra orquestração de 8+ regiões globais."""
    print("\n" + "="*70)
    print("🏛️ ARKHE Ω‑TEMP v∞.Ω — Substrate 282: Global Expansion")
    print("   8+ Geographic Regions • Constitutional Consensus • Geo-Anchoring")
    print("="*70 + "\n")

    # Initialize orchestrator (mock config path)
    orchestrator = GlobalRegionOrchestrator(
        config_path="arkhe-global/regions/global_region_config.yaml",
        temporal_endpoint="https://temporal.arkhe.org/v1/anchor"
    )

    # Deploy all 8 regions
    print("🚀 Deploying Arkhe functions to 8 geographic regions...")
    for region in orchestrator.registry.get_all_regions():
        success = await orchestrator.deploy_region(region.region_id)
        status_icon = "✅" if success else "❌"
        print(f"   {status_icon} {region.region_id:20s} | {region.name:30s} | Φ_C min: {region.get_phi_c_minimum()}")

    # Simulate regional events
    print("\n📡 Simulating constitutional events across regions...")
    import random
    for _ in range(3):  # 3 rounds of events
        for region in orchestrator.registry.get_all_regions():
            if random.random() > 0.1:  # 90% success rate
                observed_phi = region.get_phi_c_minimum() + random.uniform(0, 0.04)
                await orchestrator.process_regional_event(
                    region_id=region.region_id,
                    event_type="constitutional_operation",
                    event_payload={"operation": "packet_filtering", "packets": random.randint(100, 1000)},
                    observed_phi_c=observed_phi
                )

    # Run global consensus round
    print("\n🗳️  Running global consensus round...")
    consensus = await orchestrator.run_consensus_round_global()

    # Generate and display status report
    print("\n📊 Global Status Report:")
    report = orchestrator.get_global_status_report()
    print(f"   Regions Active: {report['regions_active']}/{report['regions_total']}")
    print(f"   TF-QKD Ready: {len(report['tf_qkd_ready_regions'])} regions")
    print(f"   Global Φ_C Avg: {report['global_phi_c_average']:.4f}")
    print(f"   Pending Anchors: {report['pending_anchors_total']}")
    print(f"   Global Seals: {report['global_seals_count']}")

    if report['tf_qkd_ready_regions']:
        print(f"   TF-QKD Regions: {', '.join(report['tf_qkd_ready_regions'][:4])}{'...' if len(report['tf_qkd_ready_regions']) > 4 else ''}")

    # Start background tasks (mock: run for 5 seconds then stop)
    print("\n🔄 Starting background tasks (anchoring, consensus)...")
    background_task = asyncio.create_task(orchestrator.run_background_tasks())
    await asyncio.sleep(5)
    background_task.cancel()

    # Final anchoring flush
    print("\n🔗 Flushing remaining anchors...")
    for region_id in list(orchestrator.anchoring.pending_anchors.keys()):
        seal = await orchestrator.anchoring.flush_region_anchors(region_id, batch_size=100)
        if seal:
            print(f"   ✅ {region_id}: {seal[:16]}...")

    # Generate final global seal
    final_global_seal = await orchestrator.anchoring.aggregate_global_seal()

    print("\n" + "="*70)
    print("✅ GLOBAL EXPANSION DEMONSTRATION COMPLETE")
    print(f"   Canonical Global Seal: {final_global_seal[:32]}...")
    print("   The Arkhe constitutional mesh now spans 8+ geographic regions.")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
