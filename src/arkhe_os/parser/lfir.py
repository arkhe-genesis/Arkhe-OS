import json
class LFIRNodeType:
    VARIABLE = "VARIABLE"
    BLOCK = "BLOCK"

class LFIRNode:
    def __init__(self, id, node_type, substrate):
        self.id = id
        self.node_type = node_type
        self.substrate = substrate
        self.attributes = {}

class LFIREdge:
    def __init__(self, source, target, relation, weight, attributes=None):
        self.source = source
        self.target = target
        self.relation = relation
        self.weight = weight
        self.attributes = attributes or {}

class LFIRGraph:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.metadata = {}
        self.coherence_score = 0.0

    def add_node(self, node):
        self.nodes.append(node)

    def add_edge(self, edge):
        self.edges.append(edge)

    def to_dict(self):
        return {
            "nodes": [{"id": n.id, "type": n.node_type, "attributes": n.attributes} for n in self.nodes],
            "edges": [{"source": e.source, "target": e.target, "relation": e.relation, "weight": e.weight, "attributes": e.attributes} for e in self.edges],
            "metadata": self.metadata,
            "coherence_score": self.coherence_score
        }

    def to_json(self, path):
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f)

    @classmethod
    def from_json(cls, path):
        with open(path, 'r') as f:
            data = json.load(f)
        graph = cls()
        # simplified mapping back to objects for the sake of the test mocking
        for node_data in data.get("nodes", []):
            node = LFIRNode(node_data["id"], node_data["type"], "reciprocal_nn")
            node.attributes = node_data.get("attributes", {})
            graph.add_node(node)
        for edge_data in data.get("edges", []):
            graph.add_edge(LFIREdge(edge_data["source"], edge_data["target"], edge_data["relation"], edge_data["weight"], edge_data.get("attributes", {})))
        graph.coherence_score = data.get("coherence_score", 0.0)
        return graph