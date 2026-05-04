# arkhe_time_aggregator.py — Agregador de dados temporais com buffer compartilhado
import numpy as np
import asyncio
import json
import struct
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import multiprocessing.shared_memory as shm
import time

@dataclass
class SyncMeasurement:
    """Medição de sincronização entre dois nós."""
    measurement_id: str
    timestamp_tai_ns: int
    node_a_id: str
    node_b_id: str
    node_a_time_ns: int
    node_b_time_ns: int
    gnss_common_view_sats: List[str]
    fiber_path_length_km: float
    wr_calibration_offset_ps: int
    computed_time_diff_ns: float  # (node_a - node_b) corrigido
    metadata: Dict

class TimeDataAggregator:
    """
    Agregador de dados temporais usando SharedArrayBuffer (via multiprocessing).
    Permite streaming em tempo real para múltiplos consumidores (análise, dashboard, STARK).
    """

    def __init__(self, node_pairs: List[tuple], buffer_size: int = 10000):
        self.node_pairs = node_pairs
        self.buffer_size = buffer_size

        # Criar SharedArrayBuffer para medições (estrutura fixa para performance)
        # Cada medição: 16 floats (64 bytes) + 256 bytes de metadados JSON
        self.measurement_struct_size = 320  # bytes por medição
        self.shared_buffer = shm.SharedMemory(
            name="arkhe_sync_measurements",
            create=True,
            size=buffer_size * self.measurement_struct_size
        )

        # Índices de controle no buffer compartilhado
        self.write_index = 0
        self.read_indices: Dict[str, int] = {}  # Por consumidor

        # Lock para acesso concorrente (em produção: usar semáforo do SO)
        self._lock = asyncio.Lock()

        # Consumidores registrados
        self.consumers: Dict[str, asyncio.Queue] = {}

    async def add_measurement(self, measurement: SyncMeasurement):
        """Adiciona uma medição ao buffer compartilhado (thread-safe)."""
        async with self._lock:
            # Serializar medição para formato binário fixo
            binary_data = self._serialize_measurement(measurement)

            # Escrever no buffer compartilhado
            start_offset = self.write_index * self.measurement_struct_size
            end_offset = start_offset + len(binary_data)
            self.shared_buffer.buf[start_offset:end_offset] = binary_data

            # Atualizar índice de escrita (circular)
            self.write_index = (self.write_index + 1) % self.buffer_size

            # Notificar consumidores registrados
            for consumer_queue in self.consumers.values():
                await consumer_queue.put(measurement)

    def _serialize_measurement(self, m: SyncMeasurement) -> bytes:
        """Serializa medição para formato binário fixo (320 bytes)."""
        # Layout: [8B timestamp][8B node_a_time][8B node_b_time][4B fiber_km]
        #         [4B wr_offset_ps][4B computed_diff][256B metadata_json][4B padding]

        metadata_json = json.dumps(asdict(m), separators=(',', ':'))[:256].ljust(256, '\x00').encode('ascii')

        return struct.pack(
            '<QQQff f 256s 4x',  # little-endian: 3x uint64, 3x float, 256B string, 4B padding
            m.timestamp_tai_ns,
            m.node_a_time_ns,
            m.node_b_time_ns,
            m.fiber_path_length_km,
            m.wr_calibration_offset_ps,
            m.computed_time_diff_ns,
            metadata_json
        )

    def get_measurements_for_pair(self, node_a: str, node_b: str,
                                  limit: int = 1000) -> List[SyncMeasurement]:
        """Recupera medições para um par específico de nós."""
        measurements = []
        # Percorrer buffer circular (simplificado; em produção: usar índice por par)
        for i in range(min(limit, self.buffer_size)):
            offset = ((self.write_index - i - 1) % self.buffer_size) * self.measurement_struct_size
            binary_data = bytes(self.shared_buffer.buf[offset:offset + self.measurement_struct_size])

            try:
                m = self._deserialize_measurement(binary_data)
                if m.node_a_id == node_a and m.node_b_id == node_b:
                    measurements.append(m)
            except Exception:
                continue

        return measurements

    def _deserialize_measurement(self, binary_data: bytes) -> SyncMeasurement:
        """Deserializa medição do formato binário fixo."""
        timestamp, a_time, b_time, fiber_km, wr_offset, diff, metadata_json = struct.unpack(
            '<QQQff f 256s', binary_data[:316]
        )

        metadata = json.loads(metadata_json.decode('ascii').strip('\x00'))
        return SyncMeasurement(**metadata)  # Em produção: reconstruir objeto completo

    def register_consumer(self, consumer_id: str, queue: asyncio.Queue):
        """Registra um consumidor para receber notificações de novas medições."""
        self.consumers[consumer_id] = queue
        self.read_indices[consumer_id] = self.write_index

    def unregister_consumer(self, consumer_id: str):
        """Remove um consumidor registrado."""
        if consumer_id in self.consumers:
            del self.consumers[consumer_id]
            del self.read_indices[consumer_id]

    def close(self):
        """Libera recursos do buffer compartilhado."""
        self.shared_buffer.close()
        self.shared_buffer.unlink()
