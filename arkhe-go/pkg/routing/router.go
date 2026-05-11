package routing

import (
	"fmt"
	"math"
	"sync"
	"time"

	arkhecore "github.com/arkhe-os/arkhe-go/pkg/core"
	"github.com/arkhe-os/arkhe-go/pkg/consensus"
	"github.com/arkhe-os/arkhe-go/pkg/consistency"
)

// ============================================================================
// Roteador Temporal ARKHE
// ============================================================================

var (
	ErrRouteNotFound     = fmt.Errorf("rota não encontrada")
	ErrNodeNotFound      = fmt.Errorf("nó não encontrado")
	ErrRouteExpired      = fmt.Errorf("rota expirada")
	ErrInvalidRouteState = fmt.Errorf("estado de rota inválido")

	// TempInf representa infinito temporal (inacessível).
	TempInf = math.Inf(1)
)

// RouteHop representa um salto na rota.
type RouteHop struct {
	Address   arkhecore.Address
	Cost      float64
	Consensus consensus.Score
}

// TemporalRoute é uma rota temporal entre dois nós.
type TemporalRoute struct {
	Source       arkhecore.Address
	Destination  arkhecore.Address
	Hops         []RouteHop
	TotalCost    float64
	MinConsensus consensus.Score
	TTL          int64
	IsValidFlag  bool
	CreatedAt    int64
}

// IsValid verifica se a rota é válida (não expirou).
func (r *TemporalRoute) IsValid(now arkhecore.Timestamp) bool {
	return r.IsValidFlag && now <= arkhecore.Timestamp(r.CreatedAt+r.TTL)
}

// WeightedLength retorna o comprimento ponderado da rota.
func (r *TemporalRoute) WeightedLength() float64 {
	if r.MinConsensus <= 0 {
		return TempInf
	}
	return r.TotalCost / float64(r.MinConsensus)
}

func (r *TemporalRoute) String() string {
	return fmt.Sprintf("Route[%s→%s]: cost=%.4f, consensus=%.4f, hops=%d",
		r.Source[:8], r.Destination[:8],
		r.TotalCost, r.MinConsensus, len(r.Hops))
}

// RouterConfig configura o roteador.
type RouterConfig struct {
	ConsistencyThreshold consensus.Score
	MaxHops              int
	EnableOracle         bool
	ConcurrentSearches   int
}

// DefaultRouterConfig retorna a configuração padrão.
func DefaultRouterConfig() *RouterConfig {
	return &RouterConfig{
		ConsistencyThreshold: consensus.DefaultThresholds().ParadoxFree,
		MaxHops:              50,
		EnableOracle:         true,
		ConcurrentSearches:   4,
	}
}

// TemporalRouter é o roteador temporal do ARKHE.
type TemporalRouter struct {
	cfg     *RouterConfig
	oracle  *consensus.ConsistencyOracle
	forward *consistency.ForwardChecker
	backward *consistency.BackwardChecker

	// Grafo de adjacência: nodeID → lista de arestas
	mu     sync.RWMutex
	graph  map[arkhecore.Address][]EdgeInfo
	nodes  map[arkhecore.Address]NodeInfo

	// Cache de rotas
	routeCache     map[routeKey]*TemporalRoute
	cacheMu        sync.RWMutex
	maxCacheSize   int
}

// EdgeInfo descreve uma aresta no grafo.
type EdgeInfo struct {
	Target     arkhecore.Address
	Weight     float64
	Consistency consensus.Score
	CreatedAt  int64
	Expires    int64
	Meta       EdgeMeta
}

// NodeInfo descreve um nó na rede.
type NodeInfo struct {
	Address     arkhecore.Address
	Type        string
	Position    [3]float64 // Posição em AU
	Consistency consensus.Score
	LastSeen    int64
}

// routeKey é a chave do cache de rotas.
type routeKey struct {
	Source arkhecore.Address
	Dest   arkhecore.Address
}

