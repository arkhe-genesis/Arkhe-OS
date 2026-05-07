package lfir

import "encoding/json"
import "os"

// LFIRNodeType is the type of a node in the Lingua Franca Intermediate Representation.
type LFIRNodeType string

const (
	LFIRNodeTypeModule    LFIRNodeType = "LFIRModule"
	LFIROperation LFIRNodeType = "LFIROperation"
	LFIRType      LFIRNodeType = "LFIRType"
	LFIRMetadata  LFIRNodeType = "LFIRMetadata"
)

type LFIRNode struct {
	ID         string
	Type       LFIRNodeType
	Name       string
	SourceLang  string
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

type LFIRMetrics struct {
	CoherenceScore float64
	NodeCount      int
	EdgeCount      int
}

// LFIRGraph represents the full intermediate representation.
type LFIRGraph struct {
	RootNodes []string
	Nodes     map[string]*LFIRNode
	Edges     map[string][]string // directed edges parent -> children
	Metrics   LFIRMetrics
}

// NewLFIRGraph creates a new LFIR graph.
func NewLFIRGraph() *LFIRGraph {
	return &LFIRGraph{
		RootNodes: make([]string, 0),
		Nodes:     make(map[string]*LFIRNode),
		Edges:     make(map[string][]string),
	}
}

// AddNode adds a node to the graph.
func (g *LFIRGraph) AddNode(node *LFIRNode) {
	g.Nodes[node.ID] = node
}

// Link links a parent node to a child node.
func (g *LFIRGraph) Link(parentID, childID string) {
	g.Edges[parentID] = append(g.Edges[parentID], childID)
}

func (g *LFIRGraph) ToJSONFile(filepath string) error {
	data, err := json.MarshalIndent(g, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(filepath, data, 0644)
}
