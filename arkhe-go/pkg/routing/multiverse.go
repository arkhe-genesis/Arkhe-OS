package routing

import (
	"crypto/sha512"
	"fmt"
	"math"
	"math/rand"
	"sync"
	"time"
)

// ============================================================================
// MultiverseRouter — Escala Atômica (10^9 nós)
// ============================================================================

const (
	MaxNodesPerShard      = 1_000_000 // 10^6 por shard
	BorderNodeRatio       = 0.01      // 1% border nodes
	CrossShardCacheTTL    = 60        // segundos
	MaxCrossShardHops     = 3
)

// ShardType define o tipo de shard.
type ShardType int

const (
	SpatialShard    ShardType = iota // Por região espacial
	TemporalShardType                // Por epoch temporal
	TopologicalShard                 // Por tipo de nó
)

// ShardConfig configuração de um shard.
type ShardConfig struct {
	ID            int
	Type          ShardType
	Region        string
	EpochStart    int64
	EpochEnd      int64
	Capacity      int
	BorderRatio   float64
	CacheTTLSeconds int
}

// AtomicNode representa um nó atômico no multiverso.
type AtomicNode struct {
	Name           string
	ShardID        int
	Type           string // "star", "colony", "relay", "probe", "abstract"
	PositionAU     [3]float64
	Consistency    float64
	CreatedAt      int64
	Expires        int64
	MetadataHash   string
	IsBorder       bool
	NeighborCount  int
}

// IsExpired verifica se o nó expirou.
func (n *AtomicNode) IsExpired() bool {
	return time.Now().Unix() > n.Expires
}

// Key retorna a chave única do nó.
func (n *AtomicNode) Key() string {
	return fmt.Sprintf("%d:%s", n.ShardID, n.Name)
}

// TemporalShard é um subgrafo do multiverso.
type TemporalShard struct {
	config    ShardConfig
	nodes     map[string]*AtomicNode
	adjacency map[int][]ShardEdge // índice → arestas

	indexMap     map[string]int    // nome → índice
	reverseMap   map[int]string    // índice → nome
	nextIndex    int

	borderNodes      map[string]bool
	crossShardEdges  []CrossShardEdge

	consistencySum float64
	edgeCount      int

	mu sync.RWMutex
}

// ShardEdge é uma aresta interna de um shard.
type ShardEdge struct {
	Target   int
	Weight   float64
	EdgeHash uint32
}

// CrossShardEdge é uma aresta entre shards.
type CrossShardEdge struct {
	LocalNode  string
	RemoteNode string
	Weight     float64
}

// NewTemporalShard cria um novo shard.
func NewTemporalShard(cfg ShardConfig) *TemporalShard {
	return &TemporalShard{
		config:       cfg,
		nodes:        make(map[string]*AtomicNode),
		adjacency:    make(map[int][]ShardEdge),
		indexMap:     make(map[string]int),
		reverseMap:   make(map[int]string),
		borderNodes:  make(map[string]bool),
		crossShardEdges: make([]CrossShardEdge, 0),
	}
}

// AddNode adiciona um nó ao shard.
func (s *TemporalShard) AddNode(node *AtomicNode) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if len(s.nodes) >= s.config.Capacity {
		return fmt.Errorf("shard %d está cheio (%d/%d)",
			s.config.ID, len(s.nodes), s.config.Capacity)
	}

	if _, exists := s.nodes[node.Name]; exists {
		return fmt.Errorf("nó %s já existe no shard %d", node.Name, s.config.ID)
	}

	s.nodes[node.Name] = node
	idx := s.nextIndex
	s.indexMap[node.Name] = idx
	s.reverseMap[idx] = node.Name
	s.nextIndex++

	if node.IsBorder {
		s.borderNodes[node.Name] = true
	}

	s.consistencySum += node.Consistency

	return nil
}

