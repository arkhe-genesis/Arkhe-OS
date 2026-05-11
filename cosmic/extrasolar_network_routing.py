#!/usr/bin/env python3
"""
extrasolar_network_routing.py — Rede de 10+ sistemas exoplanetários com roteamento via vórtice galáctico.
"""

import numpy as np
import torch
import heapq
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import hashlib

# Importar componentes existentes
from cosmic.extrasolar_expansion import ExtrasolarZone, ExtrasolarGalacticVortex, ExtrasolarVortexConfig

@dataclass
class CosmicNode:
    """Nó na rede cósmica (zona exoplanetária)."""
    zone: ExtrasolarZone
    name: str
    distance_from_earth_ly: float
    galactic_longitude_deg: float
    galactic_latitude_deg: float
    stellar_type: str
    habitable_zone: bool
    mission_criticality: float  # 0.0 a 1.0
    resource_capacity: Dict[str, float]  # energia, compute, bandwidth
    online: bool = True

    def to_dict(self) -> Dict:
        return {
            'zone': self.zone.name,
            'name': self.name,
            'distance_ly': self.distance_from_earth_ly,
            'galactic_coords': (self.galactic_longitude_deg, self.galactic_latitude_deg),
            'stellar_type': self.stellar_type,
            'habitable': self.habitable_zone,
            'criticality': self.mission_criticality,
            'resources': self.resource_capacity,
            'online': self.online
        }

