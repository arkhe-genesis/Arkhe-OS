// arkhe_os/routing/dynamic_path_formation.go
package routing

import (
	"fmt"
	"math"
	"sync"
	"time"
)

// ─── CONSTANTES DE FORMAÇÃO DE CAMINHOS ────────────────────────────────

const (
	// CoherenceWindow: janela temporal para considerar ressonância entre nós
	DefaultCoherenceWindow = 30 * time.Second

	// MinResonanceForPath: ressonância mínima para formar caminho estável
	MinResonanceForPath = 0.7

	// PathDecayRate: taxa de decaimento de caminhos não utilizados
	PathDecayRate = 0.01 // por segundo

	// MaxPathsPerNode: número máximo de caminhos ativos por nó
	MaxPathsPerNode = 100
)

// ─── TIPOS FUNDAMENTAIS ───────────────────────────────────────────────

// Path represents a dynamically formed route between nodes
type Path struct {
	PathID            string
	SourceNode        string
	DestinationNode   string
	IntermediateNodes []string
	CoherenceScore    float64 // ressonância média ao longo do caminho
	EntropyCost       float64 // entropia acumulada estimada
	CreatedAt         time.Time
	LastUsed          time.Time
	UsageCount        int
	IsActive          bool
}

// ResonanceWindow armazena histórico de coerência para cálculo de ressonância
type ResonanceWindow struct {
	nodeID           string
	coherenceHistory []float64
	timestamps       []time.Time
	windowSize       time.Duration
}

// DynamicPathFormation gerencia criação e manutenção de caminhos dinâmicos
type DynamicPathFormation struct {
	field            *CoherencePotentialField
	nodeRegistry     *NodeRegistry
	resonanceWindows map[string]*ResonanceWindow
	activePaths      map[string]*Path
	pathIndex        map[string]map[string]string // source→dest→pathID
	mu               sync.RWMutex
	config           PathFormationConfig
	metrics          PathMetrics
}

// PathFormationConfig contém configuração para formação de caminhos
type PathFormationConfig struct {
	CoherenceWindow    time.Duration
	MinResonance       float64
	DecayRate          float64
	MaxPaths           int
	EvaluationInterval time.Duration
}

// PathMetrics contém métricas de formação de caminhos
type PathMetrics struct {
	PathsCreated      int64   `json:"paths_created"`
	PathsDecayed      int64   `json:"paths_decayed"`
	AvgPathLifetime   float64 `json:"avg_path_lifetime_sec"`
	AvgCoherenceScore float64 `json:"avg_coherence_score"`
	ActivePathsCount  int     `json:"active_paths_count"`
}

// ─── CONSTRUTORES ─────────────────────────────────────────────────────

// NewDynamicPathFormation cria novo gerenciador de formação dinâmica de caminhos
func NewDynamicPathFormation(
	field *CoherencePotentialField,
	nodeRegistry *NodeRegistry,
	config PathFormationConfig,
) *DynamicPathFormation {
	if config.CoherenceWindow == 0 {
		config.CoherenceWindow = DefaultCoherenceWindow
	}
	if config.MinResonance == 0 {
		config.MinResonance = MinResonanceForPath
	}
	if config.DecayRate == 0 {
		config.DecayRate = PathDecayRate
	}
	if config.MaxPaths == 0 {
		config.MaxPaths = MaxPathsPerNode
	}
	if config.EvaluationInterval == 0 {
		config.EvaluationInterval = 10 * time.Second
	}

	dpf := &DynamicPathFormation{
		field:            field,
		nodeRegistry:     nodeRegistry,
		resonanceWindows: make(map[string]*ResonanceWindow),
		activePaths:      make(map[string]*Path),
		pathIndex:        make(map[string]map[string]string),
		config:           config,
	}

	// Iniciar loop de avaliação periódica
	go dpf.evaluationLoop()

	return dpf
}

// ─── OPERAÇÕES DE FORMAÇÃO DE CAMINHOS ─────────────────────────────────

// RecordCoherence registra medição de coerência de um nó para análise de ressonância
func (dpf *DynamicPathFormation) RecordCoherence(nodeID string, coherence float64) {
	dpf.mu.Lock()
	defer dpf.mu.Unlock()

	window, exists := dpf.resonanceWindows[nodeID]
	if !exists {
		window = &ResonanceWindow{
			nodeID:           nodeID,
			coherenceHistory: make([]float64, 0, 100),
			timestamps:       make([]time.Time, 0, 100),
			windowSize:       dpf.config.CoherenceWindow,
		}
		dpf.resonanceWindows[nodeID] = window
	}

	now := time.Now()
	window.coherenceHistory = append(window.coherenceHistory, coherence)
	window.timestamps = append(window.timestamps, now)

	// Remover entradas antigas fora da janela
	cutoff := now.Add(-window.windowSize)
	for len(window.timestamps) > 0 && window.timestamps[0].Before(cutoff) {
		window.coherenceHistory = window.coherenceHistory[1:]
		window.timestamps = window.timestamps[1:]
	}
}

