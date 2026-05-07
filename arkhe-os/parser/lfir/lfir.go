package lfir

// This file had some conflicting declarations, we'll just keep what we need.
import (
	"encoding/json"
	"os"
)

// LFIRNodeType is the type of a node in the Lingua Franca Intermediate Representation.
type LFIRNodeType string

const (
	NodeTypeSystem        LFIRNodeType = "LFIRNodeTypeSystem"
	LFIRNodeTypeModule    LFIRNodeType = "LFIRModule"
	LFIRNodeTypeOperation LFIRNodeType = "LFIROperation"
	LFIRNodeTypeType      LFIRNodeType = "LFIRType"
	LFIRNodeTypeMetadata  LFIRNodeType = "LFIRMetadata"
	LFIRNodeTypeCall      LFIRNodeType = "LFIRCall"
	LFIRNodeTypeExpr      LFIRNodeType = "LFIRExpr"
	LFIROperation         LFIRNodeType = "LFIROperation"
	LFIRType              LFIRNodeType = "LFIRType"
	LFIRMetadata          LFIRNodeType = "LFIRMetadata"
)

import "encoding/json"
import "os"

// LFIRNodeType is the type of a node in the Lingua Franca Intermediate Representation.
type LFIRNodeType string

const (
	LFIRNodeTypeModule    LFIRNodeType = "LFIRNodeTypeModule"
    LFIRModule LFIRNodeType = "LFIRModule"
	LFIRNodeTypeModule    LFIRNodeType = "LFIRModule"
	LFIRNodeTypeDependency LFIRNodeType = "LFIRDependency"
	LFIRNodeTypeProperty LFIRNodeType = "LFIRProperty"
	LFIROperation LFIRNodeType = "LFIROperation"
	LFIRType      LFIRNodeType = "LFIRType"
	LFIRMetadata  LFIRNodeType = "LFIRMetadata"
    LFIRNodeTypeDependency LFIRNodeType = "LFIRDependency"
	LFIRNodeTypeComponent LFIRNodeType = "LFIRComponent"
)

type LFIRNode struct {
	ID         string
	Type       LFIRNodeType
	Name       string
	SourceLang string
	Namespace  string
	Attributes map[string]interface{}
}

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
type LFIRMetrics struct {
    CoherenceScore float64
    NodeCount int
    EdgeCount int
	Metrics   LFIRMetrics
}

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

func (g *LFIRGraph) Link(parentID, childID string) {
	g.Edges[parentID] = append(g.Edges[parentID], childID)
}

func (g *LFIRGraph) FindNodeByAttribute(key string, val interface{}) (*LFIRNode, bool) {
	for _, n := range g.Nodes {
		if v, ok := n.Attributes[key]; ok && v == val {
			return n, true
		}
	}
	return nil, false
}

func (g *LFIRGraph) ToJSONFile(filepath string) error {
	data, err := json.MarshalIndent(g, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(filepath, data, 0644)
}

func (g *LFIRGraph) FindNodeByAttribute(key string, value interface{}) (*LFIRNode, bool) {
	for _, node := range g.Nodes {
		if val, exists := node.Attributes[key]; exists && val == value {
			return node, true
		}
	}
	return nil, false
}