// NewTemporalRouter cria um novo roteador temporal.
func NewTemporalRouter(cfg *RouterConfig) *TemporalRouter {
	if cfg == nil {
		cfg = DefaultRouterConfig()
	}

	return &TemporalRouter{
		cfg:         cfg,
		oracle:      consensus.NewConsistencyOracle(nil),
		forward:     consistency.NewForwardChecker(&consistency.ForwardCheckConfig{
			ConsistencyThreshold: cfg.ConsistencyThreshold,
			EnableOracle:         cfg.EnableOracle,
		}),
		backward:    consistency.NewBackwardChecker(cfg.ConsistencyThreshold),
		graph:       make(map[arkhecore.Address][]EdgeInfo),
		nodes:       make(map[arkhecore.Address]NodeInfo),
		routeCache:  make(map[routeKey]*TemporalRoute),
		maxCacheSize: 10000,
	}
}

// RegisterNode registra um nó na rede.
func (r *TemporalRouter) RegisterNode(node NodeInfo) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if node.Address == (arkhecore.Address{}) {
		return fmt.Errorf("endereço de nó não pode ser zero")
	}

	r.nodes[node.Address] = node
	if _, exists := r.graph[node.Address]; !exists {
		r.graph[node.Address] = make([]EdgeInfo, 0)
	}

	return nil
}

// AddRoute adiciona uma rota (aresta) ao grafo.
func (r *TemporalRouter) AddRoute(src, dst arkhecore.Address, weight float64, meta EdgeMeta) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if src == dst {
		return fmt.Errorf("rota para o mesmo nó")
	}

	edge := EdgeInfo{
		Target:      dst,
		Weight:      weight,
		Consistency: consensus.Score(meta.Consistency),
		CreatedAt:   meta.CreatedAt,
		Expires:     meta.TTL + meta.CreatedAt,
		Meta:        meta,
	}

	r.graph[src] = append(r.graph[src], edge)

	// Invalidar cache de rotas que passam por src
	r.invalidateCache(src)

	return nil
}

// FindRoute encontra a melhor rota entre dois nós.
func (r *TemporalRouter) FindRoute(source, dest arkhecore.Address) (*TemporalRoute, error) {
	now := arkhecore.Now()

	// Verificar cache primeiro
	if route, ok := r.getCachedRoute(source, dest); ok {
		if route.IsValid(now) {
			return route, nil
		}
		// Rota expirada, remover do cache
		r.deleteCachedRoute(source, dest)
	}

	r.mu.RLock()
	defer r.mu.RUnlock()

	// Verificar se nós existem
	if _, exists := r.nodes[source]; !exists {
		return nil, fmt.Errorf("%w: source %s", ErrNodeNotFound, source)
	}
	if _, exists := r.nodes[dest]; !exists {
		return nil, fmt.Errorf("%w: dest %s", ErrNodeNotFound, dest)
	}

	// Construir grafo para Dijkstra
	graph := r.buildDijkstraGraph()

	// Configurar Oracle
	var oracle OracleEvalFunc
	var oraclePtr *OracleEvalFunc
	if r.cfg.EnableOracle {
		oracle = r.oracleEvalFunc()
		oraclePtr = &oracle
	}

	// Executar Dijkstra
	dist := TsinghuaDijkstra(graph, r.nodeIndex(source), oraclePtr)

	destIdx := r.nodeIndex(dest)
	if dist[destIdx] == math.Inf(1) {
		return nil, ErrRouteNotFound
	}

	// Reconstruir caminho
	predecessors := r.dijkstraPredecessors(graph, r.nodeIndex(source), oracle)
	path := ReconstructPath(predecessors, r.nodeIndex(source), destIdx)

	if path == nil {
		return nil, ErrRouteNotFound
	}

	// Construir rota
	route := &TemporalRoute{
		Source:      source,
		Destination: dest,
		TotalCost:   dist[destIdx],
		TTL:         3600 * int64(arkhecore.BlockInterval/1e9),
		CreatedAt:   int64(now),
			IsValidFlag:     true,
	}

	// Preencher hops
	minCons := consensus.ScoreTop
	for _, nodeIdx := range path {
		addr := r.indexToAddress(nodeIdx)
		hop := RouteHop{
			Address: addr,
		}

		// Obter score de consistência
		if nodeInfo, ok := r.nodes[addr]; ok {
			hop.Consensus = nodeInfo.Consistency
			hop.Cost = 0 // Será preenchido pela distância
			if nodeInfo.Consistency < minCons {
				minCons = nodeInfo.Consistency
			}
		}

		route.Hops = append(route.Hops, hop)
	}

	route.MinConsensus = minCons

	// Verificar consistência forward
	for _, hop := range route.Hops {
		_ = hop // Em produção: verificar cada hop
	}

	// Cache
	r.cacheRoute(source, dest, route)

	return route, nil
}

