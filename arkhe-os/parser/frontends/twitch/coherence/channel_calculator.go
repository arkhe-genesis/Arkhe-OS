// parser/frontends/twitch/coherence/channel_calculator.go
package coherence

import (
	"math"
    "strings"
    "time"
    "arkhe/parser/frontends/twitch/models"
)

// ChannelAnalysis acumula métricas para cálculo de coerência de canal
type ChannelAnalysis struct {
	ChannelID             string
	ContentConsistency    float64 // Consistência de categoria/branding (0-1)
	ScheduleAdherence     float64 // Aderência a schedule de streams (0-1)
	CommunityHealth       float64 // Saúde da comunidade (0-1)
	MonetizationBalance   float64 // Equilíbrio de fontes de receita (0-1)
	ToxicityPenalty       float64 // Penalidade por toxicidade (0-1, menor é melhor)

	// Métricas de chat
	TotalChatMessages     int
	AvgSentiment          float64 // -1 a +1
    SentimentScore        float64
	ToxicityRate          float64 // Proporção de mensagens tóxicas

	// Contagem de grafo
	TotalNodes            int
	TotalEdges            int
}

// TwitchCoherenceConfig configura pesos para cálculo de coerência Twitch
type TwitchCoherenceConfig struct {
	ContentConsistencyWeight  float64 // Peso para consistência de conteúdo
	ScheduleAdherenceWeight   float64 // Peso para aderência a schedule
	CommunityHealthWeight     float64 // Peso para saúde da comunidade
	MonetizationBalanceWeight float64 // Peso para equilíbrio de monetização
	ToxicityPenaltyWeight     float64 // Peso para penalidade de toxicidade
}

// DefaultTwitchConfig retorna configurações padrão
func DefaultTwitchConfig() *TwitchCoherenceConfig {
	return &TwitchCoherenceConfig{
		ContentConsistencyWeight:  0.30,
		ScheduleAdherenceWeight:   0.20,
		CommunityHealthWeight:     0.30,
		MonetizationBalanceWeight: 0.15,
		ToxicityPenaltyWeight:     0.05,
	}
}

// CalculateChannelCoherence calcula Φ_C para canal Twitch
func CalculateChannelCoherence(analysis *ChannelAnalysis, cfg *TwitchCoherenceConfig) float64 {
	// Componentes individuais
	contentScore := analysis.ContentConsistency
	scheduleScore := analysis.ScheduleAdherence
	communityScore := analysis.CommunityHealth
	monetizationScore := analysis.MonetizationBalance
	toxicityFactor := 1.0 - analysis.ToxicityPenalty // Converter penalidade para fator positivo

	// Combinação ponderada
	coherence := cfg.ContentConsistencyWeight*contentScore +
		cfg.ScheduleAdherenceWeight*scheduleScore +
		cfg.CommunityHealthWeight*communityScore +
		cfg.MonetizationBalanceWeight*monetizationScore +
		cfg.ToxicityPenaltyWeight*toxicityFactor

	// Normalizar para [0, 1]
	return math.Max(0.0, math.Min(1.0, coherence))
}

// CalculateRealtimeStreamCoherence calcula Φ_C em tempo real para stream ao vivo
func CalculateRealtimeStreamCoherence(stream *models.Stream, chat *models.ChatLog, window time.Duration) float64 {
	if stream == nil {
		return 0.0
	}

	// Engajamento: chat rate normalizado por viewers
	engagement := 0.0
	if stream.ViewerCount > 0 && chat != nil {
		chatRate := chat.MsgsPerMinute
		// Normalizar: 1 msg/viewer/min = 1.0, saturar em 10 msgs/viewer/min
		engagement = math.Min(1.0, chatRate/float64(stream.ViewerCount)*10)
	}

	// Qualidade técnica: penalizar buffering (simulado)
	// Em produção: integrar com métricas reais de player
	qualityFactor := 1.0 // Assumir boa qualidade por default

	// Ambiente saudável: penalizar alta taxa de moderação
	moderationFactor := 1.0
	if chat != nil && chat.TotalMessages > 0 {
		modRate := float64(len(chat.Messages)) // Simplificado
		if modRate > 0.1 { // Mais de 10% das mensagens são ações de mod
			moderationFactor = math.Exp(-2.0 * (modRate - 0.1))
		}
	}

	// Relevância de conteúdo: título/tags vs categoria
	relevanceFactor := calculateContentRelevance(stream)

	// Combinação
	coherence := engagement * qualityFactor * moderationFactor * relevanceFactor

	return math.Max(0.0, math.Min(1.0, coherence))
}

func calculateContentRelevance(stream *models.Stream) float64 {
	if stream == nil || stream.Title == "" {
		return 0.5 // Neutro se sem informação
	}

	// Heurística simples: verificar se título menciona categoria
	titleLower := strings.ToLower(stream.Title)
	categoryLower := strings.ToLower(stream.Category)

	if strings.Contains(titleLower, categoryLower) {
		return 1.0
	}

	// Verificar tags
	for _, tag := range stream.Tags {
		if strings.Contains(titleLower, strings.ToLower(tag)) {
			return 0.9
		}
	}

	// Fallback: assumir relevância moderada
	return 0.7
}
