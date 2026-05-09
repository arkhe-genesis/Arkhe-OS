// parser/frontends/agile/coherence/agile_calculator.go
package coherence

import (
	"math"
)

// AgileMetrics acumula métricas para cálculo de coerência de processo ágil
type AgileMetrics struct {
	// Métricas de fluxo
	TotalItems           int
	CompletedItems       int
	AvgCycleTimeDays     float64
	AvgLeadTimeDays      float64
	FlowEfficiency       float64 // value_added_time / lead_time

	// Métricas de previsibilidade (Scrum)
	VelocityStability    float64 // 1 - CV(velocity)
	CommitmentAccuracy   float64 // delivered / planned

	// Métricas de qualidade
	QualityScore         float64 // 1 - defect_rate
	DefectEscapeRate     float64

	// Métricas de saúde da equipe
	WasteRatio           float64 // (blocked_time + rework) / total_effort
	BlockerResolutionDays float64
	RetroSentimentScore  float64 // -1 a +1

	// Métricas de CFD (Kanban)
	BottleneckSeverity   float64 // 0 a 1
	CFDStability         float64 // 1 - variação de inclinação
}

// AgileCoherenceConfig configura pesos para cálculo de coerência ágil
type AgileCoherenceConfig struct {
	FlowWeight         float64 // Peso para eficiência de fluxo
	PredictabilityWeight float64 // Peso para previsibilidade
	QualityWeight      float64 // Peso para qualidade
	TeamHealthWeight   float64 // Peso para saúde da equipe
	WastePenalty       float64 // Penalidade por desperdício
	Methodology        string  // "scrum" ou "kanban"
}

// DefaultAgileConfig retorna configurações padrão baseadas na metodologia
func DefaultAgileConfig(methodology string) *AgileCoherenceConfig {
	if methodology == "scrum" {
		return &AgileCoherenceConfig{
			FlowWeight:         0.25,
			PredictabilityWeight: 0.35, // Scrum enfatiza previsibilidade
			QualityWeight:      0.25,
			TeamHealthWeight:   0.15,
			WastePenalty:       0.10,
			Methodology:        "scrum",
		}
	}
	// Kanban padrão
	return &AgileCoherenceConfig{
		FlowWeight:         0.40, // Kanban enfatiza fluxo contínuo
		PredictabilityWeight: 0.20,
		QualityWeight:      0.25,
		TeamHealthWeight:   0.15,
		WastePenalty:       0.10,
		Methodology:        "kanban",
	}
}

// CalculateAgileCoherence calcula Φ_C para processos ágeis
func CalculateAgileCoherence(m *AgileMetrics, cfg *AgileCoherenceConfig) float64 {
	// Calcular componentes individuais
	flowScore := calculateFlowScore(m)
	predictabilityScore := calculatePredictabilityScore(m, cfg)
	qualityScore := calculateQualityScore(m)
	teamHealthScore := calculateTeamHealthScore(m)
	wastePenalty := calculateWastePenalty(m, cfg)

	// Combinação ponderada
	coherence := cfg.FlowWeight*flowScore +
		cfg.PredictabilityWeight*predictabilityScore +
		cfg.QualityWeight*qualityScore +
		cfg.TeamHealthWeight*teamHealthScore -
		cfg.WastePenalty*wastePenalty

	// Normalizar para [0, 1]
	return math.Max(0.0, math.Min(1.0, coherence))
}

func calculateFlowScore(m *AgileMetrics) float64 {
	// Flow efficiency: ideal é próximo de 1 (todo tempo é valor agregado)
	efficiency := m.FlowEfficiency
	if efficiency > 1 {
		efficiency = 1 // Cap para evitar valores > 1 devido a simplificações
	}

	// Penalizar cycle time muito variável
	cv := calculateCoefficientOfVariation([]float64{m.AvgCycleTimeDays}) // Simplificado
	stabilityFactor := math.Exp(-0.5 * cv)

	return efficiency * stabilityFactor
}

func calculatePredictabilityScore(m *AgileMetrics, cfg *AgileCoherenceConfig) float64 {
	if cfg.Methodology == "scrum" {
		// Para Scrum: combinar velocity stability e commitment accuracy
		return (m.VelocityStability + m.CommitmentAccuracy) / 2
	}
	// Para Kanban: usar throughput stability
	return m.VelocityStability // Reutilizar como proxy de throughput stability
}

func calculateQualityScore(m *AgileMetrics) float64 {
	// Combinar quality score e defect escape rate
	defectImpact := 1.0 - m.DefectEscapeRate
	return (m.QualityScore + defectImpact) / 2
}

func calculateTeamHealthScore(m *AgileMetrics) float64 {
	// Combinar sentiment de retrospectivas e resolução de blockers
	sentimentFactor := (m.RetroSentimentScore + 1) / 2 // Normalizar -1..1 para 0..1

	// Blocker resolution: ideal é rápido (< 1 dia)
	blockerFactor := math.Exp(-0.5 * m.BlockerResolutionDays)
	if blockerFactor < 0.3 {
		blockerFactor = 0.3 // Floor para evitar penalidade excessiva
	}

	return (sentimentFactor + blockerFactor) / 2
}

func calculateWastePenalty(m *AgileMetrics, cfg *AgileCoherenceConfig) float64 {
	// Waste ratio já está normalizado [0, 1]
	// Aplicar fator de penalidade configurável
	return m.WasteRatio * cfg.WastePenalty
}

// calculateCoefficientOfVariation calcula CV = std/mean para uma série
func calculateCoefficientOfVariation(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}

	mean := 0.0
	for _, v := range values {
		mean += v
	}
	mean /= float64(len(values))

	if mean == 0 {
		return 0
	}

	variance := 0.0
	for _, v := range values {
		diff := v - mean
		variance += diff * diff
	}
	variance /= float64(len(values))

	std := math.Sqrt(variance)
	return std / mean
}
