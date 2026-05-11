from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import numpy as np
from .psa import SemanticGraph, PSA

@dataclass
class EnrichedFeatures:
    """Vetor de características completo para o PEFM."""
    artifact_id: str
    timestamp_ns: int

    # Features do PSA
    coherence_score: float
    component_S: float
    component_C: float
    component_I: float
    component_P: float
    component_E: float

    # Features agregadas do grafo
    vertex_count: int
    edge_count: int
    domain_sensitivity: float

    def to_feature_vector(self) -> np.ndarray:
        return np.array([
            self.coherence_score,
            self.component_S,
            self.component_C,
            self.component_I,
            self.component_P,
            self.component_E,
            float(self.vertex_count),
            float(self.edge_count),
            self.domain_sensitivity,
        ])

class FeatureEnricher:
    def __init__(self, psa: PSA):
        self.psa = psa

    def enrich(self, artifact_id: str, G: SemanticGraph, timestamp_ns: int) -> EnrichedFeatures:
        res = self.psa.calculate_score(G)

        return EnrichedFeatures(
            artifact_id=artifact_id,
            timestamp_ns=timestamp_ns,
            coherence_score=res["score"],
            component_S=res["S"],
            component_C=res["C"],
            component_I=res["I"],
            component_P=res["P"],
            component_E=res["E"],
            vertex_count=len(G.claims),
            edge_count=len(G.edges),
            domain_sensitivity=self.psa.critical_domains.get(G.domain, 0.15)
        )