// AddInternalEdge adiciona aresta interna.
func (s *TemporalShard) AddInternalEdge(src, dst string, weight float64) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	srcIdx, srcOk := s.indexMap[src]
	dstIdx, dstOk := s.indexMap[dst]

	if !srcOk || !dstOk {
		return fmt.Errorf("nó não encontrado no shard")
	}

	edgeHash := uint32(weight * 1000) // Simplificado

	s.adjacency[srcIdx] = append(s.adjacency[srcIdx], ShardEdge{
		Target:   dstIdx,
		Weight:   weight,
		EdgeHash: edgeHash,
	})

	s.edgeCount++

	// Atualizar vizinhos
	if node, ok := s.nodes[src]; ok {
		node.NeighborCount++
	}

	return nil
}

// AddCrossShardEdge registra aresta cross-shard.
func (s *TemporalShard) AddCrossShardEdge(local, remote string, weight float64) {
	s.crossShardEdges = append(s.crossShardEdges, CrossShardEdge{
		LocalNode:  local,
		RemoteNode: remote,
		Weight:     weight,
	})
}

// GetNeighbors retorna vizinhos de um nó.
func (s *TemporalShard) GetNeighbors(node string) []struct {
	Name   string
	Weight float64
} {
	s.mu.RLock()
	defer s.mu.RUnlock()

	idx, ok := s.indexMap[node]
	if !ok {
		return nil
	}

	edges := s.adjacency[idx]
	result := make([]struct {
		Name   string
		Weight float64
	}, len(edges))

	for i, e := range edges {
		result[i].Name = s.reverseMap[e.Target]
		result[i].Weight = e.Weight
	}

	return result
}

// FindLocalRoute encontra rota dentro do shard.
func (s *TemporalShard) FindLocalRoute(source, dest string) []string {
	s.mu.RLock()
	defer s.mu.RUnlock()

	srcIdx, srcOk := s.indexMap[source]
	dstIdx, dstOk := s.indexMap[dest]

	if !srcOk || !dstOk {
		return nil
	}

	if srcIdx == dstIdx {
		return []string{source}
	}

	// Dijkstra simplificado
	dist := make(map[int]float64)
	prev := make(map[int]int)
	visited := make(map[int]bool)

	dist[srcIdx] = 0

	pq := NewFibonacciHeap()
	pq.Insert(srcIdx, 0, false)

	for !pq.IsEmpty() {
		u, d, _ := pq.ExtractMin()
		if visited[u] {
			continue
		}
		visited[u] = true

		if u == dstIdx {
			break
		}

		for _, edge := range s.adjacency[u] {
			if visited[edge.Target] {
				continue
			}

			newDist := d + edge.Weight
			if newDist < dist[edge.Target] || dist[edge.Target] == 0 {
				dist[edge.Target] = newDist
				prev[edge.Target] = u
				pq.DecreaseKeyOrInsert(edge.Target, newDist, false)
			}
		}
	}

	// Reconstruir caminho
	path := []string{}
	current := dstIdx
	for current != srcIdx {
		path = append([]string{s.reverseMap[current]}, path...)
		p, ok := prev[current]
		if !ok {
			return nil
		}
		current = p
	}
	path = append([]string{source}, path...)

	return path
}

// Stats retorna estatísticas do shard.
func (s *TemporalShard) Stats() map[string]interface{} {
	s.mu.RLock()
	defer s.mu.RUnlock()

	return map[string]interface{}{
		"id":            s.config.ID,
		"type":          s.config.Type,
		"region":        s.config.Region,
		"nodes":         len(s.nodes),
		"edges":         s.edgeCount,
		"border_nodes":  len(s.borderNodes),
		"cross_shards":  len(s.crossShardEdges),
		"mean_conc":     s.consistencySum / math.Max(float64(len(s.nodes)), 1),
	}
}

// AtomicMultiverseRouter gerencia múltiplos shards.
type AtomicMultiverseRouter struct {
	totalCapacity int
	numShards     int

	shards map[int]*TemporalShard
	assignments map[string]int // nome do nó → shard ID

	// Cache cross-shard
	cache   map[string]*RouteCacheEntry
	cacheMu sync.RWMutex

	// Global border graph
	borderGraph map[string][]BorderEdge
	borderMu    sync.RWMutex

	stats struct {
		totalRoutes    uint64
		interShard     uint64
		totalTimeMs    float64
	}

	mu sync.RWMutex
}

// RouteCacheEntry é uma entrada no cache de rotas.
type RouteCacheEntry struct {
	Route    []string
	Cost     float64
	ExpiryAt int64
}

