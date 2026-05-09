// parser/lfir/coherence_metrics.go
// Cálculo de métricas de coerência para projetos de jogos
package lfir

import (
	"math"
)

// GameCoherenceCalculator calcula Φ_C para diferentes tipos de artefatos de jogos
type GameCoherenceCalculator struct {
	UnityConfig  UnityCoherenceConfig
	SteamConfig  SteamCoherenceConfig
	WorkshopConfig WorkshopCoherenceConfig
}

// UnityCoherenceConfig configura pesos para cálculo de coerência Unity
type UnityCoherenceConfig struct {
	UtilizationWeight  float64 // Peso para utilização de GameObjects
	IntegrityWeight    float64 // Peso para integridade de referências
	PerformanceWeight  float64 // Peso para performance (draw calls)
	MissingRefPenalty  float64 // Penalidade por referência quebrada
	MaxDrawCalls       int     // Limite de draw calls para score 1.0
}

// DefaultUnityConfig retorna configurações padrão para Unity
func DefaultUnityConfig() UnityCoherenceConfig {
	return UnityCoherenceConfig{
		UtilizationWeight: 0.35,
		IntegrityWeight:   0.40,
		PerformanceWeight: 0.25,
		MissingRefPenalty: 0.5,
		MaxDrawCalls:      1000,
	}
}

// SteamCoherenceConfig configura pesos para cálculo de coerência Steam
type SteamCoherenceConfig struct {
	IntegrityWeight    float64
	CompletenessWeight float64
	ReliabilityWeight  float64
	MaxDepotSizeGB     float64
}

func DefaultSteamConfig() SteamCoherenceConfig {
	return SteamCoherenceConfig{
		IntegrityWeight:    0.45,
		CompletenessWeight: 0.35,
		ReliabilityWeight:  0.20,
		MaxDepotSizeGB:     50.0,
	}
}

// CalculateUnityCoherence calcula Φ_C para cenas/prefabs Unity
func (c *GameCoherenceCalculator) CalculateUnityCoherence(metrics *UnitySceneMetrics) float64 {
	utilization := c.calculateUnityUtilization(metrics)
	integrity := c.calculateUnityIntegrity(metrics)
	performance := c.calculateUnityPerformance(metrics)

	return c.UnityConfig.UtilizationWeight*utilization +
		c.UnityConfig.IntegrityWeight*integrity +
		c.UnityConfig.PerformanceWeight*performance
}

func (c *GameCoherenceCalculator) calculateUnityUtilization(m *UnitySceneMetrics) float64 {
	if m.TotalGameObjects == 0 {
		return 1.0
	}
	return float64(m.ActiveGameObjects) / float64(m.TotalGameObjects)
}

func (c *GameCoherenceCalculator) calculateUnityIntegrity(m *UnitySceneMetrics) float64 {
	return math.Exp(-c.UnityConfig.MissingRefPenalty * float64(m.MissingReferences))
}

func (c *GameCoherenceCalculator) calculateUnityPerformance(m *UnitySceneMetrics) float64 {
	if c.UnityConfig.MaxDrawCalls == 0 {
		return 1.0
	}
	score := 1.0 - float64(m.EstimatedDrawCalls)/float64(c.UnityConfig.MaxDrawCalls)
	return math.Max(0.0, score)
}

// CalculateSteamCoherence calcula Φ_C para builds Steam
func (c *GameCoherenceCalculator) CalculateSteamCoherence(metrics *SteamBuildMetrics) float64 {
	integrity := c.calculateSteamIntegrity(metrics)
	completeness := c.calculateSteamCompleteness(metrics)
	reliability := metrics.ReliabilityScore

	return c.SteamConfig.IntegrityWeight*integrity +
		c.SteamConfig.CompletenessWeight*completeness +
		c.SteamConfig.ReliabilityWeight*reliability
}

func (c *GameCoherenceCalculator) calculateSteamIntegrity(m *SteamBuildMetrics) float64 {
	if m.FileCount == 0 {
		return 1.0
	}
	issueRatio := float64(m.MissingFiles+m.ChecksumMismatches) / float64(m.FileCount)
	return math.Exp(-2.0 * issueRatio)
}

func (c *GameCoherenceCalculator) calculateSteamCompleteness(m *SteamBuildMetrics) float64 {
	if m.DepotCount == 0 {
		return 0.5
	}
	if m.TotalSizeGB > c.SteamConfig.MaxDepotSizeGB {
		return 0.7
	}
	return 1.0
}

// WorkshopCoherenceConfig para itens do Steam Workshop
type WorkshopCoherenceConfig struct {
	ConversionWeight   float64
	FreshnessWeight    float64
	QualityWeight      float64
	FreshnessDecayRate float64 // ν no decaimento exponencial
}

func DefaultWorkshopConfig() WorkshopCoherenceConfig {
	return WorkshopCoherenceConfig{
		ConversionWeight:   0.40,
		FreshnessWeight:    0.30,
		QualityWeight:      0.30,
		FreshnessDecayRate: 0.001, // Decaimento por dia
	}
}

// CalculateWorkshopCoherence calcula Φ_C para itens do Workshop
func (c *GameCoherenceCalculator) CalculateWorkshopCoherence(
	subscribers, views int,
	daysSinceUpdate int,
	ratingNormalized float64,
) float64 {
	// Taxa de conversão: subscribers/views
	conversion := 0.0
	if views > 0 {
		conversion = float64(subscribers) / float64(views)
		// Normalizar para [0,1] com saturação
		conversion = math.Min(1.0, conversion*10)
	}

	// Frescor: decaimento exponencial com tempo desde última atualização
	freshness := math.Exp(-c.WorkshopConfig.FreshnessWeight * c.WorkshopConfig.FreshnessDecayRate * float64(daysSinceUpdate))

	// Qualidade: rating já normalizado
	quality := ratingNormalized

	return c.WorkshopConfig.ConversionWeight*conversion +
		c.WorkshopConfig.FreshnessWeight*freshness +
		c.WorkshopConfig.QualityWeight*quality
}
