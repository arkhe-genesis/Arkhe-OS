# arkhe_os/orchestrator/graph/substrate_graph.py
"""
Grafo de dependências e coerência entre substratos do ARKHE OS.
"""
import numpy as np
import networkx as nx
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum, auto

class SubstrateID(Enum):
    """Identificadores canônicos de substratos."""
    FLOQUET = 280          # Floquet Quantum Phases
    PSI_TOE = 283          # Ψ_ToE Theoretical Predicates
    VALIDATION = 284       # Experimental Validation Harness
    FEDERATION = 285       # Federated Validation Network
    LEDGER = 287           # Public Validation Ledger
    ORCHESTRATOR = 290     # Cross-Substrate Coherence Orchestrator (self)

@dataclass
class CoherenceEdge:
    """Aresta do grafo representando coerência transversal entre substratos."""
    source: SubstrateID
    target: SubstrateID
    coherence_value: float  # Φ_C^(ij) ∈ [0,1]
    sigma: float           # Parâmetro de sensibilidade σ_ij
    sample_count: int      # Número de amostras usadas para estimar Φ_C^(ij)
    last_updated: float    # Timestamp da última atualização
    metadata: Dict = field(default_factory=dict)

    def update(self, new_coherence: float, new_sigma: float,
               new_samples: int, timestamp: float):
        """Atualiza peso da aresta com nova estimativa de coerência."""
        # Média móvel exponencial para suavizar flutuações
        alpha = min(1.0, new_samples / (self.sample_count + new_samples))
        self.coherence_value = (1 - alpha) * self.coherence_value + alpha * new_coherence
        self.sigma = (1 - alpha) * self.sigma + alpha * new_sigma
        self.sample_count += new_samples
        self.last_updated = timestamp

class SubstrateGraph:
    """Grafo direcionado de coerência entre substratos."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.edges: Dict[Tuple[SubstrateID, SubstrateID], CoherenceEdge] = {}
        self._initialize_default_edges()

    def _initialize_default_edges(self):
        """Inicializa arestas padrão com valores conservativos."""
        default_pairs = [
            (SubstrateID.FLOQUET, SubstrateID.PSI_TOE),
            (SubstrateID.PSI_TOE, SubstrateID.VALIDATION),
            (SubstrateID.VALIDATION, SubstrateID.FEDERATION),
            (SubstrateID.FEDERATION, SubstrateID.LEDGER),
            (SubstrateID.LEDGER, SubstrateID.PSI_TOE),  # Feedback loop
            (SubstrateID.ORCHESTRATOR, SubstrateID.FLOQUET),
            (SubstrateID.ORCHESTRATOR, SubstrateID.PSI_TOE),
            (SubstrateID.ORCHESTRATOR, SubstrateID.VALIDATION),
            (SubstrateID.ORCHESTRATOR, SubstrateID.FEDERATION),
            (SubstrateID.ORCHESTRATOR, SubstrateID.LEDGER),
        ]

        for src, tgt in default_pairs:
            edge = CoherenceEdge(
                source=src, target=tgt,
                coherence_value=0.85,  # Valor inicial conservativo
                sigma=0.1,              # Sensibilidade inicial
                sample_count=100,
                last_updated=0.0
            )
            self.graph.add_edge(src, tgt, weight=edge.coherence_value)
            self.edges[(src, tgt)] = edge

    def update_coherence(self, src: SubstrateID, tgt: SubstrateID,
                        coherence_samples: List[float],
                        sigma_estimate: float,
                        timestamp: float):
        """
        Atualiza peso de coerência para aresta (src, tgt) baseado em amostras.

        Args:
            coherence_samples: Lista de valores de coerência observados
            sigma_estimate: Estimativa do parâmetro de sensibilidade σ_ij
            timestamp: Timestamp da atualização
        """
        if (src, tgt) not in self.edges:
            # Criar nova aresta se não existir
            edge = CoherenceEdge(
                source=src, target=tgt,
                coherence_value=np.mean(coherence_samples),
                sigma=sigma_estimate,
                sample_count=len(coherence_samples),
                last_updated=timestamp
            )
            self.graph.add_edge(src, tgt, weight=edge.coherence_value)
            self.edges[(src, tgt)] = edge
        else:
            # Atualizar aresta existente
            edge = self.edges[(src, tgt)]
            edge.update(
                new_coherence=np.mean(coherence_samples),
                new_sigma=sigma_estimate,
                new_samples=len(coherence_samples),
                timestamp=timestamp
            )
            self.graph[src][tgt]['weight'] = edge.coherence_value

    def compute_global_coherence(self) -> float:
        """Calcula coerência global como média ponderada das arestas."""
        if not self.edges:
            return 0.0

        # Ponderar por número de amostras (mais amostras = mais confiança)
        total_weight = sum(e.sample_count for e in self.edges.values())
        if total_weight == 0:
            return np.mean([e.coherence_value for e in self.edges.values()])

        weighted_sum = sum(
            e.coherence_value * e.sample_count
            for e in self.edges.values()
        )
        return weighted_sum / total_weight

    def detect_anomalies(self, threshold: float = 0.70) -> List[Dict]:
        """Detecta arestas com coerência abaixo do threshold."""
        anomalies = []
        for (src, tgt), edge in self.edges.items():
            if edge.coherence_value < threshold:
                anomalies.append({
                    'source': src.name,
                    'target': tgt.name,
                    'coherence': edge.coherence_value,
                    'sigma': edge.sigma,
                    'sample_count': edge.sample_count,
                    'severity': 'critical' if edge.coherence_value < 0.50 else 'warning'
                })
        return anomalies

    def to_dict(self) -> Dict:
        """Serializa grafo para exportação/auditoria."""
        return {
            'nodes': [s.name for s in self.graph.nodes()],
            'edges': [
                {
                    'source': e.source.name,
                    'target': e.target.name,
                    'coherence': e.coherence_value,
                    'sigma': e.sigma,
                    'sample_count': e.sample_count,
                    'last_updated': e.last_updated
                }
                for e in self.edges.values()
            ],
            'global_coherence': self.compute_global_coherence(),
            'anomaly_count': len(self.detect_anomalies())
        }