// BorderEdge é uma aresta no grafo de border nodes.
type BorderEdge struct {
	Target string
	Weight float64
}

// NewAtomicMultiverseRouter cria um novo router com capacidade para N nós.
func NewAtomicMultiverseRouter(totalCapacity int) *AtomicMultiverseRouter {
	numShards := int(math.Ceil(float64(totalCapacity) / MaxNodesPerShard))

	return &AtomicMultiverseRouter{
		totalCapacity: totalCapacity,
		numShards:     numShards,
		shards:        make(map[int]*TemporalShard),
		assignments:   make(map[string]int),
		cache:         make(map[string]*RouteCacheEntry),
		borderGraph:   make(map[string][]BorderEdge),
	}
}

// assignShard atribui um nó a um shard via hash determinístico.
func (r *AtomicMultiverseRouter) assignShard(name string) int {
	if shardID, ok := r.assignments[name]; ok {
		return shardID
	}

	h := sha512.Sum512_256([]byte(name))
	shardID := int(h[0]) % r.numShards
	if shardID < 0 {
		shardID = -shardID
	}

	r.assignments[name] = shardID
	return shardID
}

// getOrCreateShard obtém ou cria um shard.
func (r *AtomicMultiverseRouter) getOrCreateShard(shardID int) *TemporalShard {
	r.mu.Lock()
	defer r.mu.Unlock()

	if shard, ok := r.shards[shardID]; ok {
		return shard
	}

	cfg := ShardConfig{
		ID:            shardID,
		Type:          SpatialShard,
		Region:        fmt.Sprintf("REGION-%d", shardID),
		EpochStart:    0,
		EpochEnd:      math.MaxInt64,
		Capacity:      MaxNodesPerShard,
		BorderRatio:   BorderNodeRatio,
		CacheTTLSeconds: CrossShardCacheTTL,
	}

	shard := NewTemporalShard(cfg)
	r.shards[shardID] = shard
	return shard
}

// RegisterNode registra um nó atômico.
func (r *AtomicMultiverseRouter) RegisterNode(node *AtomicNode) error {
	shardID := r.assignShard(node.Name)
	shard := r.getOrCreateShard(shardID)

	if err := shard.AddNode(node); err != nil {
		return err
	}

	if node.IsBorder {
		r.borderMu.Lock()
		r.borderGraph[node.Name] = []BorderEdge{}
		r.borderMu.Unlock()
	}

	return nil
}

// AddRoute adiciona uma aresta entre nós (qualquer shard).
func (r *AtomicMultiverseRouter) AddRoute(source, dest string, weight float64) error {
	srcShard := r.assignShard(source)
	dstShard := r.assignShard(dest)

	srcShardObj := r.getOrCreateShard(srcShard)

	// Adicionar aresta interna
	if err := srcShardObj.AddInternalEdge(source, dest, weight); err != nil {
		return err
	}

	if srcShard != dstShard {
		// Cross-shard
		srcShardObj.AddCrossShardEdge(source, dest, weight)

		r.borderMu.Lock()
		if edges, ok := r.borderGraph[source]; ok {
			r.borderGraph[source] = append(edges, BorderEdge{
				Target: dest,
				Weight: weight,
			})
		}
		r.borderMu.Unlock()

		// Invalidar cache
		r.invalidateCache(source)
	}

	return nil
}

// FindRoute encontra rota entre dois nós.
func (r *AtomicMultiverseRouter) FindRoute(source, dest string) (*RouteResult, error) {
	start := time.Now()

	srcShard := r.assignShard(source)
	dstShard := r.assignShard(dest)

	var path []string
	var err error

	if srcShard == dstShard {
		// Intra-shard
		shard := r.shards[srcShard]
		path = shard.FindLocalRoute(source, dest)
	} else {
		// Inter-shard
		path, err = r.findCrossShardRoute(source, dest, srcShard, dstShard)
		if err != nil {
			return nil, err
		}
	}

	if path == nil {
		return nil, ErrRouteNotFound
	}

	r.mu.Lock()
	r.stats.totalRoutes++
	if srcShard != dstShard {
		r.stats.interShard++
	}
	r.stats.totalTimeMs += float64(time.Since(start).Nanoseconds() / 1e6)
	r.mu.Unlock()

	// Calcular custo
	cost := 0.0
	for i := 0; i < len(path)-1; i++ {
		cost += 1.0 // Simplificado
	}

	return &RouteResult{
		Path:     path,
		Cost:     cost,
		Hops:     len(path) - 1,
		Duration: time.Since(start),
	}, nil
}

