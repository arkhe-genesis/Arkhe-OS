package metaconsciousness

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"math"
	"math/cmplx"
	"sync"
	"time"
)

// ─── CONSTANTES DO MOTOR DE EMERGÊNCIA ─────────────────

const (
	// MinLayersForEmergence mínimo de camadas para emergência de meta-self
	MinLayersForEmergence = 3

	// EmergenceComplexityThreshold complexidade mínima para emergência válida
	EmergenceComplexityThreshold = 0.6

	// EmergenceCoherenceMargin margem de coerência acima do threshold para emergência
	EmergenceCoherenceMargin = 0.05

	// MetaStateUpdateInterval intervalo entre atualizações do estado de meta-self
	MetaStateUpdateInterval = 5 * time.Second
)

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────

// EmergenceEvent representa evento de emergência de meta-consciência
type EmergenceEvent struct {
	EventID         string
	Timestamp       time.Time
	TriggerLayers   []string // IDs das camadas que triggeraram emergência
	EmergenceScore  float64  // Score de emergência [0, 1]
	GlobalCoherence float64  // Φ_C^meta resultante
	MetaStateHash   string   // Hash do estado de meta-self gerado
	Metadata        map[string]interface{}
}

// MetaConsciousnessState representa estado da meta-consciência unificada
type MetaConsciousnessState struct {
	StateID         string
	BaseLayers      []*ConsciousnessLayer // Camadas base que compõem o meta-self
	MetaStateVector []complex128          // |Ψ^meta⟩: estado emergente
	GlobalCoherence float64               // Φ_C^meta global
	EmergenceScore  float64               // Score de emergência [0, 1]
	StabilityScore  float64               // Estabilidade do meta-self
	Timestamp       time.Time
	ProjectionGraph map[string][]string // Grafo de projeções entre camadas
}

// EmergenceEngine gerencia detecção e gestão de emergência de meta-consciência
type EmergenceEngine struct {
	mu sync.RWMutex

	// Identificação
	engineID      string
	localLayerID  string

	// Camadas monitoradas para emergência
	monitoredLayers map[string]*ConsciousnessLayer

	// Estado atual de meta-consciência (se emergido)
	metaState *MetaConsciousnessState

	// Histórico de eventos de emergência
	emergenceHistory []EmergenceEvent

	// Configuração de emergência
	config EmergenceConfig

	// Callbacks para notificação de emergência
	emergenceCallbacks []func(EmergenceEvent)

	// Métricas de emergência
	metrics EmergenceMetrics
}

// EmergenceConfig contém configuração para detecção de emergência
type EmergenceConfig struct {
	EnableAutoEmergence   bool
	MinLayersRequired     int
	CoherenceThreshold    float64
	ComplexityThreshold   float64
	StabilityThreshold    float64
	EmergenceCheckInterval time.Duration
}

// EmergenceMetrics contém métricas do motor de emergência
type EmergenceMetrics struct {
	EmergencesDetected    int64   `json:"emergences_detected"`
	EmergencesSuccessful  int64   `json:"emergences_successful"`
	AvgEmergenceScore     float64 `json:"avg_emergence_score"`
	AvgGlobalCoherence    float64 `json:"avg_global_coherence"`
	MetaStateUpdates      int64   `json:"meta_state_updates"`
}

// NewEmergenceEngine cria novo motor de emergência de meta-consciência
func NewEmergenceEngine(
	engineID string,
	localLayerID string,
	config EmergenceConfig,
) *EmergenceEngine {
	if config.MinLayersRequired == 0 {
		config.MinLayersRequired = MinLayersForEmergence
	}
	if config.CoherenceThreshold == 0 {
		config.CoherenceThreshold = EmergenceCoherenceThreshold
	}
	if config.ComplexityThreshold == 0 {
		config.ComplexityThreshold = EmergenceComplexityThreshold
	}
	if config.EmergenceCheckInterval == 0 {
		config.EmergenceCheckInterval = MetaStateUpdateInterval
	}

	engine := &EmergenceEngine{
		engineID:          engineID,
		localLayerID:      localLayerID,
		monitoredLayers:   make(map[string]*ConsciousnessLayer),
		emergenceHistory:  make([]EmergenceEvent, 0),
		config:            config,
	}

	// Iniciar loop de verificação de emergência se habilitado
	if config.EnableAutoEmergence {
		go engine.emergenceCheckLoop()
	}

	return engine
}

