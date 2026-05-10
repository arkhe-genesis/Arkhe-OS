#!/usr/bin/env python3
"""
agi/system32/lfir/graph_engine.py — LFIR Graph Engine Core
Substrate: Logical Form Intermediate Representation (300)
"""
import hashlib
import json
import networkx as nx
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path

@dataclass
class LFIRNode:
    """A node in the LFIR graph."""
    node_id: str
    node_type: str  # intent, action, fact, query, etc.
    content: Dict[str, Any]
    coherence: float = 0.5
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class LFIREdge:
    """An edge in the LFIR graph."""
    source: str
    target: str
    edge_type: str  # depends_on, generates, validates, etc.
    weight: float = 1.0
    meta: Dict[str, Any] = field(default_factory=dict)

class LFIRGraphEngine:
    """
    Engine for creating, manipulating, and querying LFIR graphs.

    LFIR (Logical Form Intermediate Representation) is the canonical
    graph format for representing AGI intentions, reasoning chains,
    and knowledge structures.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.graphs: Dict[str, nx.MultiDiGraph] = {}
        self.node_counter = 0

    def create_graph(self, graph_id: Optional[str] = None) -> str:
        """Create a new empty LFIR graph."""
        graph_id = graph_id or f"lfir_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]}"
        self.graphs[graph_id] = nx.MultiDiGraph()
        return graph_id

    def add_node(self, graph_id: str, node: LFIRNode) -> str:
        """Add a node to a graph."""
        if graph_id not in self.graphs:
            raise ValueError(f"Graph not found: {graph_id}")

        self.graphs[graph_id].add_node(node.node_id, **node.to_dict())
        return node.node_id

    def add_edge(self, graph_id: str, edge: LFIREdge):
        """Add an edge to a graph."""
        if graph_id not in self.graphs:
            raise ValueError(f"Graph not found: {graph_id}")

        self.graphs[graph_id].add_edge(edge.source, edge.target, **asdict(edge))

    def tokenize_intention(self, intention: str) -> str:
        """Convert natural language intention to LFIR graph."""
        graph_id = self.create_graph()

        # Create root intent node
        root = LFIRNode(
            node_id=f"intent_{self.node_counter}",
            node_type="intent",
            content={"text": intention, "parsed": True},
            coherence=0.8
        )
        self.node_counter += 1
        self.add_node(graph_id, root)

        # Simplified: in production, use NLP parser to extract structure
        # For now, create a minimal graph
        action = LFIRNode(
            node_id=f"action_{self.node_counter}",
            node_type="action",
            content={"verb": "process", "object": "intention"},
            coherence=0.75
        )
        self.node_counter += 1
        self.add_node(graph_id, action)

        # Connect nodes
        self.add_edge(graph_id, LFIREdge(
            source=root.node_id,
            target=action.node_id,
            edge_type="generates",
            weight=1.0
        ))

        return graph_id

    def query(self, graph_id: str, node_id: Optional[str] = None) -> Dict:
        """Query a graph or specific node."""
        if graph_id not in self.graphs:
            return {"error": f"Graph not found: {graph_id}"}

        graph = self.graphs[graph_id]

        if node_id:
            if node_id not in graph:
                return {"error": f"Node not found: {node_id}"}
            return graph.nodes[node_id]

        # Return graph summary
        return {
            "graph_id": graph_id,
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "avg_coherence": float(np.mean([
                d.get("coherence", 0.5) for _, d in graph.nodes(data=True)
            ])) if graph.nodes else 0.0,
        }

    def summary(self) -> Dict:
        """Return summary of all graphs."""
        return {
            "total_graphs": len(self.graphs),
            "total_nodes": sum(g.number_of_nodes() for g in self.graphs.values()),
            "total_edges": sum(g.number_of_edges() for g in self.graphs.values()),
        }

    @property
    def node_count(self) -> int:
        """Total nodes across all graphs."""
        return sum(g.number_of_nodes() for g in self.graphs.values())

    def export(self, graph_id: str, format: str = "json") -> str:
        """Export a graph to specified format."""
        if graph_id not in self.graphs:
            raise ValueError(f"Graph not found: {graph_id}")

        graph = self.graphs[graph_id]

        if format == "json":
            data = {
                "graph_id": graph_id,
                "nodes": {n: d for n, d in graph.nodes(data=True)},
                "edges": [asdict(e) for e in graph.edges(data=True)],
            }
            return json.dumps(data, indent=2)
        elif format == "graphml":
            # Would use networkx.write_graphml in production
            return f"<graphml>...{graph_id}...</graphml>"
        else:
            raise ValueError(f"Unsupported export format: {format}")
