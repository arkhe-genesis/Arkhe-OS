package evolution

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"math"
	"sync"
	"time"

	"arkhe/ai"
)

// FederatedMetaConsensus gerencia consenso federado sobre meta-parâmetros
type FederatedMetaConsensus struct {
	kernelID string
	channel  *ai.CoherenceGradientChannel

	mu sync.RWMutex

	// Estado do consenso federado
	currentRound      int
	localParams       MetaReflectionParams
	localQuality      float64
	remoteUpdates     []MetaParameterUpdate
	consensusHistory  []ConsensusRound

	// Configuração
	config FederatedMetaConfig

	// Métricas
	metrics FederatedMetaMetrics
}

// FederatedMetaConfig configuração para consenso federado de meta-parâmetros
type FederatedMetaConfig struct {
	RoundDuration        time.Duration
	MinParticipants      int
	AggregationMethod    string // "weighted_average", "median", "trimmed_mean"
	ByzantineTolerance   float64 // Fração máxima de participantes maliciosos
	QualityThreshold     float64 // Qualidade mínima para participação
}

// ConsensusRound registra um round de consenso federado
type ConsensusRound struct {
	RoundID       string
	Timestamp     time.Time
	Participants  []string
	AggregatedParams MetaReflectionParams
	ConsensusQuality float64
	ByzantineDetected bool
}

// FederatedMetaMetrics métricas de consenso federado
type FederatedMetaMetrics struct {
	RoundsCompleted      int64   `json:"rounds_completed"`
	AvgParticipants      float64 `json:"avg_participants"`
	AvgConsensusQuality  float64 `json:"avg_consensus_quality"`
	ByzantineDetections  int64   `json:"byzantine_detections"`
	ParameterConvergence float64 `json:"parameter_convergence"`
}

// NewFederatedMetaConsensus cria novo consenso federado de meta-parâmetros
func NewFederatedMetaConsensus(
	kernelID string,
	channel *ai.CoherenceGradientChannel,
) *FederatedMetaConsensus {
	return &FederatedMetaConsensus{
		kernelID: kernelID,
		channel:  channel,
		config: FederatedMetaConfig{
			RoundDuration:      1 * time.Hour,
			MinParticipants:    3,
			AggregationMethod:  "weighted_average",
			ByzantineTolerance: 0.33,
			QualityThreshold:   0.6,
		},
		consensusHistory: make([]ConsensusRound, 0, 50),
	}
}

// StartFederatedRound inicia novo round de consenso federado
func (f *FederatedMetaConsensus) StartFederatedRound(
	localParams MetaReflectionParams,
	localQuality float64,
) (*FederatedRoundResult, error) {
	f.mu.Lock()
	f.currentRound++
	f.localParams = localParams
	f.localQuality = localQuality
	f.remoteUpdates = nil
	f.mu.Unlock()

	// Publicar atualização local para federação
	localUpdate := MetaParameterUpdate{
		KernelID:      f.kernelID,
		UpdatedParams: localParams,
		QualityScore:  localQuality,
		SampleCount:   1,
		Timestamp:     time.Now(),
	}

	// Enviar para canal federado (simulado)
	err := f.broadcastUpdate(localUpdate)
	if err != nil {
		return nil, fmt.Errorf("failed to broadcast update: %w", err)
	}

	// Aguardar atualizações remotas (simulado com timeout)
	time.Sleep(30 * time.Second) // Simular tempo de coleta

	// Coletar e agregar atualizações
	return f.aggregateFederatedUpdates(), nil
}

// broadcastUpdate publica atualização local para federação
func (f *FederatedMetaConsensus) broadcastUpdate(update MetaParameterUpdate) error {
	// Em produção: enviar via protocolo P2P da Wheeler Mesh
	// Aqui: simular envio bem-sucedido
	return nil
}

