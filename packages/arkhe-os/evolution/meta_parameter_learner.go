package evolution

import (
	"fmt"
	"math"
	"sync"
	"time"
)

// MetaParameterLearner aprende parâmetros ótimos para processo de reflexão
type MetaParameterLearner struct {
	kernelID string
	params   MetaReflectionParams
	mu       sync.RWMutex

	// Histórico de atualizações para estimativa de gradientes
	updateHistory []ParameterUpdateRecord

	// Estado do otimizador meta
	metaOptimizerState MetaOptimizerState
}

// ParameterUpdateRecord registra uma atualização de parâmetros
type ParameterUpdateRecord struct {
	Timestamp      time.Time
	OldParams      MetaReflectionParams
	NewParams      MetaReflectionParams
	QualityBefore  float64
	QualityAfter   float64
	Context        map[string]interface{}
}

// MetaOptimizerState estado interno do otimizador de meta-parâmetros
type MetaOptimizerState struct {
	FirstMoment  map[string]float64 // Para Adam-like optimization
	SecondMoment map[string]float64
	Step         int
}

// MetaParameterUpdate representa uma atualização proposta de parâmetros
type MetaParameterUpdate struct {
	KernelID      string
	UpdatedParams MetaReflectionParams
	QualityScore  float64
	SampleCount   int
	Timestamp     time.Time
}

// NewMetaParameterLearner cria novo aprendiz de parâmetros meta-reflexivos
func NewMetaParameterLearner(kernelID string, initialParams MetaReflectionParams) *MetaParameterLearner {
	return &MetaParameterLearner{
		kernelID: kernelID,
		params:   initialParams,
		metaOptimizerState: MetaOptimizerState{
			FirstMoment:  make(map[string]float64),
			SecondMoment: make(map[string]float64),
			Step:         0,
		},
	}
}

// ComputeMetaGradients calcula gradientes meta para ajuste de parâmetros
func (l *MetaParameterLearner) ComputeMetaGradients(
	episodes []MetaReflectionEpisode,
	qualityScores []float64,
) (map[string]float64, error) {
	l.mu.Lock()
	defer l.mu.Unlock()

	if len(episodes) != len(qualityScores) {
		return nil, fmt.Errorf("episode/quality count mismatch")
	}

	gradients := make(map[string]float64)

	// Calcular gradientes via diferenças finitas em parâmetros-chave
	paramNames := []string{
		"ReflectionWindow",
		"InsightValueThreshold",
		"ConfidenceThreshold",
		"UtilityWeight",
		"NoveltyWeight",
		"ActionableWeight",
	}

	for _, paramName := range paramNames {
		// Gradiente aproximado: (f(x+ε) - f(x-ε)) / 2ε
		// Simplificação: usar correlação entre valor do parâmetro e qualidade
		paramValues := make([]float64, len(episodes))
		for i, ep := range episodes {
			paramValues[i] = extractParamFromEpisode(ep, paramName)
		}

		corr := computeCorrelation(paramValues, qualityScores)
		gradients[paramName] = corr * 0.01 // Scale gradient

		// Registrar para otimizador Adam-like
		l.updateOptimizerState(paramName, gradients[paramName])
	}

	// Aplicar atualização via Adam-like rule
	l.applyMetaUpdate(gradients)

	return gradients, nil
}

// updateOptimizerState atualiza estado do otimizador meta (Adam-like)
func (l *MetaParameterLearner) updateOptimizerState(paramName string, gradient float64) {
	l.metaOptimizerState.Step++
	step := float64(l.metaOptimizerState.Step)

	beta1, beta2 := 0.9, 0.999
	epsilon := 1e-8

	// Update moments
	l.metaOptimizerState.FirstMoment[paramName] = beta1*l.metaOptimizerState.FirstMoment[paramName] + (1-beta1)*gradient
	l.metaOptimizerState.SecondMoment[paramName] = beta2*l.metaOptimizerState.SecondMoment[paramName] + (1-beta2)*gradient*gradient

	// Bias correction
	mHat := l.metaOptimizerState.FirstMoment[paramName] / (1 - math.Pow(beta1, step))
	vHat := l.metaOptimizerState.SecondMoment[paramName] / (1 - math.Pow(beta2, step))

	// Gradient atualizado (armazenado para aplicação posterior)
	_ = mHat / (math.Sqrt(vHat) + epsilon)
}

