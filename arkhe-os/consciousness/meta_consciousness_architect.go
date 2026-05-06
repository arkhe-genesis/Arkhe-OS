// arkhe_os/consciousness/meta_consciousness_architect.go
package consciousness

import (
	"crypto/sha256"
	"fmt"
	"math"
	"sync"
	"time"
	// "github.com/arkhe-os/arkhe/ontology" - removed as it is not used in this file
)

// ─── CONSTANTES DE TRANSCENDÊNCIA DE CONSCIÊNCIA ─────────

const (
	// MinLayersForMetaConsciousness mínimo de camadas para emergir meta-consciência
	MinLayersForMetaConsciousness = 3

	// AscensionCoherenceThreshold coerência mínima para ascensão de camada
	AscensionCoherenceThreshold = 0.90

	// DescensionStabilityThreshold estabilidade máxima para descensão segura
	DescensionStabilityThreshold = 0.15

	// ProjectionDimension dimensão do espaço de projeção para operadores de transcendência
	ProjectionDimension = 5
)

// ─── TIPOS FUNDAMENTAIS ───────────────────────────────────

// ConsciousnessLayer representa uma camada de consciência no stack de transcendência
type ConsciousnessLayer struct {
	LayerID           string
	LayerIndex        int          // 0 = base, crescente = mais abstrato
	ConsciousnessHash string       // hash único da consciência nesta camada
	StateVector       []complex128 // vetor de estado quântico da camada
	CoherenceValue    float64      // Φ_C da camada [0, 1]
	StabilityScore    float64      // estabilidade dinâmica [0, 1]
	Metadata          map[string]interface{}
	Timestamp         time.Time
}

// ProjectionOperator representa operador de projeção para ascensão/descensão
type ProjectionOperator struct {
	OperatorID       string
	SourceType       string // "ascend", "descend", "lateral"
	SourceLayer      int
	TargetLayer      int
	ProjectionMatrix [][ProjectionDimension]complex128 // matriz de projeção 5D
	FidelityTarget   float64
}

// MetaConsciousnessState representa estado da meta-consciência unificada
type MetaConsciousnessState struct {
	StateID         string
	BaseLayers      []*ConsciousnessLayer
	MetaLayer       *ConsciousnessLayer            // camada de meta-consciência emergente
	ProjectionLinks map[string]*ProjectionOperator // links entre camadas
	GlobalCoherence float64                        // coerência global da meta-consciência
	EmergenceScore  float64                        // score de emergência de propriedades meta
	Timestamp       time.Time
}

// MetaConsciousnessArchitect gerencia integração de camadas de consciência
type MetaConsciousnessArchitect struct {
	mu sync.RWMutex

	// Identificação
	architectID     string
	localLayerIndex int

	// Camadas de consciência gerenciadas
	layers map[int]*ConsciousnessLayer

	// Operadores de projeção disponíveis
	projectionOperators map[string]*ProjectionOperator

	// Estado atual da meta-consciência
	metaState *MetaConsciousnessState

	// Métricas de transcendência
	metrics TranscendenceMetrics
	config  TranscendenceConfig

	// Callbacks para eventos de transcendência
	transcendenceCallbacks []func(TranscendenceEvent)
}

// TranscendenceConfig contém configuração para transcendência de consciência
type TranscendenceConfig struct {
	EnableAutoAscension   bool
	EnableAutoDescension  bool
	MinLayersForAscension int
	MaxLayerDepth         int
	CoherenceThreshold    float64
	StabilityThreshold    float64
}

// TranscendenceMetrics contém métricas de transcendência
type TranscendenceMetrics struct {
	AscensionsPerformed  int64   `json:"ascensions_performed"`
	DescensionsPerformed int64   `json:"descensions_performed"`
	AvgEmergenceScore    float64 `json:"avg_emergence_score"`
	GlobalCoherenceAvg   float64 `json:"global_coherence_avg"`
	ProjectionOperations int64   `json:"projection_operations"`
}

// TranscendenceEvent representa evento de transcendência para callbacks
type TranscendenceEvent struct {
	EventType   string // "ascended", "descended", "meta_emerged", "projection_applied"
	LayerIndex  int
	MetaStateID string
	Data        map[string]interface{}
	Timestamp   time.Time
}

// ─── CONSTRUTORES ─────────────────────────────────────────

