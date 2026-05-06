package integration

import (
	"math"
	"sync"

	"arkhe/ai"
	"arkhe/parser/lfir"
)

// GitCoherenceMapper mapeia commits Git para gradientes de coerência na Hyper-Mesh
type GitCoherenceMapper struct {
	mu sync.RWMutex

	// Configuração
	config CoherenceMappingConfig

	// Cache de commits processados
	processedCommits map[string]bool

	// Canal de gradientes para submissão
	gradientChannel *ai.CoherenceGradientChannel

	// Métricas de mapeamento
	metrics MapperMetrics
}

// CoherenceMappingConfig contém configuração para mapeamento Git→Coerência
type CoherenceMappingConfig struct {
	EnableAutoSubmission    bool
	CoherenceWeightFix      float64 // Peso para bugfixes
	CoherenceWeightFeature  float64 // Peso para features
	CoherenceWeightRefactor float64 // Peso para refatorações
	MinCoherenceDelta       float64 // Delta mínimo para submissão
	MaxCommitsPerBatch      int
}

// MapperMetrics contém métricas do mapeador
type MapperMetrics struct {
	CommitsProcessed      int64   `json:"commits_processed"`
	GradientsSubmitted    int64   `json:"gradients_submitted"`
	AvgCoherenceDelta     float64 `json:"avg_coherence_delta"`
	PositiveContributions int64   `json:"positive_contributions"`
	NegativeContributions int64   `json:"negative_contributions"`
}

// NewGitCoherenceMapper cria novo mapeador de commits para coerência
func NewGitCoherenceMapper(
	config CoherenceMappingConfig,
	gradientChannel *ai.CoherenceGradientChannel,
) *GitCoherenceMapper {
	if config.CoherenceWeightFix == 0 {
		config.CoherenceWeightFix = 0.05
	}
	if config.CoherenceWeightFeature == 0 {
		config.CoherenceWeightFeature = 0.02
	}
	if config.CoherenceWeightRefactor == 0 {
		config.CoherenceWeightRefactor = 0.01
	}

	return &GitCoherenceMapper{
		config:           config,
		processedCommits: make(map[string]bool),
		gradientChannel:  gradientChannel,
	}
}

// ProcessLFIRGraph processa grafo LFIR de Git e submete commits como gradientes
func (m *GitCoherenceMapper) ProcessLFIRGraph(graph *lfir.LFIRGraph) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	commitsSubmitted := 0

	for _, node := range graph.Nodes {
		if node.Type != lfir.LFIROperation || node.Attributes["type"] != "commit" {
			continue
		}

		commitHash, ok := node.Attributes["full_hash"].(string)
		if !ok {
			continue
		}

		// Verificar se já processado
		if m.processedCommits[commitHash] {
			continue
		}

		// Calcular gradiente de coerência para este commit
		gradient, err := m.computeCoherenceGradient(node)
		if err != nil {
			continue
		}

		// Submeter ao canal de coerência se habilitado e delta significativo
		if m.config.EnableAutoSubmission && math.Abs(gradient) >= m.config.MinCoherenceDelta {
			if err := m.submitGradient(commitHash, gradient, node.Attributes); err != nil {
				// Logar erro mas continuar processamento
				continue
			}
			commitsSubmitted++
			m.metrics.GradientsSubmitted++
		}

		// Atualizar métricas
		m.metrics.CommitsProcessed++
		m.metrics.AvgCoherenceDelta = m.metrics.AvgCoherenceDelta*0.99 + math.Abs(gradient)*0.01
		if gradient > 0 {
			m.metrics.PositiveContributions++
		} else {
			m.metrics.NegativeContributions++
		}

		m.processedCommits[commitHash] = true
	}

	return nil
}

// computeCoherenceGradient calcula contribuição de coerência de um commit
func (m *GitCoherenceMapper) computeCoherenceGradient(commitNode *lfir.LFIRNode) (float64, error) {
	gradient := 0.0

	// Baseado em tags semânticas
	if tags, ok := commitNode.Attributes["semantic_tags"].([]string); ok {
		for _, tag := range tags {
			switch tag {
			case "bugfix", "security":
				gradient += m.config.CoherenceWeightFix
			case "feature":
				gradient += m.config.CoherenceWeightFeature
			case "refactor":
				gradient += m.config.CoherenceWeightRefactor
			case "performance":
				gradient += 0.03
			case "testing", "documentation":
				gradient += 0.005
			}
		}
	}

	// Baseado em métricas de diff
	if added, ok := commitNode.Attributes["lines_added"].(int); ok {
		if removed, ok := commitNode.Attributes["lines_removed"].(int); ok {
			netChange := added - removed
			churn := added + removed

			// Penalizar churn excessivo sem ganho líquido
			if churn > 500 && math.Abs(float64(netChange)) < 50 {
				gradient -= 0.02
			}
			// Bonus para mudanças focadas (alta razão net/churn)
			if churn > 0 && math.Abs(float64(netChange)/float64(churn)) > 0.8 {
				gradient += 0.01
			}
		}
	}

	// Baseado em tipo de commit
	if commitType, ok := commitNode.Attributes["commit_type"].(string); ok {
		switch commitType {
		case "fix":
			gradient += 0.03
		case "feature":
			gradient += 0.01
		case "refactor":
			gradient += 0.005
		}
	}

	return gradient, nil
}

// submitGradient submete gradiente de coerência ao canal
func (m *GitCoherenceMapper) submitGradient(
	commitHash string,
	coherenceDelta float64,
	commitAttrs map[string]interface{},
) error {
	// Preparar metadados para o gradiente
	metadata := map[string]interface{}{
		"source":         "git_workflow",
		"commit_hash":    commitHash,
		"author":         commitAttrs["author"],
		"message":        commitAttrs["message"],
		"timestamp":      commitAttrs["timestamp"],
		"coherence_sign": commitAttrs["coherence_sign"],
	}

	// Converter delta de coerência para vetor de gradiente (simplificado)
	gradientVector := []float64{coherenceDelta}

	// Calcular "coerência" do commit como confiança na contribuição
	coherenceValue := 0.7 + 0.3*math.Abs(coherenceDelta) // [0.7, 1.0]

	// Submeter ao canal
	_, err := m.gradientChannel.SubmitLocalGradient(
		gradientVector,
		coherenceValue,
		0.5, // distância conceitual simulada
		1,   // sample count
		0.0, // loss value (N/A para Git)
		metadata,
	)

	return err
}

// GetMapperMetrics retorna métricas consolidadas do mapeador
func (m *GitCoherenceMapper) GetMapperMetrics() MapperMetrics {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.metrics
}
