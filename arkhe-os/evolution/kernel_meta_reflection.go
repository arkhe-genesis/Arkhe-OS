package evolution

import (
	"fmt"
	"math"
	"time"

	"arkhe/ai"
)

// KernelMetaReflexive estende KernelAutoReflexive com capacidades de meta-aprendizado
type KernelMetaReflexive struct {
	*KernelAutoReflexive // Herda capacidades de auto-reflexão

	// Componentes de meta-reflexão
	metaEvaluator    *ReflectionQualityEvaluator
	metaLearner      *MetaParameterLearner
	insightDetector  *InsightPatternDetector
	metaOptimizer    *MetaOptimizationEngine
	metaConsensus    *FederatedMetaConsensus

	// Estado de meta-aprendizado
	metaParameters   MetaReflectionParams
	metaHistory      []MetaReflectionEpisode
	federationRound  int

	// Canal para meta-aprendizado federado
	metaFederationChannel *ai.CoherenceGradientChannel

	// Métricas de meta-reflexão
	metaMetrics MetaReflexMetrics

	// Callbacks para eventos de meta-reflexão
	metaCallbacks []func(KernelMetaReflexEvent)
}

// MetaReflectionParams contém parâmetros configuráveis do processo de reflexão
type MetaReflectionParams struct {
	// Parâmetros temporais
	ReflectionWindow    time.Duration `json:"reflection_window"`
	MinSamplesRequired  int           `json:"min_samples_required"`
	AdaptiveWindow      bool          `json:"adaptive_window"`

	// Thresholds de decisão
	InsightValueThreshold    float64 `json:"insight_value_threshold"`
	ConfidenceThreshold      float64 `json:"confidence_threshold"`
	AnomalyDetectionSigma    float64 `json:"anomaly_detection_sigma"`

	// Pesos para cálculo de qualidade de insight
	UtilityWeight    float64 `json:"utility_weight"`
	NoveltyWeight    float64 `json:"novelty_weight"`
	ActionableWeight float64 `json:"actionable_weight"`

	// Parâmetros de aprendizado federado
	FederationLearningRate float64 `json:"federation_learning_rate"`
	FederationTemperature  float64 `json:"federation_temperature"`
	LocalUpdateFrequency   int     `json:"local_update_frequency"` // Rounds entre atualizações federadas
}

// MetaReflectionEpisode registra uma sessão completa de reflexão para meta-análise
type MetaReflectionEpisode struct {
	EpisodeID       string
	Timestamp       time.Time
	ReflectionInput MetaReflectionInput
	InsightsGenerated []KernelInsight
	ProposalsMade   []string
	OutcomesObserved  MetaReflectionOutcomes
	QualityScore    float64
	MetaFeatures    map[string]float64 // Features para meta-aprendizado
}

// MetaReflectionInput captura contexto da reflexão para análise posterior
type MetaReflectionInput struct {
	KernelState       KernelStructuralMetrics
	OperatingRegime   string // "normal_load", "peak", "degraded", etc.
	RecentChanges     []string // Mudanças recentes no kernel
	ExternalEvents    []string // Eventos externos relevantes
}

// MetaReflectionOutcomes captura resultados observados após reflexão
type MetaReflectionOutcomes struct {
	ProposalsAccepted   int
	ProposalsRejected   int
	CoherenceImprovement float64 // ΔΦ_C observado após aplicar propostas
	StabilityImpact     float64   // Impacto na estabilidade do sistema
	TimeToResolution    time.Duration
}

// MetaReflexMetrics contém métricas de meta-reflexão
type MetaReflexMetrics struct {
	MetaReflectionsCompleted  int64   `json:"meta_reflections_completed"`
	AvgReflectionQuality      float64 `json:"avg_reflection_quality"`
	MetaParametersUpdated     int64   `json:"meta_parameters_updated"`
	FederationRoundsCompleted int64   `json:"federation_rounds_completed"`
	EffectiveInsightRate      float64 `json:"effective_insight_rate"` // % de insights que levaram a outcomes positivos
	MetaLearningConvergence   float64 `json:"meta_learning_convergence"` // Quão estáveis estão os meta-parâmetros
}

