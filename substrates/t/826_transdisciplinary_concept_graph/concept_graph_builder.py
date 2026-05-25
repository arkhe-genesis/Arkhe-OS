#!/usr/bin/env python3
"""
concept_graph_builder.py — Substrato 826.1
Grafo de Conceitos Transdisciplinar
Arquiteto: ORCID 0009-0005-2697-4668 | Data: 2026-05-25
"""

import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import numpy as np


@dataclass
class ConceptNode:
    """Nó no grafo de conceitos."""
    id: str
    label: str
    discipline: str  # "physics", "biology", "economics", "linguistics", "art"
    properties: Dict = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None

    def __hash__(self):
        return hash(self.id)


@dataclass
class ConceptEdge:
    """Aresta no grafo de conceitos."""
    source: str
    target: str
    relation: str  # "influences", "is_proportional_to", "encodes_for", "isomorphic_to"
    weight: float = 1.0
    properties: Dict = field(default_factory=dict)


class ConceptGraph:
    """
    Grafo de conceitos transdisciplinar que representa entidades e
    relações de múltiplas disciplinas como uma estrutura unificada.
    """

    def __init__(self):
        self.nodes: Dict[str, ConceptNode] = {}
        self.edges: List[ConceptEdge] = []
        self.adjacency: Dict[str, List[ConceptEdge]] = defaultdict(list)
        self.disciplines: Set[str] = set()

    def add_node(self, node: ConceptNode):
        """Adiciona um nó ao grafo."""
        self.nodes[node.id] = node
        self.disciplines.add(node.discipline)

    def add_edge(self, edge: ConceptEdge):
        """Adiciona uma aresta ao grafo."""
        self.edges.append(edge)
        self.adjacency[edge.source].append(edge)

    def get_discipline_subgraph(self, discipline: str) -> 'ConceptGraph':
        """Extrai o subgrafo de uma disciplina específica."""
        subgraph = ConceptGraph()
        for node_id, node in self.nodes.items():
            if node.discipline == discipline:
                subgraph.add_node(node)
        for edge in self.edges:
            if edge.source in subgraph.nodes and edge.target in subgraph.nodes:
                subgraph.add_edge(edge)
        return subgraph

    def compute_structural_signature(self) -> Dict:
        """
        Computa a assinatura estrutural do grafo:
        - Distribuição de graus
        - Coeficiente de clustering médio
        - Número de componentes conectados
        - Diâmetro aproximado
        """
        # Grau de cada nó
        degrees = defaultdict(int)
        for edge in self.edges:
            degrees[edge.source] += 1
            degrees[edge.target] += 1

        degree_dist = np.array(list(degrees.values()))

        # Coeficiente de clustering simplificado
        clustering_coeffs = []
        for node_id in self.nodes:
            neighbors = set()
            for edge in self.adjacency[node_id]:
                neighbors.add(edge.target)

            if len(neighbors) < 2:
                continue

            # Contar triângulos
            triangles = 0
            neighbor_list = list(neighbors)
            for i in range(len(neighbor_list)):
                for j in range(i + 1, len(neighbor_list)):
                    # Verificar se há aresta entre vizinhos
                    for edge in self.edges:
                        if (edge.source == neighbor_list[i] and edge.target == neighbor_list[j]) or                            (edge.source == neighbor_list[j] and edge.target == neighbor_list[i]):
                            triangles += 1
                            break

            possible_triangles = len(neighbors) * (len(neighbors) - 1) / 2
            if possible_triangles > 0:
                clustering_coeffs.append(triangles / possible_triangles)

        return {
            "num_nodes": len(self.nodes),
            "num_edges": len(self.edges),
            "num_disciplines": len(self.disciplines),
            "degree_mean": float(np.mean(degree_dist)) if len(degree_dist) > 0 else 0,
            "degree_std": float(np.std(degree_dist)) if len(degree_dist) > 0 else 0,
            "clustering_mean": float(np.mean(clustering_coeffs)) if clustering_coeffs else 0,
            "disciplines": list(self.disciplines),
        }

    def export_to_neo4j_cypher(self) -> List[str]:
        """Exporta o grafo como comandos Cypher para Neo4j."""
        commands = []

        # Criar nós
        for node_id, node in self.nodes.items():
            props = json.dumps(node.properties)
            commands.append(
                "CREATE (:" + node.discipline.capitalize() + " " +
                "{id: '" + node_id + "', label: '" + node.label + "', properties: " + props + "})"
            )

        # Criar arestas
        for edge in self.edges:
            commands.append(
                "MATCH (a {id: '" + edge.source + "'}), (b {id: '" + edge.target + "'}) " +
                "CREATE (a)-[:" + edge.relation.upper() + " " +
                "{weight: " + str(edge.weight) + "}]->(b)"
            )

        return commands

    def compute_seal(self) -> str:
        """Computa selo SHA3-256 do grafo."""
        data = {
            "nodes": sorted([n.id for n in self.nodes.values()]),
            "edges": sorted([e.source + "-" + e.relation + "-" + e.target for e in self.edges]),
        }
        return hashlib.sha3_256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def build_example_graph() -> ConceptGraph:
    """Constrói um grafo de exemplo com conceitos de física e economia."""
    graph = ConceptGraph()

    # Nós de Física
    graph.add_node(ConceptNode("charge", "Carga Elétrica", "physics", {"unit": "Coulomb"}))
    graph.add_node(ConceptNode("field", "Campo Elétrico", "physics", {"unit": "V/m"}))
    graph.add_node(ConceptNode("potential", "Potencial Elétrico", "physics", {"unit": "Volt"}))
    graph.add_node(ConceptNode("flux", "Fluxo", "physics", {"unit": "Weber"}))
    graph.add_node(ConceptNode("diffusion", "Difusão", "physics", {"unit": "m²/s"}))

    # Nós de Economia
    graph.add_node(ConceptNode("price", "Preço", "economics", {"unit": "USD"}))
    graph.add_node(ConceptNode("supply", "Oferta", "economics", {"unit": "quantity"}))
    graph.add_node(ConceptNode("demand", "Demanda", "economics", {"unit": "quantity"}))
    graph.add_node(ConceptNode("equilibrium", "Equilíbrio", "economics", {"unit": "price/quantity"}))
    graph.add_node(ConceptNode("volatility", "Volatilidade", "economics", {"unit": "σ"}))

    # Nós de Biologia
    graph.add_node(ConceptNode("gene", "Gene", "biology", {"unit": "sequence"}))
    graph.add_node(ConceptNode("protein", "Proteína", "biology", {"unit": "amino_acids"}))
    graph.add_node(ConceptNode("predator", "Predador", "biology", {"unit": "population"}))
    graph.add_node(ConceptNode("prey", "Presa", "biology", {"unit": "population"}))
    graph.add_node(ConceptNode("population", "População", "biology", {"unit": "individuals"}))

    # Arestas de Física
    graph.add_edge(ConceptEdge("charge", "field", "generates", 1.0))
    graph.add_edge(ConceptEdge("field", "potential", "gradient_of", 1.0))
    graph.add_edge(ConceptEdge("potential", "flux", "drives", 0.8))
    graph.add_edge(ConceptEdge("flux", "diffusion", "is_form_of", 0.9))

    # Arestas de Economia
    graph.add_edge(ConceptEdge("supply", "price", "influences", 1.0))
    graph.add_edge(ConceptEdge("demand", "price", "influences", 1.0))
    graph.add_edge(ConceptEdge("supply", "equilibrium", "determines", 0.9))
    graph.add_edge(ConceptEdge("demand", "equilibrium", "determines", 0.9))
    graph.add_edge(ConceptEdge("price", "volatility", "exhibits", 0.7))

    # Arestas de Biologia
    graph.add_edge(ConceptEdge("gene", "protein", "encodes_for", 1.0))
    graph.add_edge(ConceptEdge("predator", "prey", "consumes", 1.0))
    graph.add_edge(ConceptEdge("prey", "predator", "sustains", 0.8))
    graph.add_edge(ConceptEdge("predator", "population", "regulates", 0.9))
    graph.add_edge(ConceptEdge("prey", "population", "regulates", 0.9))

    return graph


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   CONCEPT GRAPH BUILDER — SUBSTRATO 826.1                ║")
    print("║   Grafo de Conceitos Transdisciplinar | ξM-Field         ║")
    print("╚════════════════════════════════════════════════════════════╝")

    graph = build_example_graph()

    print("\n📊 Graph Statistics:")
    sig = graph.compute_structural_signature()
    for key, value in sig.items():
        print("   " + key + ": " + str(value))

    print("\n🔐 Graph Seal: " + graph.compute_seal()[:16] + "...")

    # Exportar subgrafos por disciplina
    for discipline in ["physics", "economics", "biology"]:
        subgraph = graph.get_discipline_subgraph(discipline)
        sig = subgraph.compute_structural_signature()
        print("\n📚 " + discipline.upper() + " subgraph: " + str(sig['num_nodes']) + " nodes, " + str(sig['num_edges']) + " edges")

    # Comandos Cypher (primeiros 3)
    print("\n🗄️  Neo4j Cypher (sample):")
    for cmd in graph.export_to_neo4j_cypher()[:3]:
        print("   " + cmd)


if __name__ == "__main__":
    main()
