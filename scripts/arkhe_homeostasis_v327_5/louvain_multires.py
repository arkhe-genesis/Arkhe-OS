#!/usr/bin/env python3
"""
louvain_multires.py
Detecção de comunidades Louvain com varredura de resolução para encontrar estruturas coerentes.
"""
import numpy as np
import networkx as nx
from scipy.sparse import csr_matrix
from typing import Dict, List, Optional

def detect_communities_multires(J: np.ndarray,
                                resolution_range: List[float] = [0.3, 0.5, 0.7, 1.0, 1.5],
                                min_community_size: int = 10,
                                cohesion_threshold: float = 0.3) -> Dict:
    """
    Detecta comunidades em múltiplas resoluções e seleciona a configuração ótima.

    Critérios de seleção:
    1. Maximizar número de comunidades com |ρ| > cohesion_threshold
    2. Preferir resoluções que produzem comunidades de tamanho balanceado
    3. Penalizar fragmentação excessiva (muitas comunidades < min_community_size)
    """
    results_by_resolution = {}

    for resolution in resolution_range:
        # Construir grafo a partir da matriz de couplings
        J_abs = np.abs(J)
        # Filtrar ruído
        J_abs[J_abs < 1e-3] = 0
        J_sparse = csr_matrix(J_abs)
        G = nx.from_scipy_sparse_array(J_sparse)
        G.remove_nodes_from(list(nx.isolates(G)))

        # Detectar comunidades com resolução específica
        if len(G.nodes) > 0:
            partition = nx.community.louvain_communities(G, resolution=resolution, seed=42)
        else:
            partition = []

        # Filtrar comunidades muito pequenas
        valid_communities = [c for c in partition if len(c) >= min_community_size]

        # Calcular coesão para cada comunidade
        community_stats = []
        for cid, crystals in enumerate(valid_communities):
            rho = _compute_cohesion(J, list(crystals))
            community_stats.append({
                'id': cid,
                'size': len(crystals),
                'cohesion': rho,
                'crystals': list(crystals),
                'is_coherent': abs(rho) >= cohesion_threshold
            })

        # Métricas agregadas
        n_coherent = sum(1 for c in community_stats if c['is_coherent'])
        avg_size = np.mean([c['size'] for c in community_stats]) if community_stats else 0
        size_std = np.std([c['size'] for c in community_stats]) if community_stats else 0

        # Score de qualidade: mais comunidades coerentes + tamanho balanceado
        quality_score = (
            n_coherent * 2.0 +  # Peso maior para coerência
            1.0 / (1.0 + size_std / max(avg_size, 1))  # Penalizar variância de tamanho
        )

        results_by_resolution[resolution] = {
            'communities': community_stats,
            'n_total': len(community_stats),
            'n_coherent': n_coherent,
            'avg_size': avg_size,
            'size_std': size_std,
            'quality_score': quality_score
        }

        print(f"   resolution={resolution:.1f}: {len(community_stats)} comunidades, "
              f"{n_coherent} coerentes, quality={quality_score:.2f}")

    # Selecionar melhor resolução
    best_resolution = max(results_by_resolution.keys(),
                         key=lambda r: results_by_resolution[r]['quality_score'])

    return {
        'best_resolution': best_resolution,
        'all_results': results_by_resolution,
        'selected_communities': results_by_resolution[best_resolution]['communities']
    }

def _compute_cohesion(J: np.ndarray, community: List[int]) -> float:
    """Calcula coesão assinada ρ para uma comunidade."""
    pairs = [(i, j) for idx, i in enumerate(community) for j in community[idx+1:]]
    if not pairs:
        return 0.0

    signs = [np.sign(J[i, j]) for i, j in pairs if abs(J[i, j]) > 1e-8]
    return np.mean(signs) if signs else 0.0