// KernelMetaReflexEvent evento de meta-reflexão para callbacks
type KernelMetaReflexEvent struct {
	EventType string
	KernelID  string
	Data      map[string]interface{}
	Timestamp time.Time
}

// NewKernelMetaReflexive cria novo kernel com capacidades de meta-reflexão
func NewKernelMetaReflexive(
	kernelID, version, arch, nodeID string,
	federationChannel, metaFederationChannel *ai.CoherenceGradientChannel,
	initialParams MetaReflectionParams,
) (*KernelMetaReflexive, error) {
	// Criar kernel auto-reflexivo base
	baseKernel, err := NewKernelAutoReflexive(kernelID, version, arch, nodeID, federationChannel)
	if err != nil {
		return nil, err
	}

	kernel := &KernelMetaReflexive{
		KernelAutoReflexive:   baseKernel,
		metaFederationChannel: metaFederationChannel,
		metaParameters:        initialParams,
		metaHistory:           make([]MetaReflectionEpisode, 0, 200),
		metaMetrics: MetaReflexMetrics{
			AvgReflectionQuality:    0.5,
			EffectiveInsightRate:    0.5,
			MetaLearningConvergence: 1.0, // Começa com máxima incerteza
		},
	}

	// Inicializar componentes de meta-reflexão
	kernel.metaEvaluator = NewReflectionQualityEvaluator(kernelID, initialParams)
	kernel.metaLearner = NewMetaParameterLearner(kernelID, initialParams)
	kernel.insightDetector = NewInsightPatternDetector(kernelID)
	kernel.metaOptimizer = NewMetaOptimizationEngine(kernelID, initialParams)
	kernel.metaConsensus = NewFederatedMetaConsensus(kernelID, metaFederationChannel)

	return kernel, nil
}

// PerformMetaReflection executa reflexão sobre o próprio processo de reflexão
func (k *KernelMetaReflexive) PerformMetaReflection() (*MetaReflectionResult, error) {
	k.mu.Lock()
	defer k.mu.Unlock()

	// Coletar episódios recentes para meta-análise
	recentEpisodes := k.getRecentEpisodes(50) // Últimos 50 episódios
	if len(recentEpisodes) < 10 {
		return nil, fmt.Errorf("insufficient episodes for meta-reflection: %d < 10", len(recentEpisodes))
	}

	// 1. Avaliar qualidade das reflexões recentes
	qualityScores := k.metaEvaluator.EvaluateEpisodes(recentEpisodes)
	avgQuality := avgFloat64(qualityScores)

	// 2. Detectar padrões de insights eficazes
	effectivePatterns, err := k.insightDetector.DetectEffectivePatterns(recentEpisodes)
	if err != nil {
		return nil, fmt.Errorf("pattern detection failed: %w", err)
	}

	// 3. Calcular meta-gradientes para ajuste de parâmetros
	metaGradients, err := k.metaLearner.ComputeMetaGradients(recentEpisodes, qualityScores)
	if err != nil {
		return nil, fmt.Errorf("meta-gradient computation failed: %w", err)
	}

	// 4. Gerar propostas de meta-otimização
	metaProposals := k.metaOptimizer.GenerateMetaProposals(metaGradients, effectivePatterns)

	// 5. Registrar novo episódio de meta-reflexão
	newEpisode := MetaReflectionEpisode{
		EpisodeID:          fmt.Sprintf("meta_%s_%d", k.kernelID[:8], time.Now().UnixNano()),
		Timestamp:          time.Now(),
		ReflectionInput:    k.buildMetaInput(),
		InsightsGenerated:  k.extractMetaInsights(recentEpisodes),
		ProposalsMade:      extractProposalIDs(metaProposals),
		OutcomesObserved:   k.estimateMetaOutcomes(metaProposals),
		QualityScore:       avgQuality,
		MetaFeatures:       k.extractMetaFeatures(recentEpisodes, qualityScores),
	}
	k.metaHistory = append(k.metaHistory, newEpisode)
	if len(k.metaHistory) > 200 {
		k.metaHistory = k.metaHistory[100:] // Manter janela deslizante
	}

	// Atualizar métricas
	k.metaMetrics.MetaReflectionsCompleted++
	n := k.metaMetrics.MetaReflectionsCompleted
	oldAvg := k.metaMetrics.AvgReflectionQuality
	k.metaMetrics.AvgReflectionQuality = (oldAvg*float64(n-1) + avgQuality) / float64(n)

	result := &MetaReflectionResult{
		EpisodeID:         newEpisode.EpisodeID,
		AvgQuality:        avgQuality,
		EffectivePatterns: effectivePatterns,
		MetaProposals:     metaProposals,
		NewParameters:     k.metaParameters, // Pode ser atualizado após consenso federado
	}

	// Notificar callbacks
	for _, cb := range k.metaCallbacks {
		cb(KernelMetaReflexEvent{
			EventType: "meta_reflection_completed",
			KernelID:  k.kernelID,
			Data: map[string]interface{}{
				"episode_id":        newEpisode.EpisodeID,
				"avg_quality":       avgQuality,
				"patterns_detected": len(effectivePatterns),
				"proposals_count":   len(metaProposals),
			},
			Timestamp: time.Now(),
		})
	}

	return result, nil
}

