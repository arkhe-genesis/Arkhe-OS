#!/usr/bin/env python3
"""
mcp/context.py — LFIR Context Manager for MCP
Manages conversation contexts as LFIR graphs with Φ_C tracking.
"""
import asyncio
import hashlib
import json
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
import networkx as nx

@dataclass
class ContextNode:
    """A node in the LFIR context graph."""
    node_id: str
    node_type: str  # intent, action, fact, query, response, etc.
    content: Dict[str, Any]
    coherence: float
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class ContextEdge:
    """An edge in the LFIR context graph."""
    source: str
    target: str
    edge_type: str  # depends_on, generates, validates, etc.
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LFIRContext:
    """A conversation context backed by an LFIR graph."""
    context_id: str
    graph: nx.MultiDiGraph
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_coherence(self) -> float:
        """Calculate overall coherence for this context."""
        if not self.graph.nodes:
            return 0.0
        coherences = [self.graph.nodes[n].get("coherence", 0.5) for n in self.graph.nodes]
        return sum(coherences) / len(coherences)

class LFIRContextManager:
    """Manages LFIR-backed contexts for MCP sessions."""

    def __init__(self, max_size: int = 10000, retention_hours: int = 24):
        self.max_size = max_size
        self.retention_seconds = retention_hours * 3600
        self.contexts: Dict[str, LFIRContext] = {}
        self.context_index: Dict[str, List[str]] = defaultdict(list)  # type -> context_ids
        self._cleanup_task: Optional[asyncio.Task] = None

    async def create_context(self,
                            initial_graph: Optional[Dict] = None,
                            metadata: Optional[Dict] = None) -> str:
        """Create a new LFIR context."""
        context_id = str(uuid.uuid4())
        graph = nx.MultiDiGraph()

        # Add initial nodes if provided
        if initial_graph:
            for node_data in initial_graph.get("nodes", []):
                node = ContextNode(**node_data)
                graph.add_node(node.node_id, **node.to_dict())

            for edge_data in initial_graph.get("edges", []):
                edge = ContextEdge(**edge_data)
                graph.add_edge(edge.source, edge.target, **asdict(edge))

        context = LFIRContext(
            context_id=context_id,
            graph=graph,
            metadata=metadata or {}
        )
        self.contexts[context_id] = context

        # Index by node types for faster lookup
        for node_id in graph.nodes:
            node_type = graph.nodes[node_id].get("node_type", "unknown")
            self.context_index[node_type].append(context_id)

        return context_id

    async def update_context(self,
                            context_id: str,
                            additions: Optional[List[Dict]] = None,
                            removals: Optional[List[str]] = None) -> float:
        """Update a context with new nodes/edges or removals."""
        if context_id not in self.contexts:
            raise ValueError(f"Context not found: {context_id}")

        context = self.contexts[context_id]
        old_coherence = context.get_coherence()

        # Add new nodes
        if additions:
            for item in additions:
                if "node_type" in item:  # It's a node
                    node = ContextNode(**item)
                    context.graph.add_node(node.node_id, **node.to_dict())
                    self.context_index[node.node_type].append(context_id)
                elif "edge_type" in item:  # It's an edge
                    edge = ContextEdge(**item)
                    context.graph.add_edge(edge.source, edge.target, **asdict(edge))

        # Remove nodes (and their edges)
        if removals:
            for node_id in removals:
                if node_id in context.graph:
                    node_type = context.graph.nodes[node_id].get("node_type")
                    context.graph.remove_node(node_id)
                    if node_type and context_id in self.context_index[node_type]:
                        self.context_index[node_type].remove(context_id)

        context.last_updated = time.time()
        new_coherence = context.get_coherence()

        # Enforce max size by pruning oldest low-coherence nodes
        await self._enforce_size_limit(context)

        return new_coherence - old_coherence

    async def _enforce_size_limit(self, context: LFIRContext):
        """Prune context if it exceeds max_size, removing lowest coherence nodes first."""
        while len(context.graph.nodes) > self.max_size:
            # Find node with lowest coherence
            lowest = min(
                context.graph.nodes(data=True),
                key=lambda x: x[1].get("coherence", 0)
            )
            node_id = lowest[0]
            context.graph.remove_node(node_id)

    async def get_context_coherence(self, context_id: str) -> float:
        """Get current coherence score for a context."""
        if context_id not in self.contexts:
            return 0.0
        return self.contexts[context_id].get_coherence()

    async def get_current_coherence(self) -> float:
        """Get average coherence across all active contexts."""
        if not self.contexts:
            return 0.0
        coherences = [ctx.get_coherence() for ctx in self.contexts.values()]
        return sum(coherences) / len(coherences)

    async def query_contexts(self,
                            node_type: Optional[str] = None,
                            min_coherence: float = 0.0,
                            limit: int = 10) -> List[Dict]:
        """Query contexts by type and coherence."""
        results = []

        if node_type:
            candidate_contexts = self.context_index.get(node_type, [])
        else:
            candidate_contexts = list(self.contexts.keys())

        for ctx_id in candidate_contexts:
            if ctx_id not in self.contexts:
                continue
            ctx = self.contexts[ctx_id]
            if ctx.get_coherence() >= min_coherence:
                results.append({
                    "context_id": ctx_id,
                    "coherence": ctx.get_coherence(),
                    "node_count": len(ctx.graph.nodes),
                    "last_updated": ctx.last_updated,
                    "metadata": ctx.metadata
                })

        # Sort by coherence descending, then by recency
        results.sort(key=lambda x: (-x["coherence"], -x["last_updated"]))
        return results[:limit]

    async def cleanup(self):
        """Remove expired contexts."""
        now = time.time()
        expired = [
            ctx_id for ctx_id, ctx in self.contexts.items()
            if now - ctx.last_updated > self.retention_seconds
        ]
        for ctx_id in expired:
            del self.contexts[ctx_id]
            # Clean up index
            for node_type in self.context_index:
                if ctx_id in self.context_index[node_type]:
                    self.context_index[node_type].remove(ctx_id)

        if expired:
            print(f"🧹 Cleaned up {len(expired)} expired contexts")

    async def start_cleanup_loop(self, interval_seconds: int = 3600):
        """Start background cleanup task."""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(interval_seconds)
                await self.cleanup()

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    async def stop_cleanup_loop(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
