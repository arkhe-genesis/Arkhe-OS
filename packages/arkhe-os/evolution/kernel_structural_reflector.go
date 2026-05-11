package evolution

import (
	"fmt"
	"math"
	"sort"
	"time"
)

// KernelStructuralReflector analisa histórico estrutural para extrair insights reflexivos
type KernelStructuralReflector struct {
	kernelID             string
	reflectionWindow     time.Duration
	minSamplesForInsight int
}

// KernelInsight representa um insight extraído da reflexão estrutural
type KernelInsight struct {
	InsightID   string
	Description string
	Category    string  // "syscall_performance", "module_health", "config_security", "anomaly"
	Confidence  float64 // [0, 1]
	Value       float64 // Valor quantitativo do insight (ganho potencial)
	Evidence    []string
	Timestamp   time.Time
}

// KernelReflectionResult resultado completo de uma sessão de reflexão
type KernelReflectionResult struct {
	ReflectionID    string
	KernelID        string
	TimeRange       [2]time.Time
	Insights        []KernelInsight
	Patterns        []string
	Anomalies       []KernelAnomaly
	InsightValue    float64
	Recommendations []string
}

// KernelAnomaly representa uma anomalia detectada no histórico estrutural
type KernelAnomaly struct {
	AnomalyID   string
	Timestamp   time.Time
	Description string
	Severity    string // "low", "medium", "high", "critical"
	Metrics     map[string]float64
}

// NewKernelStructuralReflector cria novo reflexor estrutural do kernel
func NewKernelStructuralReflector(kernelID string, window time.Duration) *KernelStructuralReflector {
	return &KernelStructuralReflector{
		kernelID:             kernelID,
		reflectionWindow:     window,
		minSamplesForInsight: 20,
	}
}

// Analyze executa análise reflexiva sobre histórico estrutural do kernel
func (r *KernelStructuralReflector) Analyze(
	coherenceSamples []KernelCoherenceSample,
	metricsSamples []KernelStructuralMetrics,
	window time.Duration,
) (*KernelReflectionResult, error) {
	if len(coherenceSamples) < r.minSamplesForInsight {
		return nil, fmt.Errorf("insufficient samples: %d < %d", len(coherenceSamples), r.minSamplesForInsight)
	}

	// Filtrar amostras dentro da janela de reflexão
	now := time.Now()
	windowStart := now.Add(-window)
	var filteredCoherence []KernelCoherenceSample
	var filteredMetrics []KernelStructuralMetrics

	for i, s := range coherenceSamples {
		if s.Timestamp.After(windowStart) {
			filteredCoherence = append(filteredCoherence, s)
			if i < len(metricsSamples) {
				filteredMetrics = append(filteredMetrics, metricsSamples[i])
			}
		}
	}

	if len(filteredCoherence) < r.minSamplesForInsight {
		return nil, fmt.Errorf("insufficient samples in window: %d", len(filteredCoherence))
	}

	// Ordenar por timestamp
	sort.Slice(filteredCoherence, func(i, j int) bool {
		return filteredCoherence[i].Timestamp.Before(filteredCoherence[j].Timestamp)
	})

	// Extrair insights via múltiplos analisadores
	var insights []KernelInsight
	insights = append(insights, r.analyzeSyscallPerformance(filteredCoherence)...)
	insights = append(insights, r.analyzeModuleHealth(filteredCoherence, filteredMetrics)...)
	insights = append(insights, r.analyzeConfigSecurity(filteredMetrics)...)
	insights = append(insights, r.detectStructuralAnomalies(filteredCoherence)...)

	// Filtrar insights com base no limite
	// Embora pudéssemos receber isso como parâmetro, simularemos o limite de 0.15 aqui
	// (ou seria melhor adicionar um campo metaParameters). Para simplicidade de integração:
	var filteredInsights []KernelInsight
	for _, insight := range insights {
		if insight.Value*insight.Confidence > 0.15 {
			filteredInsights = append(filteredInsights, insight)
		} else if insight.Value*insight.Confidence < -0.15 {
			filteredInsights = append(filteredInsights, insight)
		}
	}
	insights = filteredInsights

	// Calcular valor agregado de insights
	insightValue := 0.0
	for _, insight := range insights {
		insightValue += insight.Value * insight.Confidence
	}
	insightValue /= math.Max(1, float64(len(insights)))

	// Gerar recomendações baseadas em insights
	recommendations := r.generateKernelRecommendations(insights)

	result := &KernelReflectionResult{
		ReflectionID:    fmt.Sprintf("kernel_reflex_%s_%d", r.kernelID[:8], time.Now().UnixNano()),
		KernelID:        r.kernelID,
		TimeRange:       [2]time.Time{filteredCoherence[0].Timestamp, filteredCoherence[len(filteredCoherence)-1].Timestamp},
		Insights:        insights,
		InsightValue:    insightValue,
		Recommendations: recommendations,
	}

	return result, nil
}

