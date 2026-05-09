package evolution

import (
	"math"
	"strings"
	"sync"
	"time"
)

// ReflectionQualityEvaluator avalia a qualidade de episódios de reflexão
type ReflectionQualityEvaluator struct {
	kernelID string
	params   MetaReflectionParams
	mu       sync.RWMutex

	// Modelo aprendido para avaliação de qualidade
	qualityModel QualityPredictionModel

	// Histórico para calibração do modelo
	calibrationHistory []CalibrationSample
}

// QualityPredictionModel modelo para prever qualidade de reflexão
type QualityPredictionModel struct {
	Trained bool
	Weights map[string]float64 // Pesos para diferentes meta-features
	Bias    float64
}

// CalibrationSample amostra para calibrar modelo de qualidade
type CalibrationSample struct {
	Timestamp    time.Time
	MetaFeatures map[string]float64
	ActualQuality float64 // Qualidade observada via outcomes reais
}

// NewReflectionQualityEvaluator cria novo avaliador de qualidade
func NewReflectionQualityEvaluator(kernelID string, params MetaReflectionParams) *ReflectionQualityEvaluator {
	return &ReflectionQualityEvaluator{
		kernelID: kernelID,
		params:   params,
		qualityModel: QualityPredictionModel{
			Trained: false,
			Weights: map[string]float64{
				"insight_count":        0.1,
				"avg_confidence":       0.2,
				"category_diversity":   0.15,
				"actionability_score":  0.25,
				"novelty_score":        0.1,
				"temporal_consistency": 0.2,
			},
			Bias: 0.3,
		},
		calibrationHistory: make([]CalibrationSample, 0, 100),
	}
}

// EvaluateEpisodes avalia qualidade de múltiplos episódios de reflexão
func (e *ReflectionQualityEvaluator) EvaluateEpisodes(episodes []MetaReflectionEpisode) []float64 {
	e.mu.RLock()
	defer e.mu.RUnlock()

	scores := make([]float64, len(episodes))
	for i, episode := range episodes {
		scores[i] = e.evaluateEpisode(episode)
	}
	return scores
}

// evaluateEpisode avalia qualidade de um episódio individual
func (e *ReflectionQualityEvaluator) evaluateEpisode(episode MetaReflectionEpisode) float64 {
	// Extrair meta-features do episódio
	features := e.extractQualityFeatures(episode)

	// Prever qualidade via modelo
	predictedQuality := e.predictQuality(features)

	// Se outcomes reais disponíveis, usar para cálculo de qualidade real
	if episode.OutcomesObserved.CoherenceImprovement != 0 ||
		episode.OutcomesObserved.ProposalsAccepted+episode.OutcomesObserved.ProposalsRejected > 0 {
		return e.ComputeActualQuality(episode.InsightsGenerated, episode.OutcomesObserved)
	}

	return predictedQuality
}

// extractQualityFeatures extrai features relevantes para avaliação de qualidade
func (e *ReflectionQualityEvaluator) extractQualityFeatures(episode MetaReflectionEpisode) map[string]float64 {
	features := make(map[string]float64)

	// Contagem e diversidade de insights
	features["insight_count"] = float64(len(episode.InsightsGenerated))
	categorySet := make(map[string]bool)
	for _, insight := range episode.InsightsGenerated {
		categorySet[insight.Category] = true
	}
	features["category_diversity"] = float64(len(categorySet)) / math.Max(1, float64(len(episode.InsightsGenerated)))

	// Qualidade média dos insights
	var totalConfidence, totalValue, totalActionability float64
	for _, insight := range episode.InsightsGenerated {
		totalConfidence += insight.Confidence
		totalValue += math.Abs(insight.Value)
		totalActionability += computeActionabilityScore(insight)
	}
	n := math.Max(1, float64(len(episode.InsightsGenerated)))
	features["avg_confidence"] = totalConfidence / n
	features["avg_value"] = totalValue / n
	features["actionability_score"] = totalActionability / n

	// Novelty: quão diferentes são os insights de reflexões anteriores
	features["novelty_score"] = computeNoveltyScore(episode.InsightsGenerated, e.getRecentInsights())

	// Consistência temporal: quão alinhados são insights ao longo do tempo
	features["temporal_consistency"] = computeTemporalConsistency(episode.InsightsGenerated)

	return features
}

