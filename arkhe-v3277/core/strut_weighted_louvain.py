#!/usr/bin/env python3
"""
strut_weighted_louvain.py
Detecção de comunidades Louvain com pesos específicos baseados nos tipos de strut (H/V/D).
"""
import numpy as np
import networkx as nx
from scipy.sparse import csr_matrix
from typing import Dict, List, Optional, Tuple

class StrutWeightedLouvain:
    """
    Louvain Multi-resolução que pesa acoplamentos (J) de acordo com
    a tipologia dos struts da estrutura OR (Horizontal, Vertical, Diagonal).
    """

    def __init__(self,
                 h_weight: float = 1.0,
                 v_weight: float = 1.0,
                 d_weight: float = 0.5,
                 resolution_range: List[float] = [0.3, 0.5, 0.7, 1.0, 1.5],
                 min_community_size: int = 10,
                 cohesion_threshold: float = 0.3):
        self.h_weight = h_weight
        self.v_weight = v_weight
        self.d_weight = d_weight
        self.resolution_range = resolution_range
        self.min_community_size = min_community_size
        self.cohesion_threshold = cohesion_threshold

    def _apply_strut_weights(self, J: np.ndarray, strut_types: Dict[Tuple[int, int], str]) -> np.ndarray:
        """Aplica multiplicadores de peso H/V/D na matriz de acoplamento J."""
        J_weighted = J.copy()

        # struts is a dictionary mapping (node_i, node_j) -> type ('H', 'V', 'D')
        for (i, j), strut_type in strut_types.items():
            if i < J_weighted.shape[0] and j < J_weighted.shape[1]:
                weight_multiplier = 1.0
                if strut_type == 'H':
                    weight_multiplier = self.h_weight
                elif strut_type == 'V':
                    weight_multiplier = self.v_weight
                elif strut_type == 'D':
                    weight_multiplier = self.d_weight

                J_weighted[i, j] *= weight_multiplier
                J_weighted[j, i] *= weight_multiplier # Simetria

        return J_weighted

    def detect_communities_weighted(self, J: np.ndarray, strut_types: Dict[Tuple[int, int], str]) -> Dict:
        """
        Detecta comunidades pesando as conexões de acordo com o tipo de strut.
        """
        J_weighted = self._apply_strut_weights(J, strut_types)

        results_by_resolution = {}

        for resolution in self.resolution_range:
            # Construir grafo a partir da matriz de couplings
            J_abs = np.abs(J_weighted)
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
            valid_communities = [c for c in partition if len(c) >= self.min_community_size]

            # Calcular coesão para cada comunidade
            community_stats = []
            for cid, crystals in enumerate(valid_communities):
                rho = self._compute_cohesion(J, list(crystals)) # Cohesion against original J
                community_stats.append({
                    'id': cid,
                    'size': len(crystals),
                    'cohesion': rho,
                    'crystals': list(crystals),
                    'is_coherent': abs(rho) >= self.cohesion_threshold
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

        # Selecionar melhor resolução
        best_resolution = max(results_by_resolution.keys(),
                             key=lambda r: results_by_resolution[r]['quality_score'])

        return {
            'best_resolution': best_resolution,
            'all_results': results_by_resolution,
            'selected_communities': results_by_resolution[best_resolution]['communities']
        }

    def _compute_cohesion(self, J: np.ndarray, community: List[int]) -> float:
        """Calcula coesão assinada ρ para uma comunidade."""
        pairs = [(i, j) for idx, i in enumerate(community) for j in community[idx+1:]]
        if not pairs:
            return 0.0

        signs = [np.sign(J[i, j]) for i, j in pairs if abs(J[i, j]) > 1e-8]
        return float(np.mean(signs)) if signs else 0.0