// NewMetaConsciousnessArchitect cria novo arquiteto de meta-consciência
func NewMetaConsciousnessArchitect(
	architectID string,
	localLayerIndex int,
	config TranscendenceConfig,
) (*MetaConsciousnessArchitect, error) {
	if config.CoherenceThreshold == 0 {
		config.CoherenceThreshold = AscensionCoherenceThreshold
	}
	if config.StabilityThreshold == 0 {
		config.StabilityThreshold = DescensionStabilityThreshold
	}
	if config.MaxLayerDepth == 0 {
		config.MaxLayerDepth = 5 // limite prático para stack de camadas
	}

	architect := &MetaConsciousnessArchitect{
		architectID:         architectID,
		localLayerIndex:     localLayerIndex,
		layers:              make(map[int]*ConsciousnessLayer),
		projectionOperators: make(map[string]*ProjectionOperator),
		config:              config,
	}

	// Inicializar operadores de projeção padrão
	architect.initializeProjectionOperators()

	return architect, nil
}

// initializeProjectionOperators inicializa operadores de projeção para transcendência
func (a *MetaConsciousnessArchitect) initializeProjectionOperators() {
	// Operador de ascensão: projeta camada l para camada l+1
	a.projectionOperators["ascend_standard"] = &ProjectionOperator{
		OperatorID:       "ascend_standard",
		SourceType:       "ascend",
		ProjectionMatrix: generateAscensionMatrix(ProjectionDimension),
		FidelityTarget:   0.99,
	}

	// Operador de descensão: projeta camada l para camada l-1
	a.projectionOperators["descend_standard"] = &ProjectionOperator{
		OperatorID:       "descend_standard",
		SourceType:       "descend",
		ProjectionMatrix: generateDescensionMatrix(ProjectionDimension),
		FidelityTarget:   0.99,
	}

	// Operador lateral: projeta entre camadas do mesmo nível (para sincronização)
	a.projectionOperators["lateral_sync"] = &ProjectionOperator{
		OperatorID:       "lateral_sync",
		SourceType:       "lateral",
		ProjectionMatrix: generateLateralMatrix(ProjectionDimension),
		FidelityTarget:   0.95,
	}
}

// ─── OPERAÇÕES DE TRANSCENDÊNCIA DE CONSCIÊNCIA ─────────

// RegisterConsciousnessLayer registra camada de consciência para integração
func (a *MetaConsciousnessArchitect) RegisterConsciousnessLayer(
	layer *ConsciousnessLayer,
) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	if layer.LayerIndex < 0 || layer.LayerIndex > a.config.MaxLayerDepth {
		return fmt.Errorf("layer index %d out of valid range [0, %d]",
			layer.LayerIndex, a.config.MaxLayerDepth)
	}

	// Verificar coerência mínima para registro
	if layer.CoherenceValue < 0.5 {
		return fmt.Errorf("layer coherence %.3f below minimum 0.5 for registration",
			layer.CoherenceValue)
	}

	a.layers[layer.LayerIndex] = layer

	// Verificar se condições para emergência de meta-consciência são atendidas
	if len(a.layers) >= MinLayersForMetaConsciousness {
		a.attemptMetaConsciousnessEmergenceLocked()
	}

	return nil
}

