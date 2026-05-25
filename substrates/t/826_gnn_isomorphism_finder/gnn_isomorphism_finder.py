#!/usr/bin/env python3
"""
gnn_isomorphism_finder.py — Substrato 826.2
GNN Isomorphism Finder usando Graph Isomorphism Network (GIN)
Arquiteto: ORCID 0009-0005-2697-4668 | Data: 2026-05-25

Requer: torch, torch-geometric, numpy
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GINConv, global_mean_pool, global_add_pool
from torch_geometric.data import Data, Batch
from typing import Dict, List, Tuple, Optional
import numpy as np


class GINIsomorphismNet(nn.Module):
    """
    Graph Isomorphism Network para detecção de isomorfismos
    entre grafos de conceitos de diferentes disciplinas.

    Baseado no paper: "How Powerful are Graph Neural Networks?" (Xu et al., 2019)
    """

    def __init__(self, in_channels: int, hidden_channels: int = 64, num_layers: int = 3, dropout: float = 0.2):
        super().__init__()

        self.num_layers = num_layers
        self.dropout = dropout

        # Camadas GIN
        self.convs = nn.ModuleList()
        self.batch_norms = nn.ModuleList()

        # Primeira camada
        mlp = nn.Sequential(
            nn.Linear(in_channels, hidden_channels),
            nn.ReLU(),
            nn.Linear(hidden_channels, hidden_channels),
        )
        self.convs.append(GINConv(mlp))
        self.batch_norms.append(nn.BatchNorm1d(hidden_channels))

        # Camadas intermediárias
        for _ in range(num_layers - 1):
            mlp = nn.Sequential(
                nn.Linear(hidden_channels, hidden_channels),
                nn.ReLU(),
                nn.Linear(hidden_channels, hidden_channels),
            )
            self.convs.append(GINConv(mlp))
            self.batch_norms.append(nn.BatchNorm1d(hidden_channels))

        # Projeção para embedding de grafo
        self.graph_embedding = nn.Sequential(
            nn.Linear(hidden_channels, hidden_channels),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels, 32),  # Embedding final de 32 dimensões
        )

        # Classificador de isomorfismo
        # Entrada: concatenação de embeddings de dois grafos (32 + 32 = 64)
        self.isomorphism_classifier = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid(),
        )

    def forward(self, x, edge_index, batch):
        """Forward pass para um grafo."""
        for conv, bn in zip(self.convs, self.batch_norms):
            x = conv(x, edge_index)
            x = bn(x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        # Pooling global para obter embedding do grafo
        # Usamos mean + add pool para capturar mais informação estrutural
        x_mean = global_mean_pool(x, batch)
        x_add = global_add_pool(x, batch)
        x = (x_mean + x_add) / 2

        x = self.graph_embedding(x)
        return x

    def compute_isomorphism_score(self, data1: Data, data2: Data) -> float:
        """
        Computa o score de isomorfismo entre dois grafos.
        Retorna valor em [0, 1] onde 1 = isomorfismo perfeito.
        """
        self.eval()
        with torch.no_grad():
            # Embeddings individuais
            emb1 = self.forward(data1.x, data1.edge_index, data1.batch)
            emb2 = self.forward(data2.x, data2.edge_index, data2.batch)

            # Concatenar e classificar
            combined = torch.cat([emb1, emb2], dim=-1)
            score = self.isomorphism_classifier(combined)

            return score.item()

    def compute_functor_mapping(self, data1: Data, data2: Data) -> Dict[int, int]:
        """
        Tenta aprender um mapeamento (functor) entre nós dos dois grafos.
        Retorna dict: node_id_1 -> node_id_2.

        Usa embeddings de nós (antes do pooling) para encontrar correspondências.
        """
        self.eval()
        with torch.no_grad():
            # Obter embeddings de nós (antes do pooling)
            x1 = data1.x
            x2 = data2.x

            for conv, bn in zip(self.convs, self.batch_norms):
                x1 = conv(x1, data1.edge_index)
                x1 = bn(x1)
                x1 = F.relu(x1)

                x2 = conv(x2, data2.edge_index)
                x2 = bn(x2)
                x2 = F.relu(x2)

            # Mapear cada nó do grafo 1 para o mais próximo no grafo 2
            # Usando distância euclidiana nos embeddings
            mapping = {}
            for i in range(x1.size(0)):
                # Distância euclidiana para todos os nós do grafo 2
                distances = torch.norm(x2 - x1[i], dim=1)
                closest = torch.argmin(distances).item()
                confidence = torch.exp(-distances[closest]).item()
                mapping[i] = {
                    "target": closest,
                    "confidence": confidence,
                    "distance": distances[closest].item(),
                }

            return mapping

    def compute_iota_score(self, data1: Data, data2: Data) -> Dict:
        """
        Computa o score ι (iota) completo entre dois grafos.
        Combina isomorfismo estrutural com qualidade do mapeamento.
        """
        iso_score = self.compute_isomorphism_score(data1, data2)
        mapping = self.compute_functor_mapping(data1, data2)

        # Qualidade média do mapeamento
        avg_confidence = np.mean([m["confidence"] for m in mapping.values()])
        avg_distance = np.mean([m["distance"] for m in mapping.values()])

        # ι combina isomorfismo estrutural com coerência do mapeamento
        iota = (iso_score * 0.6) + (avg_confidence * 0.4)

        return {
            "iota": float(iota),
            "isomorphism_score": float(iso_score),
            "avg_mapping_confidence": float(avg_confidence),
            "avg_mapping_distance": float(avg_distance),
            "mapping": mapping,
            "is_canonical": iota > 0.95,
            "is_strong": iota > 0.8,
            "is_suggestive": iota > 0.6,
        }


def create_graph_data_from_concept_graph(concept_graph, node_feature_dim: int = 16) -> Data:
    """
    Converte um ConceptGraph em um PyTorch Geometric Data object.

    Features dos nós:
    - One-hot da disciplina
    - Propriedades numéricas normalizadas
    - Posição no embedding (se disponível)
    """
    num_nodes = len(concept_graph.nodes)

    if num_nodes == 0:
        # Retornar grafo vazio
        return Data(
            x=torch.zeros(1, node_feature_dim),
            edge_index=torch.zeros(2, 0, dtype=torch.long),
            batch=torch.zeros(1, dtype=torch.long),
        )

    # Features dos nós
    disciplines = sorted(list(concept_graph.disciplines))
    x = torch.zeros(num_nodes, node_feature_dim)

    node_id_to_idx = {node_id: idx for idx, node_id in enumerate(concept_graph.nodes.keys())}

    for node_id, node in concept_graph.nodes.items():
        idx = node_id_to_idx[node_id]

        # One-hot da disciplina (primeiras posições)
        if node.discipline in disciplines:
            disc_idx = disciplines.index(node.discipline)
            if disc_idx < node_feature_dim:
                x[idx, disc_idx] = 1.0

        # Propriedades numéricas (posições seguintes)
        prop_offset = len(disciplines)
        for prop_key, prop_value in node.properties.items():
            if isinstance(prop_value, (int, float)) and prop_offset < node_feature_dim:
                # Normalização simples: log scale
                x[idx, prop_offset] = np.log1p(abs(float(prop_value)))
                prop_offset += 1
                if prop_offset >= node_feature_dim:
                    break

        # Se houver embedding pré-computado, usar
        if node.embedding is not None and len(node.embedding) > 0:
            emb_len = min(len(node.embedding), node_feature_dim - prop_offset)
            if emb_len > 0:
                x[idx, prop_offset:prop_offset + emb_len] = torch.tensor(node.embedding[:emb_len])

    # Arestas (grafo não-direcionado)
    edge_index = []
    for edge in concept_graph.edges:
        src_idx = node_id_to_idx.get(edge.source)
        tgt_idx = node_id_to_idx.get(edge.target)
        if src_idx is not None and tgt_idx is not None:
            edge_index.append([src_idx, tgt_idx])
            edge_index.append([tgt_idx, src_idx])  # Não-direcionado

    if edge_index:
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.zeros(2, 0, dtype=torch.long)

    # Batch (um único grafo)
    batch = torch.zeros(num_nodes, dtype=torch.long)

    return Data(x=x, edge_index=edge_index, batch=batch)


def train_gnn(model: GINIsomorphismNet,
              pairs: List[Tuple[Data, Data, float]],
              epochs: int = 100,
              lr: float = 1e-3) -> List[float]:
    """
    Treina o GNN com pares de grafos e labels de isomorfismo.

    Args:
        model: GINIsomorphismNet
        pairs: Lista de (graph1, graph2, label) onde label ∈ {0, 1}
        epochs: Número de épocas
        lr: Learning rate

    Returns:
        Lista de losses por época
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()

    losses = []

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0

        for data1, data2, label in pairs:
            optimizer.zero_grad()

            # Forward
            emb1 = model(data1.x, data1.edge_index, data1.batch)
            emb2 = model(data2.x, data2.edge_index, data2.batch)

            combined = torch.cat([emb1, emb2], dim=-1)
            pred = model.isomorphism_classifier(combined)

            # Loss
            target = torch.tensor([[label]], dtype=torch.float)
            loss = criterion(pred, target)

            # Backward
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        avg_loss = epoch_loss / len(pairs)
        losses.append(avg_loss)

        if (epoch + 1) % 10 == 0:
            print(f"[826.2] Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

    return losses


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   GNN ISOMORPHISM FINDER — SUBSTRATO 826.2               ║")
    print("║   Graph Isomorphism Network | PyTorch Geometric          ║")
    print("║   ι (iota) Score: Isomorfismo + Mapeamento               ║")
    print("╚════════════════════════════════════════════════════════════╝")

    # Verificar disponibilidade de PyTorch Geometric
    try:
        import torch_geometric
        print(f"✅ PyTorch Geometric version: {torch_geometric.__version__}")
    except ImportError:
        print("❌ PyTorch Geometric não encontrado!")
        print("   Instale com: pip install torch-geometric")
        return

    # Criar modelo
    model = GINIsomorphismNet(in_channels=16, hidden_channels=64, num_layers=3, dropout=0.2)
    print(f"\n📊 Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Criar grafos de exemplo
    from concept_graph_builder import build_example_graph

    graph = build_example_graph()
    physics = graph.get_discipline_subgraph("physics")
    economics = graph.get_discipline_subgraph("economics")
    biology = graph.get_discipline_subgraph("biology")

    # Converter para PyG
    data_physics = create_graph_data_from_concept_graph(physics, node_feature_dim=16)
    data_economics = create_graph_data_from_concept_graph(economics, node_feature_dim=16)
    data_biology = create_graph_data_from_concept_graph(biology, node_feature_dim=16)

    print(f"\n📐 Physics graph: {data_physics.num_nodes} nodes, {data_physics.num_edges} edges")
    print(f"📈 Economics graph: {data_economics.num_nodes} nodes, {data_economics.num_edges} edges")
    print(f"🧬 Biology graph: {data_biology.num_nodes} nodes, {data_biology.num_edges} edges")

    # Treinar com pares sintéticos (stub)
    print(f"\n🔄 Training on synthetic pairs...")
    train_pairs = [
        (data_physics, data_physics, 1.0),      # Isomorfismo perfeito (mesmo grafo)
        (data_economics, data_economics, 1.0),  # Isomorfismo perfeito
        (data_physics, data_economics, 0.3),    # Baixo isomorfismo (stub)
        (data_physics, data_biology, 0.5),     # Médio isomorfismo (stub)
    ]

    losses = train_gnn(model, train_pairs, epochs=50, lr=1e-3)
    print(f"✅ Training complete. Final loss: {losses[-1]:.4f}")

    # Avaliar
    print(f"\n🎯 Evaluating isomorphism scores:")

    # Physics ↔ Economics
    result = model.compute_iota_score(data_physics, data_economics)
    print(f"\n   Physics ↔ Economics:")
    print(f"   ι = {result['iota']:.4f}")
    print(f"   Isomorphism: {result['isomorphism_score']:.4f}")
    print(f"   Mapping confidence: {result['avg_mapping_confidence']:.4f}")
    print(f"   Canonical: {result['is_canonical']} | Strong: {result['is_strong']} | Suggestive: {result['is_suggestive']}")

    # Physics ↔ Biology
    result = model.compute_iota_score(data_physics, data_biology)
    print(f"\n   Physics ↔ Biology:")
    print(f"   ι = {result['iota']:.4f}")
    print(f"   Isomorphism: {result['isomorphism_score']:.4f}")
    print(f"   Mapping confidence: {result['avg_mapping_confidence']:.4f}")
    print(f"   Canonical: {result['is_canonical']} | Strong: {result['is_strong']} | Suggestive: {result['is_suggestive']}")

    # Functor mapping (Physics → Economics)
    mapping = model.compute_functor_mapping(data_physics, data_economics)
    print(f"\n🔗 Functor Mapping (Physics → Economics):")
    for src, info in list(mapping.items())[:5]:
        print(f"   Node {src} → Node {info['target']} (confidence: {info['confidence']:.4f})")

    print(f"\n✅ GNN Isomorphism Finder ready for Substrate 826.")


if __name__ == "__main__":
    main()