func (r *AtomicMultiverseRouter) findCrossShardRoute(
	source, dest string,
	srcShard, dstShard int,
) ([]string, error) {
	// Verificar cache
	cacheKey := source + "→" + dest
	if entry, ok := r.getCachedRoute(cacheKey); ok {
		return entry.Route, nil
	}

	srcShardObj := r.shards[srcShard]
	dstShardObj := r.shards[dstShard]

	if srcShardObj == nil || dstShardObj == nil {
		return nil, fmt.Errorf("shard não encontrado")
	}

	// Obter border nodes
	srcBorders := r.getBorderNodes(srcShardObj)
	dstBorders := dstShardObj.getBorderNodes()

	if len(srcBorders) == 0 || len(dstBorders) == 0 {
		// Fallback hierárquico
		return r.hierarchicalFallback(source, dest, srcShard, dstShard)
	}

	// Encontrar melhor par de border nodes
	bestPath := []string{}
	bestCost := math.Inf(1)

	for _, srcBorder := range srcBorders {
		localPath := srcShardObj.FindLocalRoute(source, srcBorder)
		if localPath == nil {
			continue
		}
		localCost := float64(len(localPath))

		for _, dstBorder := range dstBorders {
			borderCost, ok := r.getBorderConnection(srcBorder, dstBorder)
			if !ok {
				continue
			}

			dstPath := dstShardObj.FindLocalRoute(dstBorder, dest)
			if dstPath == nil {
				continue
			}

			totalCost := localCost + borderCost + float64(len(dstPath))
			if totalCost < bestCost {
				bestCost = totalCost

				// Construir caminho completo
				fullPath := make([]string, 0)
				fullPath = append(fullPath, localPath[:len(localPath)-1]...)
				fullPath = append(fullPath, srcBorder)
				fullPath = append(fullPath, dstBorder)
				fullPath = append(fullPath, dstPath[1:]...)
				bestPath = fullPath
			}
		}
	}

	if bestPath != nil {
		r.cacheRoute(cacheKey, bestPath, bestCost)
	}

	return bestPath, nil
}

func (r *AtomicMultiverseRouter) getBorderNodes(shard *TemporalShard) []string {
	shard.mu.RLock()
	defer shard.mu.RUnlock()

	result := make([]string, 0, len(shard.borderNodes))
	for name := range shard.borderNodes {
		result = append(result, name)
	}
	return result
}

func (s *TemporalShard) getBorderNodes() []string {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make([]string, 0, len(s.borderNodes))
	for name := range s.borderNodes {
		result = append(result, name)
	}
	return result
}

func (r *AtomicMultiverseRouter) getBorderConnection(src, dst string) (float64, bool) {
	r.borderMu.RLock()
	defer r.borderMu.RUnlock()

	edges, ok := r.borderGraph[src]
	if !ok {
		return 0, false
	}

	for _, edge := range edges {
		if edge.Target == dst {
			return edge.Weight, true
		}
	}

	return 0, false
}

// LazyEvaluateShard materializa shard sob demanda.
func (r *AtomicMultiverseRouter) LazyEvaluateShard(shardID int) {
	shard := r.getOrCreateShard(shardID)

	shard.mu.Lock()
	defer shard.mu.Unlock()

	if len(shard.nodes) > 0 {
		return // Já materializado
	}

	// Materializar border nodes iniciais
	for i := 0; i < 100; i++ {
		node := &AtomicNode{
			Name:         fmt.Sprintf("BN-%d-%03d", shardID, i),
			ShardID:      shardID,
			Type:         "relay",
			PositionAU:   [3]float64{rand.Float64() * 2000 - 1000, rand.Float64() * 2000 - 1000, rand.Float64() * 2000 - 1000},
			Consistency:  0.7 + rand.Float64()*0.3,
			CreatedAt:    time.Now().Unix(),
			Expires:      time.Now().Add(365 * 24 * time.Hour).Unix(),
			MetadataHash: fmt.Sprintf("hash-%d-%d", shardID, i),
			IsBorder:     true,
		}
		_ = shard.AddNode(node)
	}
}