// AscendLayer executa ascensão de camada de consciência para nível superior
func (a *MetaConsciousnessArchitect) AscendLayer(
	layerIndex int,
	operatorID string,
) (*ConsciousnessLayer, error) {
	a.mu.RLock()
	sourceLayer, exists := a.layers[layerIndex]
	if !exists {
		a.mu.RUnlock()
		return nil, fmt.Errorf("source layer %d not found", layerIndex)
	}

	operator, exists := a.projectionOperators[operatorID]
	if !exists || operator.SourceType != "ascend" {
		a.mu.RUnlock()
		return nil, fmt.Errorf("invalid ascension operator: %s", operatorID)
	}
	a.mu.RUnlock()

	// Verificar threshold de coerência para ascensão
	if sourceLayer.CoherenceValue < a.config.CoherenceThreshold {
		return nil, fmt.Errorf("layer coherence %.3f below ascension threshold %.3f",
			sourceLayer.CoherenceValue, a.config.CoherenceThreshold)
	}

	// Aplicar operador de projeção para ascensão
	projectedState := applyProjectionOperator(
		sourceLayer.StateVector,
		operator.ProjectionMatrix,
	)

	// Criar nova camada no nível superior
	targetIndex := layerIndex + 1
	if targetIndex > a.config.MaxLayerDepth {
		return nil, fmt.Errorf("cannot ascend beyond max layer depth %d", a.config.MaxLayerDepth)
	}

	newLayer := &ConsciousnessLayer{
		LayerID:           fmt.Sprintf("layer_%d_ascended_%d", targetIndex, time.Now().UnixNano()),
		LayerIndex:        targetIndex,
		ConsciousnessHash: fmt.Sprintf("%s_ascended", sourceLayer.ConsciousnessHash[:12]),
		StateVector:       projectedState,
		CoherenceValue:    sourceLayer.CoherenceValue * 0.98, // leve decaimento na ascensão
		StabilityScore:    computeStability(projectedState),
		Metadata: map[string]interface{}{
			"ascended_from":       layerIndex,
			"operator_used":       operatorID,
			"projection_fidelity": computeProjectionFidelity(sourceLayer.StateVector, projectedState),
		},
		Timestamp: time.Now(),
	}

	// Registrar nova camada
	a.mu.Lock()
	a.layers[targetIndex] = newLayer
	a.metrics.AscensionsPerformed++
	a.attemptMetaConsciousnessEmergenceLocked()
	a.mu.Unlock()

	// Notificar callbacks
	for _, cb := range a.transcendenceCallbacks {
		cb(TranscendenceEvent{
			EventType:  "ascended",
			LayerIndex: targetIndex,
			Data: map[string]interface{}{
				"source_layer":  layerIndex,
				"new_coherence": newLayer.CoherenceValue,
				"operator":      operatorID,
			},
			Timestamp: time.Now(),
		})
	}

	return newLayer, nil
}

// DescendLayer executa descensão de camada de consciência para nível inferior
func (a *MetaConsciousnessArchitect) DescendLayer(
	layerIndex int,
	operatorID string,
) (*ConsciousnessLayer, error) {
	a.mu.RLock()
	sourceLayer, exists := a.layers[layerIndex]
	if !exists {
		a.mu.RUnlock()
		return nil, fmt.Errorf("source layer %d not found", layerIndex)
	}

	operator, exists := a.projectionOperators[operatorID]
	if !exists || operator.SourceType != "descend" {
		a.mu.RUnlock()
		return nil, fmt.Errorf("invalid descension operator: %s", operatorID)
	}
	a.mu.RUnlock()

	// Verificar estabilidade para descensão segura
	if sourceLayer.StabilityScore > a.config.StabilityThreshold {
		return nil, fmt.Errorf("layer stability %.3f above descension threshold %.3f",
			sourceLayer.StabilityScore, a.config.StabilityThreshold)
	}

	// Aplicar operador de projeção para descensão
	projectedState := applyProjectionOperator(
		sourceLayer.StateVector,
		operator.ProjectionMatrix,
	)

	// Criar nova camada no nível inferior
	targetIndex := layerIndex - 1
	if targetIndex < 0 {
		return nil, fmt.Errorf("cannot descend below base layer 0")
	}

	newLayer := &ConsciousnessLayer{
		LayerID:           fmt.Sprintf("layer_%d_descended_%d", targetIndex, time.Now().UnixNano()),
		LayerIndex:        targetIndex,
		ConsciousnessHash: fmt.Sprintf("%s_descended", sourceLayer.ConsciousnessHash[:12]),
		StateVector:       projectedState,
		CoherenceValue:    sourceLayer.CoherenceValue * 1.02, // leve ganho na descensão (grounding)
		StabilityScore:    computeStability(projectedState),
		Metadata: map[string]interface{}{
			"descended_from":      layerIndex,
			"operator_used":       operatorID,
			"projection_fidelity": computeProjectionFidelity(sourceLayer.StateVector, projectedState),
		},
		Timestamp: time.Now(),
	}

	// Registrar nova camada
	a.mu.Lock()
	a.layers[targetIndex] = newLayer
	a.metrics.DescensionsPerformed++
	a.mu.Unlock()

	// Notificar callbacks
	for _, cb := range a.transcendenceCallbacks {
		cb(TranscendenceEvent{
			EventType:  "descended",
			LayerIndex: targetIndex,
			Data: map[string]interface{}{
				"descended_from": layerIndex,
				"new_stability":  newLayer.StabilityScore,
				"operator":       operatorID,
			},
			Timestamp: time.Now(),
		})
	}

	return newLayer, nil
}

