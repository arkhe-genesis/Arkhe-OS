#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arkhe_distributed_topology.py
Gerenciamento da topologia distribuída de grau 3 para o Sistema Arkhe v3.0-Ω.

Responsabilidades:
- Manter grau constante = 3 por nó
- Monitorar λ₂ local e trigger rewiring adaptativo
- Validar chirality field (χ = 0.618) para Klein bubbles
"""

import numpy as np
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Set, Tuple, Optional
from enum import Enum
from datetime import datetime, timezone, timezone
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

# Constantes
DEGREE_TARGET = 3
LAMBDA2_MIN_CRITICAL = 0.847  # Regime crítico Kuramoto
LAMBDA2_MAX_SUPERCRITICAL = 0.999  # Limite superior de coerência
LAMBDA2_THRESHOLD_ADD = 0.90  # Trigger para add edge
LAMBDA2_THRESHOLD_REMOVE = 0.999  # Trigger para remove edge
CHI_CHIRAL = 0.618  # Campo de quiralidade (Golden ratio)
KLEIN_BUBBLE_PERIOD = 13  # Período de inserção de aresta quiral

# ============================================================================
# Data Classes
# ============================================================================

class TopoState(Enum):
    """Estado da topologia de um nó."""
    STABLE = "stable"  # λ₂ dentro da faixa ótima
    SUBCRITICAL = "subcritical"  # λ₂ < 0.90, precisa adicionar edge
    SUPERCRITICAL = "supercritical"  # λ₂ > 0.999, pode remover edge
    REBALANCING = "rebalancing"  # Em processo de rewiring

@dataclass
class TopologyEdge:
    """Representa uma aresta na malha."""
    source_id: int
    target_id: int
    is_chiral: bool = False  # Se é aresta de quiralidade
    weight: float = 1.0
    created_at_ns: int = 0
    latency_ms: float = 0.0

@dataclass
class TopologyNode:
    """Estado de topologia de um nó individual."""
    node_id: int
    degree: int = 0
    neighbors: Set[int] = None
    local_lambda2: float = 0.0
    topo_state: TopoState = TopoState.STABLE
    laplacian_evals: List[complex] = None
    rewire_count: int = 0
    last_rewire_ns: int = 0
    
    def __post_init__(self):
        if self.neighbors is None:
            self.neighbors = set()
        if self.laplacian_evals is None:
            self.laplacian_evals = []

# ============================================================================
# Topologia Distribuída: Grau 3
# ============================================================================

class DistributedTopology:
    """
    Gerenciador de topologia de grau 3 para rede Arkhe.
    Implementa rewiring adaptativo baseado em λ₂ local.
    """
    
    def __init__(self, num_nodes: int):
        self.num_nodes = num_nodes
        self.nodes: Dict[int, TopologyNode] = {
            i: TopologyNode(node_id=i) for i in range(num_nodes)
        }
        self.edges: List[TopologyEdge] = []
        self.metrics = {
            "total_rewires": 0,
            "chiral_edges": 0,
            "edges_added": 0,
            "edges_removed": 0,
            "lambda2_global": 0.0,
            "avg_lambda2_local": 0.0,
            "coherence_state": "UNKNOWN"
        }
        self.history = []  # Para análise temporal
        
        logger.info(f"DistributedTopology inicializada com {num_nodes} nós")
    
    def initialize_cubic_grid(self):
        """
        Inicializa uma malha cúbica com grau 3.
        Para N=13, cria um anel com 3 vizinhos cada.
        """
        if self.num_nodes == 13:
            # Topologia de anel cúbico para 13 nós
            self._init_ring_cubic_13()
        elif self.num_nodes == 1024:
            # Supernós: topologia de toro cúbico
            self._init_toroidal_cubic_1024()
        else:
            # Genérica: vizinhança cíclica com 3 conexões
            self._init_generic_degree3(self.num_nodes)
    
    def _init_ring_cubic_13(self):
        """Inicializa topologia de anel cúbico para 13 nós (camada local)."""
        for i in range(13):
            neighbors = {
                (i - 1) % 13,  # Vizinho anterior
                (i + 1) % 13,  # Vizinho próximo
                (i + 7) % 13,  # Vizinho distante (7 = 13/2 - 1/2, cria pequeno mundo)
            }
            self.nodes[i].neighbors = neighbors
            self.nodes[i].degree = 3
    
    def _init_toroidal_cubic_1024(self):
        """Inicializa topologia de toro cúbico para 1024 nós (supernós)."""
        # Assumindo grid 32x32 em 2D (será 3D em implementação futura)
        side = int(np.sqrt(1024))
        for i in range(1024):
            x, y = i % side, i // side
            neighbors = {
                ((x - 1) % side) * side + y,  # Esquerda
                ((x + 1) % side) * side + y,  # Direita
                x * side + ((y + 1) % side),  # Cima
                x * side + ((y - 1) % side),  # Baixo
            }
            # Reduzir para grau 3 (remover um)
            neighbors = set(list(neighbors)[:3])
            self.nodes[i].neighbors = neighbors
            self.nodes[i].degree = 3
    
    def _init_generic_degree3(self, n: int):
        """Inicializa topologia genérica de grau 3 para N nós."""
        for i in range(n):
            neighbors = {
                (i - 1) % n,
                (i + 1) % n,
                (i + n // 2) % n,  # Aresta longa (small-world)
            }
            self.nodes[i].neighbors = neighbors
            self.nodes[i].degree = 3
    
    def compute_local_laplacian(self, node_id: int) -> np.ndarray:
        """
        Computa a matriz Laplaciana local em torno de um nó.
        Apenas entre o nó e seus vizinhos.
        """
        node = self.nodes[node_id]
        neighbor_ids = sorted(list(node.neighbors))
        n_local = len(neighbor_ids) + 1  # Nó + vizinhos
        
        # Mapear IDs globais para índices locais
        global_to_local = {neighbor_ids[i]: i + 1 for i in range(len(neighbor_ids))}
        global_to_local[node_id] = 0
        
        # Construir Laplaciana local
        L = np.zeros((n_local, n_local))
        
        # Diagonal: grau
        for i, nid in enumerate([node_id] + neighbor_ids):
            degree = len(self.nodes[nid].neighbors)
            L[i, i] = degree
        
        # Fora-diagonal: -1 para cada aresta
        for i, nid in enumerate([node_id] + neighbor_ids):
            for neighbor in self.nodes[nid].neighbors:
                if neighbor in global_to_local:
                    j = global_to_local[neighbor]
                    L[i, j] -= 1
        
        return L
    
    def compute_local_lambda2(self, node_id: int) -> float:
        """
        Computa o segundo maior autovalor da Laplaciana local (λ₂).
        Este é o "spectral gap local" usado para monitorar coerência.
        """
        L = self.compute_local_laplacian(node_id)
        
        try:
            evals = np.linalg.eigvalsh(L)
            evals_sorted = np.sort(evals)[::-1]  # Ordem decrescente
            
            # λ₂ é o segundo maior (note: λ₁ = 0 sempre para Laplaciana)
            if len(evals_sorted) > 1:
                lambda2 = float(evals_sorted[1])
            else:
                lambda2 = 0.0
            
            # Store para posterior
            self.nodes[node_id].laplacian_evals = evals_sorted
            self.nodes[node_id].local_lambda2 = lambda2
            
            return lambda2
        except np.linalg.LinAlgError as e:
            logger.warning(f"Erro ao computar λ₂ para nó {node_id}: {e}")
            return 0.0
    
    def update_topo_state(self, node_id: int):
        """Atualiza estado de topologia baseado em λ₂ local."""
        lambda2 = self.compute_local_lambda2(node_id)
        
        if lambda2 < LAMBDA2_THRESHOLD_ADD:
            self.nodes[node_id].topo_state = TopoState.SUBCRITICAL
        elif lambda2 > LAMBDA2_THRESHOLD_REMOVE:
            self.nodes[node_id].topo_state = TopoState.SUPERCRITICAL
        else:
            self.nodes[node_id].topo_state = TopoState.STABLE
    
    def add_edge_adaptive(self, node_id: int) -> bool:
        """
        Adiciona aresta temporária se λ₂ < 0.90.
        Escolhe vizinho com mínima redundância (menor grau local).
        """
        node = self.nodes[node_id]
        
        if len(node.neighbors) >= DEGREE_TARGET:
            # Já no limite de grau 3
            return False
        
        # Encontrar candidato com menor grau
        candidates = [i for i in range(self.num_nodes) if i not in node.neighbors]
        if not candidates:
            return False
        
        min_degree_candidate = min(candidates, key=lambda c: self.nodes[c].degree)
        
        # Adicionar aresta
        node.neighbors.add(min_degree_candidate)
        self.nodes[min_degree_candidate].neighbors.add(node_id)
        node.degree = len(node.neighbors)
        self.nodes[min_degree_candidate].degree = len(self.nodes[min_degree_candidate].neighbors)
        
        # Log
        self.metrics["edges_added"] += 1
        self.metrics["total_rewires"] += 1
        self.nodes[node_id].rewire_count += 1
        self.nodes[node_id].last_rewire_ns = int(datetime.now(timezone.utc).timestamp() * 1e9)
        
        logger.info(f"Aresta adicionada: {node_id} → {min_degree_candidate} (λ₂ subcrítico)")
        return True
    
    def remove_edge_adaptive(self, node_id: int) -> bool:
        """
        Remove aresta redundante se λ₂ > 0.999 (economia energética).
        """
        node = self.nodes[node_id]
        
        if len(node.neighbors) <= DEGREE_TARGET:
            return False
        
        # Encontrar aresta com menor "importância" (menor impacto em λ₂)
        # Heurística: remover aresta para vizinho com maior grau
        max_degree_neighbor = max(node.neighbors, key=lambda n: self.nodes[n].degree)
        
        # Remover
        node.neighbors.discard(max_degree_neighbor)
        self.nodes[max_degree_neighbor].neighbors.discard(node_id)
        node.degree = len(node.neighbors)
        self.nodes[max_degree_neighbor].degree = len(self.nodes[max_degree_neighbor].neighbors)
        
        self.metrics["edges_removed"] += 1
        self.metrics["total_rewires"] += 1
        self.nodes[node_id].rewire_count += 1
        
        logger.info(f"Aresta removida: {node_id} → {max_degree_neighbor} (λ₂ supercrítico)")
        return True
    
    def insert_chiral_edge(self, node_id: int):
        """
        Insere aresta quiral a cada KLEIN_BUBBLE_PERIOD nós.
        Cria propriedade não-orientável (Klein bottle) local.
        """
        if node_id % KLEIN_BUBBLE_PERIOD == 0:
            # Calcular nó "quiral" (deslocado de forma não-trivial)
            chiral_target = (node_id + 7 + int(CHI_CHIRAL * 100)) % self.num_nodes
            
            self.nodes[node_id].neighbors.add(chiral_target)
            self.nodes[chiral_target].neighbors.add(node_id)
            
            self.metrics["chiral_edges"] += 1
            logger.debug(f"Aresta quiral inserida: {node_id} → {chiral_target}")
    
    def compute_global_lambda2(self) -> float:
        """
        Computa λ₂ global da matriz Laplaciana da rede toda.
        Métrica cara, usar apenas em snapshots.
        """
        # Construir Laplaciana global
        L = np.zeros((self.num_nodes, self.num_nodes))
        
        for i in range(self.num_nodes):
            deg = len(self.nodes[i].neighbors)
            L[i, i] = deg
            for j in self.nodes[i].neighbors:
                L[i, j] -= 1
        
        try:
            evals = np.linalg.eigvalsh(L)
            evals_sorted = np.sort(evals)[::-1]
            lambda2 = float(evals_sorted[1]) if len(evals_sorted) > 1 else 0.0
            self.metrics["lambda2_global"] = lambda2
            return lambda2
        except np.linalg.LinAlgError as e:
            logger.error(f"Erro ao computar λ₂ global: {e}")
            return 0.0
    
    def rebalance_topology(self):
        """
        Ciclo de rebalanceamento: atualiza estados e ativa rewiring adaptativo.
        Executar periodicamente (ex: a cada 1 segundo).
        """
        logger.debug("=== Ciclo de Rebalanceamento ===")
        
        for nid in range(self.num_nodes):
            # 1. Atualizar estado
            self.update_topo_state(nid)
            
            # 2. Executar ações baseadas em estado
            if self.nodes[nid].topo_state == TopoState.SUBCRITICAL:
                self.add_edge_adaptive(nid)
            elif self.nodes[nid].topo_state == TopoState.SUPERCRITICAL:
                self.remove_edge_adaptive(nid)
            
            # 3. Inserir arestas quirais periodicamente
            self.insert_chiral_edge(nid)
        
        # 4. Computar λ₂ global para telemetria
        global_lambda2 = self.compute_global_lambda2()
        avg_local = np.mean([self.nodes[i].local_lambda2 for i in range(self.num_nodes)])
        
        self.metrics["avg_lambda2_local"] = avg_local
        
        # Determinar estado de coerência global
        if global_lambda2 > 0.995:
            self.metrics["coherence_state"] = "HYPER_COHERENT"
        elif global_lambda2 > 0.95:
            self.metrics["coherence_state"] = "COHERENT"
        elif global_lambda2 > LAMBDA2_MIN_CRITICAL:
            self.metrics["coherence_state"] = "CRITICAL"
        else:
            self.metrics["coherence_state"] = "DECOHERENT"
        
        # Log de telemetria
        logger.info(f"λ₂_global={global_lambda2:.6f} | λ₂_avg={avg_local:.6f} | "
                    f"Estado={self.metrics['coherence_state']} | "
                    f"Rewires={self.metrics['total_rewires']}")
        
        return global_lambda2
    
    def get_telemetry(self) -> Dict:
        """Retorna métricas de telemetria para monitoramento."""
        node_states = []
        for i in range(min(5, self.num_nodes)):
            node = self.nodes[i]
            state = {
                "node_id": node.node_id,
                "degree": node.degree,
                "neighbors": list(node.neighbors),
                "local_lambda2": float(node.local_lambda2),
                "topo_state": node.topo_state.value,
                "rewire_count": node.rewire_count
            }
            node_states.append(state)
        
        return {
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "num_nodes": self.num_nodes,
            "metrics": self.metrics.copy(),
            "node_states": node_states,
            "degree_distribution": [len(self.nodes[i].neighbors) for i in range(self.num_nodes)],
        }
    
    def export_config(self) -> str:
        """Exporte configuração de topologia em JSON."""
        config = {
            "topology": {
                "degree": DEGREE_TARGET,
                "type": "dynamic_cubic",
                "chirality_field": CHI_CHIRAL,
                "klein_bubble_period": KLEIN_BUBBLE_PERIOD,
                "nodes": self.num_nodes
            },
            "metrics": self.metrics.copy(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return json.dumps(config, indent=2)


# ============================================================================
# Teste e Demonstração
# ============================================================================

if __name__ == "__main__":
    # Teste com 13 nós (Fase 1: Anél de Coerência Local)
    print("\n=== Teste: Topologia de 13 Nós (Coerência Local) ===\n")
    
    topo = DistributedTopology(13)
    topo.initialize_cubic_grid()
    
    # Simular 5 ciclos de rebalanceamento
    for cycle in range(5):
        print(f"\n[Ciclo {cycle+1}]")
        lambda2 = topo.rebalance_topology()
        
    # Exportar telemetria final
    print("\n=== Telemetria Final ===")
    print(json.dumps(topo.get_telemetry(), indent=2))
    
    # Exportar configuração
    print("\n=== Configuração Exportada ===")
    print(topo.export_config())