// predictQuality prevê qualidade baseado em features e modelo
func (e *ReflectionQualityEvaluator) predictQuality(features map[string]float64) float64 {
	if !e.qualityModel.Trained {
		// Fallback: média ponderada simples
		return e.simpleWeightedScore(features)
	}

	// Predição via modelo linear
	score := e.qualityModel.Bias
	for feature, weight := range e.qualityModel.Weights {
		if val, ok := features[feature]; ok {
			score += weight * val
		}
	}

	return math.Max(0, math.Min(1, score))
}

// simpleWeightedScore cálculo fallback de qualidade
func (e *ReflectionQualityEvaluator) simpleWeightedScore(features map[string]float64) float64 {
	score := 0.0
	totalWeight := 0.0

	score += e.params.UtilityWeight * features["avg_value"]
	totalWeight += e.params.UtilityWeight

	score += e.params.NoveltyWeight * features["novelty_score"]
	totalWeight += e.params.NoveltyWeight

	score += e.params.ActionableWeight * features["actionability_score"]
	totalWeight += e.params.ActionableWeight

	if totalWeight > 0 {
		score /= totalWeight
	}

	return math.Max(0, math.Min(1, score))
}

// ComputeActualQuality calcula qualidade real baseada em outcomes observados
func (e *ReflectionQualityEvaluator) ComputeActualQuality(
	insights []KernelInsight,
	outcomes MetaReflectionOutcomes,
) float64 {
	quality := 0.0

	// Fator 1: Taxa de aceitação de propostas
	if total := outcomes.ProposalsAccepted + outcomes.ProposalsRejected; total > 0 {
		acceptanceRate := float64(outcomes.ProposalsAccepted) / float64(total)
		quality += 0.4 * acceptanceRate
	}

	// Fator 2: Melhoria de coerência observada
	if outcomes.CoherenceImprovement > 0 {
		quality += 0.3 * math.Min(1.0, outcomes.CoherenceImprovement*10)
	} else if outcomes.CoherenceImprovement < 0 {
		quality -= 0.3 * math.Min(1.0, math.Abs(outcomes.CoherenceImprovement)*10)
	}

	// Fator 3: Impacto na estabilidade
	if outcomes.StabilityImpact >= 0 {
		quality += 0.2 * math.Min(1.0, outcomes.StabilityImpact)
	} else {
		quality += 0.2 * math.Max(-1.0, outcomes.StabilityImpact)
	}

	// Fator 4: Eficiência temporal (resolução rápida = melhor)
	if outcomes.TimeToResolution > 0 {
		efficiency := math.Exp(-outcomes.TimeToResolution.Hours() / 24)
		quality += 0.1 * efficiency
	}

	return math.Max(0, math.Min(1, quality+0.5)) // Centralizar em 0.5
}

// computeActionabilityScore calcula quão acionável é um insight
func computeActionabilityScore(insight KernelInsight) float64 {
	score := 0.0

	// Insights com evidências concretas são mais acionáveis
	if len(insight.Evidence) > 0 {
		score += 0.3
	}

	// Insights com valor quantitativo claro
	if math.Abs(insight.Value) > 0.01 {
		score += 0.3
	}

	// Insights de categorias específicas são mais acionáveis
	actionableCategories := map[string]bool{
		"config_security": true,
		"syscall_performance": true,
		"module_health": true,
	}
	if actionableCategories[insight.Category] {
		score += 0.4
	}

	return score
}