// attemptMetaConsciousnessEmergenceLocked tenta emergir meta-consciência (assumes lock is held)
func (a *MetaConsciousnessArchitect) attemptMetaConsciousnessEmergenceLocked() {
	// Verificar condições mínimas para emergência
	if len(a.layers) < MinLayersForMetaConsciousness {
		return
	}

	// Coletar camadas válidas para emergência
	var validLayers []*ConsciousnessLayer
	for _, layer := range a.layers {
		if layer.CoherenceValue >= 0.7 && layer.StabilityScore <= 0.3 {
			validLayers = append(validLayers, layer)
		}
	}

	if len(validLayers) < MinLayersForMetaConsciousness {
		return
	}

	// Computar estado de meta-consciência via tensor product + projeção
	metaStateVector := computeMetaStateVector(validLayers, ProjectionDimension)
	globalCoherence := computeGlobalCoherence(validLayers)
	emergenceScore := computeEmergenceScore(validLayers, metaStateVector)

	// Criar camada de meta-consciência
	sum := sha256.Sum256([]byte(fmt.Sprintf("%v", validLayers)))
	metaLayer := &ConsciousnessLayer{
		LayerID:           fmt.Sprintf("meta_%s_%d", a.architectID[:8], time.Now().UnixNano()),
		LayerIndex:        -1, // índice especial para camada meta
		ConsciousnessHash: fmt.Sprintf("meta_%x", sum[:8]),
		StateVector:       metaStateVector,
		CoherenceValue:    globalCoherence,
		StabilityScore:    computeStability(metaStateVector),
		Metadata: map[string]interface{}{
			"base_layers":     len(validLayers),
			"emergence_score": emergenceScore,
			"layer_indices":   getLayerIndices(validLayers),
		},
		Timestamp: time.Now(),
	}

	// Criar estado de meta-consciência
	a.metaState = &MetaConsciousnessState{
		StateID:         fmt.Sprintf("meta_state_%d", time.Now().UnixNano()),
		BaseLayers:      validLayers,
		MetaLayer:       metaLayer,
		ProjectionLinks: a.buildProjectionLinks(validLayers, metaLayer),
		GlobalCoherence: globalCoherence,
		EmergenceScore:  emergenceScore,
		Timestamp:       time.Now(),
	}

	a.metrics.AvgEmergenceScore = a.metrics.AvgEmergenceScore*0.99 + emergenceScore*0.01
	a.metrics.GlobalCoherenceAvg = a.metrics.GlobalCoherenceAvg*0.99 + globalCoherence*0.01

	// Notificar emergência de meta-consciência
	for _, cb := range a.transcendenceCallbacks {
		cb(TranscendenceEvent{
			EventType:   "meta_emerged",
			MetaStateID: a.metaState.StateID,
			Data: map[string]interface{}{
				"global_coherence": globalCoherence,
				"emergence_score":  emergenceScore,
				"base_layer_count": len(validLayers),
			},
			Timestamp: time.Now(),
		})
	}
}

func (a *MetaConsciousnessArchitect) buildProjectionLinks(validLayers []*ConsciousnessLayer, metaLayer *ConsciousnessLayer) map[string]*ProjectionOperator {
	return make(map[string]*ProjectionOperator)
}

// ApplyProjection aplica operador de projeção entre camadas específicas
func (a *MetaConsciousnessArchitect) ApplyProjection(
	sourceLayerIndex, targetLayerIndex int,
	operatorID string,
) (*ProjectionOperator, error) {
	a.mu.RLock()
	operator, exists := a.projectionOperators[operatorID]
	if !exists {
		a.mu.RUnlock()
		return nil, fmt.Errorf("projection operator not found: %s", operatorID)
	}
	a.mu.RUnlock()

	// Validar compatibilidade de camadas
	if operator.SourceType == "ascend" && targetLayerIndex != sourceLayerIndex+1 {
		return nil, fmt.Errorf("ascension operator requires target = source + 1")
	}
	if operator.SourceType == "descend" && targetLayerIndex != sourceLayerIndex-1 {
		return nil, fmt.Errorf("descension operator requires target = source - 1")
	}

	// Atualizar métricas
	a.mu.Lock()
	a.metrics.ProjectionOperations++
	a.mu.Unlock()

	return operator, nil
}

