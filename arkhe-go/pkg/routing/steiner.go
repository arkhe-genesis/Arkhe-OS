package routing

import (
	"fmt"
	"math"
)

// ============================================================================
// Steiner Broadcast — Árvore de Steiner para Multicast Ótimo
// ============================================================================

// SteinerNode é um nó na árvore de Steiner.
type SteinerNode struct {
	Name     string
	Children []*SteinerEdge
	Parent   *SteinerEdge
	IsTerminal bool
}

// SteinerEdge é uma aresta na árvore de Steiner.
type SteinerEdge struct {
	Source *SteinerNode
	Target *SteinerNode
	Cost   float64
	Path   []string // Caminho real no grafo
}

// SteinerTree é uma árvore de Steiner.
type SteinerTree struct {
	Root          *SteinerNode
	Terminals     map[string]bool
	TotalCost     float64
	EdgesUsed     []*SteinerEdge
	Savings       float64 // Economia vs unicast
	HopsSaved     int
}

func (t *SteinerTree) String() string {
	return fmt.Sprintf("SteinerTree{cost=%.2f, terminals=%d, savings=%.1f%%}",
		t.TotalCost, len(t.Terminals), t.Savings*100)
}

// SteinerOptimizer implementa a aproximação MST-based.
type SteinerOptimizer struct {
	graph       [][]Edge
	vertexMap   map[string]int
	reverseMap  []string
	distMatrix  map[string]map[string]float64
	pathCache   map[string]map[string][]string
}

// NewSteinerOptimizer cria um novo otimizador.
func NewSteinerOptimizer(
	graph [][]Edge,
	vertexMap map[string]int,
	reverseMap []string,
) *SteinerOptimizer {
	return &SteinerOptimizer{
		graph:      graph,
		vertexMap:  vertexMap,
		reverseMap: reverseMap,
		distMatrix: make(map[string]map[string]float64),
		pathCache:  make(map[string]map[string][]string),
	}
}

func uniqueStrings(arr []string) []string {
	keys := make(map[string]bool)
	list := []string{}
	for _, entry := range arr {
		if _, value := keys[entry]; !value {
			keys[entry] = true
			list = append(list, entry)
		}
	}
	return list
}

