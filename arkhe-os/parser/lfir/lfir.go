package lfir

import (
	"encoding/json"
	"os"
)

// LFIRNodeType is the type of a node in the Lingua Franca Intermediate Representation.
type LFIRNodeType string

const (
	LFIRNodeTypeModule     LFIRNodeType = "LFIRModule"
	LFIRNodeTypeOperation  LFIRNodeType = "LFIROperation"
	LFIRNodeTypeType       LFIRNodeType = "LFIRType"
	LFIRNodeTypeMetadata   LFIRNodeType = "LFIRMetadata"
	LFIRNodeTypeCall       LFIRNodeType = "LFIRCall"
	LFIRNodeTypeExpr       LFIRNodeType = "LFIRExpr"
	LFIRNodeTypeDependency LFIRNodeType = "LFIRDependency"
	LFIRNodeTypeProperty   LFIRNodeType = "LFIRProperty"
)

type LFIREdge struct {
	ID     string
	Source string
	Target string
	Type   string
}

type LFIRMetrics struct {
	CoherenceScore     float64
	SemanticDensity    float64
	AccessibilityScore float64
	NodeCount          int
	EdgeCount          int
}

type LFIRNode struct {
	ID         string
	Type       LFIRNodeType
	Name       string
	SourceLang string
	Namespace  string
	Attributes map[string]interface{}
}

// NewLFIRNode creates a new LFIR node.
func NewLFIRNode(nodeType LFIRNodeType, name string, sourceLang string) *LFIRNode {
	return &LFIRNode{
		ID:         name + "_" + string(nodeType),
		Type:       nodeType,
		Name:       name,
		SourceLang: sourceLang,
		Attributes: make(map[string]interface{}),
	}
}

// LFIRGraph represents the full intermediate representation.
type LFIRGraph struct {
	RootNodes []string
	Nodes     []*LFIRNode
	Edges     []*LFIREdge
	Metrics   LFIRMetrics
}

func NewLFIRGraph() *LFIRGraph {
	return &LFIRGraph{
		RootNodes: make([]string, 0),
		Nodes:     make([]*LFIRNode, 0),
		Edges:     make([]*LFIREdge, 0),
	}
}

// AddNode adds a node to the graph.
func (g *LFIRGraph) AddNode(node *LFIRNode) {
	g.Nodes = append(g.Nodes, node)
}

func (g *LFIRGraph) Link(parentID, childID string) {
	g.Edges = append(g.Edges, &LFIREdge{Source: parentID, Target: childID})
}

func (g *LFIRGraph) ToJSONFile(path string) error {
	b, err := json.MarshalIndent(g, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, b, 0644)
}

func (g *LFIRGraph) FindNodeByAttribute(key string, val interface{}) (*LFIRNode, bool) {
	for _, n := range g.Nodes {
		if v, ok := n.Attributes[key]; ok && v == val {
			return n, true
		}
	}
	return nil, false
}