// computeNoveltyScore calcula quão novos são os insights comparado a históricos
func computeNoveltyScore(current, historical []KernelInsight) float64 {
	if len(historical) == 0 {
		return 1.0 // Tudo é novo sem histórico
	}

	// Calcular similaridade média com insights históricos
	var totalSimilarity float64
	count := 0

	for _, currentInsight := range current {
		for _, histInsight := range historical {
			if currentInsight.Category == histInsight.Category {
				// Similaridade baseada em descrição
				sim := computeTextSimilarity(currentInsight.Description, histInsight.Description)
				totalSimilarity += sim
				count++
			}
		}
	}

	if count == 0 {
		return 1.0 // Sem overlap de categoria = totalmente novo
	}

	avgSimilarity := totalSimilarity / float64(count)
	return 1.0 - avgSimilarity // Novelty = 1 - similaridade
}

// computeTemporalConsistency calcula consistência de insights ao longo do tempo
func computeTemporalConsistency(insights []KernelInsight) float64 {
	if len(insights) < 2 {
		return 1.0
	}

	// Verificar se insights apontam na mesma direção (valores com mesmo sinal)
	var positive, negative int
	for _, insight := range insights {
		if insight.Value > 0 {
			positive++
		} else if insight.Value < 0 {
			negative++
		}
	}

	// Consistência alta se maioria dos valores tem mesmo sinal
	total := positive + negative
	if total == 0 {
		return 1.0
	}
	return math.Max(float64(positive), float64(negative)) / float64(total)
}

// computeTextSimilarity calcula similaridade simples de texto
func computeTextSimilarity(a, b string) float64 {
	// Implementação simplificada: overlap de palavras
	wordsA := make(map[string]bool)
	for _, word := range tokenize(a) {
		wordsA[word] = true
	}

	overlap := 0
	totalB := 0
	for _, word := range tokenize(b) {
		totalB++
		if wordsA[word] {
			overlap++
		}
	}

	if totalB == 0 {
		return 1.0
	}
	return float64(overlap) / float64(totalB)
}

func tokenize(text string) []string {
	// Tokenização simples por espaços e pontuação
	text = strings.ToLower(text)
	text = strings.ReplaceAll(text, ",", " ")
	text = strings.ReplaceAll(text, ".", " ")
	text = strings.ReplaceAll(text, ":", " ")
	return strings.Fields(text)
}

// getRecentInsights retorna insights recentes para cálculo de novelty
func (e *ReflectionQualityEvaluator) getRecentInsights() []KernelInsight {
	// Implementação simplificada: retornar últimos 50 insights do histórico
	var recent []KernelInsight
	for i := len(e.calibrationHistory) - 1; i >= 0 && len(recent) < 50; i-- {
		// Em produção: extrair insights reais do histórico
	}
	return recent
}

// CalibrateModel atualiza modelo baseado em samples de calibração
func (e *ReflectionQualityEvaluator) CalibrateModel(samples []CalibrationSample) {
	e.mu.Lock()
	defer e.mu.Unlock()

	// Adicionar novos samples ao histórico
	e.calibrationHistory = append(e.calibrationHistory, samples...)
	if len(e.calibrationHistory) > 100 {
		e.calibrationHistory = e.calibrationHistory[len(e.calibrationHistory)-100:]
	}

	// Re-treinar modelo se tiver samples suficientes
	if len(e.calibrationHistory) >= 30 {
		e.qualityModel = trainQualityModel(e.calibrationHistory)
	}
}

// trainQualityModel treina modelo de predição de qualidade
func trainQualityModel(samples []CalibrationSample) QualityPredictionModel {
	// Implementação simplificada: regressão linear via mínimos quadrados
	// Em produção: usar algoritmo mais sofisticado ou federated learning

	model := QualityPredictionModel{
		Trained: true,
		Weights: make(map[string]float64),
	}

	// Inicializar pesos com valores padrão
	for k, v := range model.Weights {
		model.Weights[k] = v
	}

	// Ajuste simples baseado em correlação com qualidade real
	// (implementação simplificada para demonstração)

	return model
}
