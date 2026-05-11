// arkhe_os/routing/coherence_potential_field.go
package routing

import (
	"fmt"
	"math"
	"sync"
	"time"
)

// Dummy types for references not provided
type CosmicNode struct {
	ID          string
	Name        string
	Coherence   float64
	Resonance   float64
	Scale       int
	Address     CosmicAddress
	Reputation  float64
	CurrentLoad float64
	MaxCapacity float64
	UptimeHours float64
}

type CosmicAddress [32]byte

func NewCosmicAddress(scale int, coherence, resonance float64, branchAngle float32, branchPhase float32, branchIndex uint32, nodeName string) CosmicAddress {
	return CosmicAddress{}
}

func (ca CosmicAddress) Scale() int         { return 0 }
func (ca CosmicAddress) Coherence() float64 { return 0.5 }
func (ca CosmicAddress) BranchID() uint64   { return 0 }
func (ca CosmicAddress) NodeHash() []byte   { return make([]byte, 12) }

// ─── CONSTANTES DO CAMPO DE COERÊNCIA ─────────────────────────────────

const (
	// KernelWidth padrão para influência de nós no campo
	DefaultKernelWidth = 0.15 // em unidades normalizadas do espaço de endereços

	// UpdateInterval para recálculo do campo
	FieldUpdateInterval = 5 * time.Second

	// MinCoherenceForInfluence: nós com Φ_C abaixo deste valor não influenciam o campo
	MinCoherenceForInfluence = 0.3

	// MaxFieldCacheSize: número máximo de pontos cacheados para interpolação
	MaxFieldCacheSize = 10000
)

// ─── TIPOS FUNDAMENTAIS ───────────────────────────────────────────────

// CoherencePotentialField modela Φ_C(x,t) como campo escalar contínuo
type CoherencePotentialField struct {
	nodes         map[string]*CosmicNode // referência aos nós da rede
	addressMapper *AddressSpaceMapper    // mapeamento CosmicAddress → ℝ³
	kernelWidth   float64                // σ do kernel Gaussiano
	cache         *FieldCache            // cache de avaliações recentes
	mu            sync.RWMutex
	lastUpdate    time.Time
	metrics       FieldMetrics
}

// FieldMetrics contém métricas do campo de coerência
type FieldMetrics struct {
	EvaluationsCount    int64   `json:"evaluations_count"`
	AvgEvaluationTimeUs float64 `json:"avg_evaluation_time_us"`
	CacheHitRate        float64 `json:"cache_hit_rate"`
	ActiveInfluencers   int     `json:"active_influencers"` // nós com Φ_C > threshold
}

// FieldCache armazena avaliações recentes para interpolação rápida
type FieldCache struct {
	entries map[uint64]CacheEntry // hash do endereço → valor cacheado
	maxSize int
	mu      sync.RWMutex
}

// CacheEntry armazena uma avaliação do campo em um ponto
type CacheEntry struct {
	AddressHash uint64
	Value       float64
	Gradient    [3]float64 // ∇Φ_C neste ponto
	Timestamp   time.Time
}

// AddressSpaceMapper converte CosmicAddress para coordenadas ℝ³ para cálculo de campo
type AddressSpaceMapper struct {
	// Mapeia os 256 bits do endereço para 3 dimensões usando hashing projetivo
	// Dimensão 1: escala cosmológica + coerência (bits 0-95)
	// Dimensão 2: identificador de ramo (bits 96-159)
	// Dimensão 3: ID do nó (bits 160-255)
}

func (asm *AddressSpaceMapper) MapToSpace(addr CosmicAddress) [3]float64 {
	return [3]float64{0, 0, 0}
}

// ─── CONSTRUTORES ─────────────────────────────────────────────────────

// NewCoherencePotentialField cria novo campo de potencial de coerência
func NewCoherencePotentialField(
	nodes map[string]*CosmicNode,
	kernelWidth float64,
) (*CoherencePotentialField, error) {
	if kernelWidth <= 0 {
		kernelWidth = DefaultKernelWidth
	}

	return &CoherencePotentialField{
		nodes:         nodes,
		addressMapper: NewAddressSpaceMapper(),
		kernelWidth:   kernelWidth,
		cache: &FieldCache{
			entries: make(map[uint64]CacheEntry),
			maxSize: MaxFieldCacheSize,
		},
		lastUpdate: time.Now(),
	}, nil
}

// NewAddressSpaceMapper cria mapper de endereços para espaço contínuo
func NewAddressSpaceMapper() *AddressSpaceMapper {
	return &AddressSpaceMapper{}
}

// ─── OPERAÇÕES DO CAMPO ───────────────────────────────────────────────

