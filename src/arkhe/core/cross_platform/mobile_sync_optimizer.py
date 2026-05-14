#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mobile_sync_optimizer.py — Substrato 7.9.0: Otimização de Sync para Redes Móveis
Compressão adaptativa, priorização de dados críticos, e fallback offline-first.
"""

import asyncio, json, time, hashlib, zlib
from typing import Optional, Dict, List, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum, auto


class NetworkCondition(Enum):
    """Condições de rede detectadas para otimização de sync."""
    WIFI_HIGH_SPEED = "wifi_high"      # ≥50 Mbps, baixa latência
    WIFI_MEDIUM = "wifi_medium"         # 10-50 Mbps
    CELLULAR_5G = "cellular_5g"         # 5G: 50-200 Mbps
    CELLULAR_4G = "cellular_4g"         # 4G/LTE: 5-50 Mbps
    CELLULAR_3G = "cellular_3g"         # 3G: 0.5-5 Mbps
    CELLULAR_EDGE = "cellular_edge"     # EDGE/2G: <0.5 Mbps
    OFFLINE = "offline"                 # Sem conexão

@dataclass
class SyncCompressionConfig:
    """Configuração de compressão adaptativa baseada em rede."""
    network_condition: NetworkCondition
    enable_compression: bool = True
    compression_level: int = 6  # 1-9 para zlib
    min_payload_size_for_compression: int = 1024  # Bytes
    prioritize_critical_fields: List[str] = field(default_factory=lambda: ["phi_c_coherence", "temporal_anchor", "security_credentials"])
    allow_lossy_compression: bool = False  # Para dados não-críticos
    max_payload_size_bytes: int = 500 * 1024  # 500 KB limite para redes lentas

class MobileSyncOptimizer:
    """
    Otimizador de sincronização para redes móveis com compressão adaptativa.

    Estratégia:
    1. Detectar condição de rede atual (via NetworkInformation API ou native bridge)
    2. Selecionar estratégia de compressão baseada em bandwidth/latência
    3. Priorizar campos críticos (Φ_C, segurança) sobre dados auxiliares
    4. Aplicar compressão lossless (zlib) ou lossy (quantização) conforme configuração
    5. Fallback para offline-first quando rede indisponível
    """

    # Perfis de compressão por condição de rede
    COMPRESSION_PROFILES = {
        NetworkCondition.WIFI_HIGH_SPEED: {
            "compression_level": 1,  # Rápido, pouca compressão
            "max_payload_kb": 2048,
            "prioritize_critical": False,
            "allow_lossy": False,
        },
        NetworkCondition.WIFI_MEDIUM: {
            "compression_level": 4,
            "max_payload_kb": 1024,
            "prioritize_critical": False,
            "allow_lossy": False,
        },
        NetworkCondition.CELLULAR_5G: {
            "compression_level": 5,
            "max_payload_kb": 512,
            "prioritize_critical": True,
            "allow_lossy": False,
        },
        NetworkCondition.CELLULAR_4G: {
            "compression_level": 7,
            "max_payload_kb": 256,
            "prioritize_critical": True,
            "allow_lossy": True,  # Quantização leve para floats
        },
        NetworkCondition.CELLULAR_3G: {
            "compression_level": 9,  # Máxima compressão
            "max_payload_kb": 64,
            "prioritize_critical": True,
            "allow_lossy": True,  # Quantização agressiva
        },
        NetworkCondition.CELLULAR_EDGE: {
            "compression_level": 9,
            "max_payload_kb": 16,  # Muito restritivo
            "prioritize_critical": True,
            "allow_lossy": True,
            "critical_fields_only": True,  # Enviar apenas campos essenciais
        },
        NetworkCondition.OFFLINE: {
            "compression_level": 9,
            "max_payload_kb": 0,  # Não enviar, apenas armazenar local
            "prioritize_critical": True,
            "allow_lossy": True,
            "offline_mode": True,
        },
    }

    def __init__(
        self,
        network_detector: Optional[Callable[[], NetworkCondition]] = None,
        config: Optional[SyncCompressionConfig] = None,
    ):
        self.network_detector = network_detector or self._detect_network_default
        self.config = config
        self.offline_queue: List[Dict] = []
        self.sync_stats: Dict[str, int] = {
            "total_syncs": 0,
            "compressed_payloads": 0,
            "bytes_saved": 0,
            "offline_queued": 0,
        }

    def _detect_network_default(self) -> NetworkCondition:
        """Detecção padrão de rede (simulado). Em produção: usar APIs nativas."""
        # Em produção:
        # - iOS: NWPathMonitor
        # - Android: ConnectivityManager + NetworkCallback
        # - Web: NetworkInformation API (experimental)
        return NetworkCondition.CELLULAR_4G  # Simulado para demo

    async def prepare_payload_for_sync(
        self,
        data: Dict,
        custom_config: Optional[SyncCompressionConfig] = None,
    ) -> Tuple[bytes, "SyncMetadata"]:
        """
        Prepara payload para sincronização com compressão adaptativa.

        Returns:
            (payload comprimido em bytes, metadados para descompressão)
        """
        config = custom_config or self.config or self._create_default_config()
        network = config.network_condition or self.network_detector()
        profile = self.COMPRESSION_PROFILES.get(network, self.COMPRESSION_PROFILES[NetworkCondition.CELLULAR_4G])

        # 1. Filtrar campos baseado em prioridade
        filtered_data = self._prioritize_fields(data, profile["prioritize_critical"], config.prioritize_critical_fields)

        # 2. Aplicar compressão lossy se permitido e necessário
        if profile["allow_lossy"] and config.allow_lossy_compression:
            filtered_data = self._apply_lossy_compression(filtered_data, network)

        # 3. Serializar para JSON compacto
        json_str = json.dumps(filtered_data, separators=(',', ':'), sort_keys=True)
        original_size = len(json_str.encode('utf-8'))

        # 4. Aplicar compressão zlib se benéfico
        compressed_bytes = json_str.encode('utf-8')
        compression_ratio = 1.0

        if config.enable_compression and original_size >= config.min_payload_size_for_compression:
            compressed = zlib.compress(compressed_bytes, level=profile["compression_level"])
            if len(compressed) < original_size:
                compressed_bytes = compressed
                compression_ratio = original_size / len(compressed)
                self.sync_stats["compressed_payloads"] += 1
                self.sync_stats["bytes_saved"] += original_size - len(compressed)

        # 5. Verificar limite de payload
        if len(compressed_bytes) > profile["max_payload_kb"] * 1024 and network != NetworkCondition.OFFLINE:
            # Recursivamente reduzir dados até caber no limite
            filtered_data = self._reduce_payload_size(filtered_data, profile["max_payload_kb"] * 1024)
            json_str = json.dumps(filtered_data, separators=(',', ':'), sort_keys=True)
            compressed_bytes = zlib.compress(json_str.encode('utf-8'), level=9)

        # 6. Criar metadados para descompressão no receptor
        metadata = SyncMetadata(
            original_size=original_size,
            compressed_size=len(compressed_bytes),
            compression_ratio=compression_ratio,
            network_condition=network.value,
            compression_level=profile["compression_level"],
            lossy_applied=profile["allow_lossy"] and config.allow_lossy_compression,
            timestamp=time.time(),
            critical_fields=config.prioritize_critical_fields,
        )

        # 7. Se offline, enfileirar para sync posterior
        if network == NetworkCondition.OFFLINE:
            self.offline_queue.append({
                "payload": compressed_bytes,
                "metadata": metadata,
                "queued_at": time.time(),
            })
            self.sync_stats["offline_queued"] += 1
            # Retornar payload vazio + flag offline
            metadata.offline_queued = True
            return b"", metadata

        return compressed_bytes, metadata

    def _create_default_config(self) -> SyncCompressionConfig:
        return SyncCompressionConfig(network_condition=self.network_detector())

    def _prioritize_fields(
        self,
        data: Dict,
        prioritize_critical: bool,
        critical_fields: List[str],
    ) -> Dict:
        """Filtra dados mantendo campos críticos primeiro."""
        if not prioritize_critical:
            return data

        result = {}
        # Primeiro: campos críticos
        for field in critical_fields:
            if field in data:
                result[field] = data[field]
        # Depois: demais campos
        for key, value in data.items():
            if key not in result and key not in critical_fields:
                result[key] = value
        return result

    def _apply_lossy_compression(self, data: Dict, network: NetworkCondition) -> Dict:
        """Aplica compressão lossy (quantização) para dados numéricos."""
        # Fator de quantização baseado na rede
        quantization_bits = {
            NetworkCondition.CELLULAR_4G: 3,  # ~3 bits de precisão
            NetworkCondition.CELLULAR_3G: 2,
            NetworkCondition.CELLULAR_EDGE: 1,
        }.get(network, 4)

        def quantize_float(value: float, bits: int) -> float:
            """Quantiza float para número limitado de bits significativos."""
            if not isinstance(value, (int, float)):
                return value
            # Arredondar para múltiplo de 2^(-bits)
            multiplier = 2 ** bits
            return round(value * multiplier) / multiplier

        def recurse(obj):
            if isinstance(obj, dict):
                return {k: recurse(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [recurse(v) for v in obj]
            elif isinstance(obj, float):
                return quantize_float(obj, quantization_bits)
            else:
                return obj

        return recurse(data)

    def _reduce_payload_size(self, data: Dict, max_bytes: int) -> Dict:
        """Reduz payload removendo campos não-críticos até caber no limite."""
        # Estratégia simples: remover campos por ordem de prioridade decrescente
        priority_order = [
            "phi_c_coherence", "temporal_anchor", "security_credentials",  # Críticos
            "operation", "result", "timestamp",  # Importantes
            "metadata", "context", "debug_info",  # Auxiliares
            "raw_data", "intermediate_states",  # Removíveis primeiro
        ]

        result = data.copy()
        current_size = len(json.dumps(result, separators=(',', ':')).encode('utf-8'))

        # Remover campos de baixa prioridade iterativamente
        for field in reversed(priority_order):
            if current_size <= max_bytes:
                break
            if field in result:
                del result[field]
                current_size = len(json.dumps(result, separators=(',', ':')).encode('utf-8'))

        return result

    async def decompress_payload(
        self,
        compressed_bytes: bytes,
        metadata: "SyncMetadata",
    ) -> Dict:
        """Descomprime payload recebido com base nos metadados."""
        if metadata.offline_queued:
            # Payload offline: retornar vazio, processar depois
            return {}

        # Descomprimir zlib
        if metadata.compressed_size < metadata.original_size:
            decompressed = zlib.decompress(compressed_bytes)
        else:
            decompressed = compressed_bytes

        # Parse JSON
        data = json.loads(decompressed.decode('utf-8'))

        # Se lossy foi aplicado, pode-se aplicar pós-processamento (opcional)
        if metadata.lossy_applied:
            # Em produção: aplicar suavização ou interpolação
            pass

        return data

    async def flush_offline_queue(self) -> List["SyncResult"]:
        """Tenta enviar itens enfileirados durante offline quando conexão retorna."""
        results = []
        current_network = self.network_detector()

        if current_network == NetworkCondition.OFFLINE:
            return results  # Ainda offline

        # Processar fila em ordem
        while self.offline_queue:
            item = self.offline_queue.pop(0)
            # Re-preparar payload com condição de rede atual
            config = SyncCompressionConfig(network_condition=current_network)
            # Re-comprimir com nova condição
            payload, metadata = await self.prepare_payload_for_sync(
                await self.decompress_payload(item["payload"], item["metadata"]),
                config
            )
            # Simular envio
            results.append(SyncResult(
                success=True,
                bytes_sent=len(payload),
                network_condition=current_network.value,
                was_offline_queued=True,
            ))
            self.sync_stats["total_syncs"] += 1

        return results

    def get_optimization_stats(self) -> Dict:
        """Retorna estatísticas de otimização para monitoramento."""
        avg_compression = (
            self.sync_stats["bytes_saved"] /
            (self.sync_stats["compressed_payloads"] * 1024)
            if self.sync_stats["compressed_payloads"] > 0 else 0
        )
        return {
            **self.sync_stats,
            "avg_compression_ratio": f"{1 + avg_compression:.2f}x",
            "offline_queue_size": len(self.offline_queue),
            "current_network": self.network_detector().value,
        }


@dataclass
class SyncMetadata:
    """Metadados para descompressão e auditoria de payload sincronizado."""
    original_size: int
    compressed_size: int
    compression_ratio: float
    network_condition: str
    compression_level: int
    lossy_applied: bool
    timestamp: float
    critical_fields: List[str]
    offline_queued: bool = False


@dataclass
class SyncResult:
    """Resultado de uma operação de sincronização otimizada."""
    success: bool
    bytes_sent: int
    network_condition: str
    was_offline_queued: bool = False
    error: Optional[str] = None
