#!/usr/bin/env python3
"""
Sophon Network Simulator (v∞.406.1)
Simulates network performance metrics and compares coherence routing vs. traditional Dijkstra.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import numpy as np
import json
import networkx as nx
from typing import Dict, List, Tuple
from core.sophon_network_protocol import SophonNetworkProtocol, TopologicalAddress

def create_random_graph(num_nodes: int, p: float = 0.3) -> nx.Graph:
    """Create a random G(n,p) graph representing network topology."""
    return nx.erdos_renyi_graph(num_nodes, p, seed=105)

def simulate_network(num_nodes: int = 50, num_packets: int = 1000):
    print(f"📡 Simulating Sophon Network with {num_nodes} nodes and {num_packets} packets...", file=sys.stderr)

    # 1. Initialize protocol and replace graph with a random connected one
    protocol = SophonNetworkProtocol({'network_nodes': num_nodes, 'seed_numpy': 105, 'mp_dps': 50})

    # Generate random topology
    nx_graph = create_random_graph(num_nodes, p=0.15)
    while not nx.is_connected(nx_graph):
        nx_graph = create_random_graph(num_nodes, p=0.2)

    # Inject topology into CoherenceGraph
    # For edges that don't exist in nx_graph, set distance to infinity
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j and not nx_graph.has_edge(i, j):
                protocol.graph.dist_matrix[i, j] = np.inf

    # Create distance matrix for traditional Dijkstra (hop count)
    hop_matrix = np.full((num_nodes, num_nodes), np.inf)
    for u, v in nx_graph.edges():
        hop_matrix[u, v] = 1.0
        hop_matrix[v, u] = 1.0

    # Standard Dijkstra implementation for comparison
    def find_shortest_path_hops(src_idx: int, dest_idx: int) -> List[int]:
        import heapq
        dist = np.full(num_nodes, np.inf)
        dist[src_idx] = 0
        prev = [-1] * num_nodes
        pq = [(0, src_idx)]

        while pq:
            d, u = heapq.heappop(pq)
            if u == dest_idx:
                path = []
                while prev[u] != -1:
                    path.append(u)
                    u = prev[u]
                path.append(src_idx)
                return path[::-1]

            if d > dist[u]:
                continue

            for v in range(num_nodes):
                if u != v and nx_graph.has_edge(u, v):
                    alt = dist[u] + 1
                    if alt < dist[v]:
                        dist[v] = alt
                        prev[v] = u
                        heapq.heappush(pq, (alt, v))
        return []

    # 2. Run simulation
    coherence_success = 0
    traditional_success = 0

    coherence_path_lengths = []
    traditional_path_lengths = []

    coherence_routing_time = 0.0
    traditional_routing_time = 0.0

    total_coherence_cost = 0.0
    total_traditional_coherence_cost = 0.0

    payload = b"Simulation Packet"

    for _ in range(num_packets):
        src_idx = np.random.randint(0, num_nodes)
        dest_idx = np.random.randint(0, num_nodes)
        while src_idx == dest_idx:
            dest_idx = np.random.randint(0, num_nodes)

        # Coherence routing
        t0 = time.perf_counter()
        coh_path = protocol.compute_route(src_idx, dest_idx)
        coherence_routing_time += (time.perf_counter() - t0)

        # Traditional routing
        t0 = time.perf_counter()
        trad_path = find_shortest_path_hops(src_idx, dest_idx)
        traditional_routing_time += (time.perf_counter() - t0)

        if coh_path:
            coherence_success += 1
            coherence_path_lengths.append(len(coh_path) - 1)
            # Calculate total coherence cost for path
            cost = 0
            for i in range(len(coh_path)-1):
                u, v = coh_path[i], coh_path[i+1]
                # Coherence cost is 1 - coherence distance.
                # Our distance matrix stores coherence distance.
                # Actually dist_matrix has: 1 - |<psi|phi>|
                cost += protocol.graph.dist_matrix[u, v]
            total_coherence_cost += cost

        if trad_path:
            traditional_success += 1
            traditional_path_lengths.append(len(trad_path) - 1)
            cost = 0
            for i in range(len(trad_path)-1):
                u, v = trad_path[i], trad_path[i+1]
                # Original graph distance matrix doesn't change
                original_dist = protocol.nodes[u].coherence_distance(protocol.nodes[v])
                cost += original_dist
            total_traditional_coherence_cost += cost


    # 3. Compile metrics
    metrics = {
        "network": {
            "nodes": num_nodes,
            "edges": nx_graph.number_of_edges(),
            "packets_simulated": num_packets
        },
        "coherence_routing": {
            "delivery_rate": coherence_success / num_packets,
            "avg_hops": float(np.mean(coherence_path_lengths)) if coherence_path_lengths else 0,
            "avg_coherence_loss": total_coherence_cost / coherence_success if coherence_success > 0 else 0,
            "avg_routing_time_ms": (coherence_routing_time / num_packets) * 1000
        },
        "traditional_dijkstra": {
            "delivery_rate": traditional_success / num_packets,
            "avg_hops": float(np.mean(traditional_path_lengths)) if traditional_path_lengths else 0,
            "avg_coherence_loss": total_traditional_coherence_cost / traditional_success if traditional_success > 0 else 0,
            "avg_routing_time_ms": (traditional_routing_time / num_packets) * 1000
        },
        "comparison": {
            "coherence_preservation_improvement":
                1.0 - (total_coherence_cost / coherence_success) /
                (total_traditional_coherence_cost / traditional_success) if traditional_success > 0 and coherence_success > 0 else 0,
            "latency_overhead_ratio":
                (coherence_routing_time / traditional_routing_time) if traditional_routing_time > 0 else 0
        }
    }

    print("\n📊 Simulation Results:", file=sys.stderr)
    print(f"  Delivery Rate (Coherence): {metrics['coherence_routing']['delivery_rate']*100:.1f}%", file=sys.stderr)
    print(f"  Delivery Rate (Traditional): {metrics['traditional_dijkstra']['delivery_rate']*100:.1f}%", file=sys.stderr)
    print(f"  Avg Coherence Loss (Coherence): {metrics['coherence_routing']['avg_coherence_loss']:.4f}", file=sys.stderr)
    print(f"  Avg Coherence Loss (Traditional): {metrics['traditional_dijkstra']['avg_coherence_loss']:.4f}", file=sys.stderr)
    print(f"  Coherence Preservation Improvement: {metrics['comparison']['coherence_preservation_improvement']*100:.1f}%", file=sys.stderr)
    print(f"  Routing Time (Coherence): {metrics['coherence_routing']['avg_routing_time_ms']:.4f} ms", file=sys.stderr)
    print(f"  Routing Time (Traditional): {metrics['traditional_dijkstra']['avg_routing_time_ms']:.4f} ms", file=sys.stderr)

    print(json.dumps(metrics, indent=2))

    return metrics

if __name__ == "__main__":
    simulate_network(num_nodes=50, num_packets=1000)