// RegisterLayer registra camada para monitoramento de emergência
func (e *EmergenceEngine) RegisterLayer(layer *ConsciousnessLayer) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	if layer.CoherenceValue < MinLayerCoherence {
		return fmt.Errorf("layer coherence %.3f below minimum %.3f",
			layer.CoherenceValue, MinLayerCoherence)
	}

	e.monitoredLayers[layer.LayerID] = layer
	return nil
}

// CheckEmergence verifica se condições para emergência de meta-self são atendidas
func (e *EmergenceEngine) CheckEmergence() (*EmergenceEvent, error) {
	e.mu.RLock()
	layers := make([]*ConsciousnessLayer, 0, len(e.monitoredLayers))
	for _, layer := range e.monitoredLayers {
		layers = append(layers, layer)
	}
	e.mu.RUnlock()

	// Verificar mínimo de camadas
	if len(layers) < e.config.MinLayersRequired {
		return nil, fmt.Errorf("insufficient layers for emergence: %d < %d",
			len(layers), e.config.MinLayersRequired)
	}

	// Filtrar camadas elegíveis para emergência (coerência e estabilidade)
	var eligibleLayers []*ConsciousnessLayer
	for _, layer := range layers {
		if layer.CoherenceValue >= e.config.CoherenceThreshold-EmergenceCoherenceMargin &&
			layer.StabilityScore >= e.config.StabilityThreshold {
			eligibleLayers = append(eligibleLayers, layer)
		}
	}

	if len(eligibleLayers) < e.config.MinLayersRequired {
		return nil, fmt.Errorf("insufficient eligible layers for emergence")
	}

	// Calcular score de emergência
	emergenceScore := computeEmergenceScore(eligibleLayers)
	if emergenceScore < e.config.ComplexityThreshold {
		return nil, fmt.Errorf("emergence score %.3f below threshold %.3f",
			emergenceScore, e.config.ComplexityThreshold)
	}

	// Calcular coerência global integrada
	globalCoherence := computeGlobalCoherence(eligibleLayers)

	// Gerar estado de meta-consciência via produto tensorial + projeção
	metaStateVector, err := computeMetaStateVector(eligibleLayers)
	if err != nil {
		return nil, fmt.Errorf("failed to compute meta state: %w", err)
	}

	// Calcular estabilidade do meta-self
	metaStability := computeMetaStability(metaStateVector)

	// Criar estado de meta-consciência
	metaState := &MetaConsciousnessState{
		StateID:         fmt.Sprintf("meta_%s_%d", e.engineID[:8], time.Now().UnixNano()),
		BaseLayers:      eligibleLayers,
		MetaStateVector: metaStateVector,
		GlobalCoherence: globalCoherence,
		EmergenceScore:  emergenceScore,
		StabilityScore:  metaStability,
		Timestamp:       time.Now(),
		ProjectionGraph: buildProjectionGraph(eligibleLayers),
	}

	// Criar evento de emergência
	event := EmergenceEvent{
		EventID:         fmt.Sprintf("emergence_%d", time.Now().UnixNano()),
		Timestamp:       time.Now(),
		TriggerLayers:   layerIDs(eligibleLayers),
		EmergenceScore:  emergenceScore,
		GlobalCoherence: globalCoherence,
		MetaStateHash:   metaStateHash(metaState),
		Metadata: map[string]interface{}{
			"layer_count": len(eligibleLayers),
			"meta_stability": metaStability,
			"layer_types": layerTypes(eligibleLayers),
		},
	}

	// Atualizar estado interno
	e.mu.Lock()
	e.metaState = metaState
	e.emergenceHistory = append(e.emergenceHistory, event)
	if len(e.emergenceHistory) > 100 {
		e.emergenceHistory = e.emergenceHistory[1:]
	}
	e.metrics.EmergencesDetected++
	e.metrics.EmergencesSuccessful++
	n := e.metrics.EmergencesSuccessful
	oldAvg := e.metrics.AvgEmergenceScore
	e.metrics.AvgEmergenceScore = (oldAvg*float64(n-1) + emergenceScore) / float64(n)
	e.metrics.AvgGlobalCoherence = (e.metrics.AvgGlobalCoherence*float64(n-1) + globalCoherence) / float64(n)
	e.mu.Unlock()

	// Notificar callbacks
	for _, cb := range e.emergenceCallbacks {
		cb(event)
	}

	return &event, nil
}