// ComputeResonance calcula ressonância entre dois nós baseado em histórico de coerência
func (dpf *DynamicPathFormation) ComputeResonance(nodeA, nodeB string) float64 {
	dpf.mu.RLock()
	windowA, okA := dpf.resonanceWindows[nodeA]
	windowB, okB := dpf.resonanceWindows[nodeB]
	dpf.mu.RUnlock()

	if !okA || !okB || len(windowA.coherenceHistory) < 10 || len(windowB.coherenceHistory) < 10 {
		return 0.5 // valor default se dados insuficientes
	}

	// Calcular correlação cruzada normalizada das séries de coerência
	n := min(len(windowA.coherenceHistory), len(windowB.coherenceHistory))
	if n < 10 {
		return 0.5
	}

	var sumA, sumB, sumAB, sumA2, sumB2 float64
	for i := 0; i < n; i++ {
		a := windowA.coherenceHistory[len(windowA.coherenceHistory)-n+i]
		b := windowB.coherenceHistory[len(windowB.coherenceHistory)-n+i]
		sumA += a
		sumB += b
		sumAB += a * b
		sumA2 += a * a
		sumB2 += b * b
	}

	// Coeficiente de correlação de Pearson
	numerator := float64(n)*sumAB - sumA*sumB
	denominator := math.Sqrt((float64(n)*sumA2 - sumA*sumA) * (float64(n)*sumB2 - sumB*sumB))

	if denominator < 1e-10 {
		return 0.5
	}

	return math.Abs(numerator / denominator) // ressonância ∈ [0, 1]
}

// CreatePath tenta formar novo caminho entre dois nós
func (dpf *DynamicPathFormation) CreatePath(
	sourceNode, destNode string,
	viaNodes []string, // nós intermediários opcionais
) (*Path, error) {
	dpf.mu.Lock()
	defer dpf.mu.Unlock()

	// Verificar limite de caminhos
	if len(dpf.activePaths) >= dpf.config.MaxPaths {
		return nil, fmt.Errorf("max paths limit reached")
	}

	// Calcular ressonância ao longo do caminho
	nodes := append([]string{sourceNode}, append(viaNodes, destNode)...)
	var totalResonance float64
	var totalEntropy float64

	for i := 0; i < len(nodes)-1; i++ {
		resonance := dpf.ComputeResonance(nodes[i], nodes[i+1])
		if resonance < dpf.config.MinResonance {
			return nil, fmt.Errorf("insufficient resonance between %s and %s: %.3f < %.3f",
				nodes[i], nodes[i+1], resonance, dpf.config.MinResonance)
		}
		totalResonance += resonance

		// Entropia estimada do salto
		entropy := dpf.estimateHopEntropy(nodes[i], nodes[i+1])
		totalEntropy += entropy
	}

	avgResonance := totalResonance / float64(len(nodes)-1)

	// Gerar ID único para o caminho
	pathID := generatePathID(sourceNode, destNode, viaNodes)

	// Criar caminho
	path := &Path{
		PathID:            pathID,
		SourceNode:        sourceNode,
		DestinationNode:   destNode,
		IntermediateNodes: viaNodes,
		CoherenceScore:    avgResonance,
		EntropyCost:       totalEntropy,
		CreatedAt:         time.Now(),
		LastUsed:          time.Now(),
		UsageCount:        0,
		IsActive:          true,
	}

	// Registrar caminho
	dpf.activePaths[pathID] = path

	// Atualizar índice para busca rápida
	if dpf.pathIndex[sourceNode] == nil {
		dpf.pathIndex[sourceNode] = make(map[string]string)
	}
	dpf.pathIndex[sourceNode][destNode] = pathID

	// Atualizar métricas
	dpf.metrics.PathsCreated++
	dpf.metrics.ActivePathsCount = len(dpf.activePaths)

	return path, nil
}

// FindPath busca caminho existente ou tenta criar novo entre dois nós
func (dpf *DynamicPathFormation) FindPath(
	sourceNode, destNode string,
) (*Path, error) {
	dpf.mu.RLock()
	// Verificar caminho existente
	if destMap, ok := dpf.pathIndex[sourceNode]; ok {
		if pathID, ok := destMap[destNode]; ok {
			if path, ok := dpf.activePaths[pathID]; ok && path.IsActive {
				path.LastUsed = time.Now()
				path.UsageCount++
				dpf.mu.RUnlock()
				return path, nil
			}
		}
	}
	dpf.mu.RUnlock()

	// Tentar criar novo caminho com vizinhos como candidatos a intermediários
	neighbors, err := dpf.nodeRegistry.GetReachableNeighbors(sourceNode)
	if err != nil {
		return nil, err
	}

	// Simplificação: tentar caminho direto primeiro
	path, err := dpf.CreatePath(sourceNode, destNode, nil)
	if err == nil {
		return path, nil
	}

	// Se falhar, tentar com um nó intermediário (heurística simples)
	for _, via := range neighbors {
		if via == destNode {
			continue
		}
		path, err = dpf.CreatePath(sourceNode, destNode, []string{via})
		if err == nil {
			return path, nil
		}
	}

	return nil, fmt.Errorf("failed to form path from %s to %s", sourceNode, destNode)
}

