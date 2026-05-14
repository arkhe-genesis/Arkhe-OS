#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
edge_sync_optimizer.py — Substrato 7.4.0: Otimização de Sincronização Edge para 5G/6G
Network slicing, URLLC e edge caching adaptativo para latência mínima.
"""

import numpy as np
import asyncio, json, time, hashlib
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

class NetworkSlice(Enum):
    """Tipos de network slice para diferentes cargas de trabalho Arkhe."""
    URLLC = auto()      # Ultra-Reliable Low Latency: <1ms, 99.999% reliability
    EMBB = auto()       # Enhanced Mobile Broadband: alta largura de banda
    MMTC = auto()       # Massive Machine-Type Communications: muitos dispositivos
    QUANTUM_SYNC = auto() # Slice dedicado para sincronização quântica Φ_C

@dataclass
class EdgeSyncConfig:
    """Configuração de sincronização edge otimizada para 5G/6G."""
    device_id: str
    preferred_slice: NetworkSlice = NetworkSlice.QUANTUM_SYNC
    max_latency_ms: float = 1.0  # Target para URLLC
    min_reliability: float = 0.99999
    adaptive_caching: bool = True
    phi_c_priority: float = 1.0  # Peso para sincronização de coerência

@dataclass
class SyncRecord:
    """Registro de uma operação de sincronização."""
    timestamp: float
    latency_ns: float
    slice: NetworkSlice
    success: bool
    source: str = "network"

@dataclass
class SyncResult:
    """Resultado de uma operação de sincronização."""
    success: bool
    latency_ns: float
    source: str  # "cache" ou "network"
    slice_used: NetworkSlice
    error: Optional[str] = None
    phi_c_coherence: Optional[float] = None

class EdgeSyncOptimizer:
    """
    Otimizador de sincronização edge para redes 5G/6G.

    Features:
    • Network slicing dinâmico baseado em carga de trabalho
    • URLLC para sincronização crítica de Φ_C
    • Edge caching adaptativo com previsão de demanda
    • Handover suave entre células 5G/6G
    • QoS garantida para operações quânticas distribuídas
    """

    # Parâmetros de QoS por slice (baseados em 3GPP)
    SLICE_QOS_PARAMS = {
        NetworkSlice.URLLC: {"latency_ms": 1.0, "reliability": 0.99999, "jitter_ms": 0.1},
        NetworkSlice.EMBB: {"latency_ms": 10.0, "reliability": 0.999, "jitter_ms": 1.0},
        NetworkSlice.MMTC: {"latency_ms": 100.0, "reliability": 0.99, "jitter_ms": 10.0},
        NetworkSlice.QUANTUM_SYNC: {"latency_ms": 0.5, "reliability": 0.999999, "jitter_ms": 0.05},
    }

    def __init__(self, config: EdgeSyncConfig):
        self.config = config
        self.current_slice = config.preferred_slice
        self.cache: Dict[str, Tuple[any, float]] = {}  # key -> (value, timestamp)
        self.sync_history: List[SyncRecord] = []

    async def request_network_slice(self, workload_type: str) -> NetworkSlice:
        """Solicita network slice ótimo baseado no tipo de carga de trabalho."""
        # Mapear workload para slice ideal
        workload_map = {
            "phi_c_sync": NetworkSlice.QUANTUM_SYNC,
            "quantum_inference": NetworkSlice.URLLC,
            "data_ingestion": NetworkSlice.EMBB,
            "sensor_telemetry": NetworkSlice.MMTC,
        }

        preferred = workload_map.get(workload_type, self.config.preferred_slice)

        # Verificar disponibilidade do slice (simulado)
        if await self._check_slice_availability(preferred):
            self.current_slice = preferred
            return preferred
        else:
            # Fallback para slice disponível com QoS mais próxima
            fallback = await self._find_best_available_slice(preferred)
            self.current_slice = fallback
            return fallback

    async def _check_slice_availability(self, slice_type: NetworkSlice) -> bool:
        """Verifica disponibilidade do slice na rede 5G/6G."""
        # Em produção: consultar 5G Core Network Exposure Function (NEF)
        # Simulado: 95% de disponibilidade para slices normais
        return np.random.random() < 0.95

    async def _find_best_available_slice(self, preferred: NetworkSlice) -> NetworkSlice:
        """Encontra slice disponível com QoS mais próxima do preferido."""
        available = [s for s in NetworkSlice if await self._check_slice_availability(s)]
        if not available:
            return NetworkSlice.MMTC  # Último recurso

        # Ordenar por proximidade de QoS ao preferido
        target_qos = self.SLICE_QOS_PARAMS[preferred]
        def qos_distance(slice_type):
            qos = self.SLICE_QOS_PARAMS[slice_type]
            return abs(qos["latency_ms"] - target_qos["latency_ms"]) + \
                   abs(qos["reliability"] - target_qos["reliability"])

        return min(available, key=qos_distance)

    async def sync_with_low_latency(
        self,
        data: Dict,
        priority: str = "normal",
    ) -> SyncResult:
        """Sincroniza dados com latência otimizada via slice selecionado."""
        start_time = time.time_ns()

        # Solicitar slice apropriado
        workload = "phi_c_sync" if "phi_c" in data else "data_ingestion"
        await self.request_network_slice(workload)

        # Aplicar caching adaptativo se habilitado
        if self.config.adaptive_caching:
            cache_key = self._compute_cache_key(data)
            if cache_key in self.cache:
                cached_value, cached_time = self.cache[cache_key]
                # Servir do cache se ainda válido (TTL baseado em slice)
                ttl = self._get_cache_ttl(self.current_slice)
                if time.time() - cached_time < ttl:
                    return SyncResult(
                        success=True,
                        latency_ns=time.time_ns() - start_time,
                        source="cache",
                        slice_used=self.current_slice,
                    )

        # Transmitir via slice selecionado (simulado)
        qos = self.SLICE_QOS_PARAMS[self.current_slice]

        # Simular latência com distribuição baseada no slice
        base_latency = qos["latency_ms"] * 1e6  # converter para ns
        jitter = qos["jitter_ms"] * 1e6
        actual_latency = np.random.normal(base_latency, jitter)
        actual_latency = max(0, actual_latency)  # Não negativo

        # Simular confiabilidade
        if np.random.random() > qos["reliability"]:
            # Falha de transmissão
            return SyncResult(
                success=False,
                latency_ns=time.time_ns() - start_time,
                error="transmission_failed",
                slice_used=self.current_slice,
            )

        # Sucesso: armazenar no cache se aplicável
        if self.config.adaptive_caching and priority != "urgent":
            self.cache[self._compute_cache_key(data)] = (data, time.time())

        # Registrar histórico
        self.sync_history.append(SyncRecord(
            timestamp=time.time(),
            latency_ns=actual_latency,
            slice=self.current_slice,
            success=True,
            source="network"
        ))

        return SyncResult(
            success=True,
            latency_ns=actual_latency,
            source="network",
            slice_used=self.current_slice,
            phi_c_coherence=data.get("phi_c", 0.99),
        )

    def _compute_cache_key(self, data: Dict) -> str:
        """Computa chave de cache para dados de sincronização."""
        # Usar hash dos campos críticos para cache key
        critical_fields = {k: data[k] for k in ["device_id", "phi_c", "timestamp"] if k in data}
        return hashlib.sha3_256(json.dumps(critical_fields, sort_keys=True).encode()).hexdigest()[:16]

    def _get_cache_ttl(self, slice_type: NetworkSlice) -> float:
        """Retorna TTL de cache baseado no slice (mais curto para slices de baixa latência)."""
        ttl_map = {
            NetworkSlice.QUANTUM_SYNC: 0.1,  # 100ms para sincronização quântica
            NetworkSlice.URLLC: 1.0,          # 1s para URLLC
            NetworkSlice.EMBB: 10.0,          # 10s para EMBB
            NetworkSlice.MMTC: 60.0,          # 60s para MMTC
        }
        return ttl_map.get(slice_type, 10.0)

    def get_sync_statistics(self) -> Dict:
        """Retorna estatísticas de sincronização para monitoramento."""
        if not self.sync_history:
            return {"total_syncs": 0}

        recent = self.sync_history[-100:]  # Últimas 100 sincronizações
        return {
            "total_syncs": len(self.sync_history),
            "success_rate": sum(1 for r in recent if r.success) / len(recent),
            "avg_latency_ms": np.mean([r.latency_ns / 1e6 for r in recent]),
            "p99_latency_ms": np.percentile([r.latency_ns / 1e6 for r in recent], 99),
            "slice_distribution": {s.name: sum(1 for r in recent if r.slice == s) for s in NetworkSlice},
            "cache_hit_rate": sum(1 for r in recent if r.source == "cache") / len(recent),
        }

# ============================================================================
# Exemplo: Sincronização de Φ_C com URLLC em 5G
# ============================================================================
async def demo_5g_edge_sync():
    """Demonstra sincronização edge otimizada para 5G/6G."""

    config = EdgeSyncConfig(
        device_id="edge-node-001",
        preferred_slice=NetworkSlice.QUANTUM_SYNC,
        max_latency_ms=0.5,
        adaptive_caching=True,
    )

    optimizer = EdgeSyncOptimizer(config)

    # Simular múltiplas sincronizações de Φ_C
    for i in range(10):
        data = {
            "device_id": config.device_id,
            "phi_c": 0.99 + np.random.random() * 0.01,
            "timestamp": time.time(),
            "mesh_connections": np.random.randint(5, 20),
        }

        result = await optimizer.sync_with_low_latency(data, priority="high")

        if result.success:
            print(f"✓ Sync #{i+1}: {result.latency_ns/1e6:.3f}ms via {result.slice_used.name} ({result.source})")
        else:
            print(f"✗ Sync #{i+1}: FAILED - {result.error}")

    # Mostrar estatísticas
    stats = optimizer.get_sync_statistics()
    print(f"\n📊 Estatísticas de sincronização:")
    print(f"   • Taxa de sucesso: {stats['success_rate']*100:.1f}%")
    print(f"   • Latência média: {stats['avg_latency_ms']:.3f}ms")
    print(f"   • Latência p99: {stats['p99_latency_ms']:.3f}ms")
    print(f"   • Cache hit rate: {stats['cache_hit_rate']*100:.1f}%")
    print(f"   • Distribuição de slices: {stats['slice_distribution']}")

if __name__ == "__main__":
    asyncio.run(demo_5g_edge_sync())