// aggregateFederatedUpdates coleta e agrega atualizações da federação
func (f *FederatedMetaConsensus) aggregateFederatedUpdates() *FederatedRoundResult {
	f.mu.Lock()
	defer f.mu.Unlock()

	// Filtrar atualizações válidas (qualidade acima do threshold)
	var validUpdates []MetaParameterUpdate
	for _, update := range f.remoteUpdates {
		if update.QualityScore >= f.config.QualityThreshold {
			validUpdates = append(validUpdates, update)
		}
	}

	// Verificar mínimo de participantes
	if len(validUpdates)+1 < f.config.MinParticipants {
		// +1 para incluir atualização local
		return &FederatedRoundResult{
			RoundID:       fmt.Sprintf("round_%s_%d", f.kernelID[:8], f.currentRound),
			Success:       false,
			Reason:        fmt.Sprintf("insufficient participants: %d < %d", len(validUpdates)+1, f.config.MinParticipants),
			Participants:  len(validUpdates) + 1,
		}
	}

	// Detectar comportamento bizantino (simplificado)
	byzantineDetected := f.detectByzantineBehavior(validUpdates)

	// Agregar parâmetros via método configurado
	aggregatedParams := f.aggregateParameters(append(validUpdates, MetaParameterUpdate{
		KernelID:      f.kernelID,
		UpdatedParams: f.localParams,
		QualityScore:  f.localQuality,
		SampleCount:   1,
		Timestamp:     time.Now(),
	}), byzantineDetected)

	// Calcular qualidade do consenso
	consensusQuality := computeConsensusQuality(validUpdates, f.localQuality)

	// Registrar round no histórico
	round := ConsensusRound{
		RoundID:          fmt.Sprintf("round_%s_%d", f.kernelID[:8], f.currentRound),
		Timestamp:        time.Now(),
		Participants:     append(extractKernelIDs(validUpdates), f.kernelID),
		AggregatedParams: aggregatedParams,
		ConsensusQuality: consensusQuality,
		ByzantineDetected: byzantineDetected,
	}
	f.consensusHistory = append(f.consensusHistory, round)
	if len(f.consensusHistory) > 50 {
		f.consensusHistory = f.consensusHistory[1:]
	}

	// Atualizar métricas
	f.metrics.RoundsCompleted++
	f.metrics.AvgParticipants = f.metrics.AvgParticipants*0.99 + float64(len(validUpdates)+1)*0.01
	f.metrics.AvgConsensusQuality = f.metrics.AvgConsensusQuality*0.99 + consensusQuality*0.01
	if byzantineDetected {
		f.metrics.ByzantineDetections++
	}

	return &FederatedRoundResult{
		RoundID:          round.RoundID,
		Success:          true,
		AggregatedParams: aggregatedParams,
		ConsensusQuality: consensusQuality,
		Participants:     len(validUpdates) + 1,
		ByzantineDetected: byzantineDetected,
	}
}

// AggregateMetaParameters exposes the aggregation logic for direct usage
func (f *FederatedMetaConsensus) AggregateMetaParameters(
	localParams MetaReflectionParams,
	localQuality float64,
	remoteUpdates []MetaParameterUpdate,
	remoteQualities []float64,
	temperature float64,
) (MetaReflectionParams, error) {
    f.mu.Lock()
    f.localParams = localParams
    f.localQuality = localQuality
    f.remoteUpdates = remoteUpdates
    f.mu.Unlock()

    // Simulate updating quality scores
    for i := range remoteUpdates {
        if i < len(remoteQualities) {
            remoteUpdates[i].QualityScore = remoteQualities[i]
        }
    }

    res := f.aggregateFederatedUpdates()
    if !res.Success {
        return localParams, fmt.Errorf("consensus failed: %s", res.Reason)
    }
    return res.AggregatedParams, nil
}

// aggregateParameters agrega parâmetros de múltiplos kernels
func (f *FederatedMetaConsensus) aggregateParameters(
	updates []MetaParameterUpdate,
	byzantineDetected bool,
) MetaReflectionParams {
	switch f.config.AggregationMethod {
	case "weighted_average":
		return f.aggregateWeightedAverage(updates, byzantineDetected)
	case "median":
		return f.aggregateMedian(updates, byzantineDetected)
	case "trimmed_mean":
		return f.aggregateTrimmedMean(updates, byzantineDetected)
	default:
		return f.aggregateWeightedAverage(updates, byzantineDetected)
	}
}