// applyMetaUpdate aplica atualização de parâmetros baseada em gradientes
func (l *MetaParameterLearner) applyMetaUpdate(gradients map[string]float64) {
	learningRate := 0.01 // Meta-learning rate

	for paramName, gradient := range gradients {
		currentValue := getParamValue(l.params, paramName)
		newValue := currentValue - learningRate*gradient

		// Aplicar bounds e validação
		newValue = clampParamValue(paramName, newValue)
		setParamValue(&l.params, paramName, newValue)
	}

	// Registrar atualização
	l.updateHistory = append(l.updateHistory, ParameterUpdateRecord{
		Timestamp:     time.Now(),
		OldParams:     l.params, // Cópia seria ideal
		NewParams:     l.params,
		QualityBefore: 0, // Preencher se disponível
		QualityAfter:  0,
	})
	if len(l.updateHistory) > 100 {
		l.updateHistory = l.updateHistory[len(l.updateHistory)-100:]
	}
}

// GenerateAdaptiveWindow calcula janela de reflexão adaptativa baseada em volatilidade
func (l *MetaParameterLearner) GenerateAdaptiveWindow(
	recentCoherence []float64,
	operatingRegime string,
) time.Duration {
	if len(recentCoherence) < 10 {
		return l.params.ReflectionWindow
	}

	// Calcular volatilidade da coerência
	variance := varianceFloat64(recentCoherence)

	// Regime-adaptive: diferentes regimes precisam de diferentes janelas
	baseWindow := l.params.ReflectionWindow

	switch operatingRegime {
	case "peak_load", "degraded":
		// Regimes instáveis: janela menor para resposta rápida
		return time.Duration(float64(baseWindow) * 0.5)
	case "idle":
		// Regime estável: janela maior para análise mais profunda
		return time.Duration(float64(baseWindow) * 1.5)
	default:
		// Normal: ajustar baseado em volatilidade
		if variance > 0.01 {
			return time.Duration(float64(baseWindow) * 0.7)
		} else if variance < 0.001 {
			return time.Duration(float64(baseWindow) * 1.3)
		}
		return baseWindow
	}
}

// GetOptimalThresholds retorna thresholds otimizados baseado em histórico
func (l *MetaParameterLearner) GetOptimalThresholds(
	historicalEpisodes []MetaReflectionEpisode,
) (insightThreshold, confidenceThreshold float64) {
	// Encontrar thresholds que maximizam qualidade de insights selecionados
	bestInsightThreshold := l.params.InsightValueThreshold
	bestConfidenceThreshold := l.params.ConfidenceThreshold
	bestScore := -math.MaxFloat64

	// Grid search simplificado
	for it := 0.1; it <= 0.5; it += 0.05 {
		for ct := 0.5; ct <= 0.95; ct += 0.05 {
			score := l.evaluateThresholds(historicalEpisodes, it, ct)
			if score > bestScore {
				bestScore = score
				bestInsightThreshold = it
				bestConfidenceThreshold = ct
			}
		}
	}

	return bestInsightThreshold, bestConfidenceThreshold
}

// evaluateThresholds avalia qualidade de thresholds específicos
func (l *MetaParameterLearner) evaluateThresholds(
	episodes []MetaReflectionEpisode,
	insightThreshold, confidenceThreshold float64,
) float64 {
	totalQuality := 0.0
	count := 0

	for _, ep := range episodes {
		// Filtrar insights pelos thresholds
		var filteredInsights []KernelInsight
		for _, insight := range ep.InsightsGenerated {
			if math.Abs(insight.Value) >= insightThreshold &&
				insight.Confidence >= confidenceThreshold {
				filteredInsights = append(filteredInsights, insight)
			}
		}

		if len(filteredInsights) > 0 {
			// Qualidade baseada em outcomes dos insights filtrados
			quality := computeFilteredQuality(filteredInsights, ep.OutcomesObserved)
			totalQuality += quality
			count++
		}
	}

	if count == 0 {
		return 0 // Thresholds muito restritivos
	}
	return totalQuality / float64(count)
}