// ApproximateSteinerTree constrói aproximação 2× da árvore de Steiner.
//
// Algoritmo:
// 1. Computar all-pairs shortest paths entre {source} ∪ terminals
// 2. Construir grafo completo (MST graph)
// 3. Computar MST do grafo completo (Prim)
// 4. Substituir arestas MST pelos caminhos reais
// 5. Remover ciclos → Árvore de Steiner
func (o *SteinerOptimizer) Approximate(
	source string,
	terminals []string,
) *SteinerTree {
	allNodes := append([]string{source}, terminals...)
	uniqueNodes := uniqueStrings(allNodes)

	// 1. Computar all-pairs shortest paths
	for _, srcStr := range uniqueNodes {
		srcIdx, ok := o.vertexMap[srcStr]
		if !ok {
			continue
		}

		dist := TsinghuaDijkstra(o.graph, srcIdx, nil)
		predecessors := o.dijkstraPredecessors(o.graph, srcIdx, nil)

		o.distMatrix[srcStr] = make(map[string]float64)
		o.pathCache[srcStr] = make(map[string][]string)

		for _, dstStr := range uniqueNodes {
			if srcStr == dstStr {
				o.distMatrix[srcStr][dstStr] = 0
				continue
			}

			dstIdx, ok := o.vertexMap[dstStr]
			if !ok {
				o.distMatrix[srcStr][dstStr] = math.Inf(1)
				continue
			}

			o.distMatrix[srcStr][dstStr] = dist[dstIdx]

			// Reconstruct Path
			pathIdxs := ReconstructPath(predecessors, srcIdx, dstIdx)
			if pathIdxs != nil {
				pathStrs := make([]string, len(pathIdxs))
				for i, idx := range pathIdxs {
					pathStrs[i] = o.reverseMap[idx]
				}
				o.pathCache[srcStr][dstStr] = pathStrs
			}
		}
	}

	// 2 & 3. Computar MST do grafo completo (Prim)
	mstEdges := o.computeMST(uniqueNodes)

	// 4. Expand MST edges to real paths
	treeNodes := make(map[string]*SteinerNode)
	root := &SteinerNode{
		Name: source,
		IsTerminal: true,
	}
	treeNodes[source] = root

	terminalMap := make(map[string]bool)
	for _, term := range terminals {
		terminalMap[term] = true
	}

	var allEdges []*SteinerEdge
	totalCost := 0.0

	// We simply build a directed tree from source outward.
	// This uses BFS or DFS on the MST edges.
	adjacency := make(map[string][]struct{
		to string
		cost float64
	})
	for _, e := range mstEdges {
		adjacency[e.u] = append(adjacency[e.u], struct{to string; cost float64}{e.v, e.w})
		adjacency[e.v] = append(adjacency[e.v], struct{to string; cost float64}{e.u, e.w})
	}

	visited := make(map[string]bool)

	var buildTree func(curr string, parentNode *SteinerNode)
	buildTree = func(curr string, parentNode *SteinerNode) {
		visited[curr] = true

		for _, neighbor := range adjacency[curr] {
			if visited[neighbor.to] {
				continue
			}

			childNode := &SteinerNode{
				Name: neighbor.to,
				IsTerminal: terminalMap[neighbor.to],
			}

			path := o.pathCache[curr][neighbor.to]

			edge := &SteinerEdge{
				Source: parentNode,
				Target: childNode,
				Cost: neighbor.cost,
				Path: path,
			}
			parentNode.Children = append(parentNode.Children, edge)
			childNode.Parent = edge
			allEdges = append(allEdges, edge)
			totalCost += neighbor.cost

			buildTree(neighbor.to, childNode)
		}
	}

	buildTree(source, root)

	return &SteinerTree{
		Root: root,
		Terminals: terminalMap,
		TotalCost: totalCost,
		EdgesUsed: allEdges,
		Savings: 0.0,
		HopsSaved: 0,
	}
}

type mstEdge struct {
	u string
	v string
	w float64
}

func (o *SteinerOptimizer) computeMST(nodes []string) []mstEdge {
	if len(nodes) == 0 {
		return nil
	}

	visited := make(map[string]bool)
	var mst []mstEdge

	// Starts from nodes[0]
	visited[nodes[0]] = true

	for len(visited) < len(nodes) {
		minW := math.Inf(1)
		var bestU, bestV string

		for u := range visited {
			for _, v := range nodes {
				if visited[v] {
					continue
				}

				w := o.distMatrix[u][v]
				if w < minW {
					minW = w
					bestU = u
					bestV = v
				}
			}
		}

		if bestU == "" || bestV == "" {
			break // Disconnected
		}

		mst = append(mst, mstEdge{u: bestU, v: bestV, w: minW})
		visited[bestV] = true
	}

	return mst
}

func (o *SteinerOptimizer) dijkstraPredecessors(
	graph [][]Edge,
	source int,
	oracle OracleEvalFunc,
) []int {
	n := len(graph)
	predecessors := make([]int, n)
	for i := range predecessors {
		predecessors[i] = -1
	}

	dist := make([]float64, n)
	for i := range dist {
		dist[i] = math.Inf(1)
	}
	dist[source] = 0

	heap := NewFibonacciHeap()
	heap.Insert(source, 0, false)

	visited := make([]bool, n)

	for !heap.IsEmpty() {
		u, d, _ := heap.ExtractMin()

		if visited[u] || u < 0 {
			continue
		}
		visited[u] = true

		if d > dist[u] {
			continue
		}

		for _, edge := range graph[u] {
			if visited[edge.To] {
				continue
			}

			w := edge.Weight
			if oracle != nil {
				if report := oracle(u, edge); report.Pruned {
					continue
				} else {
					w = report.AdjW
				}
			}

			newDist := dist[u] + w
			if newDist < dist[edge.To] {
				dist[edge.To] = newDist
				predecessors[edge.To] = u
				heap.DecreaseKeyOrInsert(edge.To, newDist, false)
			}
		}
	}

	return predecessors
}
