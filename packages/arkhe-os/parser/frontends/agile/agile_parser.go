// parser/frontends/agile/agile_parser.go
package agile

import (
	"fmt"
	"path/filepath"
	"time"

	"arkhe/parser/frontends/agile/formats"
	"arkhe/parser/frontends/agile/models"
	"arkhe/parser/frontends/agile/analyzers"
	"arkhe/parser/frontends/agile/coherence"
	"arkhe/parser/lfir"
)

// AgileParser implementa Parser para artefatos Scrum/Kanban
type AgileParser struct {
	ToolType       string // "jira", "trello", "azure", "github", "linear", "generic"
	Methodology    string // "scrum", "kanban", "scrumban"
	AnalyzeRetros  bool   // Analisar sentimento de retrospectivas
	DetectBottlenecks bool // Detectar gargalos via CFD
}

// NewAgileParser cria parser com configurações padrão
func NewAgileParser() *AgileParser {
	return &AgileParser{
		ToolType:          "generic",
		Methodology:       "kanban",
		AnalyzeRetros:     true,
		DetectBottlenecks: true,
	}
}

func (p *AgileParser) GetLanguage() string { return "agile-workflow" }

func (p *AgileParser) GetExtensions() []string {
	return []string{".json", ".csv", ".xml", ".yaml", ".md"}
}

// Parse é o método principal
func (p *AgileParser) Parse(source []byte, filename string, metadata map[string]interface{}) (*lfir.LFIRGraph, error) {
	graph := lfir.NewLFIRGraph()
	root := lfir.NewLFIRNode(
		lfir.LFIRNodeTypeModule,
		fmt.Sprintf("agile_project_%s_%d", filepath.Base(filename), time.Now().Unix()),
		"agile",
	)
	graph.AddNode(root)
	graph.RootNodes = append(graph.RootNodes, root.ID)

	// Selecionar adapter baseado na ferramenta
	adapter, err := p.selectAdapter(filename)
	if err != nil {
		return nil, fmt.Errorf("failed to select adapter: %w", err)
	}

	// Parse artefatos da ferramenta
	project, err := adapter.Parse(source, filename)
	if err != nil {
		return nil, fmt.Errorf("failed to parse agile artifacts: %w", err)
	}

	// Converter para modelo interno
	internalModel := p.convertToInternalModel(project)

	// Construir grafo LFIR
	lfirBuilder := models.NewAgileLFIRBuilder(graph, root.ID, p.Methodology)
	if err := lfirBuilder.Build(internalModel); err != nil {
		return nil, fmt.Errorf("failed to build LFIR: %w", err)
	}

	// Analisar métricas ágeis
	metrics, err := p.analyzeMetrics(internalModel)
	if err != nil {
		return nil, fmt.Errorf("failed to analyze metrics: %w", err)
	}

	// Calcular coerência do processo
	cfg := coherence.DefaultAgileConfig(p.Methodology)
	coherenceScore := coherence.CalculateAgileCoherence(metrics, cfg)

	// Detectar gargalos se habilitado
	if p.DetectBottlenecks && p.Methodology == "kanban" {
		bottlenecks := analyzers.DetectBottlenecks(internalModel.CFD)
		root.Attributes["bottleneck_count"] = len(bottlenecks)
		root.Attributes["bottlenecks"] = bottlenecks
		// Penalizar coerência por gargalos severos
		for _, bn := range bottlenecks {
			if bn.Severity > 0.7 {
				coherenceScore *= 0.95 // 5% redução por gargalo severo
			}
		}
	}

	// Analisar retrospectivas se habilitado
	if p.AnalyzeRetros && internalModel.Retrospectives != nil {
		sentiment := analyzers.AnalyzeRetroSentiment(internalModel.Retrospectives)
		root.Attributes["retro_sentiment"] = sentiment
		root.Attributes["team_health_factor"] = sentiment.Score
	}

	// Atualizar root com métricas
	root.Attributes["tool_type"] = p.ToolType
	root.Attributes["methodology"] = p.Methodology
	root.Attributes["total_items"] = metrics.TotalItems
	root.Attributes["completed_items"] = metrics.CompletedItems
	root.Attributes["avg_cycle_time_days"] = metrics.AvgCycleTimeDays
	root.Attributes["avg_lead_time_days"] = metrics.AvgLeadTimeDays
	root.Attributes["flow_efficiency"] = metrics.FlowEfficiency
	root.Attributes["velocity_stability"] = metrics.VelocityStability
	root.Attributes["quality_score"] = metrics.QualityScore
	root.Attributes["waste_ratio"] = metrics.WasteRatio
	root.Attributes["coherence_score"] = coherenceScore
	root.Attributes["coherence_flow"] = metrics.FlowEfficiency
	root.Attributes["coherence_predictability"] = metrics.VelocityStability
	root.Attributes["coherence_quality"] = metrics.QualityScore

	graph.Metrics.CoherenceScore = coherenceScore
	graph.Metrics.NodeCount = metrics.TotalItems
	graph.Metrics.EdgeCount = len(internalModel.Transitions)

	return graph, nil
}