class CosmicNetworkRouter:
    """
    Roteador para rede cósmica de zonas exoplanetárias.

    Usa Dijkstra geométrico com heurística de curvatura galáctica
    para encontrar caminhos ótimos entre zonas via vórtice galáctico.
    """

    def __init__(
        self,
        galactic_vortex: ExtrasolarGalacticVortex,
        coherence_length_ly: float = 1000.0,
        latency_per_ly_ms: float = 1.0  # simplificação: 1ms por ano-luz
    ):
        self.galactic_vortex = galactic_vortex
        self.L_coh = coherence_length_ly
        self.latency_per_ly = latency_per_ly_ms

        # Catálogo de nós (Terra + 10 sistemas exoplanetários)
        self.nodes: Dict[str, CosmicNode] = {}
        self._initialize_catalog()

        # Grafo de adjacência (pre-computado)
        self.adjacency: Dict[str, List[Tuple[str, float]]] = {}
        self._build_graph()

        # Cache de rotas para performance
        self.route_cache: Dict[Tuple[str, str], List[str]] = {}

    def _initialize_catalog(self):
        """Inicializa catálogo de nós cósmicos."""
        # Terra (hub central)
        self.nodes['EARTH'] = CosmicNode(
            zone=ExtrasolarZone.EARTH_ORBIT if hasattr(ExtrasolarZone, 'EARTH_ORBIT') else ExtrasolarZone.PROXIMA_B,
            name='Earth Orbit',
            distance_from_earth_ly=0.0,
            galactic_longitude_deg=0.0,
            galactic_latitude_deg=0.0,
            stellar_type='G2V',
            habitable_zone=True,
            mission_criticality=1.0,
            resource_capacity={'energy': 1000.0, 'compute': 500.0, 'bandwidth': 100.0}
        )

        # 10 sistemas exoplanetários (expandido do v166)
        extrasolar_systems = [
            ('PROXIMA_B', 'Proxima Centauri b', 4.24, 312.6, -1.9, 'M5.5V', True, 0.95, {'energy': 50.0, 'compute': 20.0, 'bandwidth': 5.0}),
            ('TRAPPIST_1E', 'TRAPPIST-1e', 39.6, 295.2, -34.7, 'M8V', True, 0.9, {'energy': 40.0, 'compute': 15.0, 'bandwidth': 4.0}),
            ('KEPLER_452B', 'Kepler-452b', 1402.0, 78.4, 12.1, 'G2V', True, 0.7, {'energy': 30.0, 'compute': 10.0, 'bandwidth': 2.0}),
            ('LHS_1140B', 'LHS 1140b', 49.0, 45.3, -20.1, 'M4.5V', True, 0.85, {'energy': 45.0, 'compute': 18.0, 'bandwidth': 4.5}),
            ('TOI_715B', 'TOI-715b', 137.0, 112.8, 8.4, 'M4V', True, 0.8, {'energy': 35.0, 'compute': 12.0, 'bandwidth': 3.0}),
            ('ROSS_128B', 'Ross 128b', 11.0, 185.2, -15.3, 'M4V', True, 0.88, {'energy': 48.0, 'compute': 19.0, 'bandwidth': 4.8}),
            ('GLIESE_667Cc', 'Gliese 667Cc', 23.6, 332.1, -22.8, 'M1.5V', True, 0.82, {'energy': 42.0, 'compute': 16.0, 'bandwidth': 4.2}),
            ('HD_40307g', 'HD 40307g', 42.0, 245.7, -18.9, 'K2.5V', True, 0.75, {'energy': 38.0, 'compute': 14.0, 'bandwidth': 3.8}),
            ('TAU_CETI_e', 'Tau Ceti e', 11.9, 173.4, -34.2, 'G8V', True, 0.86, {'energy': 46.0, 'compute': 17.5, 'bandwidth': 4.6}),
            ('WOLF_1061c', 'Wolf 1061c', 13.8, 201.5, -12.7, 'M3V', True, 0.84, {'energy': 44.0, 'compute': 16.5, 'bandwidth': 4.4}),
            ('K2_18b', 'K2-18b', 124.0, 89.3, 5.2, 'M2.5V', True, 0.78, {'energy': 36.0, 'compute': 13.0, 'bandwidth': 3.6}),
        ]

        for node_id, name, dist, lon, lat, star_type, habitable, criticality, resources in extrasolar_systems:
            self.nodes[node_id] = CosmicNode(
                zone=getattr(ExtrasolarZone, node_id, ExtrasolarZone.PROXIMA_B),
                name=name,
                distance_from_earth_ly=dist,
                galactic_longitude_deg=lon,
                galactic_latitude_deg=lat,
                stellar_type=star_type,
                habitable_zone=habitable,
                mission_criticality=criticality,
                resource_capacity=resources
            )

        print(f"✅ Catálogo cósmico inicializado com {len(self.nodes)} nós")

    def _build_graph(self):
        """Constrói grafo de adjacência com pesos baseados em coerência e latência."""
        node_ids = list(self.nodes.keys())

        for source_id in node_ids:
            source = self.nodes[source_id]
            neighbors = []

            for target_id in node_ids:
                if source_id == target_id:
                    continue

                target = self.nodes[target_id]

                # Calcular distância entre nós (aproximação euclidiana em ly)
                dist_ly = abs(source.distance_from_earth_ly - target.distance_from_earth_ly)

                # Fator de coerência: decai exponencialmente com distância
                coherence_factor = np.exp(-dist_ly / self.L_coh)

                # Fator de alinhamento galáctico (melhor roteamento se próximos em coordenadas galácticas)
                d_lon = abs(source.galactic_longitude_deg - target.galactic_longitude_deg)
                d_lat = abs(source.galactic_latitude_deg - target.galactic_latitude_deg)
                alignment_factor = np.exp(-(d_lon**2 + d_lat**2) / (2 * 30**2))  # 30° como escala

                # Fator de criticidade combinada (priorizar links de alta criticidade)
                criticality_factor = (source.mission_criticality + target.mission_criticality) / 2

                # Peso da aresta: menor = melhor caminho
                # Combinar: 1/coerência + latência + penalidade por desalinhamento
                latency_ms = dist_ly * self.latency_per_ly
                weight = (1.0 / (coherence_factor + 1e-6)) + latency_ms * 0.01 + (1.0 - alignment_factor) * 10

                # Aplicar fator de criticidade (reduz peso para links críticos)
                weight *= (1.0 - criticality_factor * 0.3)

                neighbors.append((target_id, weight))

            self.adjacency[source_id] = neighbors

    def find_optimal_route(
        self,
        source: str,
        destination: str,
        resource_requirements: Optional[Dict[str, float]] = None,
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        Encontra rota ótima entre source e destination via Dijkstra geométrico.

        Args:
            source: ID do nó de origem
            destination: ID do nó de destino
            resource_requirements: recursos mínimos necessários em cada hop
            use_cache: usar cache de rotas se disponível

        Returns:
            Dict com rota, custo total, métricas, ou None se sem rota
        """
        if source not in self.nodes or destination not in self.nodes:
            return None

        # Verificar cache
        cache_key = (source, destination, tuple(sorted(resource_requirements.items())) if resource_requirements else None)
        if use_cache and cache_key in self.route_cache:
            return self._build_route_result(source, destination, self.route_cache[cache_key])

        # Dijkstra com heap
        heap = [(0.0, source, [source])]  # (custo, nó, caminho)
        visited = set()
        costs = {source: 0.0}

        while heap:
            cost, current, path = heapq.heappop(heap)

            if current == destination:
                # Rota encontrada: armazenar em cache
                if use_cache:
                    self.route_cache[cache_key] = path
                return self._build_route_result(source, destination, path, cost)

            if current in visited:
                continue
            visited.add(current)

            for neighbor, edge_weight in self.adjacency.get(current, []):
                if neighbor in visited:
                    continue

                # Verificar requisitos de recursos (se especificado)
                if resource_requirements:
                    neighbor_node = self.nodes[neighbor]
                    if not self._meets_resource_requirements(neighbor_node, resource_requirements):
                        continue

                new_cost = cost + edge_weight

                if neighbor not in costs or new_cost < costs[neighbor]:
                    costs[neighbor] = new_cost
                    heapq.heappush(heap, (new_cost, neighbor, path + [neighbor]))

        # Sem rota encontrada
        return None

    def _meets_resource_requirements(self, node: CosmicNode, requirements: Dict[str, float]) -> bool:
        """Verifica se nó atende requisitos de recursos."""
        for resource, required in requirements.items():
            if node.resource_capacity.get(resource, 0) < required:
                return False
        return True

    def _build_route_result(
        self,
        source: str,
        destination: str,
        path: List[str],
        total_cost: Optional[float] = None
    ) -> Dict:
        """Constrói resultado estruturado da rota."""
        # Calcular métricas da rota
        total_distance = sum(
            abs(self.nodes[path[i]].distance_from_earth_ly - self.nodes[path[i+1]].distance_from_earth_ly)
            for i in range(len(path) - 1)
        )
        total_latency = total_distance * self.latency_per_ly
        avg_coherence = np.mean([
            np.exp(-abs(self.nodes[path[i]].distance_from_earth_ly - self.nodes[path[i+1]].distance_from_earth_ly) / self.L_coh)
            for i in range(len(path) - 1)
        ])

        return {
            'source': source,
            'destination': destination,
            'path': path,
            'hops': len(path) - 1,
            'total_distance_ly': total_distance,
            'estimated_latency_ms': total_latency,
            'average_coherence': avg_coherence,
            'total_cost': total_cost,
            'nodes_details': [self.nodes[nid].to_dict() for nid in path],
            'timestamp': time.time()
        }

    def broadcast_to_network(
        self,
        source: str,
        message: Dict,
        target_zones: Optional[List[str]] = None,
        priority: str = 'normal'
    ) -> Dict:
        """
        Broadcast de mensagem para múltiplas zonas via roteamento ótimo.

        Args:
            source: nó de origem
            message: conteúdo da mensagem
            target_zones: lista de destinos (None = broadcast para todos)
            priority: 'high', 'normal', 'low' (afeta seleção de rota)

        Returns:
            Dict com status de entrega para cada destino
        """
        destinations = target_zones or [nid for nid in self.nodes if nid != source]
        results = {}

        for dest in destinations:
            # Ajustar requisitos baseado em prioridade
            resource_reqs = None
            if priority == 'high':
                resource_reqs = {'bandwidth': 10.0}  # exigir mais banda para alta prioridade

            route = self.find_optimal_route(source, dest, resource_requirements=resource_reqs)

            if route:
                # Simular envio da mensagem (em produção: via protocolo quântico)
                delivery_success = np.random.random() < route['average_coherence']
                results[dest] = {
                    'status': 'delivered' if delivery_success else 'failed',
                    'route': route['path'],
                    'hops': route['hops'],
                    'latency_ms': route['estimated_latency_ms'],
                    'coherence': route['average_coherence']
                }
            else:
                results[dest] = {
                    'status': 'no_route',
                    'reason': 'No viable path found'
                }

        return {
            'broadcast_id': hashlib.sha256(f"{source}_{time.time()}".encode()).hexdigest()[:12],
            'source': source,
            'total_destinations': len(destinations),
            'successful_deliveries': sum(1 for r in results.values() if r['status'] == 'delivered'),
            'results': results,
            'timestamp': time.time()
        }

    def get_network_health_report(self) -> Dict:
        """Gera relatório de saúde da rede cósmica."""
        online_nodes = [n for n in self.nodes.values() if n.online]
        avg_coherence = np.mean([
            np.exp(-abs(n1.distance_from_earth_ly - n2.distance_from_earth_ly) / self.L_coh)
            for i, n1 in enumerate(online_nodes)
            for n2 in online_nodes[i+1:]
        ]) if len(online_nodes) > 1 else 1.0

        return {
            'total_nodes': len(self.nodes),
            'online_nodes': len(online_nodes),
            'offline_nodes': len(self.nodes) - len(online_nodes),
            'average_coherence': avg_coherence,
            'high_criticality_nodes': sum(1 for n in self.nodes.values() if n.mission_criticality > 0.8),
            'habitable_zones': sum(1 for n in self.nodes.values() if n.habitable_zone),
            'cache_size': len(self.route_cache),
            'timestamp': time.time()
        }

    def update_node_status(self, node_id: str, online: bool, resource_update: Optional[Dict] = None):
        """Atualiza status de um nó (online/offline ou recursos)."""
        if node_id not in self.nodes:
            return False

        self.nodes[node_id].online = online
        if resource_update:
            self.nodes[node_id].resource_capacity.update(resource_update)

        # Invalidar cache de rotas que usam este nó
        self.route_cache = {
            k: v for k, v in self.route_cache.items()
            if node_id not in v
        }

        return True
