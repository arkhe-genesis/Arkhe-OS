#!/usr/bin/env python3
"""
topological_data_analyzer.py — Substrato 826.3
Análise Topológica de Dados usando GUDHI
Arquiteto: ORCID 0009-0005-2697-4668 | Data: 2026-05-25
"""

import numpy as np
import gudhi
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt


class TopologicalDataAnalyzer:
    """
    Analisa a topologia de grafos de conceitos usando
    homologia persistente para detectar invariantes estruturais.
    """

    def __init__(self, max_dimension: int = 2):
        self.max_dimension = max_dimension

    def compute_persistence(self, distance_matrix: np.ndarray) -> List[Tuple[int, Tuple[float, float]]]:
        """
        Computa a homologia persistente de uma matriz de distâncias.
        Retorna lista de (dimensão, (nascimento, morte)).
        """
        # Criar complexo de Rips
        rips_complex = gudhi.RipsComplex(
            distance_matrix=distance_matrix,
            max_edge_length=2.0,
        )

        # Construir simplex tree
        simplex_tree = rips_complex.create_simplex_tree(max_dimension=self.max_dimension)

        # Computar persistência
        persistence = simplex_tree.persistence()

        return persistence

    def compute_persistence_landscape(self, persistence: List[Tuple[int, Tuple[float, float]]],
                                       dimension: int = 1, num_points: int = 100) -> np.ndarray:
        """
        Computa a paisagem de persistência para uma dimensão específica.
        Retorna array de num_points valores.
        """
        # Filtrar por dimensão
        dim_persistence = [p for d, p in persistence if d == dimension]

        if not dim_persistence:
            return np.zeros(num_points)

        # Encontrar range
        all_values = []
        for birth, death in dim_persistence:
            all_values.extend([birth, death])

        min_val = min(all_values)
        max_val = max(all_values)

        if max_val == min_val:
            return np.zeros(num_points)

        # Amostrar pontos
        x_values = np.linspace(min_val, max_val, num_points)
        landscape = np.zeros(num_points)

        # Para cada ponto, computar a paisagem
        for i, x in enumerate(x_values):
            values = []
            for birth, death in dim_persistence:
                if birth <= x <= death:
                    # Triângulo da paisagem
                    mid = (birth + death) / 2
                    if x <= mid:
                        value = x - birth
                    else:
                        value = death - x
                    values.append(value)

            if values:
                landscape[i] = max(values)

        return landscape

    def compare_disciplines(self, distance_matrix1: np.ndarray,
                           distance_matrix2: np.ndarray) -> Dict:
        """
        Compara a topologia de duas disciplinas.
        Retorna métricas de similaridade estrutural.
        """
        # Computar persistência para ambas
        pers1 = self.compute_persistence(distance_matrix1)
        pers2 = self.compute_persistence(distance_matrix2)

        results = {}

        for dim in range(self.max_dimension + 1):
            # Paisagens de persistência
            land1 = self.compute_persistence_landscape(pers1, dimension=dim)
            land2 = self.compute_persistence_landscape(pers2, dimension=dim)

            # Interpolar para mesmo tamanho
            min_len = min(len(land1), len(land2))
            land1 = land1[:min_len]
            land2 = land2[:min_len]

            # Distância L2 entre paisagens
            if np.linalg.norm(land1) > 0 and np.linalg.norm(land2) > 0:
                l2_distance = np.linalg.norm(land1 - land2)
                correlation = np.corrcoef(land1, land2)[0, 1] if np.std(land1) > 0 and np.std(land2) > 0 else 0
            else:
                l2_distance = float('inf')
                correlation = 0

            # Número de features
            features1 = len([p for d, p in pers1 if d == dim])
            features2 = len([p for d, p in pers2 if d == dim])

            results["dimension_" + str(dim)] = {
                "l2_distance": float(l2_distance),
                "correlation": float(correlation),
                "features_1": features1,
                "features_2": features2,
                "isomorphism_candidate": correlation > 0.8 and l2_distance < 1.0,
            }

        return results

    def plot_persistence_diagram(self, persistence: List[Tuple[int, Tuple[float, float]]],
                                 title: str = "Persistence Diagram"):
        """Plota o diagrama de persistência."""
        gudhi.plot_persistence_diagram(persistence)
        plt.title(title)
        plt.xlabel("Birth")
        plt.ylabel("Death")
        plt.show()


