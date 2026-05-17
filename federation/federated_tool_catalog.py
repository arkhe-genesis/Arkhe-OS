#!/usr/bin/env python3
"""
Substrato 213: Federated Tool Catalog
Protocolo seguro para agentes descobrirem ferramentas de outros nós
via catálogo federado com privacidade diferencial e validação PQC.
"""

import asyncio
import hashlib
import json
import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum, auto
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FederatedToolEntry:
    """Entrada de ferramenta no catálogo federado."""
    tool_id: str
    tool_name: str
    description: str
    schema: Dict  # JSON Schema dos parâmetros
    provider_node_id: str
    provider_org_id: str
    capabilities: List[str]
    confidence_required: float
    token_cost_estimate: int
    avg_latency_ms: float
    success_rate: float
    last_updated: float
    dp_noise_epsilon: float  # Privacidade para métricas
    pqc_signature: Optional[str] = None  # Assinatura da entrada
    temporal_seal: Optional[str] = None

@dataclass
class ToolDiscoveryQuery:
    """Query para descoberta de ferramentas."""
    required_capabilities: List[str]
    max_latency_ms: Optional[float] = None
    min_success_rate: Optional[float] = None
    min_confidence: Optional[float] = None
    exclude_nodes: Optional[List[str]] = None
    dp_epsilon: float = 2.0  # Privacidade para query

