import networkx as nx
import numpy as np
from typing import Dict, List, Tuple
import time

class LFIRGraphStore:
    """Armazena e indexa grafos LFIR com metadados de coerência e temporalidade."""

    def __init__(self, db_path: str = "/var/lib/agi/memory/lfir_graph.db"):
        self.graph = nx.MultiDiGraph()
        self.db_path = db_path
        self._load_or_init()

    def _load_or_init(self):
        try:
            self.graph = nx.read_gml(self.db_path)
        except FileNotFoundError:
            self.graph = nx.MultiDiGraph()

    def store_state(self, state_id: str, lfir_graph: nx.Graph,
                   coherence: float, metadata: Dict):
        """Armazena um estado LFIR com metadados de coerência."""
        self.graph.add_node(state_id,
                           lfir=lfir_graph,
                           coherence=coherence,
                           timestamp=time.time(),
                           **metadata)

    def retrieve_by_coherence(self, min_coherence: float = 0.7) -> List[str]:
        """Recupera estados com coerência acima do limiar."""
        return [n for n, d in self.graph.nodes(data=True)
                if d.get('coherence', 0) >= min_coherence]

    def prune_low_coherence(self, threshold: float = 0.5):
        """Poda estados de baixa coerência para otimização."""
        to_remove = [n for n, d in self.graph.nodes(data=True)
                     if d.get('coherence', 0) < threshold]
        self.graph.remove_nodes_from(to_remove)
        return len(to_remove)