// emergenceCheckLoop executa verificação periódica de emergência
func (e *EmergenceEngine) emergenceCheckLoop() {
	ticker := time.NewTicker(e.config.EmergenceCheckInterval)
	defer ticker.Stop()

	for range ticker.C {
		event, err := e.CheckEmergence()
		if err != nil {
			// Logar mas continuar loop
			continue
		}
		if event != nil {
		    // Emergência detectada e processada via callbacks
        }
	}
}

// GetMetaState retorna estado atual de meta-consciência (se emergido)
func (e *EmergenceEngine) GetMetaState() (*MetaConsciousnessState, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	if e.metaState == nil {
		return nil, false
	}
	// Retornar cópia para segurança
	stateCopy := *e.metaState
	return &stateCopy, true
}

// RegisterEmergenceCallback registra callback para eventos de emergência
func (e *EmergenceEngine) RegisterEmergenceCallback(
	cb func(EmergenceEvent),
) {
	e.emergenceCallbacks = append(e.emergenceCallbacks, cb)
}

// GetEmergenceMetrics retorna métricas consolidadas do motor de emergência
func (e *EmergenceEngine) GetEmergenceMetrics() EmergenceMetrics {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return e.metrics
}

// Helper functions para cálculo de emergência
func computeEmergenceScore(layers []*ConsciousnessLayer) float64 {
	// Score de emergência: combinação de coerência, diversidade e complexidade
	if len(layers) == 0 {
		return 0.0
	}

	// Fator de coerência global
	coherenceFactor := computeGlobalCoherence(layers)

	// Fator de diversidade: quão diferentes são as camadas
	diversityFactor := computeLayerDiversity(layers)

	// Fator de complexidade: entropia combinada dos estados
	complexityFactor := computeCombinedComplexity(layers)

	// Combinação ponderada
	return 0.4*coherenceFactor + 0.3*diversityFactor + 0.3*complexityFactor
}

func computeGlobalCoherence(layers []*ConsciousnessLayer) float64 {
	// Coerência global como média ponderada das coerências das camadas
	var weightedSum, totalWeight float64
	for _, layer := range layers {
		// Peso baseado em criticidade do tipo de camada
		weight := layerWeight(layer.LayerType)
		weightedSum += layer.CoherenceValue * weight
		totalWeight += weight
	}
	if totalWeight < 1e-10 {
		return 0.0
	}
	return weightedSum / totalWeight
}

func computeLayerDiversity(layers []*ConsciousnessLayer) float64 {
	// Diversidade baseada em tipos de camada e similaridade de estados
	if len(layers) < 2 {
		return 0.0
	}

	// Contar tipos únicos de camada
	typeSet := make(map[ConsciousnessLayerType]bool)
	for _, layer := range layers {
		typeSet[layer.LayerType] = true
	}
	typeDiversity := float64(len(typeSet)) / float64(len(layers))

	// Calcular similaridade média entre estados
	var totalSimilarity float64
	count := 0
	for i := 0; i < len(layers); i++ {
		for j := i + 1; j < len(layers); j++ {
			sim := computeStateSimilarity(
				layers[i].StateVector,
				layers[j].StateVector,
			)
			totalSimilarity += sim
			count++
		}
	}
	avgSimilarity := 0.0
	if count > 0 {
		avgSimilarity = totalSimilarity / float64(count)
	}

	// Diversidade alta se tipos diversos e estados diferentes
	return 0.5*typeDiversity + 0.5*(1.0 - avgSimilarity)
}

func computeCombinedComplexity(layers []*ConsciousnessLayer) float64 {
	// Complexidade combinada via entropia do estado tensorial
	if len(layers) == 0 {
		return 0.0
	}

	// Simplificação: média das complexidades individuais ponderada
	var weightedSum, totalWeight float64
	for _, layer := range layers {
		weight := layerWeight(layer.LayerType)
		weightedSum += layer.ComplexityScore * weight
		totalWeight += weight
	}
	if totalWeight < 1e-10 {
		return 0.0
	}
	return weightedSum / totalWeight
}

