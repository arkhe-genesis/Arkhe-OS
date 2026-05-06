package lfir

type LFIRNodeType int

const (
	LFIRModule LFIRNodeType = iota
	LFIRType
	LFIRMetadata
	LFIROperation
)

type LFIRNode struct {
	ID         string
	Type       LFIRNodeType
	Name       string
	Attributes map[string]interface{}
}

func NewLFIRNode(nodeType LFIRNodeType, name, context string) *LFIRNode {
	return &LFIRNode{
		ID:         name + "_" + context,
		Type:       nodeType,
		Name:       name,
		Attributes: make(map[string]interface{}),
	}
}

type LFIRGraph struct {
	Nodes     map[string]*LFIRNode
	Edges     map[string][]string
	RootNodes []string
}

func NewLFIRGraph() *LFIRGraph {
	return &LFIRGraph{
		Nodes: make(map[string]*LFIRNode),
		Edges: make(map[string][]string),
	}
}

func (g *LFIRGraph) AddNode(node *LFIRNode) {
	g.Nodes[node.ID] = node
}

func (g *LFIRGraph) Link(parentID, childID string) {
	g.Edges[parentID] = append(g.Edges[parentID], childID)
}