// Helper functions para manipulação de parâmetros
func getParamValue(params MetaReflectionParams, name string) float64 {
	switch name {
	case "ReflectionWindow":
		return float64(params.ReflectionWindow)
	case "InsightValueThreshold":
		return params.InsightValueThreshold
	case "ConfidenceThreshold":
		return params.ConfidenceThreshold
	case "UtilityWeight":
		return params.UtilityWeight
	case "NoveltyWeight":
		return params.NoveltyWeight
	case "ActionableWeight":
		return params.ActionableWeight
	default:
		return 0
	}
}

func setParamValue(params *MetaReflectionParams, name string, value float64) {
	switch name {
	case "ReflectionWindow":
		params.ReflectionWindow = time.Duration(value)
	case "InsightValueThreshold":
		params.InsightValueThreshold = value
	case "ConfidenceThreshold":
		params.ConfidenceThreshold = value
	case "UtilityWeight":
		params.UtilityWeight = value
	case "NoveltyWeight":
		params.NoveltyWeight = value
	case "ActionableWeight":
		params.ActionableWeight = value
	}
}

func clampParamValue(name string, value float64) float64 {
	// Bounds específicos por parâmetro
	bounds := map[string][2]float64{
		"ReflectionWindow":        {float64(5 * time.Minute), float64(4 * time.Hour)},
		"InsightValueThreshold":   {0.01, 0.5},
		"ConfidenceThreshold":     {0.3, 0.99},
		"UtilityWeight":           {0.1, 0.9},
		"NoveltyWeight":           {0.0, 0.5},
		"ActionableWeight":        {0.1, 0.9},
	}

	if bounds, ok := bounds[name]; ok {
		return math.Max(bounds[0], math.Min(bounds[1], value))
	}
	return value
}

func extractParamFromEpisode(ep MetaReflectionEpisode, paramName string) float64 {
	// Extrair valor do parâmetro do contexto do episódio
	if val, ok := ep.MetaFeatures["current_"+paramName]; ok {
		return val
	}
	return 0
}

func computeCorrelation(x, y []float64) float64 {
	if len(x) != len(y) || len(x) < 2 {
		return 0
	}
	return computePearsonCorrelation(x, y)
}

func computePearsonCorrelation(x, y []float64) float64 {
	n := float64(len(x))
	var sumX, sumY, sumXY, sumX2, sumY2 float64
	for i := 0; i < len(x); i++ {
		sumX += x[i]
		sumY += y[i]
		sumXY += x[i] * y[i]
		sumX2 += x[i] * x[i]
		sumY2 += y[i] * y[i]
	}
	numerator := n*sumXY - sumX*sumY
	denominator := math.Sqrt((n*sumX2 - sumX*sumX) * (n*sumY2 - sumY*sumY))
	if denominator == 0 {
		return 0
	}
	return numerator / denominator
}

func computeFilteredQuality(
	insights []KernelInsight,
	outcomes MetaReflectionOutcomes,
) float64 {
	// Qualidade dos insights filtrados baseada em outcomes
	if outcomes.ProposalsAccepted+outcomes.ProposalsRejected == 0 {
		return 0.5 // Neutro sem dados
	}

	acceptanceRate := float64(outcomes.ProposalsAccepted) /
		float64(outcomes.ProposalsAccepted+outcomes.ProposalsRejected)

	coherenceBonus := 0.0
	if outcomes.CoherenceImprovement > 0 {
		coherenceBonus = math.Min(0.3, outcomes.CoherenceImprovement*5)
	}

	return 0.5 + 0.2*acceptanceRate + coherenceBonus
}