// Evaluate calcula Φ_C(x) em um ponto do espaço de endereços
func (f *CoherencePotentialField) Evaluate(addr CosmicAddress) (float64, [3]float64, error) {
	start := time.Now()

	// Verificar cache primeiro
	addrHash := hashAddress(addr)
	if entry, ok := f.cache.Get(addrHash); ok {
		f.metrics.CacheHitRate = f.metrics.CacheHitRate*0.99 + 0.01
		f.metrics.EvaluationsCount++
		return entry.Value, entry.Gradient, nil
	}

	f.mu.RLock()
	defer f.mu.RUnlock()

	// Mapear endereço para coordenadas ℝ³
	x := f.addressMapper.MapToSpace(addr)

	// Calcular contribuição de cada nó influente
	var totalCoherence float64
	var totalWeight float64
	var gradient [3]float64

	activeCount := 0
	for _, node := range f.nodes {
		if node.Coherence < MinCoherenceForInfluence {
			continue
		}
		activeCount++

		// Coordenadas do nó no espaço contínuo
		nodeAddr := NewCosmicAddress(
			node.Scale, node.Coherence, node.Resonance,
			0, 0, 0, node.Name, // ramo default para cálculo de campo
		)
		xNode := f.addressMapper.MapToSpace(nodeAddr)

		// Distância no espaço de endereços
		dist := euclideanDistance(x, xNode)

		// Kernel Gaussiano de influência
		influence := gaussianKernel(dist, f.kernelWidth)

		// Peso dinâmico baseado em reputação e carga
		weight := computeNodeWeight(node)

		// Contribuição para o campo
		contribution := weight * influence * node.Coherence
		totalCoherence += contribution
		totalWeight += influence * weight

		// Gradiente do kernel (para ∇Φ_C)
		if influence > 1e-10 {
			gradFactor := -2 * influence / (f.kernelWidth * f.kernelWidth)
			for i := 0; i < 3; i++ {
				gradient[i] += weight * node.Coherence * gradFactor * (x[i] - xNode[i])
			}
		}
	}

	// Normalizar pelo peso total
	var phiC float64
	if totalWeight > 1e-10 {
		phiC = totalCoherence / totalWeight
		for i := 0; i < 3; i++ {
			gradient[i] /= totalWeight
		}
	}

	// Atualizar cache
	f.cache.Put(addrHash, phiC, gradient)

	// Atualizar métricas
	elapsed := time.Since(start).Microseconds()
	f.metrics.EvaluationsCount++
	f.metrics.AvgEvaluationTimeUs = f.metrics.AvgEvaluationTimeUs*0.99 + float64(elapsed)*0.01
	f.metrics.ActiveInfluencers = activeCount

	return phiC, gradient, nil
}

// FollowGradient retorna a direção de movimento para um pacote seguindo ∇Φ_C
func (f *CoherencePotentialField) FollowGradient(
	currentAddr CosmicAddress,
	destAddr CosmicAddress,
	alpha, beta, gamma float64, // pesos da equação de movimento
) ([3]float64, error) {
	// Coordenadas atuais e de destino
	x := f.addressMapper.MapToSpace(currentAddr)
	xDest := f.addressMapper.MapToSpace(destAddr)

	// Avaliar campo e gradiente na posição atual
	_, gradPhi, err := f.Evaluate(currentAddr)
	if err != nil {
		return [3]float64{}, err
	}

	// Calcular entropia local (simplificado: inverso da coerência)
	gradEntropy := [3]float64{-gradPhi[0], -gradPhi[1], -gradPhi[2]} // ∇S ≈ -∇Φ

	// Equação de movimento: dx/dt = -∇[α·||x-x_d||² - β·Φ + γ·S]
	var direction [3]float64
	for i := 0; i < 3; i++ {
		// Termo de atração ao destino: -∇(α·||x-x_d||²) = -2α(x - x_d)
		attraction := -2 * alpha * (x[i] - xDest[i])

		// Termo de atração a alta coerência: +β·∇Φ
		coherencePull := beta * gradPhi[i]

		// Termo de repulsão de alta entropia: -γ·∇S ≈ +γ·∇Φ
		entropyPush := gamma * gradEntropy[i]

		direction[i] = attraction + coherencePull + entropyPush
	}

	// Normalizar direção
	norm := vectorNorm(direction)
	if norm > 1e-10 {
		for i := 0; i < 3; i++ {
			direction[i] /= norm
		}
	}

	return direction, nil
}

// FindNextHop determina o próximo salto ideal baseado no campo de coerência
func (f *CoherencePotentialField) FindNextHop(
	currentNodeID string,
	destAddr CosmicAddress,
	neighbors []string, // IDs dos nós vizinhos alcançáveis
) (string, float64, error) {
	if len(neighbors) == 0 {
		return "", 0, fmt.Errorf("no neighbors available")
	}

	currentAddr := f.nodes[currentNodeID].Address
	bestHop := ""
	bestScore := -math.MaxFloat64
	_ = currentAddr

	for _, neighborID := range neighbors {
		neighbor := f.nodes[neighborID]
		if neighbor == nil {
			continue
		}

		// Score baseado em: coerência do vizinho + proximidade ao destino + baixa entropia
		neighborPhi, _, err := f.Evaluate(neighbor.Address)
		if err != nil {
			continue
		}

		// Distância ao destino no espaço de endereços
		distToDest := addressDistance(neighbor.Address, destAddr)

		// Entropia estimada do vizinho

		// Score combinado (pesos ajustáveis)
		score := 0.4*neighborPhi - 0.3*distToDest - 0.3*(1.0-neighbor.Coherence)

		if score > bestScore {
			bestScore = score
			bestHop = neighborID
		}
	}

	if bestHop == "" {
		return "", 0, fmt.Errorf("no suitable next hop found")
	}

	return bestHop, bestScore, nil
}