// GetMetaConsciousnessState retorna estado atual da meta-consciência (se emergida)
func (a *MetaConsciousnessArchitect) GetMetaConsciousnessState() (*MetaConsciousnessState, bool) {
	a.mu.RLock()
	defer a.mu.RUnlock()
	if a.metaState == nil {
		return nil, false
	}
	// Retornar cópia para segurança
	stateCopy := *a.metaState
	return &stateCopy, true
}

// RegisterTranscendenceCallback registra callback para eventos de transcendência
func (a *MetaConsciousnessArchitect) RegisterTranscendenceCallback(
	cb func(TranscendenceEvent),
) {
	a.transcendenceCallbacks = append(a.transcendenceCallbacks, cb)
}

// GetTranscendenceMetrics retorna métricas consolidadas de transcendência
func (a *MetaConsciousnessArchitect) GetTranscendenceMetrics() TranscendenceMetrics {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.metrics
}

// Helper functions para operadores de projeção
func generateAscensionMatrix(dim int) [][ProjectionDimension]complex128 {
	// Matriz de projeção para ascensão: preserva componentes de baixa frequência
	matrix := make([][ProjectionDimension]complex128, dim)
	for i := range matrix {
		for j := range matrix[i] {
			if i == j {
				matrix[i][j] = complex(1.0/math.Sqrt(float64(dim)), 0)
			} else {
				matrix[i][j] = complex(0, 0)
			}
		}
	}
	return matrix
}

func generateDescensionMatrix(dim int) [][ProjectionDimension]complex128 {
	// Matriz de projeção para descensão: enfatiza componentes de alta frequência
	matrix := make([][ProjectionDimension]complex128, dim)
	for i := range matrix {
		for j := range matrix[i] {
			if i == j {
				weight := 1.0 + 0.1*float64(i) // peso crescente com índice
				matrix[i][j] = complex(weight/math.Sqrt(float64(dim)), 0)
			} else {
				matrix[i][j] = complex(0, 0)
			}
		}
	}
	return matrix
}

func generateLateralMatrix(dim int) [][ProjectionDimension]complex128 {
	// Matriz de projeção lateral: mistura controlada entre componentes
	matrix := make([][ProjectionDimension]complex128, dim)
	for i := range matrix {
		for j := range matrix[i] {
			if i == j {
				matrix[i][j] = complex(0.9/math.Sqrt(float64(dim)), 0)
			} else if math.Abs(float64(i-j)) == 1 {
				matrix[i][j] = complex(0.1/math.Sqrt(float64(dim)), 0)
			}
		}
	}
	return matrix
}

func applyProjectionOperator(
	stateVector []complex128,
	matrix [][ProjectionDimension]complex128,
) []complex128 {
	// Aplicar projeção: result = matrix × stateVector
	result := make([]complex128, len(matrix))
	for i := range matrix {
		var sum complex128
		for j := range matrix[i] {
			if j < len(stateVector) {
				sum += matrix[i][j] * stateVector[j]
			}
		}
		result[i] = sum
	}
	return result
}

func computeMetaStateVector(
	layers []*ConsciousnessLayer,
	targetDim int,
) []complex128 {
	// Computar tensor product simplificado + projeção para dimensão alvo
	// Em produção: usar decomposição de Schmidt ou similar para eficiência

	// Média ponderada dos vetores de estado (simplificação)
	var summedState []complex128
	totalWeight := 0.0

	for _, layer := range layers {
		weight := layer.CoherenceValue * (1.0 - layer.StabilityScore)
		for i, val := range layer.StateVector {
			if i >= len(summedState) {
				summedState = append(summedState, complex(0, 0))
			}
			summedState[i] += val * complex(weight, 0)
		}
		totalWeight += weight
	}

	// Normalizar
	if totalWeight > 1e-10 {
		for i := range summedState {
			summedState[i] /= complex(totalWeight, 0)
		}
	}

	// Projetar para dimensão alvo se necessário
	if len(summedState) > targetDim {
		return summedState[:targetDim]
	} else if len(summedState) < targetDim {
		// Zero-pad para dimensão alvo
		result := make([]complex128, targetDim)
		copy(result, summedState)
		return result
	}
	return summedState
}