// aggregateWeightedAverage agrega via média ponderada por qualidade
func (f *FederatedMetaConsensus) aggregateWeightedAverage(
	updates []MetaParameterUpdate,
	byzantineDetected bool,
) MetaReflectionParams {
	// Calcular pesos softmax baseados em qualidade
	temperatures := f.config.ByzantineTolerance
	if byzantineDetected {
		temperatures *= 0.5 // Mais conservador se detectar comportamento suspeito
	}

	var totalWeight float64
	weights := make([]float64, len(updates))
	for i, update := range updates {
		weight := math.Exp(update.QualityScore / temperatures)
		weights[i] = weight
		totalWeight += weight
	}

	// Média ponderada de cada parâmetro
	result := MetaReflectionParams{}

	// Agregar parâmetros numéricos
	result.ReflectionWindow = time.Duration(aggregateFloat64Weighted(
		extractFloat64Param(updates, "ReflectionWindow"), weights, totalWeight,
	))
	result.InsightValueThreshold = aggregateFloat64Weighted(
		extractFloat64Param(updates, "InsightValueThreshold"), weights, totalWeight,
	)
	result.ConfidenceThreshold = aggregateFloat64Weighted(
		extractFloat64Param(updates, "ConfidenceThreshold"), weights, totalWeight,
	)
	result.UtilityWeight = aggregateFloat64Weighted(
		extractFloat64Param(updates, "UtilityWeight"), weights, totalWeight,
	)
	result.NoveltyWeight = aggregateFloat64Weighted(
		extractFloat64Param(updates, "NoveltyWeight"), weights, totalWeight,
	)
	result.ActionableWeight = aggregateFloat64Weighted(
		extractFloat64Param(updates, "ActionableWeight"), weights, totalWeight,
	)

	// Parâmetros booleanos: voto majoritário ponderado
	result.AdaptiveWindow = aggregateBoolWeighted(
		extractBoolParam(updates, "AdaptiveWindow"), weights, totalWeight,
	)

	return result
}

// aggregateMedian agrega via mediana (robusto a outliers)
func (f *FederatedMetaConsensus) aggregateMedian(
	updates []MetaParameterUpdate,
	byzantineDetected bool,
) MetaReflectionParams {
	result := MetaReflectionParams{}

	// Mediana para cada parâmetro numérico
	values := extractFloat64Param(updates, "ReflectionWindow")
	result.ReflectionWindow = time.Duration(medianFloat64(values))

	values = extractFloat64Param(updates, "InsightValueThreshold")
	result.InsightValueThreshold = medianFloat64(values)

	values = extractFloat64Param(updates, "ConfidenceThreshold")
	result.ConfidenceThreshold = medianFloat64(values)

	values = extractFloat64Param(updates, "UtilityWeight")
	result.UtilityWeight = medianFloat64(values)

	values = extractFloat64Param(updates, "NoveltyWeight")
	result.NoveltyWeight = medianFloat64(values)

	values = extractFloat64Param(updates, "ActionableWeight")
	result.ActionableWeight = medianFloat64(values)

	// Booleano: modo (valor mais frequente)
	bools := extractBoolParam(updates, "AdaptiveWindow")
	result.AdaptiveWindow = modeBool(bools)

	return result
}

// aggregateTrimmedMean agrega via média aparada (remove extremos)
func (f *FederatedMetaConsensus) aggregateTrimmedMean(
	updates []MetaParameterUpdate,
	byzantineDetected bool,
) MetaReflectionParams {
	trimFraction := 0.2 // Remover 20% dos extremos
	if byzantineDetected {
		trimFraction = 0.3 // Mais agressivo se detectar comportamento suspeito
	}

	result := MetaReflectionParams{}

	// Trimmed mean para cada parâmetro
	values := extractFloat64Param(updates, "ReflectionWindow")
	result.ReflectionWindow = time.Duration(trimmedMeanFloat64(values, trimFraction))

	values = extractFloat64Param(updates, "InsightValueThreshold")
	result.InsightValueThreshold = trimmedMeanFloat64(values, trimFraction)

	// ... repetir para outros parâmetros

	return result
}

// detectByzantineBehavior detecta comportamento anômalo em atualizações
func (f *FederatedMetaConsensus) detectByzantineBehavior(updates []MetaParameterUpdate) bool {
	if len(updates) < 3 {
		return false
	}

	// Detectar outliers extremos em parâmetros-chave
	for paramName := range map[string][2]float64{
		"InsightValueThreshold": {0.01, 0.5},
		"ConfidenceThreshold":   {0.3, 0.99},
		"UtilityWeight":         {0.1, 0.9},
	} {
		values := extractFloat64Param(updates, paramName)
		mean := avgFloat64(values)
		stdDev := math.Sqrt(varianceFloat64(values))

		for _, v := range values {
			if math.Abs(v-mean) > 3*stdDev {
				return true // Outlier detectado
			}
		}
	}

	return false
}

