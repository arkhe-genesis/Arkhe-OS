// parser/frontends/twitch/analyzers/revenue_balance.go
package analyzers

import (
	"math"

	"arkhe/parser/frontends/twitch/models"
)

// CalculateRevenueBalance analisa diversificação de receitas
// Alta coerência = receitas diversificadas (baixo risco)
// Baixa coerência = dependência de uma única fonte (ex: 1 sponsor polêmico)
func CalculateRevenueBalance(revenue []models.RevenueEntry) float64 {
	if len(revenue) == 0 {
		return 0.5 // Neutro
	}

	// Agregar por tipo
	totals := make(map[string]float64)
	totalRevenue := 0.0

	for _, entry := range revenue {
		totals[entry.Type] += entry.Amount
		totalRevenue += entry.Amount
	}

	if totalRevenue == 0 {
		return 0.5
	}

	// Calcular Herfindahl-Hirschman Index (HHI) para concentração
	hhi := 0.0
	for _, amount := range totals {
		share := amount / totalRevenue
		hhi += share * share
	}

	// HHI varia de ~0 (muito diversificado) a 1.0 (monopólio/1 fonte)
	// Invertemos para que 1.0 seja o melhor score (balanceado)
	balanceScore := 1.0 - hhi

	// Normalizar (um HHI de 0.2 já é muito diversificado, HHI 1.0 = 0 balance)
	// Mapear [0, 1] HHI -> [1, 0] Score de forma menos linear
	normalizedScore := math.Min(1.0, balanceScore * 1.5)

	return normalizedScore
}

// CalculateToxicityPenalty quantifica penalidade sistêmica por ambiente tóxico
func CalculateToxicityPenalty(toxicityRate float64, actions []models.ModerationAction) float64 {
	// Penalidade baseada na taxa de mensagens tóxicas
	basePenalty := toxicityRate * 10.0 // 10% de chat tóxico = penalty máximo (1.0)

	// Analisar se a moderação está sendo efetiva
	// Se há muitas ações de moderação vs toxicidade, a moderação está agindo
	modEffectiveness := 0.0
	if toxicityRate > 0 && len(actions) > 0 {
		// Simplificação: proporção de bans/timeouts
		modEffectiveness = 0.5
	}

	// Reduzir penalidade se moderação for efetiva
	finalPenalty := basePenalty * (1.0 - modEffectiveness)

	return math.Max(0.0, math.Min(1.0, finalPenalty))
}
