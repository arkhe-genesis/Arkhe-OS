#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arkhe_phase_routing.py
Roteamento distribuído por gradiente de fase para Arkhe v3.0-Ω.

Algoritmo: Descida greedy em ∇θ com perturbação térmica para escape
de mínimos locais. Memory O(1) por nó.

Protocolo: Mensagens carregam target_phase (θ_dest) e self_cross_id
(para suporte a retrocausalidade fraca).
"""

import numpy as np
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
from datetime import datetime, timezone, timezone
from collections import deque
import logging

# ============================================================================
# Configuração e Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constantes de Roteamento
PHASE_TOLERANCE = 0.05  # ~2.86 graus (converged)
MIN_TEMPERATURE = 0.01  # Perturbação mínima
MAX_TEMPERATURE = 1.0  # Perturbação máxima
TEMPERATURE_DECAY = 0.95  # Cooling schedule (simulated annealing)

# Constantes Quânticas
FREQUENCY_HZ = 40.0  # Frequência de oscilação (40 Hz)
PERIOD_SECONDS = 1.0 / FREQUENCY_HZ  # 0.025s
RETROCAUSALITY_WINDOW_MS = 25  # Janela de pre-ACK

# ============================================================================
# Enums e Data Classes
# ============================================================================

class PacketState(Enum):
    """Estado de um pacote em trânsito."""
    FORWARD = "forward"  # Viajando no tempo, para frente
    PRE_ACK = "pre_ack"  # Pré-autorizado pelo destino (retrocausal)
    DELIVERED = "delivered"
    DROPPED = "dropped"

class RoutingMode(Enum):
    """Modo de roteamento usado pelo nó."""
    GREEDY = "greedy"  # Descida pura (min phase_diff)
    THERMAL = "thermal"  # Com perturbação térmica (para escape)
    BACKTRACK = "backtrack"  # Subindo gradiente temporal (retrocausal)

@dataclass
class PhasePacket:
    """Pacote de dados com roteamento por fase."""
    packet_id: str
    source_id: int
    dest_id: int
    target_phase: float  # θ_dest (radianos)
    self_cross_id: str  # "PRE_ACK" ou "FORWARD"
    payload: Dict = field(default_factory=dict)
    
    # Metadados de roteamento
    current_node: int = -1
    hop_count: int = 0
    state: PacketState = PacketState.FORWARD
    path_trace: List[int] = field(default_factory=list)
    created_at_ns: int = 0
    delivered_at_ns: int = 0
    latency_ms: float = 0.0
    
    # Telemetria
    mode_history: List[RoutingMode] = field(default_factory=list)
    phase_diff_history: List[float] = field(default_factory=list)

@dataclass
class PhaseNodeState:
    """Estado de fase de um nó no sistema."""
    node_id: int
    current_phase: float  # θ_i(t) em radianos [0, 2π)
    frequency: float  # ω_i em Hz
    amplitude: float  # A_i (amplitude de oscilação)
    
    # Vizinhos e conectividade
    neighbors: Set[int] = field(default_factory=set)
    neighbor_phases: Dict[int, float] = field(default_factory=dict)
    
    # Telemetria
    packets_routed: int = 0
    packets_dropped: int = 0
    local_mean_phase: float = 0.0
    phase_sync_quality: float = 0.0  # [0, 1] quanto maior, mais sincronizado
    
    # Temperatura (para simulated annealing)
    routing_temperature: float = 0.5

# ============================================================================
# Phaseador (Sincronizador de Fase) - Core da Física
# ============================================================================

class KuramotoOscillator:
    """
    Simula um oscilador de Kuramoto individual.
    dθ/dt = ω_i + (K/N) * Σ sin(θ_j - θ_i)
    """
    
    def __init__(self, node_id: int, frequency: float, coupling: float = 1.0):
        self.node_id = node_id
        self.frequency = frequency  # ω_i natural
        self.coupling = coupling  # K (força de acoplamento)
        
        # Estado: fase aleatória inicial
        self.phase = np.random.uniform(0, 2 * np.pi)
        self.amplitude = 1.0
        
        # Histórico (para análise)
        self.phase_history = [self.phase]
    
    def step(self, neighbor_phases: Dict[int, float], dt: float = 0.001):
        """
        Avança estado por dt (timestep).
        neighbor_phases: {neighbor_id: phase_value}
        """
        if not neighbor_phases:
            # Sem acoplamento, apenas evolução livre
            self.phase += self.frequency * dt * 2 * np.pi
        else:
            # Kuramoto coupling
            coupling_term = 0.0
            for neighbor_phase in neighbor_phases.values():
                coupling_term += np.sin(neighbor_phase - self.phase)
            
            dtheta_dt = self.frequency + (self.coupling / len(neighbor_phases)) * coupling_term
            self.phase += dtheta_dt * dt * 2 * np.pi
        
        # Normalizar para [0, 2π)
        self.phase = self.phase % (2 * np.pi)
        self.phase_history.append(self.phase)
    
    def get_phase(self) -> float:
        """Retorna fase atual."""
        return self.phase
    
    def get_phase_degrees(self) -> float:
        """Retorna fase em graus [0, 360)."""
        return (self.phase / (2 * np.pi)) * 360.0

# ============================================================================
# Roteador de Fase Distribuído
# ============================================================================

class DistributedPhaseRouter:
    """
    Roteador distribuído que funciona apenas com estado local.
    Mantém O(1) memória por nó.
    """
    
    def __init__(self, num_nodes: int, frequency_hz: float = 40.0):
        self.num_nodes = num_nodes
        self.frequency_hz = frequency_hz
        
        # Estados de osciladores
        self.oscillators: Dict[int, KuramotoOscillator] = {
            i: KuramotoOscillator(i, frequency_hz + np.random.normal(0, 0.05))
            for i in range(num_nodes)
        }
        
        # Estados de nó
        self.node_states: Dict[int, PhaseNodeState] = {
            i: PhaseNodeState(
                node_id=i,
                current_phase=self.oscillators[i].phase,
                frequency=self.oscillators[i].frequency,
                amplitude=self.oscillators[i].amplitude,
                neighbors=set()  # Será preenchido
            )
            for i in range(num_nodes)
        }
        
        # Fila de pacotes (para simulação)
        self.packet_queue: deque = deque()
        self.delivered_packets: List[PhasePacket] = []
        self.dropped_packets: List[PhasePacket] = []
        
        # Métrica global
        self.global_coherence = 0.0
        self.time_step_count = 0
        
        logger.info(f"DistributedPhaseRouter inicializado com {num_nodes} nós @ {frequency_hz}Hz")
    
    def set_neighbors(self, neighbors_dict: Dict[int, Set[int]]):
        """Define vizinhos para cada nó."""
        for node_id, neighbors in neighbors_dict.items():
            self.node_states[node_id].neighbors = neighbors.copy()
    
    def synchronize_physical_layer(self, dt: float = 0.001):
        """
        Avança a camada física (Kuramoto) um timestep.
        Cada nó integra suas ODEs locais.
        """
        # Coletar fases atuais
        phases = {i: self.oscillators[i].get_phase() for i in range(self.num_nodes)}
        
        # Atualizar cada oscilador
        for node_id in range(self.num_nodes):
            neighbors = self.node_states[node_id].neighbors
            neighbor_phases = {n: phases[n] for n in neighbors if n in phases}
            
            self.oscillators[node_id].step(neighbor_phases, dt)
            self.node_states[node_id].current_phase = self.oscillators[node_id].phase
            self.node_states[node_id].neighbor_phases = neighbor_phases.copy()
        
        # Atualizar coerência global
        phases_array = np.array([self.oscillators[i].phase for i in range(self.num_nodes)])
        self.global_coherence = float(np.abs(np.mean(np.exp(1j * phases_array))))
        
        self.time_step_count += 1
    
    def compute_phase_gradient(self, node_id: int, target_phase: float) -> Dict[int, float]:
        """
        Computa diferenças de fase em relação ao target para todos os vizinhos.
        Retorna {neighbor_id: abs_phase_diff}.
        """
        node = self.node_states[node_id]
        gradient = {}
        
        for neighbor_id in node.neighbors:
            neighbor_phase = self.node_states[neighbor_id].current_phase
            phase_diff = abs(neighbor_phase - target_phase)
            # Normalizar para [0, π] (menor distância em círculo)
            phase_diff = min(phase_diff, 2 * np.pi - phase_diff)
            gradient[neighbor_id] = phase_diff
        
        return gradient
    
    def route_packet_step(self, packet: PhasePacket) -> Optional[int]:
        """
        Processa um step do roteamento para um pacote.
        Retorna: next_node_id ou None se entregue/descartado.
        """
        node = self.node_states[packet.current_node]
        
        # Computar gradiente de fase
        gradient = self.compute_phase_gradient(packet.current_node, packet.target_phase)
        
        if not gradient:
            # Nó sem vizinhos (isolado)
            packet.state = PacketState.DROPPED
            logger.warning(f"Pacote {packet.packet_id} dropado (nó isolado {packet.current_node})")
            return None
        
        phase_diffs = list(gradient.values())
        min_phase_diff = min(phase_diffs)
        packet.phase_diff_history.append(min_phase_diff)
        
        # Teste de convergência
        if min_phase_diff < PHASE_TOLERANCE:
            # Chegou perto do target
            packet.state = PacketState.DELIVERED
            packet.hop_count += 1
            packet.path_trace.append(packet.current_node)
            packet.delivered_at_ns = int(datetime.now(timezone.utc).timestamp() * 1e9)
            packet.latency_ms = (packet.delivered_at_ns - packet.created_at_ns) / 1e6
            packet.mode_history.append(RoutingMode.GREEDY)
            logger.info(f"Pacote {packet.packet_id} entregue em {packet.hop_count} hops")
            return None
        
        # Escolher próximo nó
        # Com probabilidade decreasing por temperatura (simulated annealing)
        temp = node.routing_temperature
        
        if np.random.random() < (1.0 - temp):
            # Greedy: choose minimum
            next_node = min(gradient.keys(), key=lambda n: gradient[n])
            mode = RoutingMode.GREEDY
        else:
            # Thermal: escolha probabilística
            phase_diffs_array = np.array([gradient[n] for n in gradient.keys()])
            weights = np.exp(-phase_diffs_array / max(temp, MIN_TEMPERATURE))
            weights /= weights.sum()
            next_node = np.random.choice(list(gradient.keys()), p=weights)
            mode = RoutingMode.THERMAL
        
        packet.current_node = next_node
        packet.hop_count += 1
        packet.path_trace.append(next_node)
        packet.mode_history.append(mode)
        
        # Decay temperatura
        node.routing_temperature *= TEMPERATURE_DECAY
        node.routing_temperature = max(node.routing_temperature, MIN_TEMPERATURE)
        
        return next_node
    
    def route_packet_until_delivery(self, packet: PhasePacket, max_hops: int = 100) -> bool:
        """
        Roteia um pacote até entrega ou timeout.
        Retorna True se entregue, False caso contrário.
        """
        packet.created_at_ns = int(datetime.now(timezone.utc).timestamp() * 1e9)
        packet.path_trace = [packet.current_node]
        
        while packet.hop_count < max_hops and packet.state == PacketState.FORWARD:
            # Sincronizar camada física primeiro
            self.synchronize_physical_layer(dt=0.001)
            
            # Rotear um step
            next_node = self.route_packet_step(packet)
            if next_node is None:
                break
        
        if packet.state != PacketState.DELIVERED:
            packet.state = PacketState.DROPPED
            logger.warning(f"Pacote {packet.packet_id} dropped após {packet.hop_count} hops")
            return False
        
        return True
    
    def submit_packet(self, packet: PhasePacket):
        """Submete um pacote para roteamento."""
        self.packet_queue.append(packet)
    
    def process_queue(self, max_packets_per_cycle: int = 5):
        """Processa pacotes pendentes."""
        processed = 0
        while self.packet_queue and processed < max_packets_per_cycle:
            packet = self.packet_queue.popleft()
            self.route_packet_until_delivery(packet)
            
            if packet.state == PacketState.DELIVERED:
                self.delivered_packets.append(packet)
            else:
                self.dropped_packets.append(packet)
            
            processed += 1
    
    def get_network_state(self) -> Dict:
        """Retorna estado completo da rede."""
        return {
            "time_step": self.time_step_count,
            "global_coherence": float(self.global_coherence),
            "nodes_sample": {
                i: {
                    "phase_deg": self.oscillators[i].get_phase_degrees(),
                    "frequency": self.oscillators[i].frequency,
                    "packets_routed": self.node_states[i].packets_routed,
                }
                for i in range(min(3, self.num_nodes))  # Amostra
            },
            "delivery_success_rate": len(self.delivered_packets) / (len(self.delivered_packets) + len(self.dropped_packets) + 1e-9),
            "avg_hops": np.mean([p.hop_count for p in self.delivered_packets]) if self.delivered_packets else 0.0,
            "avg_latency_ms": np.mean([p.latency_ms for p in self.delivered_packets]) if self.delivered_packets else 0.0,
        }


# ============================================================================
# Teste e Demonstração
# ============================================================================

if __name__ == "__main__":
    print("\n=== Teste: Roteamento por Gradiente de Fase ===\n")
    
    # Criar roteador com 13 nós
    router = DistributedPhaseRouter(num_nodes=13, frequency_hz=40.0)
    
    # Definir topologia (simples: anel)
    neighbors = {i: {(i-1) % 13, (i+1) % 13, (i+7) % 13} for i in range(13)}
    router.set_neighbors(neighbors)
    
    # Submeter alguns pacotes
    for i in range(5):
        packet = PhasePacket(
            packet_id=f"pkt_{i}",
            source_id=0,
            dest_id=(i + 1) % 13,
            target_phase=router.oscillators[(i + 1) % 13].phase + 0.1,  # Fase próxima ao destino
            self_cross_id="FORWARD",
            current_node=0,
        )
        router.submit_packet(packet)
    
    # Rotear pacotes
    for step in range(100):
        router.process_queue(max_packets_per_cycle=2)
        if step % 20 == 0:
            state = router.get_network_state()
            print(f"[Step {step}] Global Coherence: {state['global_coherence']:.4f}")
    
    # Estatísticas finais
    print("\n=== Estatísticas Finais ===")
    final_state = router.get_network_state()
    print(json.dumps(final_state, indent=2))
    
    print(f"\nPacotes entregues: {len(router.delivered_packets)}")
    print(f"Pacotes dropados: {len(router.dropped_packets)}")
    
    if router.delivered_packets:
        print(f"\nExemplo de pacote entregue:")
        p = router.delivered_packets[0]
        print(f"  ID: {p.packet_id}")
        print(f"  Hops: {p.hop_count}")
        print(f"  Latência: {p.latency_ms:.2f} ms")
        print(f"  Caminho: {p.path_trace}")
