// parser/frontends/twitch/twitch_parser.go
package twitch

import (
	"context"
	"fmt"
	"path/filepath"
	"strings"
	"time"

	"arkhe/parser/frontends/twitch/api"
	"arkhe/parser/frontends/twitch/parsers"
	"arkhe/parser/frontends/twitch/models"
	"arkhe/parser/frontends/twitch/analyzers"
	"arkhe/parser/frontends/twitch/coherence"
	"arkhe/parser/lfir"
)

// TwitchParser implementa Parser para dados da Twitch
type TwitchParser struct {
	ClientID          string // Twitch API Client ID
	ClientSecret      string // Twitch API Client Secret
	AccessToken       string // OAuth access token (opcional)
	AnalyzeChat       bool   // Analisar logs de chat
	AnalyzeMonetization bool // Analisar dados de monetização
	RealtimeMode      bool   // Modo em tempo real via WebSocket
	CoherenceWindow   time.Duration // Janela para cálculo de Φ_C (default: 5min)
}

// NewTwitchParser cria parser com configurações padrão
func NewTwitchParser() *TwitchParser {
	return &TwitchParser{
		AnalyzeChat:         true,
		AnalyzeMonetization: true,
		RealtimeMode:        false,
		CoherenceWindow:     5 * time.Minute,
	}
}

func (p *TwitchParser) GetLanguage() string { return "twitch-streaming" }

func (p *TwitchParser) GetExtensions() []string {
	return []string{".json", ".txt", ".log", ".csv", ".irc"}
}

// Parse é o método principal
func (p *TwitchParser) Parse(source []byte, filename string, metadata map[string]interface{}) (*lfir.LFIRGraph, error) {
	graph := lfir.NewLFIRGraph()
	root := lfir.NewLFIRNode(
		lfir.LFIRNodeTypeModule,
		fmt.Sprintf("twitch_channel_%s_%d", filepath.Base(filename), time.Now().Unix()),
		"twitch",
	)
	graph.AddNode(root)
	graph.RootNodes = append(graph.RootNodes, root.ID)

	// Detectar tipo de dado de entrada
	dataType := detectDataType(filename, source)

	var channel *models.Channel
	var err error

	switch dataType {
	case "channel_export":
		channel, err = parsers.ParseChannelExport(source)
	case "chat_log":
		channel, err = parsers.ParseChatLog(source, metadata)
	case "stream_metrics":
		channel, err = parsers.ParseStreamMetrics(source)
	case "api_response":
		// Se temos credenciais, buscar dados via API
		if p.ClientID != "" {
			client := api.NewClient(p.ClientID, p.ClientSecret, p.AccessToken)
			channel, err = p.fetchChannelData(client, metadata)
		} else {
			channel, err = parsers.ParseAPIResponse(source)
		}
	default:
		return nil, fmt.Errorf("tipo de dado não reconhecido: %s", dataType)
	}

	if err != nil {
		return nil, fmt.Errorf("failed to parse Twitch data: %w", err)
	}

	// Construir grafo LFIR
	lfirBuilder := models.NewTwitchLFIRBuilder(graph, root.ID)
	if err := lfirBuilder.Build(channel); err != nil {
		return nil, fmt.Errorf("failed to build LFIR: %w", err)
	}

	// Analisar métricas de coerência
	analysis, err := p.analyzeChannel(channel)
	if err != nil {
		return nil, fmt.Errorf("failed to analyze channel: %w", err)
	}

	// Calcular coerência
	cfg := coherence.DefaultTwitchConfig()
	channelCoherence := coherence.CalculateChannelCoherence(analysis, cfg)

	// Modo em tempo real: calcular Φ_C com janela deslizante
	if p.RealtimeMode && channel.LiveStream != nil {
		realtimeCoherence := coherence.CalculateRealtimeStreamCoherence(
			channel.LiveStream,
			channel.Chat,
			p.CoherenceWindow,
		)
		root.Attributes["realtime_coherence"] = realtimeCoherence
		root.Attributes["coherence_window_minutes"] = p.CoherenceWindow.Minutes()
	}

	// Atualizar root com métricas
	root.Attributes["channel_id"] = channel.ID
	root.Attributes["channel_name"] = channel.Name
	root.Attributes["is_live"] = channel.LiveStream != nil
	root.Attributes["follower_count"] = channel.FollowerCount
	root.Attributes["total_views"] = channel.TotalViews
	root.Attributes["stream_count"] = len(channel.Streams)
	root.Attributes["chat_message_count"] = analysis.TotalChatMessages
	root.Attributes["coherence_score"] = channelCoherence
	root.Attributes["coherence_content_consistency"] = analysis.ContentConsistency
	root.Attributes["coherence_schedule_adherence"] = analysis.ScheduleAdherence
	root.Attributes["coherence_community_health"] = analysis.CommunityHealth
	root.Attributes["coherence_monetization_balance"] = analysis.MonetizationBalance
	root.Attributes["coherence_toxicity_penalty"] = analysis.ToxicityPenalty

	graph.Metrics.CoherenceScore = channelCoherence
	graph.Metrics.NodeCount = analysis.TotalNodes
	graph.Metrics.EdgeCount = analysis.TotalEdges

	return graph, nil
}

