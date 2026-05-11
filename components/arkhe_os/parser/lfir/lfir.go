package lfir

import "sync"

// LFIRNodeType define tipos de nós LFIR
type LFIRNodeType string

const (
	LFIRModule    LFIRNodeType = "module"
	LFIRFunction  LFIRNodeType = "function"
	LFIRType      LFIRNodeType = "type"
	LFIROperation LFIRNodeType = "operation"
	LFIRMetadata  LFIRNodeType = "metadata"
)

// LFIRNode representa um nó do Lingua Franca IR
type LFIRNode struct {
	ID           string
	Type         LFIRNodeType
	Name         string
	SourceLang   string
	Attributes   map[string]interface{}
	Children     []string
	EnergyCost   float64
	PhiOptimized bool
}

// NewLFIRNode cria um novo nó
func NewLFIRNode(nodeType LFIRNodeType, name, lang string) *LFIRNode {
	return &LFIRNode{
		ID:         name + "_id", // simplificado para o exemplo
		Type:       nodeType,
		Name:       name,
		SourceLang: lang,
		Attributes: make(map[string]interface{}),
	}
}

type Metrics struct {
	ParseTimeMs      float64
	TotalNodes       int
	PhiOptimizations int
	AvgEnergyCost    float64
}

// LFIRGraph gerencia o grafo completo
type LFIRGraph struct {
	Nodes     map[string]*LFIRNode
	RootNodes []string
	Metrics   Metrics
	Mu        sync.Mutex
}

func NewLFIRGraph() *LFIRGraph {
	return &LFIRGraph{
		Nodes: make(map[string]*LFIRNode),
	}
}

func (g *LFIRGraph) AddNode(node *LFIRNode) {
	g.Mu.Lock()
	defer g.Mu.Unlock()
	g.Nodes[node.ID] = node
}

func (g *LFIRGraph) Link(parentID, childID string) {
	g.Mu.Lock()
	defer g.Mu.Unlock()
	if parent, ok := g.Nodes[parentID]; ok {
		parent.Children = append(parent.Children, childID)
	}
}
const LFIRNetworkTopology LFIRNodeType = "network_topology"