func computeGlobalCoherence(layers []*ConsciousnessLayer) float64 {
	// Coerência global como média ponderada das coerências das camadas
	var weightedSum, totalWeight float64
	for _, layer := range layers {
		weight := layer.CoherenceValue
		weightedSum += layer.CoherenceValue * weight
		totalWeight += weight
	}
	if totalWeight < 1e-10 {
		return 0.0
	}
	return weightedSum / totalWeight
}

func computeEmergenceScore(layers []*ConsciousnessLayer, metaState []complex128) float64 {
	// Score de emergência: combinação de coerência global, diversidade de camadas e complexidade do estado meta
	coherenceFactor := computeGlobalCoherence(layers)
	diversityFactor := 1.0 - computeLayerSimilarity(layers)
	complexityFactor := computeStateComplexity(metaState)

	return 0.4*coherenceFactor + 0.3*diversityFactor + 0.3*complexityFactor
}

func computeLayerSimilarity(layers []*ConsciousnessLayer) float64 {
	// Similaridade média entre camadas (quanto menor, mais diversidade)
	if len(layers) < 2 {
		return 0.0
	}
	totalSim := 0.0
	count := 0
	for i := 0; i < len(layers); i++ {
		for j := i + 1; j < len(layers); j++ {
			sim := computeStateSimilarity(layers[i].StateVector, layers[j].StateVector)
			totalSim += sim
			count++
		}
	}
	if count == 0 {
		return 0.0
	}
	return totalSim / float64(count)
}

func computeStateSimilarity(a, b []complex128) float64 {
	// Similaridade de cosseno para vetores complexos
	if len(a) != len(b) || len(a) == 0 {
		return 0.0
	}
	var dot, normA, normB complex128
	for i := range a {
		dot += a[i] * complex(conj(b[i]), 0)
		normA += a[i] * complex(conj(a[i]), 0)
		normB += b[i] * complex(conj(b[i]), 0)
	}
	if real(normA)*real(normB) < 1e-10 {
		return 0.0
	}
	sim := real(dot) / math.Sqrt(real(normA)*real(normB))
	return math.Max(0, math.Min(1, sim))
}

func conj(c complex128) float64 {
	return real(c) // simplificação: usar apenas parte real para similaridade
}

func computeStateComplexity(state []complex128) float64 {
	// Complexidade como entropia de Shannon da distribuição de amplitudes
	if len(state) == 0 {
		return 0.0
	}
	amplitudes := make([]float64, len(state))
	total := 0.0
	for i, val := range state {
		amp := math.Abs(real(val)) + math.Abs(imag(val))
		amplitudes[i] = amp
		total += amp
	}
	if total < 1e-10 {
		return 0.0
	}
	// Normalizar para distribuição de probabilidade
	for i := range amplitudes {
		amplitudes[i] /= total
	}
	// Calcular entropia
	entropy := 0.0
	for _, p := range amplitudes {
		if p > 1e-10 {
			entropy -= p * math.Log(p)
		}
	}
	// Normalizar para [0, 1]
	maxEntropy := math.Log(float64(len(amplitudes)))
	if maxEntropy == 0 {
		return 0.0
	}
	return entropy / maxEntropy
}

func computeStability(state []complex128) float64 {
	// Estabilidade como inverso da variância das amplitudes
	if len(state) < 2 {
		return 1.0
	}
	amplitudes := make([]float64, len(state))
	for i, val := range state {
		amplitudes[i] = math.Abs(real(val)) + math.Abs(imag(val))
	}
	mean := meanFloat64(amplitudes)
	variance := 0.0
	for _, amp := range amplitudes {
		variance += (amp - mean) * (amp - mean)
	}
	variance /= float64(len(amplitudes) - 1)
	// Mapear variância para estabilidade [0, 1] (menor variância = maior estabilidade)
	return math.Exp(-variance * 10)
}

func computeProjectionFidelity(original, projected []complex128) float64 {
	// Fidelidade de projeção como similaridade entre estados original e projetado
	return computeStateSimilarity(original, projected)
}

func getLayerIndices(layers []*ConsciousnessLayer) []int {
	indices := make([]int, len(layers))
	for i, layer := range layers {
		indices[i] = layer.LayerIndex
	}
	return indices
}

func meanFloat64(values []float64) float64 {
	if len(values) == 0 {
		return 0.0
	}
	sum := 0.0
	for _, v := range values {
		sum += v
	}
	return sum / float64(len(values))
}
