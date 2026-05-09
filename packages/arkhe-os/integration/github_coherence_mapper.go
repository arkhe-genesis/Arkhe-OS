package integration

import (
	"math"
	"sync"
	"time"

	"arkhe/ai"
	"arkhe/parser/lfir"
)

// GitHubCoherenceMapper mapeia eventos sociais do GitHub para gradientes de coerência
type GitHubCoherenceMapper struct {
	mu sync.RWMutex

	// Configuração
	config GitHubCoherenceConfig

	// Cache de eventos processados
	processedEvents map[string]bool

	// Canal de gradientes para submissão
	gradientChannel *ai.CoherenceGradientChannel

	// Métricas de mapeamento
	metrics GitHubMapperMetrics

	// Modelo de saúde comunitária aprendido
	communityHealthModel CommunityHealthModel
}

// GitHubCoherenceConfig contém configuração para mapeamento GitHub→Coerência
type GitHubCoherenceConfig struct {
	EnableAutoSubmission   bool
	IssueWeightBug         float64
	IssueWeightEnhancement float64
	PRWeightConsensus      float64
	WorkflowWeightSuccess  float64
	MinCoherenceDelta      float64
	MaxEventsPerBatch      int
	EnableSentimentWeight  bool
}

// CommunityHealthModel representa modelo aprendido de saúde comunitária
type CommunityHealthModel struct {
	Trained          bool
	DiversityWeight  float64 // Peso para diversidade de contribuidores
	ResponseTimeWeight float64 // Peso para tempo de resposta
	ToxicityPenalty  float64 // Penalidade para interações tóxicas
	LastUpdated      time.Time
}

// GitHubMapperMetrics contém métricas do mapeador GitHub
type GitHubMapperMetrics struct {
	EventsProcessed       int64   `json:"events_processed"`
	GradientsSubmitted    int64   `json:"gradients_submitted"`
	AvgCoherenceDelta     float64 `json:"avg_coherence_delta"`
	IssuesMapped          int64   `json:"issues_mapped"`
	PRsMapped             int64   `json:"prs_mapped"`
	WorkflowsMapped       int64   `json:"workflows_mapped"`
	CommunityHealthScore  float64 `json:"community_health_score"`
}

// NewGitHubCoherenceMapper cria novo mapeador de eventos GitHub para coerência
func NewGitHubCoherenceMapper(
	config GitHubCoherenceConfig,
	gradientChannel *ai.CoherenceGradientChannel,
) *GitHubCoherenceMapper {
	if config.IssueWeightBug == 0 {
		config.IssueWeightBug = -0.05
	}
	if config.IssueWeightEnhancement == 0 {
		config.IssueWeightEnhancement = 0.03
	}
	if config.PRWeightConsensus == 0 {
		config.PRWeightConsensus = 0.04
	}
	if config.WorkflowWeightSuccess == 0 {
		config.WorkflowWeightSuccess = 0.02
	}

	return &GitHubCoherenceMapper{
		config:          config,
		processedEvents: make(map[string]bool),
		gradientChannel: gradientChannel,
		communityHealthModel: CommunityHealthModel{
			DiversityWeight:  0.6,
			ResponseTimeWeight: 0.3,
			ToxicityPenalty: 0.1,
		},
	}
}

// ProcessLFIRGraph processa grafo LFIR de GitHub e submete eventos como gradientes
func (m *GitHubCoherenceMapper) ProcessLFIRGraph(graph *lfir.LFIRGraph) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	for _, node := range graph.Nodes {
		if node.Attributes["type"] == nil {
			continue
		}

		eventType, ok := node.Attributes["type"].(string)
		if !ok {
			continue
		}

		eventID := node.ID
		if m.processedEvents[eventID] {
			continue
		}

		// Calcular gradiente de coerência baseado no tipo de evento
		var gradient float64
		var metadata map[string]interface{}

		switch eventType {
		case "issue":
			gradient, metadata = m.computeIssueGradient(node)
			m.metrics.IssuesMapped++
		case "pull_request":
			gradient, metadata = m.computePRGradient(node)
			m.metrics.PRsMapped++
		case "workflow_run":
			gradient, metadata = m.computeWorkflowGradient(node)
			m.metrics.WorkflowsMapped++
		case "repository":
			gradient, metadata = m.computeRepositoryGradient(node)
		case "comment", "pull_request_review":
			gradient, metadata = m.computeCommentGradient(node)
		case "star", "fork", "push", "release":
			gradient, metadata = m.computeActivityGradient(eventType, node)
		default:
			continue
		}

		// Submeter ao canal de coerência se habilitado e delta significativo
		if m.config.EnableAutoSubmission && math.Abs(gradient) >= m.config.MinCoherenceDelta {
			if err := m.submitGradient(eventID, gradient, metadata); err != nil {
				continue
			}
			m.metrics.GradientsSubmitted++
		}

		// Atualizar métricas
		m.metrics.EventsProcessed++
		m.metrics.AvgCoherenceDelta = m.metrics.AvgCoherenceDelta*0.99 + math.Abs(gradient)*0.01

		// Atualizar modelo de saúde comunitária incrementalmente
		m.updateCommunityHealthModel(node, eventType, gradient)

		m.processedEvents[eventID] = true
	}

	// Atualizar score de saúde comunitária agregado
	m.metrics.CommunityHealthScore = m.computeAggregateCommunityHealth()

	return nil
}

