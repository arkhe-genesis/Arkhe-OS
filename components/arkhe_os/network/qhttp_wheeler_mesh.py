#!/usr/bin/env python3
"""
qhttp_wheeler_mesh.py — Protocolo qhttp:// para transmissão entre nós Wheeler Mesh.
Implementa comunicação quântica topológica com roteamento baseado em geodésicas da Renda Neural.
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple, Callable, Union, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import hashlib
import asyncio
import json

class WheelerNodeType(Enum):
    """Tipos de nós na Wheeler Mesh."""
    NEURAL_LACE_NODE = auto()    # Nó da Renda Neural (Substrato 112)
    GATEWAY_NODE = auto()         # Gateway clássico-quântico
    RELAY_NODE = auto()           # Nó de retransmissão topológica
    OBSERVER_NODE = auto()        # Nó de observação/auditoria

class QHTTPMethod(Enum):
    """Métodos do protocolo qhttp://."""
    GET_STATE = auto()           # Obter estado quântico de um nó
    SEND_STATE = auto()          # Enviar estado quântico para outro nó
    SYNC_CLOCK = auto()          # Sincronizar clock quântico
    ROUTE_VIA = auto()           # Roteamento explícito via geodésica
    AUDIT_PATH = auto()          # Auditoria de caminho de transmissão

@dataclass
class QuantumStatePacket:
    """Pacote de estado quântico para transmissão via qhttp://."""
    packet_id: str
    source_node_id: str
    destination_node_id: str
    state_vector: Optional[torch.Tensor]  # |ψ⟩ para transmissão
    density_matrix: Optional[torch.Tensor]  # ρ para estados mistos
    topological_charge: int  # Q do skyrmion associado
    timestamp: float
    fidelity_threshold: float = 0.8  # Fidelidade mínima para aceitação
    route_geodesic: Optional[List[str]] = None  # Caminho geodésico preferido
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_hash(self) -> str:
        """Hash canônico do pacote para verificação de integridade."""
        data = {
            'packet_id': self.packet_id,
            'source': self.source_node_id,
            'dest': self.destination_node_id,
            'topological_charge': self.topological_charge,
            'timestamp': self.timestamp
        }
        if self.state_vector is not None:
            data['state_hash'] = hashlib.sha256(
                self.state_vector.cpu().numpy().tobytes()
            ).hexdigest()[:16]
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()[:24]

    def verify_integrity(self, received_hash: str) -> bool:
        """Verifica integridade do pacote recebido."""
        return self.compute_hash() == received_hash

@dataclass
class WheelerMeshNode:
    """Representa um nó na Wheeler Mesh."""
    node_id: str
    node_type: WheelerNodeType
    position: np.ndarray  # Coordenadas na variedade quasicristalina
    quantum_capacity: float  # Qubits/s de capacidade de transmissão
    classical_bandwidth: float  # Mbps para metadados
    connected_neighbors: List[str] = field(default_factory=list)
    _online: bool = True

    def geodesic_distance_to(self, other: 'WheelerMeshNode', base_metric) -> float:
        """Calcula distância geodésica para outro nó."""
        return base_metric.geodesic_distance(self.position, other.position)