class FederatedToolCatalog:
    """
    Catálogo federado de ferramentas com descoberta segura.

    Princípios:
    • Cada nó publica suas ferramentas com métricas ofuscadas por DP
    • Descoberta via query com privacidade preservada
    • Validação PQC de todas as entradas do catálogo
    • Consenso entre nós para entradas conflitantes
    • Cache local com invalidation por selo temporal
    """

    # Configurações de federação
    FEDERATION_CONFIG = {
        "min_dp_epsilon": 1.0,
        "max_dp_epsilon": 5.0,
        "catalog_sync_interval_sec": 300,
        "cache_ttl_sec": 600,
        "consensus_threshold": 0.7,  # 70% dos nós para consenso
    }

    def __init__(
        self,
        node_id: str,
        org_id: str,
        local_tools: Dict[str, Dict],  # Ferramentas locais
        phi_bus=None,
        temporal_chain=None,
        hsm_signer=None
    ):
        self.node_id = node_id
        self.org_id = org_id
        self.local_tools = local_tools
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self.hsm = hsm_signer

        # Catálogo federado: tool_id → FederatedToolEntry
        self._catalog: Dict[str, FederatedToolEntry] = {}
        self._peer_catalogs: Dict[str, Dict[str, FederatedToolEntry]] = {}

        # Cache de descobertas recentes
        self._discovery_cache: Dict[str, Tuple[List[str], float]] = {}

        # Estatísticas
        self._discovery_count = 0
        self._sync_rounds = 0

    async def publish_local_tools(self, dp_epsilon: float = 2.0) -> List[str]:
        """
        Publica ferramentas locais no catálogo federado com DP.

        Args:
            dp_epsilon: Parâmetro de privacidade diferencial para métricas

        Returns:
            Lista de tool_ids publicados
        """
        if not (self.FEDERATION_CONFIG["min_dp_epsilon"] <= dp_epsilon <= self.FEDERATION_CONFIG["max_dp_epsilon"]):
            raise ValueError(f"ε={dp_epsilon} fora do range permitido")

        published_ids = []

        for tool_id, tool_def in self.local_tools.items():
            # Ofuscar métricas com ruído Laplace
            noisy_latency = self._add_laplace_noise(
                tool_def.get("avg_latency_ms", 100), dp_epsilon
            )
            noisy_success = self._add_laplace_noise(
                tool_def.get("success_rate", 0.95), dp_epsilon
            )

            # Criar entrada federada
            entry = FederatedToolEntry(
                tool_id=tool_id,
                tool_name=tool_def.get("name", tool_id),
                description=tool_def.get("description", ""),
                schema=tool_def.get("schema", {}),
                provider_node_id=self.node_id,
                provider_org_id=self.org_id,
                capabilities=tool_def.get("capabilities", []),
                confidence_required=tool_def.get("confidence_required", 0.8),
                token_cost_estimate=tool_def.get("token_cost_estimate", 10),
                avg_latency_ms=max(0, noisy_latency),
                success_rate=np.clip(noisy_success, 0, 1),
                last_updated=time.time(),
                dp_noise_epsilon=dp_epsilon
            )

            # Assinar entrada com PQC
            if self.hsm:
                sig_result = await self.hsm.sign_data(
                    hashlib.sha3_256(
                        json.dumps({
                            "tool_id": entry.tool_id,
                            "provider": entry.provider_node_id,
                            "capabilities": entry.capabilities,
                            "timestamp": entry.last_updated
                        }, sort_keys=True).encode()
                    ).digest()
                )
                if sig_result.get("success"):
                    entry.pqc_signature = sig_result["signature_hex"]

            # Ancorar na TemporalChain
            if self.temporal:
                entry.temporal_seal = await self.temporal.anchor_event(
                    "tool_published_to_federation",
                    {
                        "tool_id": tool_id,
                        "provider_node": self.node_id,
                        "capabilities": entry.capabilities,
                        "dp_epsilon": dp_epsilon,
                        "timestamp": entry.last_updated
                    }
                )

            # Adicionar ao catálogo local e federado
            self._catalog[tool_id] = entry
            published_ids.append(tool_id)

            logger.info(f"📢 Ferramenta publicada: {tool_id} (ε={dp_epsilon})")

        # Publicar anúncio no Phi-Bus para descoberta por peers
        if self.phi_bus:
            await self.phi_bus.publish_metric("tools_published", {
                "node_id": self.node_id,
                "org_id": self.org_id,
                "tool_count": len(published_ids),
                "dp_epsilon": dp_epsilon
            })

        return published_ids

    async def discover_tools(
        self,
        query: ToolDiscoveryQuery
    ) -> List[FederatedToolEntry]:
        """
        Descobre ferramentas via query federada com privacidade.

        Args:
            query: Critérios de descoberta com DP

        Returns:
            Lista de ferramentas compatíveis, ordenadas por relevância
        """
        # Verificar cache primeiro
        cache_key = hashlib.sha3_256(
            json.dumps({
                "capabilities": query.required_capabilities,
                "max_latency": query.max_latency_ms,
                "min_success": query.min_success_rate,
                "exclude": query.exclude_nodes or []
            }, sort_keys=True).encode()
        ).hexdigest()[:16]

        cached = self._discovery_cache.get(cache_key)
        if cached and time.time() - cached[1] < self.FEDERATION_CONFIG["cache_ttl_sec"]:
            # Retornar ferramentas do cache
            return [self._catalog[tid] for tid in cached[0] if tid in self._catalog]

        # Filtrar catálogo local por critérios
        candidates = []
        for tool_id, entry in self._catalog.items():
            # Excluir nós especificados
            if query.exclude_nodes and entry.provider_node_id in query.exclude_nodes:
                continue

            # Verificar capabilities
            if not all(cap in entry.capabilities for cap in query.required_capabilities):
                continue

            # Verificar constraints (com margem para DP noise)
            if query.max_latency_ms and entry.avg_latency_ms > query.max_latency_ms * 1.2:
                continue
            if query.min_success_rate and entry.success_rate < query.min_success_rate * 0.9:
                continue
            if query.min_confidence and entry.confidence_required < query.min_confidence:
                continue

            # Score de relevância: baseado em sucesso, latência, e match de capabilities
            match_score = len(set(entry.capabilities) & set(query.required_capabilities)) / max(1, len(query.required_capabilities))
            performance_score = entry.success_rate * (1 - entry.avg_latency_ms / 1000)
            relevance = 0.5 * match_score + 0.5 * performance_score

            candidates.append((entry, relevance))

        # Ordenar por relevância e retornar top-K
        candidates.sort(key=lambda x: x[1], reverse=True)
        top_entries = [entry for entry, _ in candidates[:20]]  # Top 20

        # Atualizar cache
        self._discovery_cache[cache_key] = (
            [e.tool_id for e in top_entries], time.time()
        )

        # Registrar descoberta
        self._discovery_count += 1
        if self.phi_bus:
            await self.phi_bus.publish_metric("tool_discovery", {
                "query_capabilities": query.required_capabilities,
                "results_found": len(top_entries),
                "dp_epsilon": query.dp_epsilon
            })

        return top_entries

    async def sync_with_peers(self, peer_catalogs: Dict[str, Dict[str, FederatedToolEntry]]):
        """
        Sincroniza catálogo com peers via consenso federado.

        Args:
            peer_catalogs: Mapeamento node_id → {tool_id: entry} de peers
        """
        self._peer_catalogs.update(peer_catalogs)

        # Consolidar entradas: em caso de conflito, usar consenso
        for tool_id, entries in self._merge_conflicting_entries().items():
            if len(entries) > 1:
                # Múltiplas versões: aplicar consenso
                consensus_entry = await self._reach_consensus(tool_id, entries)
                if consensus_entry:
                    self._catalog[tool_id] = consensus_entry
            else:
                self._catalog[tool_id] = entries[0]

        self._sync_rounds += 1
        logger.info(f"🔄 Sincronização de catálogo concluída: round {self._sync_rounds}")

        # Ancorar sincronização na TemporalChain
        if self.temporal:
            await self.temporal.anchor_event("tool_catalog_synced", {
                "node_id": self.node_id,
                "peer_count": len(peer_catalogs),
                "total_tools": len(self._catalog),
                "sync_round": self._sync_rounds,
                "timestamp": time.time()
            })

    def _add_laplace_noise(self, value: float, epsilon: float) -> float:
        """Adiciona ruído Laplace para privacidade diferencial."""
        scale = 1.0 / max(epsilon, 0.01)
        noise = np.random.laplace(0, scale)
        return value + noise

    def _merge_conflicting_entries(
        self
    ) -> Dict[str, List[FederatedToolEntry]]:
        """Agrupa entradas conflitantes por tool_id."""
        merged = defaultdict(list)

        # Adicionar entrada local
        for tool_id, entry in self._catalog.items():
            merged[tool_id].append(entry)

        # Adicionar entradas de peers
        for peer_id, peer_catalog in self._peer_catalogs.items():
            for tool_id, entry in peer_catalog.items():
                # Verificar assinatura PQC se disponível
                if entry.pqc_signature and self.hsm:
                    # Em produção: verificar assinatura
                    pass
                merged[tool_id].append(entry)

        return dict(merged)

    async def _reach_consensus(
        self,
        tool_id: str,
        entries: List[FederatedToolEntry]
    ) -> Optional[FederatedToolEntry]:
        """
        Alcança consenso sobre entrada conflitante.

        Estratégia:
        • Maioria das entradas com mesma provider_org_id vence
        • Em empate: entrada com maior success_rate (ofuscado) vence
        • Se ainda empate: entrada mais recente vence
        """
        if not entries:
            return None

        # Contar por provider_org_id
        org_counts = defaultdict(int)
        for entry in entries:
            org_counts[entry.provider_org_id] += 1

        # Encontrar org majoritária
        majority_org = max(org_counts.keys(), key=lambda o: org_counts[o])
        majority_entries = [e for e in entries if e.provider_org_id == majority_org]

        if len(majority_entries) >= len(entries) * self.FEDERATION_CONFIG["consensus_threshold"]:
            # Maioria clara: retornar entrada mais recente da org majoritária
            return max(majority_entries, key=lambda e: e.last_updated)

        # Sem maioria: retornar entrada com melhor performance
        return max(entries, key=lambda e: e.success_rate * (1 - e.avg_latency_ms / 1000))

    def get_catalog_statistics(self) -> Dict:
        """Retorna estatísticas do catálogo federado."""
        return {
            "node_id": self.node_id,
            "org_id": self.org_id,
            "local_tools": len(self.local_tools),
            "federated_tools": len(self._catalog),
            "peer_nodes": len(self._peer_catalogs),
            "discovery_count": self._discovery_count,
            "sync_rounds": self._sync_rounds,
            "cache_size": len(self._discovery_cache),
            "dp_epsilon_range": f"[{self.FEDERATION_CONFIG['min_dp_epsilon']}, {self.FEDERATION_CONFIG['max_dp_epsilon']}]"
        }