// computeIssueGradient calcula contribuição de coerência de uma issue
func (m *GitHubCoherenceMapper) computeIssueGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"event_type": "issue",
		"title":      node.Attributes["title"],
		"state":      node.Attributes["state"],
		"labels":     node.Attributes["labels"],
	}

	// Peso base por labels (Simplificado, assumes we have coherence_delta from parsing)
	if delta, ok := node.Attributes["coherence_delta"].(float64); ok {
	    gradient = delta
    }

	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// computePRGradient calcula contribuição de coerência de um pull request
func (m *GitHubCoherenceMapper) computePRGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"event_type": "pull_request",
		"title":      node.Attributes["title"],
		"state":      node.Attributes["state"],
	}

    if delta, ok := node.Attributes["coherence_delta"].(float64); ok {
	    gradient = delta
    }

	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// computeWorkflowGradient calcula contribuição de coerência de um workflow
func (m *GitHubCoherenceMapper) computeWorkflowGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"event_type": "workflow_run",
		"name":       node.Attributes["name"],
		"status":     node.Attributes["status"],
	}

    if delta, ok := node.Attributes["coherence_delta"].(float64); ok {
	    gradient = delta
    }

	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// computeRepositoryGradient calcula contribuição de coerência de um repositório
func (m *GitHubCoherenceMapper) computeRepositoryGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"event_type": "repository",
		"name":       node.Attributes["type"],
	}
    if health, ok := node.Attributes["health_score"].(float64); ok {
	    gradient += health * 0.01
    }
	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// computeCommentGradient calcula contribuição de coerência de um comentário/review
func (m *GitHubCoherenceMapper) computeCommentGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"event_type": node.Attributes["type"],
		"author":     node.Attributes["author"],
	}
    if m.config.EnableSentimentWeight {
		if sentiment, ok := node.Attributes["sentiment_score"].(float64); ok {
			gradient += sentiment * 0.005
		}
	}
	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// computeActivityGradient calcula contribuição de coerência de atividades sociais
func (m *GitHubCoherenceMapper) computeActivityGradient(activityType string, node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"event_type": activityType,
		"actor":      node.Attributes["actor"],
	}
    if delta, ok := node.Attributes["attention_delta"].(float64); ok {
	    gradient = delta
    }
	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// submitGradient submete gradiente de coerência ao canal
func (m *GitHubCoherenceMapper) submitGradient(
	eventID string,
	coherenceDelta float64,
	metadata map[string]interface{},
) error {
	gradientMetadata := map[string]interface{}{
		"source":        "github_social_layer",
		"event_id":      eventID,
		"timestamp":     time.Now().Unix(),
		"coherence_sign": metadata["coherence_sign"],
	}
	for k, v := range metadata {
		gradientMetadata[k] = v
	}

	gradientVector := []float64{coherenceDelta}
	coherenceValue := 0.7 + 0.3*math.Abs(coherenceDelta)

	_, err := m.gradientChannel.SubmitLocalGradient(
		gradientVector,
		coherenceValue,
		0.5,
		1,
		0.0,
		gradientMetadata,
	)

	return err
}

// updateCommunityHealthModel atualiza modelo de saúde comunitária incrementalmente
func (m *GitHubCoherenceMapper) updateCommunityHealthModel(
	node *lfir.LFIRNode,
	eventType string,
	gradient float64,
) {
	if eventType == "issue" || eventType == "pull_request" {
		if author, ok := node.Attributes["author"].(string); ok && author != "" {
			m.communityHealthModel.Trained = true
		}
	}
	if m.config.EnableSentimentWeight {
		if sentiment, ok := node.Attributes["sentiment_label"].(string); ok && sentiment == "negative" {
			m.communityHealthModel.ToxicityPenalty = math.Min(0.2,
				m.communityHealthModel.ToxicityPenalty+0.001)
		}
	}
	m.communityHealthModel.LastUpdated = time.Now()
}

// computeAggregateCommunityHealth calcula score agregado de saúde comunitária
func (m *GitHubCoherenceMapper) computeAggregateCommunityHealth() float64 {
	if m.metrics.EventsProcessed == 0 {
		return 0.5
	}
	diversityScore := 0.7
	responseScore := 0.8
	toxicityScore := 1.0 - m.communityHealthModel.ToxicityPenalty
	health := (diversityScore*m.communityHealthModel.DiversityWeight + responseScore*m.communityHealthModel.ResponseTimeWeight + toxicityScore) / (m.communityHealthModel.DiversityWeight + m.communityHealthModel.ResponseTimeWeight + 1)
	return math.Max(0, math.Min(1, health))
}