// selectAdapter seleciona adapter baseado no nome do arquivo ou metadata
func (p *AgileParser) selectAdapter(filename string) (formats.ToolAdapter, error) {
	switch p.ToolType {
	case "jira":
		return formats.NewJiraAdapter(), nil
	case "trello":
		return formats.NewTrelloAdapter(), nil
	case "azure":
		return formats.NewAzureAdapter(), nil
	case "github":
		return formats.NewGitHubAdapter(), nil
	case "linear":
		return formats.NewLinearAdapter(), nil
	case "generic":
		// Auto-detect based on file structure
		return formats.AutoDetectAdapter(filename), nil
	default:
		return nil, fmt.Errorf("unsupported tool type: %s", p.ToolType)
	}
}

// convertToInternalModel converte formato da ferramenta para modelo interno
func (p *AgileParser) convertToInternalModel(project *formats.ParsedProject) *models.AgileProject {
	// Implementação de mapeamento genérico
	return &models.AgileProject{
		Name:           project.Name,
		Methodology:    p.Methodology,
		Items:          p.mapItems(project.Items),
		Transitions:    project.Transitions,
		CFD:            project.CFD,
		Sprints:        p.mapSprints(project.Sprints),
		Retrospectives: project.Retros,
		WIPLimits:      project.WIPLimits,
		Columns:        project.Columns,
	}
}

func (p *AgileParser) mapItems(items []models.WorkItem) []models.WorkItem {
	return items
}

func (p *AgileParser) mapSprints(sprints []models.Sprint) []models.Sprint {
	return sprints
}

// analyzeMetrics extrai métricas ágeis do modelo interno
func (p *AgileParser) analyzeMetrics(project *models.AgileProject) (*coherence.AgileMetrics, error) {
	metrics := &coherence.AgileMetrics{}

	// Métricas básicas de fluxo
	metrics.TotalItems = len(project.Items)
	metrics.CompletedItems = countCompleted(project.Items)

	// Cycle time e lead time via Little's Law
	if len(project.Transitions) > 0 {
		ct, lt := analyzers.CalculateCycleAndLeadTime(project.Transitions)
		metrics.AvgCycleTimeDays = ct
		metrics.AvgLeadTimeDays = lt
		if lt > 0 {
			metrics.FlowEfficiency = ct / lt // Simplificado
		}
	}

	// Velocidade e estabilidade (para Scrum)
	if p.Methodology == "scrum" && len(project.Sprints) >= 3 {
		velocities := analyzers.ExtractVelocities(project.Sprints)
		metrics.VelocityStability = analyzers.CalculateVelocityStability(velocities)
	} else {
		metrics.VelocityStability = 1.0 // Neutro para Kanban
	}

	// Qualidade: defeitos pós-release
	metrics.QualityScore = 1.0 - float64(countPostReleaseDefects(project.Items))/float64(max(1, metrics.CompletedItems))

	// Desperdício: tempo bloqueado + retrabalho
	metrics.WasteRatio = analyzers.CalculateWasteRatio(project.Items, project.Transitions)

	return metrics, nil
}

// Helpers
func countCompleted(items []models.WorkItem) int {
	count := 0
	for _, item := range items {
		if item.Status == "Done" || item.Status == "Closed" || item.Status == "Released" {
			count++
		}
	}
	return count
}

func countPostReleaseDefects(items []models.WorkItem) int {
	count := 0
	for _, item := range items {
		if item.Type == models.TypeBug && item.Status == "Done" {
			count++
		}
	}
	return count
}

func max(a, b int) int {
	if a > b { return a }
	return b
}