// analyzeSyscallPerformance analisa tendências de desempenho de syscalls
func (r *KernelStructuralReflector) analyzeSyscallPerformance(samples []KernelCoherenceSample) []KernelInsight {
	var insights []KernelInsight

	if len(samples) < 30 {
		return insights
	}

	// Calcular tendência da taxa de sucesso de syscalls
	var successRates []float64
	for _, s := range samples {
		successRates = append(successRates, s.SyscallSuccessRate)
	}

	// Regressão linear simples para tendência
	n := float64(len(successRates))
	var sumX, sumY, sumXY, sumX2 float64
	for i, rate := range successRates {
		x := float64(i)
		y := rate
		sumX += x
		sumY += y
		sumXY += x * y
		sumX2 += x * x
	}

	slope := (n*sumXY - sumX*sumY) / (n*sumX2 - sumX*sumX)

	// Insight: tendência de desempenho de syscalls
	if math.Abs(slope) > 0.0001 {
		direction := "stable"
		if slope > 0 {
			direction = "improving"
		} else {
			direction = "degrading"
		}

		insights = append(insights, KernelInsight{
			InsightID:   fmt.Sprintf("syscall_trend_%s", r.kernelID[:8]),
			Description: fmt.Sprintf("Syscall success rate %s at rate %.6f per sample", direction, slope),
			Category:    "syscall_performance",
			Confidence:  math.Min(0.95, 0.7+math.Abs(slope)*100),
			Value:       math.Abs(slope) * 0.02,
			Evidence: []string{
				fmt.Sprintf("samples_analyzed: %d", len(samples)),
				fmt.Sprintf("success_rate_range: [%.4f, %.4f]", successRates[0], successRates[len(successRates)-1]),
			},
			Timestamp: time.Now(),
		})
	}

	return insights
}

// analyzeModuleHealth analisa saúde de módulos carregados
func (r *KernelStructuralReflector) analyzeModuleHealth(
	coherenceSamples []KernelCoherenceSample,
	metricsSamples []KernelStructuralMetrics,
) []KernelInsight {
	var insights []KernelInsight

	if len(metricsSamples) < 20 {
		return insights
	}

	// Analisar correlação entre saúde de módulos e coerência
	var healthValues, coherenceValues []float64
	for i, m := range metricsSamples {
		if i < len(coherenceSamples) {
			healthValues = append(healthValues, computeModuleHealthAvg(m))
			coherenceValues = append(coherenceValues, coherenceSamples[i].Coherence)
		}
	}

	// Calcular correlação de Pearson
	var corr float64
	if len(healthValues) >= 2 {
		corr = computePearsonCorrelation(healthValues, coherenceValues)
	}

	// Insight: correlação módulo-coerência
	if math.Abs(corr) > 0.5 {
		relationship := "uncorrelated"
		if corr > 0 {
			relationship = "positively correlated"
		} else {
			relationship = "negatively correlated"
		}

		insights = append(insights, KernelInsight{
			InsightID:   fmt.Sprintf("module_corr_%s", r.kernelID[:8]),
			Description: fmt.Sprintf("Module health %s with kernel coherence (r=%.3f)", relationship, corr),
			Category:    "module_health",
			Confidence:  math.Abs(corr),
			Value:       0.02 * math.Abs(corr),
			Evidence: []string{
				fmt.Sprintf("correlation_coefficient: %.3f", corr),
				fmt.Sprintf("avg_module_health: %.3f", avgFloat64(healthValues)),
			},
			Timestamp: time.Now(),
		})
	}

	return insights
}