def create_distance_matrix_from_graph(concept_graph) -> np.ndarray:
    """Cria matriz de distâncias a partir de um grafo de conceitos."""
    nodes = list(concept_graph.nodes.keys())
    n = len(nodes)

    # Inicializar com infinito
    dist = np.full((n, n), np.inf)
    np.fill_diagonal(dist, 0)

    # Preencher com arestas
    node_idx = {node_id: idx for idx, node_id in enumerate(nodes)}

    for edge in concept_graph.edges:
        i = node_idx[edge.source]
        j = node_idx[edge.target]
        dist[i, j] = min(dist[i, j], 1.0 / edge.weight)
        dist[j, i] = min(dist[j, i], 1.0 / edge.weight)

    # Floyd-Warshall para caminhos mais curtos
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i, k] + dist[k, j] < dist[i, j]:
                    dist[i, j] = dist[i, k] + dist[k, j]

    # Normalizar
    max_dist = np.max(dist[np.isfinite(dist)])
    if max_dist > 0:
        dist = dist / max_dist

    # Substituir infinito por 2 (máximo normalizado)
    dist[np.isinf(dist)] = 2.0

    return dist


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   TOPOLOGICAL DATA ANALYZER — SUBSTRATO 826.3            ║")
    print("║   GUDHI | Homologia Persistente | ξM-Field             ║")
    print("╚════════════════════════════════════════════════════════════╝")

    from concept_graph_builder import build_example_graph

    # Criar analisador
    tda = TopologicalDataAnalyzer(max_dimension=2)

    # Construir grafos de exemplo
    graph = build_example_graph()
    physics = graph.get_discipline_subgraph("physics")
    economics = graph.get_discipline_subgraph("economics")
    biology = graph.get_discipline_subgraph("biology")

    # Criar matrizes de distância
    dist_physics = create_distance_matrix_from_graph(physics)
    dist_economics = create_distance_matrix_from_graph(economics)
    dist_biology = create_distance_matrix_from_graph(biology)

    print("\n📊 Physics subgraph: " + str(len(physics.nodes)) + " nodes")
    print("📊 Economics subgraph: " + str(len(economics.nodes)) + " nodes")
    print("📊 Biology subgraph: " + str(len(biology.nodes)) + " nodes")

    # Comparar física vs economia
    print("\n🔬 Comparing Physics ↔ Economics:")
    results = tda.compare_disciplines(dist_physics, dist_economics)
    for dim, metrics in results.items():
        print("   " + str(dim) + ": L2=" + "{:.4f}".format(metrics['l2_distance']) + ", corr=" + "{:.4f}".format(metrics['correlation']) + ", "
              "features=(" + str(metrics['features_1']) + "," + str(metrics['features_2']) + "), "
              "candidate=" + str(metrics['isomorphism_candidate']))

    # Comparar física vs biologia
    print("\n🧬 Comparing Physics ↔ Biology:")
    results = tda.compare_disciplines(dist_physics, dist_biology)
    for dim, metrics in results.items():
        print("   " + str(dim) + ": L2=" + "{:.4f}".format(metrics['l2_distance']) + ", corr=" + "{:.4f}".format(metrics['correlation']) + ", "
              "features=(" + str(metrics['features_1']) + "," + str(metrics['features_2']) + "), "
              "candidate=" + str(metrics['isomorphism_candidate']))


if __name__ == "__main__":
    main()
