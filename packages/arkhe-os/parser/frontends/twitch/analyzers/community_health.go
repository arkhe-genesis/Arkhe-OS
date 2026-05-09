// parser/frontends/twitch/analyzers/community_health.go
package analyzers

import (
	"fmt"
	"math"

	"arkhe/parser/frontends/twitch/models"
)

type CommunityAnalysis struct {
	HealthScore   float64
	TotalMessages int
	AvgSentiment  float64
	ToxicityRate  float64
}

// AnalyzeCommunityHealth analisa retenção, sentiment e toxicidade
func AnalyzeCommunityHealth(channel *models.Channel) (*CommunityAnalysis, error) {
	if channel == nil {
		return nil, fmt.Errorf("channel is nil")
	}

	analysis := &CommunityAnalysis{
		HealthScore: 0.5, // Base
	}

	if channel.Chat == nil || len(channel.Chat.Messages) == 0 {
		return analysis, nil // Sem dados de chat
	}

	analysis.TotalMessages = len(channel.Chat.Messages)

	// Calcular métricas agregadas
	totalSentiment := 0.0
	toxicCount := 0
	spamCount := 0

	for _, msg := range channel.Chat.Messages {
		// Opcionalmente integrar com VADER ou outro NLP aqui
		// Por ora usamos os valores que já vieram no parse/metadata
		totalSentiment += msg.Sentiment

		if msg.IsToxic {
			toxicCount++
		}
		if msg.IsSpam {
			spamCount++
		}
	}

	analysis.AvgSentiment = totalSentiment / float64(analysis.TotalMessages)
	analysis.ToxicityRate = float64(toxicCount) / float64(analysis.TotalMessages)
	spamRate := float64(spamCount) / float64(analysis.TotalMessages)

	// Score de Retenção (Aproximação: unique users vs total followers/viewers)
	retentionScore := 0.5
	if channel.FollowerCount > 0 {
		engagementRatio := float64(channel.Chat.UniqueUsers) / float64(channel.FollowerCount)
		// Normalizar (ex: 5% da base de followers ativa no chat = 1.0)
		retentionScore = math.Min(1.0, engagementRatio / 0.05)
	}

	// Score de Ambiente Saudável (Penaliza forte toxicidade e spam)
	envScore := 1.0 - (analysis.ToxicityRate * 5.0) - (spamRate * 2.0)
	envScore = math.Max(0.0, envScore)

	// Score de Positividade (Baseado no sentiment -1 a +1 mapeado para 0-1)
	sentimentScore := (analysis.AvgSentiment + 1.0) / 2.0

	// Peso final
	analysis.HealthScore = (retentionScore*0.3) + (envScore*0.4) + (sentimentScore*0.3)

	return analysis, nil
}
