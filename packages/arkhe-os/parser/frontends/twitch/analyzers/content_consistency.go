// parser/frontends/twitch/analyzers/content_consistency.go
package analyzers

import (
	"math"

	"arkhe/parser/frontends/twitch/models"
)

// CalculateContentConsistency analisa consistência de categoria e branding
func CalculateContentConsistency(channel *models.Channel) float64 {
	if channel == nil || len(channel.Streams) == 0 {
		return 0.5 // Neutro se sem dados
	}

	// Identificar categorias jogadas
	categories := make(map[string]int)
	var lastCategory string
	categorySwitches := 0

	for _, stream := range channel.Streams {
		if stream.Category != "" {
			categories[stream.Category]++
			if lastCategory != "" && stream.Category != lastCategory {
				categorySwitches++
			}
			lastCategory = stream.Category
		}
	}

	// Se há muito poucas streams, consistência é difícil de medir
	if len(channel.Streams) < 3 {
		return 0.6
	}

	// Calcular proporção de switches (menor = mais consistente)
	switchRatio := float64(categorySwitches) / float64(len(channel.Streams)-1)

	// Verificar categoria dominante
	maxCategoryCount := 0
	for _, count := range categories {
		if count > maxCategoryCount {
			maxCategoryCount = count
		}
	}
	dominanceRatio := float64(maxCategoryCount) / float64(len(channel.Streams))

	// Consistência é alta se:
	// 1. Alta dominância de uma categoria (niche streamer)
	// 2. Poucos switches (fases focadas, ex: speedrunner, maratonas)
	consistency := (dominanceRatio + (1.0 - switchRatio)) / 2.0

	// Variety streamers (muitos switches, baixa dominância)
	// ganham bônus se usarem tags consistentes de "Variety"
	hasVarietyTag := false
	for _, tag := range channel.Tags {
		if tag == "Variety" || tag == "Variedades" {
			hasVarietyTag = true
			break
		}
	}

	if hasVarietyTag && consistency < 0.6 {
		consistency = 0.7 // Variety streamers são consistentes em sua variedade
	}

	return math.Max(0.0, math.Min(1.0, consistency))
}

// CalculateScheduleAdherence analisa previsibilidade de horários
func CalculateScheduleAdherence(channel *models.Channel) float64 {
	if channel == nil || len(channel.Streams) < 5 {
		return 0.5 // Sem dados suficientes
	}

	// Agrupar streams por dia da semana
	// (Implementação simplificada: calcular variância da hora de início)
	var startHours []float64
	for _, stream := range channel.Streams {
		hour := float64(stream.StartedAt.Hour()) + float64(stream.StartedAt.Minute())/60.0
		startHours = append(startHours, hour)
	}

	// Calcular desvio padrão das horas de início
	mean := 0.0
	for _, h := range startHours {
		mean += h
	}
	mean /= float64(len(startHours))

	variance := 0.0
	for _, h := range startHours {
		diff := h - mean
		// Ajustar para diferença circular (23h vs 1h = 2h diferença)
		if diff > 12 {
			diff = 24 - diff
		} else if diff < -12 {
			diff = 24 + diff
		}
		variance += diff * diff
	}
	stdDev := math.Sqrt(variance / float64(len(startHours)))

	// Mapear desvio padrão para score (0-1)
	// stdDev de 0h = score 1.0 (perfeitamente pontual)
	// stdDev de 4h = score 0.0 (totalmente imprevisível)
	score := 1.0 - (stdDev / 4.0)

	return math.Max(0.0, math.Min(1.0, score))
}
