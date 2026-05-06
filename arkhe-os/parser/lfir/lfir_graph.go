package lfir

// LFIRNodeType define o tipo de um nó no LFIR Graph
type LFIRNodeType string

const (
	LFIRModule    LFIRNodeType = "LFIRModule"
	LFIROperation LFIRNodeType = "LFIROperation"
	LFIRType      LFIRNodeType = "LFIRType"
	LFIRMetadata  LFIRNodeType = "LFIRMetadata"
)

// LFIRNode representa um nó genérico no grafo LFIR
type LFIRNode struct {
	Type       LFIRNodeType
	ID         string
	SourceLang string
	Attributes map[string]interface{}
}

// NewLFIRNode cria um novo nó LFIR
func NewLFIRNode(nodeType LFIRNodeType, id, sourceLang string) *LFIRNode {
	return &LFIRNode{
		Type:       nodeType,
		ID:         id,
		SourceLang: sourceLang,
		Attributes: make(map[string]interface{}),
	}
}

// LFIRGraph representa o grafo LFIR
type LFIRGraph struct {
	Nodes     []*LFIRNode
	Edges     map[string][]string // childID -> []parentIDs (for dependency graph or vice versa)
	RootNodes []string
}

// NewLFIRGraph cria um novo grafo LFIR
func NewLFIRGraph() *LFIRGraph {
	return &LFIRGraph{
		Nodes:     make([]*LFIRNode, 0),
		Edges:     make(map[string][]string),
		RootNodes: make([]string, 0),
	}
}

// AddNode adiciona um nó ao grafo
func (g *LFIRGraph) AddNode(node *LFIRNode) {
	g.Nodes = append(g.Nodes, node)
}

// Link cria uma aresta (parent -> child)
func (g *LFIRGraph) Link(parentID, childID string) {
	g.Edges[parentID] = append(g.Edges[parentID], childID)
}

// FindNodeByAttribute finds a node by an attribute key/value pair
func (g *LFIRGraph) FindNodeByAttribute(key string, val interface{}) (*LFIRNode, bool) {
	for _, n := range g.Nodes {
		if v, ok := n.Attributes[key]; ok && v == val {
			return n, true
		}
	}
	return nil, false
}
