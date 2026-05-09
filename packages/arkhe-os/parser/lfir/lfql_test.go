package lfir

import (
	"testing"
)

func TestExecuteLFQL(t *testing.T) {
	graph := NewLFIRGraph()

	node1 := NewLFIRNode(LFIRNodeTypeOperation, "api_endpoint", "go")
	node1.Attributes["priority"] = "critical"
	graph.AddNode(node1)

	node2 := NewLFIRNode(LFIRNodeTypeOperation, "api_endpoint", "go")
	node2.Attributes["priority"] = "low"
	graph.AddNode(node2)

	graph.Metrics.CoherenceScore = 0.95

	query := `
		SELECT node.id, node.label, metric.coherence_score
		WHERE (n:api_endpoint {priority: "critical"})
		ORDER BY metric.coherence_score DESC
		LIMIT 5
	`

	res, err := ExecuteLFQL(graph, query)
	if err != nil {
		t.Fatalf("ExecuteLFQL failed: %v", err)
	}

	if len(res.Nodes) != 1 {
		t.Errorf("Expected 1 node, got %d", len(res.Nodes))
	}
	if len(res.Nodes) > 0 && res.Nodes[0].ID != node1.ID {
		t.Errorf("Expected node ID %s, got %s", node1.ID, res.Nodes[0].ID)
	}
	if res.Metrics["coherence_score"] != 0.95 {
		t.Errorf("Expected coherence_score 0.95, got %f", res.Metrics["coherence_score"])
	}
}
