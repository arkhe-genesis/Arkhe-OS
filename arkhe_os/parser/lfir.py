from enum import Enum, auto
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

class LFIRNodeType(Enum):
    Module = "Module"
    Operation = "Operation"
    Type = "Type"
    Metadata = "Metadata"

@dataclass
class LFIRNode:
    id: str
    type: LFIRNodeType
    source_lang: str
    attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LFIREdge:
    from_id: str
    to_id: str
    attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LFIRGraph:
    nodes: Dict[str, LFIRNode] = field(default_factory=dict)
    edges: List[LFIREdge] = field(default_factory=list)
    root_nodes: List[str] = field(default_factory=list)

    def add_node(self, node: LFIRNode) -> LFIRNode:
        self.nodes[node.id] = node
        return node

    def link(self, from_id: str, to_id: str, attributes: Optional[Dict] = None):
        self.edges.append(LFIREdge(from_id=from_id, to_id=to_id, attributes=attributes or {}))