// FindRoutes encontra rotas para múltiplos destinos (batch).
func (r *TemporalRouter) FindRoutes(
	source arkhecore.Address,
	destinations []arkhecore.Address,
) ([]*TemporalRoute, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	graph := r.buildDijkstraGraph()
	var oracle OracleEvalFunc
	var oraclePtr *OracleEvalFunc
	if r.cfg.EnableOracle {
		oracle = r.oracleEvalFunc()
		oraclePtr = &oracle
	}

	srcIdx := r.nodeIndex(source)
	dist := TsinghuaDijkstra(graph, srcIdx, oraclePtr)

	results := make([]*TemporalRoute, len(destinations))
	for i, dest := range destinations {
		destIdx := r.nodeIndex(dest)
		if destIdx < 0 || dist[destIdx] == math.Inf(1) {
			results[i] = nil
			continue
		}

		predecessors := r.dijkstraPredecessors(graph, srcIdx, oracle)
		path := ReconstructPath(predecessors, srcIdx, destIdx)

		if path == nil {
			results[i] = nil
			continue
		}

		route := &TemporalRoute{
			Source:      source,
			Destination: dest,
			TotalCost:   dist[destIdx],
			TTL:         3600,
			CreatedAt:   int64(arkhecore.Now()),
			IsValidFlag: true,
			Hops:        make([]RouteHop, len(path)),
		}

		for j, idx := range path {
			route.Hops[j].Address = r.indexToAddress(idx)
		}

		results[i] = route
	}

	return results, nil
}

// FindOptimalMulticast encontra a árvore de multicast ótima.
// Usa aproximação de Steiner com fator 2.
func (r *TemporalRouter) FindOptimalMulticast(
	source arkhecore.Address,
	destinations []arkhecore.Address,
) (*SteinerTree, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// 1. Build string map
	vertexMap := make(map[string]int)
	reverseMap := make([]string, len(r.nodes))

	i := 0
	for addr := range r.nodes {
		addrStr := addr.String()
		vertexMap[addrStr] = i
		reverseMap[i] = addrStr
		i++
	}

	// 2. Map nodes to graphs
	graph := r.buildDijkstraGraph()

	// 3. String representations
	srcStr := source.String()
	destStrs := make([]string, len(destinations))
	for j, dest := range destinations {
		destStrs[j] = dest.String()
	}

	opt := NewSteinerOptimizer(graph, vertexMap, reverseMap)
	tree := opt.Approximate(srcStr, destStrs)
	if tree == nil {
		return nil, fmt.Errorf("não foi possível construir árvore de Steiner")
	}

	return tree, nil
}

// ============================================================================
// Helpers internos
// ============================================================================

func (r *TemporalRouter) buildDijkstraGraph() [][]Edge {
	r.mu.RLock()
	defer r.mu.RUnlock()

	n := len(r.nodes)
	indexMap := make(map[arkhecore.Address]int, n)
	reverseMap := make(map[int]arkhecore.Address, n)

	i := 0
	for addr := range r.nodes {
		indexMap[addr] = i
		reverseMap[i] = addr
		i++
	}

	graph := make([][]Edge, n)
	for addr, edges := range r.graph {
		srcIdx, ok := indexMap[addr]
		if !ok {
			continue
		}
		graph[srcIdx] = make([]Edge, 0, len(edges))
		for _, e := range edges {
			dstIdx, ok := indexMap[e.Target]
			if !ok {
				continue
			}
			graph[srcIdx] = append(graph[srcIdx], Edge{
				To:     dstIdx,
				Weight: e.Weight,
				Meta:   e.Meta,
			})
		}
	}

	return graph
}

