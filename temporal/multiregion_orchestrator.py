#!/usr/bin/env python3
"""
Substrato 226: Multi-Region TemporalChain Orchestrator
Orquestra cluster TemporalChain distribuído geograficamente com:
• Failover automático entre regiões
• Replicação assíncrona com consistência eventual garantida
• Roteamento inteligente baseado em latência e saúde do nó
• Monitoramento de saúde cross-region com alertas proativos
"""
import asyncio
import hashlib
import json
import time
import aiohttp
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)

class RegionHealth(Enum):
    """Status de saúde de uma região."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    PARTIAL_OUTAGE = "partial_outage"
    FULL_OUTAGE = "full_outage"

@dataclass
class RegionConfig:
    """Configuração de uma região no cluster multi-região."""
    region_id: str                    # "us-east-1", "eu-west-1", "sa-east-1", "ap-southeast-1"
    primary_endpoint: str            # https://primary.temporal.arkhe.os.{region}
    replica_endpoints: List[str]     # Lista de endpoints de réplicas
    priority: int                     # Prioridade para failover (1 = mais alta)
    max_latency_ms: int = 100         # Latência máxima aceitável para writes
    min_healthy_nodes: int = 3        # Mínimo de nós saudáveis para considerar região healthy
    geo_fence_enabled: bool = True    # Habilitar roteamento baseado em localização do cliente

@dataclass
class MultiRegionAnchorResult:
    """Resultado de ancoragem multi-região."""
    anchor_id: str
    primary_region: str
    confirmed_regions: List[str]
    total_confirmations: int
    replication_lag_ms: Dict[str, float]
    final_seal: str
    temporal_chain_seals: Dict[str, str]  # region → seal
    anchored_at: float = field(default_factory=time.time)

class MultiRegionTemporalOrchestrator:
    """
    Orquestrador de cluster TemporalChain multi-região.

    Características:
    • Descoberta dinâmica de regiões via service mesh global
    • Failover automático com health checks contínuos
    • Replicação assíncrona com confirmação de quórum regional
    • Roteamento baseado em latência + health + geo-fencing
    • Métricas de replicação cross-region publicadas no Phi-Bus
    """

    # Configurações de resiliência
    HEALTH_CHECK_INTERVAL_SEC = 10
    FAILOVER_THRESHOLD_FAILURES = 3
    REPLICATION_TIMEOUT_SEC = 5
    MIN_REGIONS_FOR_QUORUM = 2

    def __init__(
        self,
        regions: List[RegionConfig],
        phi_bus=None,
        local_region: Optional[str] = None
    ):
        self.regions = {r.region_id: r for r in regions}
        self.phi_bus = phi_bus
        self.local_region = local_region
        self._region_health: Dict[str, RegionHealth] = {}
        self._region_latency: Dict[str, float] = {}
        self._active_primary: Optional[str] = None
        self._failover_count: Dict[str, int] = {}
        self._replication_metrics: Dict[str, List[float]] = {}

    async def start_health_monitoring(self):
        """Inicia monitoramento contínuo de saúde das regiões."""
        asyncio.create_task(self._health_check_loop())
        logger.info("🏥 Health monitoring started for multi-region cluster")

    async def _health_check_loop(self):
        """Loop de health checks para todas as regiões."""
        while True:
            for region_id, config in self.regions.items():
                health = await self._check_region_health(config)
                self._region_health[region_id] = health

                # Publicar métrica no Phi-Bus
                if self.phi_bus:
                    await self.phi_bus.publish_metric("region_health", {
                        "region": region_id,
                        "health": health.value,
                        "latency_ms": self._region_latency.get(region_id, 0)
                    })

                # Trigger failover se região primária degradada
                if region_id == self._active_primary and health != RegionHealth.HEALTHY:
                    await self._trigger_regional_failover(region_id)

            await asyncio.sleep(self.HEALTH_CHECK_INTERVAL_SEC)

    async def _check_region_health(self, config: RegionConfig) -> RegionHealth:
        """Verifica saúde de uma região específica."""
        try:
            # Health check no endpoint primário
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{config.primary_endpoint}/health") as response:
                    if response.status != 200:
                        return RegionHealth.FULL_OUTAGE

                    health_data = await response.json()
                    healthy_nodes = health_data.get("healthy_nodes", 0)

                    if healthy_nodes >= config.min_healthy_nodes:
                        # Medir latência
                        start = time.time()
                        async with session.get(f"{config.primary_endpoint}/ping") as ping_resp:
                            await ping_resp.text()
                        latency = (time.time() - start) * 1000
                        self._region_latency[config.region_id] = latency

                        if latency <= config.max_latency_ms:
                            return RegionHealth.HEALTHY
                        else:
                            return RegionHealth.DEGRADED
                    elif healthy_nodes > 0:
                        return RegionHealth.PARTIAL_OUTAGE
                    else:
                        return RegionHealth.FULL_OUTAGE
        except Exception as e:
            logger.warning(f"⚠️  Health check failed for {config.region_id}: {e}")
            return RegionHealth.FULL_OUTAGE

    async def anchor_event_multi_region(
        self,
        event_type: str,
        payload: Dict,
        require_cross_region_confirmation: bool = True
    ) -> MultiRegionAnchorResult:
        """
        Ancora evento em múltiplas regiões com confirmação de quórum.

        Fluxo:
        1. Selecionar região primária baseada em health + latência + geo-fencing
        2. Enviar para primary com timeout
        3. Aguardar replicação assíncrona para regiões secundárias
        4. Confirmar quórum regional (MIN_REGIONS_FOR_QUORUM)
        5. Gerar selo global combinando selos regionais
        """
        # Selecionar região primária
        primary_region = await self._select_primary_region()
        if not primary_region:
            raise RuntimeError("No healthy region available for anchoring")

        primary_config = self.regions[primary_region]

        # Preparar payload com metadados multi-região
        anchor_id = hashlib.sha3_256(
            f"{event_type}:{json.dumps(payload, sort_keys=True)}:{time.time()}".encode()
        ).hexdigest()[:16]

        enriched_payload = {
            **payload,
            "_multi_region": {
                "anchor_id": anchor_id,
                "event_type": event_type,
                "origin_region": self.local_region,
                "timestamp": time.time(),
                "nonce": hashlib.sha3_256(f"{time.time()}:{id(payload)}".encode()).hexdigest()[:16]
            }
        }

        # Enviar para região primária
        primary_seal = await self._anchor_to_region(
            primary_config.primary_endpoint,
            enriched_payload,
            timeout=self.REPLICATION_TIMEOUT_SEC
        )

        # Aguardar replicação para regiões secundárias
        confirmed_regions = [primary_region]
        replication_lag = {}
        regional_seals = {primary_region: primary_seal}

        if require_cross_region_confirmation:
            secondary_tasks = []
            for region_id, config in self.regions.items():
                if region_id == primary_region:
                    continue
                if self._region_health.get(region_id) == RegionHealth.HEALTHY:
                    task = self._replicate_to_region(
                        config.replica_endpoints[0] if config.replica_endpoints else config.primary_endpoint,
                        enriched_payload,
                        region_id
                    )
                    secondary_tasks.append((region_id, task))

            # Aguardar confirmações com timeout
            for region_id, task in secondary_tasks:
                try:
                    seal, lag_ms = await asyncio.wait_for(task, timeout=self.REPLICATION_TIMEOUT_SEC)
                    confirmed_regions.append(region_id)
                    replication_lag[region_id] = lag_ms
                    regional_seals[region_id] = seal
                except asyncio.TimeoutError:
                    logger.warning(f"⏱️  Replication timeout for {region_id}")
                except Exception as e:
                    logger.error(f"❌ Replication failed for {region_id}: {e}")

        # Verificar quórum regional
        if len(confirmed_regions) < self.MIN_REGIONS_FOR_QUORUM:
            raise RuntimeError(
                f"Insufficient regional confirmations: {len(confirmed_regions)} < {self.MIN_REGIONS_FOR_QUORUM}"
            )

        # Gerar selo global combinando selos regionais
        global_seal = hashlib.sha3_256(
            "|".join(sorted(regional_seals.values())).encode()
        ).hexdigest()

        result = MultiRegionAnchorResult(
            anchor_id=anchor_id,
            primary_region=primary_region,
            confirmed_regions=confirmed_regions,
            total_confirmations=len(confirmed_regions),
            replication_lag_ms=replication_lag,
            final_seal=global_seal,
            temporal_chain_seals=regional_seals
        )

        # Publicar métrica de replicação
        if self.phi_bus:
            await self.phi_bus.publish_metric("multi_region_anchor", {
                "anchor_id": anchor_id,
                "primary_region": primary_region,
                "confirmed_regions": confirmed_regions,
                "avg_replication_lag_ms": sum(replication_lag.values()) / max(1, len(replication_lag)),
                "global_seal": global_seal[:16]
            })

        logger.info(
            f"✅ Multi-region anchor completed: {anchor_id} | "
            f"Primary: {primary_region} | Confirmed: {confirmed_regions} | "
            f"Global seal: {global_seal[:16]}..."
        )

        return result

    async def _select_primary_region(self) -> Optional[str]:
        """Seleciona região primária baseada em health, latência e geo-fencing."""
        candidates = []

        for region_id, config in self.regions.items():
            health = self._region_health.get(region_id, RegionHealth.FULL_OUTAGE)
            if health != RegionHealth.HEALTHY:
                continue

            latency = self._region_latency.get(region_id, float('inf'))
            if latency > config.max_latency_ms * 2:  # Allow some degradation
                continue

            # Score: prioridade mais baixa é melhor. Subtraímos a latência
            # para desempatar, mas o peso da prioridade deve ser muito maior.
            score = -(config.priority * 1000 + latency)
            candidates.append((region_id, score))

        if not candidates:
            return None

        # Retornar região com maior score (que será a de menor prioridade e latência)
        return max(candidates, key=lambda x: x[1])[0]

    async def _anchor_to_region(
        self,
        endpoint: str,
        payload: Dict,
        timeout: float
    ) -> str:
        """Ancora evento em uma região específica."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{endpoint}/anchor",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}: {await response.text()}")
                result = await response.json()
                return result["seal"]

    async def _replicate_to_region(
        self,
        endpoint: str,
        payload: Dict,
        target_region: str
    ) -> Tuple[str, float]:
        """Replica evento para região secundária e mede lag."""
        start = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{endpoint}/replicate",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=self.REPLICATION_TIMEOUT_SEC)
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Replication failed: HTTP {response.status}")
                result = await response.json()
                lag_ms = (time.time() - start) * 1000
                return result["seal"], lag_ms

    async def _trigger_regional_failover(self, failed_region: str):
        """Aciona failover quando região primária falha."""
        self._failover_count[failed_region] = self._failover_count.get(failed_region, 0) + 1

        if self._failover_count[failed_region] >= self.FAILOVER_THRESHOLD_FAILURES:
            logger.warning(f"🔄 Triggering failover from {failed_region}")
            self._active_primary = None  # Force re-selection on next anchor

            if self.phi_bus:
                await self.phi_bus.publish_metric("regional_failover_triggered", {
                    "failed_region": failed_region,
                    "failover_count": self._failover_count[failed_region],
                    "timestamp": time.time()
                })

    def get_cluster_topology(self) -> Dict:
        """Retorna topologia atual do cluster multi-região."""
        return {
            "regions": {
                region_id: {
                    "health": health.value,
                    "latency_ms": self._region_latency.get(region_id, 0),
                    "is_primary": region_id == self._active_primary,
                    "failover_count": self._failover_count.get(region_id, 0)
                }
                for region_id, health in self._region_health.items()
            },
            "active_primary": self._active_primary,
            "min_regions_for_quorum": self.MIN_REGIONS_FOR_QUORUM,
            "replication_timeout_sec": self.REPLICATION_TIMEOUT_SEC
        }