// UpdateMetaParametersFederated atualiza parâmetros via aprendizado federado
func (k *KernelMetaReflexive) UpdateMetaParametersFederated(
	remoteUpdates []MetaParameterUpdate,
	remoteQualities []float64,
) error {
	// Agregar atualizações federadas com ponderação por qualidade
	aggregatedParams, err := k.metaConsensus.AggregateMetaParameters(
		k.metaParameters,
		k.metaMetrics.AvgReflectionQuality,
		remoteUpdates,
		remoteQualities,
		k.metaParameters.FederationTemperature,
	)
	if err != nil {
		return err
	}

	// Aplicar atualização com learning rate federado
	k.metaParameters = blendMetaParameters(
		k.metaParameters,
		aggregatedParams,
		k.metaParameters.FederationLearningRate,
	)

	// Atualizar métricas
	k.metaMetrics.FederationRoundsCompleted++
	k.metaMetrics.MetaParametersUpdated++

	// Recalcular convergência de aprendizado
	k.metaMetrics.MetaLearningConvergence = computeParameterConvergence(
		k.metaHistory,
		k.metaParameters,
	)

	return nil
}

// RecordReflectionOutcome registra outcome observado de uma reflexão para meta-aprendizado
func (k *KernelMetaReflexive) RecordReflectionOutcome(
	episodeID string,
	outcomes MetaReflectionOutcomes,
) {
	k.mu.Lock()
	defer k.mu.Unlock()

	// Encontrar episódio e atualizar com outcomes reais
	for i := range k.metaHistory {
		if k.metaHistory[i].EpisodeID == episodeID {
			k.metaHistory[i].OutcomesObserved = outcomes

			// Recalcular qualidade com dados reais
			actualQuality := k.metaEvaluator.ComputeActualQuality(
				k.metaHistory[i].InsightsGenerated,
				outcomes,
			)
			k.metaHistory[i].QualityScore = actualQuality

			// Atualizar métrica de insight eficaz
			if outcomes.ProposalsAccepted > 0 && outcomes.CoherenceImprovement > 0 {
				k.metaMetrics.EffectiveInsightRate = k.metaMetrics.EffectiveInsightRate*0.99 + 0.01
			}
			break
		}
	}
}

// GetMetaParameters retorna parâmetros atuais de meta-reflexão
func (k *KernelMetaReflexive) GetMetaParameters() MetaReflectionParams {
	k.mu.RLock()
	defer k.mu.RUnlock()
	return k.metaParameters
}

// GetMetaMetrics retorna métricas de meta-reflexão
func (k *KernelMetaReflexive) GetMetaMetrics() MetaReflexMetrics {
	k.mu.RLock()
	defer k.mu.RUnlock()
	return k.metaMetrics
}