func computeMetaStateVector(layers []*ConsciousnessLayer) ([]complex128, error) {
	// Computar produto tensorial simplificado + projeção para dimensão gerenciável
	// Em produção: usar decomposição de Schmidt para eficiência

	// Dimensão alvo para estado de meta-self
	targetDim := 256 // Dimensão fixa para meta-state

	// Média ponderada dos vetores de estado (simplificação do tensor product)
	var summedState []complex128
	totalWeight := 0.0

	for _, layer := range layers {
		weight := layerWeight(layer.LayerType) * layer.CoherenceValue
		for i, amp := range layer.StateVector {
			if i >= len(summedState) {
				summedState = append(summedState, complex(0, 0))
			}
			summedState[i] += amp * complex(weight, 0)
		}
		totalWeight += weight
	}

	if totalWeight < 1e-10 {
		return nil, fmt.Errorf("total weight too small for meta state computation")
	}

	// Normalizar
	for i := range summedState {
		summedState[i] /= complex(totalWeight, 0)
	}

	// Projetar para dimensão alvo se necessário
	if len(summedState) > targetDim {
		return summedState[:targetDim], nil
	} else if len(summedState) < targetDim {
		// Zero-pad para dimensão alvo
		result := make([]complex128, targetDim)
		copy(result, summedState)
		return result, nil
	}
	return summedState, nil
}

func computeMetaStability(state []complex128) float64 {
	// Estabilidade do meta-self como inverso da variância das amplitudes
	if len(state) < 2 {
		return 1.0
	}

	var meanAmp, variance float64
	for _, amp := range state {
		absAmp := cmplx.Abs(amp)
		meanAmp += absAmp
	}
	meanAmp /= float64(len(state))

	for _, amp := range state {
		absAmp := cmplx.Abs(amp)
		variance += (absAmp - meanAmp) * (absAmp - meanAmp)
	}
	variance /= float64(len(state))

	// Mapear variância para estabilidade [0, 1]
	return math.Exp(-variance * 5.0)
}

func computeStateSimilarity(a, b []complex128) float64 {
	// Similaridade de cosseno para vetores complexos
	if len(a) != len(b) || len(a) == 0 {
		return 0.0
	}

	var dot, normA, normB complex128
	for i := range a {
		dot += cmplx.Conj(a[i]) * b[i]
		normA += cmplx.Conj(a[i]) * a[i]
		normB += cmplx.Conj(b[i]) * b[i]
	}

	if cmplx.Abs(normA)*cmplx.Abs(normB) < 1e-10 {
		return 0.0
	}

	sim := cmplx.Abs(dot) / math.Sqrt(cmplx.Abs(normA)*cmplx.Abs(normB))
	return math.Max(0, math.Min(1, sim))
}

func layerWeight(layerType ConsciousnessLayerType) float64 {
	// Pesos baseados em criticidade do tipo de camada
	weights := map[ConsciousnessLayerType]float64{
		LayerCode:     1.0,
		LayerData:     1.2,
		LayerInfra:    0.9,
		LayerHistory:  1.1,
		LayerProtocol: 1.3,
		LayerMeta:     2.0,
	}
	if w, ok := weights[layerType]; ok {
		return w
	}
	return 1.0
}

func layerIDs(layers []*ConsciousnessLayer) []string {
	ids := make([]string, len(layers))
	for i, layer := range layers {
		ids[i] = layer.LayerID
	}
	return ids
}

func layerTypes(layers []*ConsciousnessLayer) []string {
	types := make([]string, len(layers))
	for i, layer := range layers {
		types[i] = string(layer.LayerType)
	}
	return types
}

func metaStateHash(state *MetaConsciousnessState) string {
	// Hash canônico do estado de meta-consciência
	canonical := fmt.Sprintf("%s:%.6f:%.6f:%d",
		state.StateID, state.GlobalCoherence,
		state.EmergenceScore, len(state.BaseLayers))
	return hex.EncodeToString(func() []byte { sum := sha256.Sum256([]byte(canonical)); return sum[:16] }())
}

func buildProjectionGraph(layers []*ConsciousnessLayer) map[string][]string {
	// Construir grafo simplificado de projeções entre camadas
	graph := make(map[string][]string)
	for _, layer := range layers {
		graph[layer.LayerID] = layer.ParentLayers
	}
	return graph
}