// ─── FUNÇÕES AUXILIARES ───────────────────────────────────────────────

// gaussianKernel calcula kernel Gaussiano de influência
func gaussianKernel(distance, sigma float64) float64 {
	if sigma <= 0 {
		sigma = DefaultKernelWidth
	}
	return math.Exp(-0.5 * (distance * distance) / (sigma * sigma))
}

// computeNodeWeight calcula peso dinâmico de um nó para influência no campo
func computeNodeWeight(node *CosmicNode) float64 {
	// Peso baseado em: reputação, carga, estabilidade temporal
	reputationWeight := node.Reputation // [0, 1]
	if node.MaxCapacity == 0 {
		node.MaxCapacity = 1
	}
	loadFactor := 1.0 - math.Min(1.0, node.CurrentLoad/node.MaxCapacity)
	stabilityFactor := 0.9 + 0.1*node.UptimeHours/(24*30) // estabiliza após 30 dias

	return reputationWeight * loadFactor * stabilityFactor
}

// euclideanDistance calcula distância euclidiana em ℝ³
func euclideanDistance(a, b [3]float64) float64 {
	var sum float64
	for i := 0; i < 3; i++ {
		diff := a[i] - b[i]
		sum += diff * diff
	}
	return math.Sqrt(sum)
}

// vectorNorm calcula norma euclidiana de vetor 3D
func vectorNorm(v [3]float64) float64 {
	var sum float64
	for i := 0; i < 3; i++ {
		sum += v[i] * v[i]
	}
	return math.Sqrt(sum)
}

// addressDistance calcula distância normalizada entre dois CosmicAddress
func addressDistance(a, b CosmicAddress) float64 {
	// Distância baseada em: diferença de escala, coerência, ramo, e ID
	scaleDiff := math.Abs(float64(a.Scale())-float64(b.Scale())) / 13.0 // 13 escalas
	cohDiff := math.Abs(a.Coherence() - b.Coherence())
	branchDiff := branchDistance(a.BranchID(), b.BranchID())
	idDiff := float64(hammingDistance(a.NodeHash(), b.NodeHash())) / 96.0 // 96 bits de ID

	// Combinação ponderada
	return 0.2*scaleDiff + 0.3*cohDiff + 0.3*branchDiff + 0.2*idDiff
}

// branchDistance calcula distância entre identificadores de ramo
func branchDistance(a, b uint64) float64 {
	// Distância angular normalizada no espaço de ramos
	diff := math.Abs(float64(int64(a) - int64(b)))
	return math.Min(diff, math.MaxUint64-diff) / float64(math.MaxUint64/2)
}

// hammingDistance conta bits diferentes entre dois hashes
func hammingDistance(a, b []byte) int {
	if len(a) != len(b) {
		return len(a) + len(b)
	}
	count := 0
	for i := 0; i < len(a); i++ {
		xor := a[i] ^ b[i]
		for xor != 0 {
			count += int(xor & 1)
			xor >>= 1
		}
	}
	return count
}

// hashAddress gera hash uint64 de um endereço para uso em cache
func hashAddress(addr CosmicAddress) uint64 {
	// Usar os primeiros 8 bytes do endereço como hash (suficiente para cache)
	var result uint64
	for i := 0; i < 8; i++ {
		result = (result << 8) | uint64(addr[i])
	}
	return result
}

// ─── OPERAÇÕES DO CACHE ───────────────────────────────────────────────

// Get recupera entrada do cache se válida (não expirada)
func (c *FieldCache) Get(addrHash uint64) (CacheEntry, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	entry, ok := c.entries[addrHash]
	if !ok {
		return CacheEntry{}, false
	}

	// Verificar validade (cache válido por 2 segundos)
	if time.Since(entry.Timestamp) > 2*time.Second {
		return CacheEntry{}, false
	}

	return entry, true
}

// Put insere nova entrada no cache, removendo antigas se necessário
func (c *FieldCache) Put(addrHash uint64, value float64, gradient [3]float64) {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Remover entradas antigas se cache cheio
	if len(c.entries) >= c.maxSize {
		oldestTime := time.Now()
		var oldestHash uint64
		for hash, entry := range c.entries {
			if entry.Timestamp.Before(oldestTime) {
				oldestTime = entry.Timestamp
				oldestHash = hash
			}
		}
		if oldestHash != 0 {
			delete(c.entries, oldestHash)
		}
	}

	c.entries[addrHash] = CacheEntry{
		AddressHash: addrHash,
		Value:       value,
		Gradient:    gradient,
		Timestamp:   time.Now(),
	}
}

// GetMetrics retorna métricas do campo de coerência
func (f *CoherencePotentialField) GetMetrics() FieldMetrics {
	f.mu.RLock()
	defer f.mu.RUnlock()
	return f.metrics
}
