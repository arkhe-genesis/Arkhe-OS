#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mobile_sync_optimizer.py — Otimização de sincronização Φ_C para redes móveis.
Adapta taxa de compressão, resolução de dados e frequência de sync
baseado na qualidade da conexão (RTT, largura de banda, tipo de rede).
"""

import asyncio, json, time, zlib, hashlib
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Callable

class NetworkType(Enum):
    WIFI = "wifi"
    ETHERNET = "ethernet"
    MOBILE_5G = "5g"
    MOBILE_4G = "4g"
    MOBILE_3G = "3g"
    OFFLINE = "offline"

@dataclass
class NetworkConditions:
    network_type: NetworkType
    rtt_ms: float
    bandwidth_mbps: float
    packet_loss: float
    jitter_ms: float
    timestamp: float

class MobileSyncOptimizer:
    """
    Otimizador de sincronização para redes móveis.

    Estratégias adaptativas:
    - 5G/WiFi: sync completo a cada 100ms, compressão leve (gzip nível 1)
    - 4G: sync a cada 500ms, compressão média (nível 5), dados resumidos
    - 3G: sync a cada 2s, compressão máxima (nível 9), apenas diff de estado
    - Offline: fila local com backoff exponencial até reconexão
    """

    # Configurações por tipo de rede
    NETWORK_PROFILES = {
        NetworkType.WIFI: {
            "sync_interval_ms": 100,
            "compression_level": 1,
            "full_state_sync": True,
            "max_payload_bytes": 1_048_576,  # 1MB
        },
        NetworkType.MOBILE_5G: {
            "sync_interval_ms": 100,
            "compression_level": 1,
            "full_state_sync": True,
            "max_payload_bytes": 524_288,  # 512KB
        },
        NetworkType.MOBILE_4G: {
            "sync_interval_ms": 500,
            "compression_level": 5,
            "full_state_sync": False,  # Apenas diff
            "max_payload_bytes": 131_072,  # 128KB
        },
        NetworkType.MOBILE_3G: {
            "sync_interval_ms": 2000,
            "compression_level": 9,
            "full_state_sync": False,
            "max_payload_bytes": 32_768,  # 32KB
        },
        NetworkType.OFFLINE: {
            "sync_interval_ms": 30_000,  # 30s tentativas
            "compression_level": 9,
            "full_state_sync": False,
            "max_payload_bytes": 16_384,  # 16KB
        },
    }

    def __init__(
        self,
        network_provider: Callable[[], NetworkConditions],
        phi_c_monitor=None,
    ):
        self.network_provider = network_provider
        self.phi_c_monitor = phi_c_monitor
        self.local_state: Dict = {}
        self.pending_queue: asyncio.Queue = asyncio.Queue()
        self._current_profile = self.NETWORK_PROFILES[NetworkType.WIFI]  # Default otimista

    async def sync_loop(self):
        """Loop principal que adapta comportamento baseado nas condições de rede."""
        while True:
            conditions = await self.network_provider()
            self._current_profile = self.NETWORK_PROFILES.get(
                conditions.network_type,
                self.NETWORK_PROFILES[NetworkType.WIFI]
            )

            if conditions.network_type == NetworkType.OFFLINE:
                await asyncio.sleep(self._current_profile["sync_interval_ms"] / 1000)
                continue

            # Processar itens da fila com compressão adaptativa
            while not self.pending_queue.empty():
                state_update = await self.pending_queue.get()
                compressed = self._compress_payload(
                    state_update,
                    self._current_profile["compression_level"],
                    self._current_profile["max_payload_bytes"]
                )
                if compressed:
                    # Enviar ao servidor de sync (implementação real: Wheeler Mesh)
                    await self._send_compressed_sync(compressed, conditions)
                self.pending_queue.task_done()

            await asyncio.sleep(self._current_profile["sync_interval_ms"] / 1000)

    def _compress_payload(
        self,
        data: Dict,
        level: int,
        max_bytes: int,
    ) -> Optional[bytes]:
        """Comprime payload e verifica se respeita limite de tamanho."""
        json_data = json.dumps(data, sort_keys=True, default=str).encode('utf-8')

        if len(json_data) <= max_bytes:
            return json_data  # Sem compressão necessária

        # Comprimir com zlib
        compressed = zlib.compress(json_data, level)

        if len(compressed) <= max_bytes:
            return compressed

        # Se ainda muito grande, truncar campos não críticos
        if not self._current_profile["full_state_sync"]:
            # Enviar apenas diff
            diff_data = self._compute_diff(self.local_state, data)
            diff_json = json.dumps(diff_data, sort_keys=True, default=str).encode('utf-8')
            diff_compressed = zlib.compress(diff_json, level)
            if len(diff_compressed) <= max_bytes:
                return diff_compressed

        # Último recurso: remover campos de histórico e reduzir precisão
        minimal_data = self._minimize_state(data)
        minimal_json = json.dumps(minimal_data, sort_keys=True, default=str).encode('utf-8')
        minimal_compressed = zlib.compress(minimal_json, level)
        return minimal_compressed if len(minimal_compressed) <= max_bytes else None

    def _compute_diff(self, old_state: Dict, new_state: Dict) -> Dict:
        """Computa diff entre dois estados (apenas campos alterados)."""
        diff = {}
        for key in new_state:
            if key not in old_state or old_state[key] != new_state[key]:
                diff[key] = new_state[key]
        diff["_diff_base"] = old_state.get("_sync_timestamp", 0)
        diff["_diff_timestamp"] = time.time()
        return diff

    def _minimize_state(self, state: Dict) -> Dict:
        """Remove campos não essenciais para sync mínimo."""
        minimal = {
            "phi_c_coherence": round(state.get("phi_c_coherence", 0.95), 3),
            "platform": state.get("platform", "unknown"),
            "last_sync_timestamp": state.get("last_sync_timestamp", time.time()),
        }
        # Arredondar floats para 3 casas decimais
        for key, value in state.items():
            if isinstance(value, float):
                minimal[key] = round(value, 3)
        return minimal

    async def _send_compressed_sync(self, compressed: bytes, conditions: NetworkConditions):
        """Envia payload comprimido via rede (simulado)."""
        # Em produção: enviar via Wheeler Mesh com retry
        latency = conditions.rtt_ms / 1000  # Converter para segundos
        await asyncio.sleep(latency * 0.1)  # Simular latência de rede

        # Ancorar envio
        if self.phi_c_monitor:
            await self.phi_c_monitor.temporal_chain.anchor_event(
                "mobile_sync_sent",
                {
                    "network_type": conditions.network_type.value,
                    "compressed_size": len(compressed),
                    "rtt_ms": conditions.rtt_ms,
                    "timestamp": time.time(),
                }
            )

    async def enqueue_sync(self, state_update: Dict):
        """Enfileira atualização de estado para sincronização."""
        await self.pending_queue.put(state_update)

    def get_current_profile_info(self) -> Dict:
        """Retorna informações do perfil de rede atual."""
        return {
            "profile": self._current_profile,
            "queue_size": self.pending_queue.qsize(),
        }