#!/usr/bin/env python3
# ============================================================
# ARKHE OS — SUBSTRATO 256: MRC NETWORKING PROTOCOL
# Multipath Reliable Connection para Hyper-Mesh
# Open Compute Project (OCP) — Adaptação ARKHE OS v∞.Ω.∇+++.256.0
# ============================================================

import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import random

class PlaneStatus(Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    RETIRED = "retired"
    RECOVERING = "recovering"

@dataclass
class Plane:
    plane_id: int
    status: PlaneStatus = PlaneStatus.ACTIVE
    coherence: float = 1.0
    latency_us: float = 1.0
    bandwidth_gbps: float = 100.0
    packets_sent: int = 0
    packets_lost: int = 0
    bytes_transferred: int = 0
    last_probe_time: float = 0.0
    failure_count: int = 0

@dataclass
class Packet:
    packet_id: int
    plane_id: int
    sequence_num: int
    payload: np.ndarray
    header: Dict
    timestamp: float
    trimmed: bool = False

@dataclass
class RouteEntry:
    dest_node: str
    segments: List[int]
    coherence_threshold: float = 0.5
    failover_planes: List[int] = field(default_factory=list)

class MRCTransportLayer:
    """
    Substrato 256: Multipath Reliable Connection para ARKHE OS.

    Mapeia conceitos MRC (OpenAI/AMD/Broadcom/Intel/Microsoft/NVIDIA, OCP 2026)
    para o domínio de coerência quântica da Hyper-Mesh.

    Integrações:
    - Substrato 120: Correção de erros com síndromes parciais (packet trimming)
    - Substrato 121: Barramento superfluido multiplexado (multi-modo)
    - Substrato 122: Roteamento A* determinístico (SRv6 estático)
    - Substrato 125: Interface CTC-fóton (camada física óptica)
    - Substrato 230: API 5D Projection (transporte de gradientes)
    """

    def __init__(self, node_id: str, num_planes: int = 8, lambda_var: float = 0.1):
        self.node_id = node_id
        self.num_planes = num_planes
        self.lambda_var = lambda_var
        self.planes = [Plane(i) for i in range(num_planes)]
        self.static_routes: Dict[str, RouteEntry] = {}
        self.packet_counter = 0
        self.sequence_counter = 0
        self.received_packets: Dict[int, Packet] = {}
        self.probe_interval_us = 100.0
        self.coherence_history: List[List[float]] = []
        self.trim_threshold = 0.3

    def _load_srv6_table(self, routes: Dict[str, RouteEntry] = None):
        """Carrega tabela de rotas SRv6 estáticas."""
        if routes:
            self.static_routes = routes
        else:
            for i in range(16):
                dest = f"node_{i:02d}"
                segments = list(range(self.num_planes))
                random.shuffle(segments)
                self.static_routes[dest] = RouteEntry(
                    dest_node=dest,
                    segments=segments[:4],
                    coherence_threshold=0.5
                )

    def compute_transmission_coherence(self) -> float:
        """
        Φ_C^transmissão = (1/P)ΣΦ_C^(p) - λ·Var(Φ_C^(p))

        Coerência composta da transmissão com penalidade por variância
        entre planos. Substrato 256 — Equação 1.
        """
        active_planes = [p for p in self.planes if p.status == PlaneStatus.ACTIVE]
        if not active_planes:
            return 0.0

        coherences = [p.coherence for p in active_planes]
        mean_coh = np.mean(coherences)
        var_coh = np.var(coherences)

        phi = mean_coh - self.lambda_var * var_coh
        return max(0.0, min(1.0, phi))

    def spray_packets(self, tensor: np.ndarray, dest_node: str) -> List[Packet]:
        """
        Pulverização adaptativa: distribui fatias do tensor por planos ativos.

        Cada plano recebe uma fatia ortogonal do tensor, análogo à excitação
        de múltiplos modos normais no barramento superfluido (Substrato 121).
        """
        active_planes = [p for p in self.planes if p.status == PlaneStatus.ACTIVE]
        if not active_planes:
            raise RuntimeError("Nenhum plano ativo disponível para transmissão")

        n_active = len(active_planes)
        slices = np.array_split(tensor, n_active)
        packets = []

        route = self.static_routes.get(dest_node)
        if not route:
            route = RouteEntry(dest_node=dest_node, segments=list(range(n_active)))

        for idx, (plane, slc) in enumerate(zip(active_planes, slices)):
            self.packet_counter += 1
            self.sequence_counter += 1

            # Packet trimming: síndrome parcial quando coerência < threshold
            should_trim = plane.coherence < self.trim_threshold

            pkt = Packet(
                packet_id=self.packet_counter,
                plane_id=plane.plane_id,
                sequence_num=self.sequence_counter,
                payload=np.array([]) if should_trim else slc,
                header={
                    'src': self.node_id,
                    'dest': dest_node,
                    'segment_list': route.segments,
                    'coherence': plane.coherence,
                    'timestamp': datetime.now().timestamp(),
                    'trimmed': should_trim,
                    'tensor_shape': tensor.shape,
                    'slice_index': idx,
                    'total_slices': n_active
                },
                timestamp=datetime.now().timestamp(),
                trimmed=should_trim
            )

            plane.packets_sent += 1
            if not should_trim:
                plane.bytes_transferred += slc.nbytes

            packets.append(pkt)

        self.coherence_history.append([p.coherence for p in self.planes])
        return packets

    def detect_failure(self, plane_id: int, loss_rate: float = 0.0) -> bool:
        """
        Detecção de falhas em microssegundos com aposentadoria imediata.

        Substrato 256 — Seção 4. Mapeia para Byzantine Fault Tolerance
        Temporal (Substrato 129 proposto).
        """
        plane = self.planes[plane_id]

        if loss_rate > 0.05 or plane.coherence < 0.1:
            plane.status = PlaneStatus.RETIRED
            plane.coherence = 0.0
            plane.failure_count += 1
            self._redistribute_traffic(plane_id)
            return True

        if loss_rate > 0.01:
            plane.status = PlaneStatus.DEGRADED
            plane.coherence *= 0.8
            return False

        return False

    def _redistribute_traffic(self, failed_plane_id: int):
        """Redistribui carga do plano falho para os ativos restantes."""
        active = [p for p in self.planes if p.status == PlaneStatus.ACTIVE]
        if active:
            boost = 1.0 + (1.0 / len(active))
            for p in active:
                p.bandwidth_gbps = min(200.0, p.bandwidth_gbps * boost)

    def send_probe(self, plane_id: int) -> bool:
        """
        Envia sonda de verificação para plano aposentado.
        Fase de aquecimento com coerência = 0.3 antes de reativação.
        """
        plane = self.planes[plane_id]
        if plane.status != PlaneStatus.RETIRED:
            return False

        if random.random() < 0.7:
            plane.status = PlaneStatus.RECOVERING
            plane.coherence = 0.3
            plane.last_probe_time = datetime.now().timestamp()
            return True

        return False

    def promote_recovered_planes(self):
        """Promove planos em recuperação para ativos se coerência > 0.8."""
        for p in self.planes:
            if p.status == PlaneStatus.RECOVERING and p.coherence >= 0.8:
                p.status = PlaneStatus.ACTIVE

    def update_coherence(self, plane_id: int, measured_coherence: float):
        """Atualiza coerência de um plano com medição externa (ex: do CTC)."""
        self.planes[plane_id].coherence = max(0.0, min(1.0, measured_coherence))

    def receive_packet(self, packet: Packet) -> Optional[np.ndarray]:
        """
        Recebe pacote e reconstrói tensor.
        Pacotes trimmados funcionam como síndromes parciais (Substrato 120).
        """
        self.received_packets[packet.sequence_num] = packet
        return packet.payload if not packet.trimmed else None

    def get_network_state(self) -> Dict:
        """Retorna estado completo da camada MRC."""
        return {
            'node_id': self.node_id,
            'transmission_coherence': self.compute_transmission_coherence(),
            'active_planes': sum(1 for p in self.planes if p.status == PlaneStatus.ACTIVE),
            'retired_planes': sum(1 for p in self.planes if p.status == PlaneStatus.RETIRED),
            'degraded_planes': sum(1 for p in self.planes if p.status == PlaneStatus.DEGRADED),
            'total_packets_sent': sum(p.packets_sent for p in self.planes),
            'total_bytes': sum(p.bytes_transferred for p in self.planes),
            'planes': [
                {
                    'id': p.plane_id,
                    'status': p.status.value,
                    'coherence': round(p.coherence, 4),
                    'bandwidth_gbps': p.bandwidth_gbps,
                    'packets_sent': p.packets_sent,
                    'failures': p.failure_count
                }
                for p in self.planes
            ]
        }


if __name__ == "__main__":
    # Demo rápida
    mrc = MRCTransportLayer("demo_node", num_planes=8)
    mrc._load_srv6_table()

    tensor = np.random.randn(1024, 1024)
    packets = mrc.spray_packets(tensor, "node_01")

    print(f"Substrato 256 MRC Demo")
    print(f"Pacotes pulverizados: {len(packets)}")
    print(f"Coerência de transmissão: {mrc.compute_transmission_coherence():.4f}")
    print(f"Estado da rede: {mrc.get_network_state()}")