// detectDataType identifica o tipo de dado de entrada
func detectDataType(filename string, source []byte) string {
	ext := strings.ToLower(filepath.Ext(filename))

	switch ext {
	case ".json":
		if strings.Contains(filename, "chat") || strings.Contains(filename, "log") {
			return "chat_log"
		}
		if strings.Contains(filename, "stream") || strings.Contains(filename, "metrics") {
			return "stream_metrics"
		}
		if strings.Contains(filename, "channel") || strings.Contains(filename, "export") {
			return "channel_export"
		}
		return "api_response"
	case ".txt", ".log", ".irc":
		return "chat_log"
	case ".csv":
		if strings.Contains(filename, "chat") {
			return "chat_log"
		}
		return "stream_metrics"
	default:
		// Tentar detectar por conteúdo
		if strings.Contains(string(source), "broadcaster_id") {
			return "api_response"
		}
		if strings.Contains(string(source), ":tmi.twitch.tv") {
			return "chat_log"
		}
		return "unknown"
	}
}

// fetchChannelData busca dados via Twitch API
func (p *TwitchParser) fetchChannelData(client *api.Client, metadata map[string]interface{}) (*models.Channel, error) {
	ctx := context.Background()

	// Obter ID do canal se necessário
	channelName, ok := metadata["channel_name"].(string)
	if !ok {
		return nil, fmt.Errorf("channel_name required in metadata for API fetch")
	}

	// Buscar dados do canal
	channelData, err := client.GetChannel(ctx, channelName)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch channel: %w", err)
	}

	// Buscar streams recentes
	streams, err := client.GetChannelStreams(ctx, channelData.ID, 10)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch streams: %w", err)
	}

	// Buscar dados de comunidade se habilitado
	var followers []models.Follower
	var subscribers []models.Subscriber
	if p.AnalyzeChat {
		// Followers / Subs are returning interface{} in mock, not models
		// followers, _ = client.GetFollowers(ctx, channelData.ID, 100)
		// subscribers, _ = client.GetSubscribers(ctx, channelData.ID, 100)
	}

	// Buscar dados de monetização se habilitado
	var revenue []models.RevenueEntry
	if p.AnalyzeMonetization {
		// revenue, _ = client.GetRevenueSummary(ctx, channelData.ID, "last_30_days")
	}
    // Convert API stream slice to models stream slice
    var modelStreams []models.Stream
    for _, s := range streams {
        modelStreams = append(modelStreams, models.Stream{
            ID: s.ID,
            Title: s.Title,
            Category: s.GameName,
            StartedAt: s.StartedAt,
            ViewerCount: s.ViewerCount,
        })
    }

    var liveStream *models.Stream
    if channelData.LiveStream != nil {
        liveStream = &models.Stream{
            ID: channelData.LiveStream.ID,
            Title: channelData.LiveStream.Title,
            Category: channelData.LiveStream.GameName,
            StartedAt: channelData.LiveStream.StartedAt,
            ViewerCount: channelData.LiveStream.ViewerCount,
        }
    }

	// Construir modelo de canal
	channel := &models.Channel{
		ID:            channelData.ID,
		Name:          channelData.Name,
		DisplayName:   channelData.DisplayName,
		Description:   channelData.Description,
		CreatedAt:     channelData.CreatedAt,
		FollowerCount: channelData.FollowerCount,
		TotalViews:    channelData.ViewCount,
		LiveStream:    liveStream,
		Streams:       modelStreams,
		Followers:     followers,
		Subscribers:   subscribers,
		Revenue:       revenue,
		Category:      channelData.Category,
		Tags:          channelData.Tags,
		Language:      channelData.Language,
		Mature:        channelData.Mature,
	}

	return channel, nil
}

// analyzeChannel executa análise de coerência do canal
func (p *TwitchParser) analyzeChannel(channel *models.Channel) (*coherence.ChannelAnalysis, error) {
	analysis := &coherence.ChannelAnalysis{
		ChannelID: channel.ID,
	}

	// Analisar consistência de conteúdo
	analysis.ContentConsistency = analyzers.CalculateContentConsistency(channel)

	// Analisar aderência a schedule
	analysis.ScheduleAdherence = analyzers.CalculateScheduleAdherence(channel)

	// Analisar saúde da comunidade
	if p.AnalyzeChat {
		chatAnalysis, err := analyzers.AnalyzeCommunityHealth(channel)
		if err != nil {
			return nil, fmt.Errorf("failed to analyze community: %w", err)
		}
		analysis.CommunityHealth = chatAnalysis.HealthScore
		analysis.TotalChatMessages = chatAnalysis.TotalMessages
		analysis.SentimentScore = chatAnalysis.AvgSentiment
		analysis.ToxicityRate = chatAnalysis.ToxicityRate
	} else {
		analysis.CommunityHealth = 0.7 // Default neutro
	}

	// Analisar equilíbrio de monetização
	if p.AnalyzeMonetization && len(channel.Revenue) > 0 {
		analysis.MonetizationBalance = analyzers.CalculateRevenueBalance(channel.Revenue)
	} else {
		analysis.MonetizationBalance = 1.0 // Neutro se sem dados
	}

	// Calcular penalidade por toxicidade
	analysis.ToxicityPenalty = analyzers.CalculateToxicityPenalty(analysis.ToxicityRate, channel.ModerationActions)

	// Contar nós e arestas do grafo implícito
	analysis.TotalNodes = 1 + len(channel.Streams) + len(channel.Followers)/100 // Amostragem
	analysis.TotalEdges = len(channel.Streams) * 2 // Stream → Channel + Stream → Category

	return analysis, nil
}