// analyzeConfigSecurity analisa conformidade de configuração de segurança
func (r *KernelStructuralReflector) analyzeConfigSecurity(metricsSamples []KernelStructuralMetrics) []KernelInsight {
	var insights []KernelInsight

	if len(metricsSamples) < 10 {
		return insights
	}

	// Verificar consistência de configurações de segurança
	var complianceScores []float64
	for _, m := range metricsSamples {
		complianceScores = append(complianceScores, computeConfigCompliance(m))
	}

	avgCompliance := avgFloat64(complianceScores)
	minCompliance := minFloat64(complianceScores)

	// Insight: conformidade de segurança
	if minCompliance < 0.90 {
		insights = append(insights, KernelInsight{
			InsightID:   fmt.Sprintf("security_compliance_%s", r.kernelID[:8]),
			Description: fmt.Sprintf("Security config compliance dropped to %.2f%% (avg: %.2f%%)", minCompliance*100, avgCompliance*100),
			Category:    "config_security",
			Confidence:  0.9,
			Value:       -0.03, // Valor negativo: problema de segurança
			Evidence: []string{
				fmt.Sprintf("min_compliance: %.3f", minCompliance),
				fmt.Sprintf("avg_compliance: %.3f", avgCompliance),
			},
			Timestamp: time.Now(),
		})
	} else if avgCompliance >= 1.0 {
		insights = append(insights, KernelInsight{
			InsightID:   fmt.Sprintf("security_optimal_%s", r.kernelID[:8]),
			Description: "All recommended security configurations are enabled",
			Category:    "config_security",
			Confidence:  0.95,
			Value:       0.01,
			Evidence:    []string{"compliance_score: 1.0"},
			Timestamp:   time.Now(),
		})
	}

	return insights
}

// detectStructuralAnomalies detecta anomalias no histórico estrutural
func (r *KernelStructuralReflector) detectStructuralAnomalies(samples []KernelCoherenceSample) []KernelInsight {
	var insights []KernelInsight

	if len(samples) < 50 {
		return insights
	}

	// Calcular média e desvio padrão de coerência
	var mean, variance float64
	for _, s := range samples {
		mean += s.Coherence
	}
	mean /= float64(len(samples))
	for _, s := range samples {
		variance += (s.Coherence - mean) * (s.Coherence - mean)
	}
	variance /= float64(len(samples))
	stdDev := math.Sqrt(variance)

	// Detectar pontos fora de 2.5σ
	threshold := 2.5 * stdDev
	for _, s := range samples {
		deviation := math.Abs(s.Coherence - mean)
		if deviation > threshold {
			_ = "medium"
			if deviation > 3.5*stdDev {
				_ = "critical"
			} else if deviation > 3.0*stdDev {
				_ = "high"
			}

			insights = append(insights, KernelInsight{
				InsightID:   fmt.Sprintf("anomaly_%s_%d", r.kernelID[:8], s.Timestamp.Unix()),
				Description: fmt.Sprintf("Structural coherence anomaly: %.3fσ deviation at %s", deviation/stdDev, s.Timestamp.Format(time.RFC3339)),
				Category:    "anomaly",
				Confidence:  0.95,
				Value:       -0.02,
				Evidence: []string{
					fmt.Sprintf("observed_coherence: %.3f", s.Coherence),
					fmt.Sprintf("expected_coherence: %.3f ± %.3f", mean, stdDev),
				},
				Timestamp: time.Now(),
			})
		}
	}

	return insights
}

// generateKernelRecommendations gera recomendações baseadas em insights
func (r *KernelStructuralReflector) generateKernelRecommendations(insights []KernelInsight) []string {
	var recommendations []string

	for _, insight := range insights {
		switch insight.Category {
		case "syscall_performance":
			if insight.Value < 0 {
				recommendations = append(recommendations, "Review syscall handling for potential performance bottlenecks")
			}
		case "module_health":
			if insight.Value < 0 {
				recommendations = append(recommendations, "Investigate module dependencies for potential health issues")
			}
		case "config_security":
			if insight.Value < 0 {
				recommendations = append(recommendations, "Enable recommended security configurations to improve structural integrity")
			}
		case "anomaly":
			recommendations = append(recommendations, "Investigate structural coherence anomaly for potential root cause")
		}
	}

	return recommendations
}

// Helper functions
func computePearsonCorrelation(x, y []float64) float64 {
	if len(x) != len(y) || len(x) < 2 {
		return 0
	}
	n := float64(len(x))
	var sumX, sumY, sumXY, sumX2, sumY2 float64
	for i := range x {
		sumX += x[i]
		sumY += y[i]
		sumXY += x[i] * y[i]
		sumX2 += x[i] * x[i]
		sumY2 += y[i] * y[i]
	}
	numerator := n*sumXY - sumX*sumY
	denominator := math.Sqrt((n*sumX2 - sumX*sumX) * (n*sumY2 - sumY*sumY))
	if denominator < 1e-10 {
		return 0
	}
	return numerator / denominator
}

func avgFloat64(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	var sum float64
	for _, v := range values {
		sum += v
	}
	return sum / float64(len(values))
}

func minFloat64(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	min := values[0]
	for _, v := range values[1:] {
		if v < min {
			min = v
		}
	}
	return min
}