func (r *TemporalRouter) oracleEvalFunc() OracleEvalFunc {
	return func(from int, edge Edge) *OracleEvalReport {
		// Converter para endereços ARKHE
		r.mu.RLock()
		reverseMap := r.buildReverseMap()
		r.mu.RUnlock()

		srcAddr, srcOk := reverseMap[from]
		dstAddr, dstOk := reverseMap[edge.To]

		if !srcOk || !dstOk {
			return &OracleEvalReport{
				Pruned: true,
				Reason: "nó não encontrado",
				AdjW:   math.Inf(1),
			}
		}

		// Avaliar pelo Oracle
		// Nota: em produção, usar o oracle real aqui
		_ = srcAddr
		_ = dstAddr

		score := consensus.ScoreTop
		var violations []string

		// Check de expiração
		if (edge.Meta.TTL + edge.Meta.CreatedAt) > 0 && time.Now().Unix() > (edge.Meta.TTL + edge.Meta.CreatedAt) {
			violations = append(violations, "aresta expirada")
			score = 0
		}

		// Check de consistência
		if edge.Meta.Consistency < 0.3 {
			violations = append(violations, "consistência muito baixa")
			score = min(score, consensus.Score(edge.Meta.Consistency))
		}

		return &OracleEvalReport{
			From:     from,
			To:       edge.To,
			Score:    float64(score),
			Pruned:   score < r.cfg.ConsistencyThreshold,
			Reason:   func() string {
				if len(violations) > 0 {
					return violations[0]
				}
				return ""
			}(),
			AdjW: func() float64 {
				if score <= 0 {
					return math.Inf(1)
				}
				return edge.Weight / float64(max(float64(score), 0.001))
			}(),
		}
	}
}

func (r *TemporalRouter) buildReverseMap() map[int]arkhecore.Address {
	result := make(map[int]arkhecore.Address, len(r.nodes))
	i := 0
	for addr := range r.nodes {
		result[i] = addr
		i++
	}
	return result
}

func (r *TemporalRouter) nodeIndex(addr arkhecore.Address) int {
	r.mu.RLock()
	defer r.mu.RUnlock()

	i := 0
	for a := range r.nodes {
		if a == addr {
			return i
		}
		i++
	}
	return -1
}

func (r *TemporalRouter) indexToAddress(idx int) arkhecore.Address {
	r.mu.RLock()
	defer r.mu.RUnlock()

	i := 0
	for addr := range r.nodes {
		if i == idx {
			return addr
		}
		i++
	}
	return arkhecore.Address{}
}

func (r *TemporalRouter) dijkstraPredecessors(
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

func (r *TemporalRouter) invalidateCache(addr arkhecore.Address) {
	r.cacheMu.Lock()
	defer r.cacheMu.Unlock()

	for key := range r.routeCache {
		if key.Source == addr || key.Dest == addr {
			delete(r.routeCache, key)
		}
	}
}

func (r *TemporalRouter) getCachedRoute(
	src, dst arkhecore.Address,
) (*TemporalRoute, bool) {
	r.cacheMu.RLock()
	defer r.cacheMu.RUnlock()

	route, exists := r.routeCache[routeKey{src, dst}]
	return route, exists
}

func (r *TemporalRouter) cacheRoute(
	src, dst arkhecore.Address,
	route *TemporalRoute,
) {
	r.cacheMu.Lock()
	defer r.cacheMu.Unlock()

	// Limitar tamanho do cache
	if len(r.routeCache) >= r.maxCacheSize {
		// Remover 10% mais antigos (simplificado)
		for key := range r.routeCache {
			delete(r.routeCache, key)
			if len(r.routeCache) < r.maxCacheSize*9/10 {
				break
			}
		}
	}

	r.routeCache[routeKey{src, dst}] = route
}

func (r *TemporalRouter) deleteCachedRoute(
	src, dst arkhecore.Address,
) {
	r.cacheMu.Lock()
	delete(r.routeCache, routeKey{src, dst})
	r.cacheMu.Unlock()
}

// ============================================================================
// Métricas de Roteamento
// ============================================================================

// RouterMetrics contém métricas do roteador.
type RouterMetrics struct {
	TotalRoutes     uint64
	CacheHits       uint64
	CacheMisses     uint64
	OracleEvals     uint64
	OraclePruned    uint64
	AvgRouteTimeMs  float64
	ActiveNodes     int
	ActiveEdges     int
}

// GetMetrics retorna as métricas atuais.
func (r *TemporalRouter) GetMetrics() *RouterMetrics {
	r.mu.RLock()
	defer r.mu.RUnlock()

	return &RouterMetrics{
		ActiveNodes: len(r.nodes),
		ActiveEdges: len(r.graph),
	}
}
