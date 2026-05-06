package lfir

// Stub for parser/lfir
// LFIRNodeType is the type of a node in the Lingua Franca Intermediate Representation.
type LFIRNodeType string

const (
	LFIRModule    LFIRNodeType = "LFIRModule"
	LFIROperation LFIRNodeType = "LFIROperation"
	LFIRType      LFIRNodeType = "LFIRType"
	LFIRMetadata  LFIRNodeType = "LFIRMetadata"
)

// LFIRNode represents a node in the intermediate representation graph.
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
	Namespace  string
	Attributes map[string]interface{}
}

// NewLFIRNode creates a new LFIR node.
func NewLFIRNode(nodeType LFIRNodeType, name string, namespace string) *LFIRNode {
	return &LFIRNode{
		ID:         name + "_" + string(nodeType), // Simple ID generation
		Type:       nodeType,
		Name:       name,
		Namespace:  namespace,
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

// LFIRGraph represents the full intermediate representation.
type LFIRGraph struct {
	RootNodes []string
	Nodes     map[string]*LFIRNode
	Edges     map[string][]string // directed edges parent -> children
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

// Link links a parent node to a child node.
func (g *LFIRGraph) Link(parentID, childID string) {
	g.Edges[parentID] = append(g.Edges[parentID], childID)
}