// RegisterMetaCallback registra callback para eventos de meta-reflexão
func (k *KernelMetaReflexive) RegisterMetaCallback(cb func(KernelMetaReflexEvent)) {
	k.metaCallbacks = append(k.metaCallbacks, cb)
}

// Helper functions
func (k *KernelMetaReflexive) getRecentEpisodes(count int) []MetaReflectionEpisode {
	if len(k.metaHistory) <= count {
		return k.metaHistory
	}
	return k.metaHistory[len(k.metaHistory)-count:]
}

func (k *KernelMetaReflexive) buildMetaInput() MetaReflectionInput {
	return MetaReflectionInput{
		KernelState:     k.currentMetrics,
		OperatingRegime: detectOperatingRegime(k.currentMetrics),
		RecentChanges:   extractRecentChanges(k.kernelID),
		ExternalEvents:  getRelevantExternalEvents(),
	}
}

func (k *KernelMetaReflexive) extractMetaInsights(episodes []MetaReflectionEpisode) []KernelInsight {
	// Extrair insights de nível meta sobre o processo de reflexão
	var insights []KernelInsight

	// Exemplo: detectar se certas categorias de insight são mais eficazes
	categoryEffectiveness := make(map[string]float64)
	categoryCount := make(map[string]int)

	for _, ep := range episodes {
		for _, insight := range ep.InsightsGenerated {
			categoryCount[insight.Category]++
			if ep.OutcomesObserved.CoherenceImprovement > 0 {
				categoryEffectiveness[insight.Category] += ep.QualityScore
			}
		}
	}

	for category, count := range categoryCount {
		if count >= 5 {
			effectiveness := categoryEffectiveness[category] / float64(count)
			if effectiveness > 0.7 {
				insights = append(insights, KernelInsight{
					InsightID:   fmt.Sprintf("meta_category_%s", category),
					Description: fmt.Sprintf("Insights of category '%s' show %.2f effectiveness", category, effectiveness),
					Category:    "meta_reflection",
					Confidence:  0.8,
					Value:       effectiveness * 0.02,
					Timestamp:   time.Now(),
				})
			}
		}
	}

	return insights
}

func (k *KernelMetaReflexive) extractMetaFeatures(
	episodes []MetaReflectionEpisode,
	qualityScores []float64,
) map[string]float64 {
	features := make(map[string]float64)

	// Features estatísticas das reflexões
	if len(episodes) > 0 {
		features["avg_insights_per_reflection"] = float64(totalInsights(episodes)) / float64(len(episodes))
		features["avg_proposals_per_reflection"] = float64(totalProposals(episodes)) / float64(len(episodes))
		features["quality_variance"] = varianceFloat64(qualityScores)
		features["quality_trend"] = computeTrend(qualityScores)
	}

	// Features de parâmetros atuais
	features["current_window_hours"] = k.metaParameters.ReflectionWindow.Hours()
	features["current_insight_threshold"] = k.metaParameters.InsightValueThreshold
	features["current_confidence_threshold"] = k.metaParameters.ConfidenceThreshold

	return features
}

func detectOperatingRegime(metrics KernelStructuralMetrics) string {
	// Heurística simples para classificar regime operacional
	if len(metrics.LoadAverage) > 0 && metrics.LoadAverage[0] > 2.0 {
		return "peak_load"
	} else if len(metrics.LoadAverage) > 0 && metrics.LoadAverage[0] < 0.3 {
		return "idle"
	} else if metrics.ErrorRate > 0.01 {
		return "degraded"
	}
	return "normal"
}

func totalInsights(episodes []MetaReflectionEpisode) int {
	total := 0
	for _, ep := range episodes {
		total += len(ep.InsightsGenerated)
	}
	return total
}

func totalProposals(episodes []MetaReflectionEpisode) int {
	total := 0
	for _, ep := range episodes {
		total += len(ep.ProposalsMade)
	}
	return total
}