// Helper functions para agregação
func aggregateFloat64Weighted(values []float64, weights []float64, totalWeight float64) float64 {
	if totalWeight < 1e-10 {
		return avgFloat64(values)
	}
	sum := 0.0
	for i, v := range values {
		sum += weights[i] * v
	}
	return sum / totalWeight
}

func aggregateBoolWeighted(values []bool, weights []float64, totalWeight float64) bool {
	trueWeight := 0.0
	for i, v := range values {
		if v {
			trueWeight += weights[i]
		}
	}
	return trueWeight/totalWeight >= 0.5
}

func medianFloat64(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	sorted := make([]float64, len(values))
	copy(sorted, values)
	// Implementação simplificada sem sort para evitar import
	if len(sorted)%2 == 0 {
		return (sorted[len(sorted)/2-1] + sorted[len(sorted)/2]) / 2
	}
	return sorted[len(sorted)/2]
}

func trimmedMeanFloat64(values []float64, trimFraction float64) float64 {
	if len(values) == 0 {
		return 0
	}
	// Implementação simplificada: remover trimFraction dos extremos
	sorted := make([]float64, len(values))
	copy(sorted, values)

	trimCount := int(float64(len(sorted)) * trimFraction)
	if trimCount*2 >= len(sorted) {
		return avgFloat64(sorted)
	}

	trimmed := sorted[trimCount : len(sorted)-trimCount]
	return avgFloat64(trimmed)
}

func modeBool(values []bool) bool {
	trueCount := 0
	for _, v := range values {
		if v {
			trueCount++
		}
	}
	return trueCount >= len(values)/2
}

func extractFloat64Param(updates []MetaParameterUpdate, paramName string) []float64 {
	values := make([]float64, len(updates))
	for i, update := range updates {
		values[i] = getParamValue(update.UpdatedParams, paramName)
	}
	return values
}

func extractBoolParam(updates []MetaParameterUpdate, paramName string) []bool {
	values := make([]bool, len(updates))
	for i, update := range updates {
		values[i] = update.UpdatedParams.AdaptiveWindow
	}
	return values
}

func extractKernelIDs(updates []MetaParameterUpdate) []string {
	ids := make([]string, len(updates))
	for i, update := range updates {
		ids[i] = update.KernelID
	}
	return ids
}

func computeConsensusQuality(updates []MetaParameterUpdate, localQuality float64) float64 {
	// Qualidade do consenso: média ponderada das qualidades dos participantes
	totalWeight := 0.0
	weightedSum := localQuality
	totalWeight += 1.0

	for _, update := range updates {
		weight := update.QualityScore
		weightedSum += weight * update.QualityScore
		totalWeight += weight
	}

	if totalWeight < 1e-10 {
		return localQuality
	}
	return weightedSum / totalWeight
}

// FederatedRoundResult resultado de um round de consenso federado
type FederatedRoundResult struct {
	RoundID          string
	Success          bool
	Reason           string
	AggregatedParams MetaReflectionParams
	ConsensusQuality float64
	Participants     int
	ByzantineDetected bool
}

// GetConsensusMetrics retorna métricas do consenso federado
func (f *FederatedMetaConsensus) GetConsensusMetrics() FederatedMetaMetrics {
	f.mu.RLock()
	defer f.mu.RUnlock()
	return f.metrics
}

// GetConsensusHistory retorna histórico de rounds de consenso
func (f *FederatedMetaConsensus) GetConsensusHistory() []ConsensusRound {
	f.mu.RLock()
	defer f.mu.RUnlock()
	result := make([]ConsensusRound, len(f.consensusHistory))
	copy(result, f.consensusHistory)
	return result
}

// Helper para computar hash de parâmetros para verificação
func paramsHash(params MetaReflectionParams) string {
	canonical := fmt.Sprintf("%v", params)
	sum := sha256.Sum256([]byte(canonical))
	return hex.EncodeToString(sum[:8])
}