class WheelerMeshProtocol:
    """
    Protocolo qhttp:// para transmissão entre nós Wheeler Mesh.
    Características:
    - Roteamento baseado em geodésicas da Renda Neural (Substrato 112)
    - Verificação de integridade via hash topológico
    - Tolerância a falhas via caminhos alternativos quasicristalinos
    - Priorização por carga topológica (skyrmion Q)
    """

    def __init__(
        self,
        local_node: WheelerMeshNode,
        base_metric: Any,  # Do Substrato 112
        fidelity_threshold: float = 0.8,
        max_hops: int = 7,
        enable_topological_routing: bool = True
    ):
        self.local_node = local_node
        self.base_metric = base_metric
        self.fidelity_threshold = fidelity_threshold
        self.max_hops = max_hops
        self.enable_topological_routing = enable_topological_routing

        # Registro de nós conhecidos
        self.known_nodes: Dict[str, WheelerMeshNode] = {local_node.node_id: local_node}

        # Filas de transmissão
        self.outbound_queue: asyncio.Queue = asyncio.Queue()
        self.inbound_queue: asyncio.Queue = asyncio.Queue()

        # Cache de rotas geodésicas
        self.route_cache: Dict[Tuple[str, str], List[str]] = {}

        # Métricas de transmissão
        self.transmission_metrics = {
            'packets_sent': 0,
            'packets_received': 0,
            'avg_fidelity': 0.0,
            'topological_errors': 0,
            'geodesic_hops_avg': 0.0
        }

        # Callbacks para eventos
        self.event_callbacks: List[Callable] = []

        # Estado do protocolo
        self._running = False
        self._task: Optional[asyncio.Task] = None

        print(f"🔗 WheelerMeshProtocol initialized: node={local_node.node_id}")

    def register_node(self, node: WheelerMeshNode) -> bool:
        """Registra novo nó na mesh conhecida."""
        if node.node_id in self.known_nodes:
            return False
        self.known_nodes[node.node_id] = node

        # Atualizar vizinhança baseada em proximidade geodésica
        for other_id, other_node in self.known_nodes.items():
            if other_id == node.node_id:
                continue
            dist = node.geodesic_distance_to(other_node, self.base_metric)
            # Conectar se dentro do mercy gap estendido
            if 0.04 <= dist <= 0.30:  # Mercy gap × 3 para conectividade
                if other_id not in node.connected_neighbors:
                    node.connected_neighbors.append(other_id)
                if node.node_id not in other_node.connected_neighbors:
                    other_node.connected_neighbors.append(node.node_id)

        print(f"  ✓ Node registered: {node.node_id} ({len(node.connected_neighbors)} neighbors)")
        return True

    def _compute_geodesic_route(
        self,
        source_id: str,
        dest_id: str,
        max_hops: Optional[int] = None
    ) -> Optional[List[str]]:
        """Computa rota geodésica ótima entre dois nós."""
        if source_id == dest_id:
            return [source_id]

        cache_key = (source_id, dest_id)
        if cache_key in self.route_cache:
            return self.route_cache[cache_key]

        max_hops = max_hops or self.max_hops

        if not self.enable_topological_routing:
            # Fallback: roteamento por menor número de hops
            return self._bfs_route(source_id, dest_id, max_hops)

        # Roteamento topológico: minimizar distância geodésica acumulada
        source = self.known_nodes.get(source_id)
        dest = self.known_nodes.get(dest_id)
        if not source or not dest:
            return None

        # A* com heurística geodésica
        import heapq

        # Priority queue: (estimated_total_cost, current_cost, node_id, path)
        pq = [(0.0, 0.0, source_id, [source_id])]
        visited = set()

        while pq:
            est_total, current_cost, current_id, path = heapq.heappop(pq)

            if current_id == dest_id:
                # Cache e retornar rota
                self.route_cache[cache_key] = path
                self.route_cache[(dest_id, source_id)] = path[::-1]  # Bidirecional
                return path

            if current_id in visited or len(path) > max_hops:
                continue
            visited.add(current_id)

            current_node = self.known_nodes[current_id]
            for neighbor_id in current_node.connected_neighbors:
                if neighbor_id in visited:
                    continue
                neighbor = self.known_nodes[neighbor_id]

                # Custo: distância geodésica real + heurística para destino
                edge_cost = current_node.geodesic_distance_to(neighbor, self.base_metric)
                heuristic = neighbor.geodesic_distance_to(dest, self.base_metric)
                new_cost = current_cost + edge_cost
                estimated = new_cost + heuristic

                heapq.heappush(pq, (estimated, new_cost, neighbor_id, path + [neighbor_id]))

        # Sem rota encontrada dentro dos limites
        return None

    def _bfs_route(
        self,
        source_id: str,
        dest_id: str,
        max_hops: int
    ) -> Optional[List[str]]:
        """Roteamento BFS simples como fallback."""
        from collections import deque

        queue = deque([(source_id, [source_id])])
        visited = {source_id}

        while queue:
            current_id, path = queue.popleft()

            if current_id == dest_id:
                return path

            if len(path) >= max_hops:
                continue

            current_node = self.known_nodes.get(current_id)
            if not current_node:
                continue

            for neighbor_id in current_node.connected_neighbors:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return None

    async def send_quantum_state(
        self,
        packet: QuantumStatePacket,
        priority: str = 'normal'  # 'high', 'normal', 'low'
    ) -> Dict[str, Any]:
        """
        Envia estado quântico via protocolo qhttp://.

        Returns:
            Dict com status da transmissão
        """
        if not self.local_node._online:
            return {'success': False, 'error': 'Node offline'}

        # Validar pacote
        if packet.source_node_id != self.local_node.node_id:
            return {'success': False, 'error': 'Source mismatch'}

        # Computar rota
        route = packet.route_geodesic or self._compute_geodesic_route(
            packet.source_node_id,
            packet.destination_node_id
        )

        if not route:
            return {'success': False, 'error': 'No viable route found'}

        # Atualizar métricas
        self.transmission_metrics['packets_sent'] += 1
        self.transmission_metrics['geodesic_hops_avg'] = (
            (self.transmission_metrics['geodesic_hops_avg'] *
             (self.transmission_metrics['packets_sent'] - 1) + len(route)) /
            self.transmission_metrics['packets_sent']
        )

        # Simular transmissão (em produção: via canal quântico real)
        # Aqui: simular degradação baseada em distância e carga topológica
        total_distance = sum(
            self.known_nodes[route[i]].geodesic_distance_to(
                self.known_nodes[route[i+1]], self.base_metric
            )
            for i in range(len(route) - 1)
        )

        # Fidelidade decai com distância e é protegida por carga topológica
        base_fidelity = np.exp(-total_distance / 2.0)
        topological_protection = 1.0 - 0.1 * abs(packet.topological_charge)
        simulated_fidelity = base_fidelity * topological_protection + np.random.normal(0, 0.01)
        simulated_fidelity = np.clip(simulated_fidelity, 0.0, 1.0)

        # Verificar threshold de fidelidade
        if simulated_fidelity < packet.fidelity_threshold:
            self.transmission_metrics['topological_errors'] += 1
            return {
                'success': False,
                'error': 'Fidelity below threshold',
                'simulated_fidelity': simulated_fidelity,
                'required_fidelity': packet.fidelity_threshold
            }

        # Enfileirar para "transmissão" (simulação assíncrona)
        await self.outbound_queue.put({
            'packet': packet,
            'route': route,
            'simulated_fidelity': simulated_fidelity,
            'priority': priority,
            'timestamp': time.time()
        })

        return {
            'success': True,
            'packet_id': packet.packet_id,
            'route': route,
            'hops': len(route),
            'simulated_fidelity': simulated_fidelity,
            'estimated_latency_ms': total_distance * 1.5  # ms por unidade geodésica
        }

    async def receive_quantum_state(
        self,
        packet: QuantumStatePacket,
        received_hash: str,
        via_node: str
    ) -> Dict[str, Any]:
        """
        Recebe estado quântico de outro nó via qhttp://.
        """
        # Verificar integridade
        if not packet.verify_integrity(received_hash):
            self.transmission_metrics['topological_errors'] += 1
            return {'success': False, 'error': 'Integrity check failed'}

        # Verificar destino
        if packet.destination_node_id != self.local_node.node_id:
            # Encaminhar se for nó de retransmissão
            if self.local_node.node_type == WheelerNodeType.RELAY_NODE:
                return await self._forward_packet(packet, received_hash, via_node)
            return {'success': False, 'error': 'Destination mismatch'}

        # Verificar fidelidade simulada (em produção: tomografia quântica)
        # Aqui: assumir fidelidade baseada em distância do último hop
        last_hop_node = self.known_nodes.get(via_node)
        if last_hop_node:
            distance = self.local_node.geodesic_distance_to(last_hop_node, self.base_metric)
            expected_fidelity = np.exp(-distance / 2.0)
        else:
            expected_fidelity = 0.95

        if expected_fidelity < packet.fidelity_threshold:
            return {
                'success': False,
                'error': 'Expected fidelity below threshold',
                'expected_fidelity': expected_fidelity
            }

        # Aceitar pacote
        self.transmission_metrics['packets_received'] += 1
        self.transmission_metrics['avg_fidelity'] = (
            (self.transmission_metrics['avg_fidelity'] *
             (self.transmission_metrics['packets_received'] - 1) + expected_fidelity) /
            self.transmission_metrics['packets_received']
        )

        # Enfileirar para processamento local
        await self.inbound_queue.put({
            'packet': packet,
            'received_via': via_node,
            'expected_fidelity': expected_fidelity,
            'timestamp': time.time()
        })

        # Notificar callbacks
        for callback in self.event_callbacks:
            try:
                callback({
                    'type': 'quantum_state_received',
                    'packet_id': packet.packet_id,
                    'source': packet.source_node_id,
                    'fidelity': expected_fidelity,
                    'topological_charge': packet.topological_charge
                })
            except Exception as e:
                print(f"⚠️ Event callback error: {e}")

        return {
            'success': True,
            'packet_id': packet.packet_id,
            'accepted_fidelity': expected_fidelity,
            'topological_charge_verified': packet.topological_charge
        }

    async def _forward_packet(
        self,
        packet: QuantumStatePacket,
        received_hash: str,
        via_node: str
    ) -> Dict[str, Any]:
        """Encaminha pacote recebido para próximo hop na rota."""
        # Determinar próximo hop baseado na rota original ou computar nova
        next_hop = None
        if packet.route_geodesic and packet.destination_node_id in packet.route_geodesic:
            idx = packet.route_geodesic.index(self.local_node.node_id)
            if idx < len(packet.route_geodesic) - 1:
                next_hop = packet.route_geodesic[idx + 1]

        if not next_hop:
            # Computar rota alternativa
            route = self._compute_geodesic_route(
                self.local_node.node_id,
                packet.destination_node_id
            )
            if route and len(route) > 1:
                next_hop = route[1]

        if not next_hop or next_hop == via_node:
            return {'success': False, 'error': 'No forward path available'}

        # Re-encaminhar (simulação)
        # Em produção: retransmitir via canal quântico com possível correção de erro
        print(f"  ↻ Forwarding packet {packet.packet_id[:12]} → {next_hop}")

        return {
            'success': True,
            'forwarded_to': next_hop,
            'packet_id': packet.packet_id
        }

    def register_event_callback(self, callback: Callable[[Dict], None]):
        """Registra callback para eventos de transmissão."""
        self.event_callbacks.append(callback)

    async def start(self):
        """Inicia loop de processamento do protocolo."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._protocol_loop())
        print(f"🚀 qhttp:// protocol started for node {self.local_node.node_id}")

    async def stop(self):
        """Para o protocolo gracefully."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print(f"⏹️ qhttp:// protocol stopped for node {self.local_node.node_id}")

    async def _protocol_loop(self):
        """Loop principal do protocolo qhttp://."""
        while self._running:
            try:
                # Processar fila de saída (prioridade: high > normal > low)
                if not self.outbound_queue.empty():
                    item = await self.outbound_queue.get()
                    # Simular "transmissão" com delay baseado em prioridade
                    delay = {'high': 0.01, 'normal': 0.05, 'low': 0.2}.get(item['priority'], 0.05)
                    await asyncio.sleep(delay)
                    # Em produção: enviar via hardware quântico real
                    self.outbound_queue.task_done()

                # Processar fila de entrada
                if not self.inbound_queue.empty():
                    item = await self.inbound_queue.get()
                    # Processar estado quântico recebido (integrar com Neural Lace)
                    # Aqui: apenas registrar para demonstração
                    self.inbound_queue.task_done()

                # Manter heartbeat da conexão
                await asyncio.sleep(0.01)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Protocol loop error: {e}")
                await asyncio.sleep(0.1)

    def get_protocol_status(self) -> Dict[str, Any]:
        """Retorna status do protocolo qhttp://."""
        return {
            'node_id': self.local_node.node_id,
            'node_type': self.local_node.node_type.name,
            'online': self.local_node._online,
            'known_nodes': len(self.known_nodes),
            'outbound_queue_size': self.outbound_queue.qsize(),
            'inbound_queue_size': self.inbound_queue.qsize(),
            'metrics': self.transmission_metrics,
            'route_cache_size': len(self.route_cache),
            'running': self._running
        }