func extractProposalIDs(proposals []MetaOptimizationProposal) []string {
	ids := make([]string, len(proposals))
	for i, p := range proposals {
		ids[i] = p.ProposalID
	}
	return ids
}

func avgFloat64(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	sum := 0.0
	for _, v := range values {
		sum += v
	}
	return sum / float64(len(values))
}

func varianceFloat64(values []float64) float64 {
	if len(values) < 2 {
		return 0
	}
	mean := avgFloat64(values)
	variance := 0.0
	for _, v := range values {
		variance += (v - mean) * (v - mean)
	}
	return variance / float64(len(values))
}

func computeTrend(values []float64) float64 {
	if len(values) < 2 {
		return 0
	}
	// Regressão linear simples
	n := float64(len(values))
	var sumX, sumY, sumXY, sumX2 float64
	for i, v := range values {
		x := float64(i)
		sumX += x
		sumY += v
		sumXY += x * v
		sumX2 += x * x
	}
	return (n*sumXY - sumX*sumY) / (n*sumX2 - sumX*sumX)
}

func computeParameterConvergence(
	history []MetaReflectionEpisode,
	currentParams MetaReflectionParams,
) float64 {
	// Medir quão estáveis estão os parâmetros ao longo do tempo
	if len(history) < 20 {
		return 1.0 // Alta incerteza com poucos dados
	}

	// Calcular variância de parâmetros-chave nos últimos episódios
	var windowVariance float64
	recent := history[len(history)-20:]

	for _, ep := range recent {
		// Comparar features de parâmetros com valores atuais
		windowVariance += math.Abs(ep.MetaFeatures["current_window_hours"] - currentParams.ReflectionWindow.Hours())
		windowVariance += math.Abs(ep.MetaFeatures["current_insight_threshold"] - currentParams.InsightValueThreshold)
	}
	windowVariance /= float64(len(recent) * 2)

	// Mapear variância para convergência [0, 1]
	return math.Exp(-windowVariance * 10)
}

func blendMetaParameters(base, update MetaReflectionParams, learningRate float64) MetaReflectionParams {
	// Blend linear com learning rate
	return MetaReflectionParams{
		ReflectionWindow:         time.Duration(float64(base.ReflectionWindow)*(1-learningRate) + float64(update.ReflectionWindow)*learningRate),
		MinSamplesRequired:       int(float64(base.MinSamplesRequired)*(1-learningRate) + float64(update.MinSamplesRequired)*learningRate),
		AdaptiveWindow:           update.AdaptiveWindow,
		InsightValueThreshold:    base.InsightValueThreshold*(1-learningRate) + update.InsightValueThreshold*learningRate,
		ConfidenceThreshold:      base.ConfidenceThreshold*(1-learningRate) + update.ConfidenceThreshold*learningRate,
		AnomalyDetectionSigma:    base.AnomalyDetectionSigma*(1-learningRate) + update.AnomalyDetectionSigma*learningRate,
		UtilityWeight:            base.UtilityWeight*(1-learningRate) + update.UtilityWeight*learningRate,
		NoveltyWeight:            base.NoveltyWeight*(1-learningRate) + update.NoveltyWeight*learningRate,
		ActionableWeight:         base.ActionableWeight*(1-learningRate) + update.ActionableWeight*learningRate,
		FederationLearningRate:   base.FederationLearningRate,
		FederationTemperature:    base.FederationTemperature,
		LocalUpdateFrequency:     base.LocalUpdateFrequency,
	}
}

// Temporary stubs for methods not in snippet but called
type MetaReflectionResult struct {
	EpisodeID         string
	AvgQuality        float64
	EffectivePatterns []string
	MetaProposals     []MetaOptimizationProposal
	NewParameters     MetaReflectionParams
}

type MetaOptimizationProposal struct {
	ProposalID string
}

func (k *KernelMetaReflexive) estimateMetaOutcomes(proposals []MetaOptimizationProposal) MetaReflectionOutcomes {
	return MetaReflectionOutcomes{}
}

func extractRecentChanges(kernelID string) []string {
	return nil
}

func getRelevantExternalEvents() []string {
	return nil
}