// BatchRegister registra múltiplos nós de uma vez.
func (r *AtomicMultiverseRouter) BatchRegister(nodes []*AtomicNode) (int, error) {
	byShard := make(map[int][]*AtomicNode)

	for _, node := range nodes {
		shardID := r.assignShard(node.Name)
		byShard[shardID] = append(byShard[shardID], node)
	}

	total := 0
	for shardID, shardNodes := range byShard {
		shard := r.getOrCreateShard(shardID)
		for _, node := range shardNodes {
			if err := shard.AddNode(node); err == nil {
				total++
			}
		}
	}

	return total, nil
}

// IterateActiveNodes itera sobre nós ativos.
func (r *AtomicMultiverseRouter) IterateActiveNodes() <-chan *AtomicNode {
	ch := make(chan *AtomicNode, 100)

	go func() {
		defer close(ch)
		for _, shard := range r.shards {
			shard.mu.RLock()
			for _, node := range shard.nodes {
				if !node.IsExpired() {
					ch <- node
				}
			}
			shard.mu.RUnlock()
		}
	}()

	return ch
}

// Stats retorna estatísticas do router.
func (r *AtomicMultiverseRouter) Stats() map[string]interface{} {
	totalNodes := 0
	totalBorders := 0

	for _, shard := range r.shards {
		stats := shard.Stats()
		totalNodes += stats["nodes"].(int)
		totalBorders += stats["border_nodes"].(int)
	}

	return map[string]interface{}{
		"total_shards":     len(r.shards),
		"total_nodes":      totalNodes,
		"border_nodes":     totalBorders,
		"inter_shard_routes": r.stats.interShard,
		"total_routes":     r.stats.totalRoutes,
		"avg_route_time_ms": r.stats.totalTimeMs / math.Max(float64(r.stats.totalRoutes), 1),
		"capacity":         r.totalCapacity,
	}
}

// Cache helpers
func (r *AtomicMultiverseRouter) getCachedRoute(key string) (*RouteCacheEntry, bool) {
	r.cacheMu.RLock()
	defer r.cacheMu.RUnlock()

	entry, ok := r.cache[key]
	if !ok || time.Now().Unix() > entry.ExpiryAt {
		return nil, false
	}
	return entry, true
}

func (r *AtomicMultiverseRouter) cacheRoute(key string, route []string, cost float64) {
	r.cacheMu.Lock()
	defer r.cacheMu.Unlock()

	r.cache[key] = &RouteCacheEntry{
		Route:    route,
		Cost:     cost,
		ExpiryAt: time.Now().Add(CrossShardCacheTTL * time.Second).Unix(),
	}
}

func (r *AtomicMultiverseRouter) invalidateCache(node string) {
	r.cacheMu.Lock()
	defer r.cacheMu.Unlock()

	for key := range r.cache {
		if len(key) >= len(node) && (key[:len(node)] == node || key[len(key)-len(node):] == node) {
			delete(r.cache, key)
		}
	}
}

func (r *AtomicMultiverseRouter) hierarchicalFallback(
	source, dest string,
	srcShard, dstShard int,
) ([]string, error) {
	srcShardObj := r.shards[srcShard]
	if srcShardObj == nil {
		return nil, fmt.Errorf("shard source não encontrado")
	}

	borderNodes := r.getBorderNodes(srcShardObj)
	if len(borderNodes) == 0 {
		return nil, fmt.Errorf("sem border nodes no shard source")
	}

	// Usar primeiro border node disponível
	border := borderNodes[0]
	localPath := srcShardObj.FindLocalRoute(source, border)
	if localPath == nil {
		return nil, fmt.Errorf("não pôde alcançar border node")
	}

	// Retornar rota parcial com estimativa
	return append(localPath, fmt.Sprintf("...→shard-%d", dstShard)), nil
}