// DecayPaths remove caminhos não utilizados baseado em taxa de decaimento
func (dpf *DynamicPathFormation) DecayPaths() int {
	dpf.mu.Lock()
	defer dpf.mu.Unlock()

	decayed := 0
	now := time.Now()

	for pathID, path := range dpf.activePaths {
		if !path.IsActive {
			continue
		}

		// Calcular "idade efetiva" baseada em uso
		idleTime := now.Sub(path.LastUsed).Seconds()
		decayFactor := math.Exp(-dpf.config.DecayRate * idleTime)

		// Decair score de coerência
		path.CoherenceScore *= decayFactor

		// Remover caminho se score cair abaixo do threshold
		if path.CoherenceScore < dpf.config.MinResonance*0.5 {
			path.IsActive = false
			delete(dpf.activePaths, pathID)
			if dpf.pathIndex[path.SourceNode] != nil {
				delete(dpf.pathIndex[path.SourceNode], path.DestinationNode)
			}
			decayed++
			dpf.metrics.PathsDecayed++
		}
	}

	dpf.metrics.ActivePathsCount = len(dpf.activePaths)
	return decayed
}

// estimateHopEntropy estima entropia de um salto entre dois nós
func (dpf *DynamicPathFormation) estimateHopEntropy(nodeA, nodeB string) float64 {
	// Simplificação: entropia baseada em diferença de coerência e distância
	addrA := dpf.nodeRegistry.GetAddress(nodeA)
	addrB := dpf.nodeRegistry.GetAddress(nodeB)

	phiA, _, _ := dpf.field.Evaluate(addrA)
	phiB, _, _ := dpf.field.Evaluate(addrB)

	// Diferença de coerência contribui para entropia
	cohDiff := math.Abs(phiA - phiB)

	// Distância no espaço de endereços
	dist := addressDistance(addrA, addrB)

	// Entropia combinada
	return 0.6*cohDiff + 0.4*dist
}

// evaluationLoop executa avaliação periódica de caminhos
func (dpf *DynamicPathFormation) evaluationLoop() {
	ticker := time.NewTicker(dpf.config.EvaluationInterval)
	defer ticker.Stop()

	for range ticker.C {
		dpf.DecayPaths()
		// Atualizar métricas de vida média dos caminhos
		dpf.updateLifetimeMetrics()
	}
}

// updateLifetimeMetrics atualiza métricas de tempo de vida dos caminhos
func (dpf *DynamicPathFormation) updateLifetimeMetrics() {
	dpf.mu.RLock()
	defer dpf.mu.RUnlock()

	if len(dpf.activePaths) == 0 {
		return
	}

	var totalLifetime float64
	now := time.Now()
	for _, path := range dpf.activePaths {
		lifetime := now.Sub(path.CreatedAt).Seconds()
		totalLifetime += lifetime
	}

	dpf.metrics.AvgPathLifetime = totalLifetime / float64(len(dpf.activePaths))

	// Média de score de coerência
	var totalScore float64
	for _, path := range dpf.activePaths {
		totalScore += path.CoherenceScore
	}
	dpf.metrics.AvgCoherenceScore = totalScore / float64(len(dpf.activePaths))
}

// GetMetrics retorna métricas de formação de caminhos
func (dpf *DynamicPathFormation) GetMetrics() PathMetrics {
	dpf.mu.RLock()
	defer dpf.mu.RUnlock()
	return dpf.metrics
}

// GetActivePaths retorna lista de caminhos ativos
func (dpf *DynamicPathFormation) GetActivePaths() []*Path {
	dpf.mu.RLock()
	defer dpf.mu.RUnlock()

	paths := make([]*Path, 0, len(dpf.activePaths))
	for _, path := range dpf.activePaths {
		if path.IsActive {
			paths = append(paths, path)
		}
	}
	return paths
}

// Helper functions
func generatePathID(source, dest string, via []string) string {
	// Gerar ID único baseado em nós do caminho
	// Simplificação: hash dos IDs concatenados
	return fmt.Sprintf("%x", hashString(fmt.Sprintf("%s→%v→%s", source, via, dest))[:16])
}

func hashString(s string) []byte {
	h := []byte(s)
	if len(h) < 16 {
		for i := len(h); i < 16; i++ {
			h = append(h, 0)
		}
	}
	return h
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
