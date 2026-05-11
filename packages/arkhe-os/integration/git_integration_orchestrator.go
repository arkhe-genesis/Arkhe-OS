package integration

import (
	"context"
	"fmt"
	"os/exec"
	"sync"
	"time"

	"arkhe/ai"
	"arkhe/parser/frontends"
)

// IntegrationMetrics contains integration metrics
type IntegrationMetrics struct {
	ScansCompleted   int64          `json:"scans_completed"`
	LastScanTime     time.Time      `json:"last_scan_time"`
	CoherenceMetrics *MapperMetrics `json:"coherence_metrics"`
}

// IntegrationEvent represents an integration event
type IntegrationEvent struct {
	EventType string
	ClusterID string
	Data      map[string]interface{}
	Timestamp time.Time
}

// GitIntegrationOrchestrator orquestra parsing Git → LFIR → Coerência
type GitIntegrationOrchestrator struct {
	mu sync.RWMutex

	// Componentes
	gitParser       *frontends.GitWorkflowFrontend
	coherenceMapper *GitCoherenceMapper

	// Configuração
	config GitIntegrationConfig

	// Estado
	repoPath     string
	lastScanTime time.Time
	scanInterval time.Duration

	// Métricas
	metrics IntegrationMetrics

	// Callbacks
	integrationCallbacks []func(IntegrationEvent)
}

// GitIntegrationConfig contém configuração para integração Git
type GitIntegrationConfig struct {
	ScanIntervalSec     int64
	EnableCoherenceMap  bool
	EnableAutoPromotion bool // Promover repositórios com alta coerência
	CoherenceThreshold  float64
}

// NewGitIntegrationOrchestrator cria novo orquestrador de integração Git
func NewGitIntegrationOrchestrator(
	repoPath string,
	config GitIntegrationConfig,
	gradientChannel *ai.CoherenceGradientChannel,
) (*GitIntegrationOrchestrator, error) {
	if config.ScanIntervalSec == 0 {
		config.ScanIntervalSec = 300 // 5 minutos padrão
	}
	if config.CoherenceThreshold == 0 {
		config.CoherenceThreshold = 0.70
	}

	orch := &GitIntegrationOrchestrator{
		repoPath:     repoPath,
		config:       config,
		scanInterval: time.Duration(config.ScanIntervalSec) * time.Second,
	}

	// Inicializar parser Git
	orch.gitParser = frontends.NewGitWorkflowFrontend(repoPath, frontends.GitParserConfig{
		IncludeDiffs:       true,
		IncludeBranches:    true,
		IncludeTags:        true,
		IncludeReflog:      config.EnableAutoPromotion,
		MaxCommits:         1000,
		SemanticAnalysis:   true,
		CoherenceMapping:   config.EnableCoherenceMap,
	})

	// Inicializar mapeador de coerência se habilitado
	if config.EnableCoherenceMap && gradientChannel != nil {
		orch.coherenceMapper = NewGitCoherenceMapper(
			CoherenceMappingConfig{
				EnableAutoSubmission: true,
				CoherenceWeightFix:   0.05,
				MinCoherenceDelta:    0.01,
			},
			gradientChannel,
		)
	}

	return orch, nil
}

// ScanRepository executa scan do repositório Git e processa para LFIR
func (orch *GitIntegrationOrchestrator) ScanRepository(ctx context.Context) error {
	orch.mu.Lock()
	orch.lastScanTime = time.Now()
	orch.mu.Unlock()

	// Executar git log para obter histórico
	cmd := exec.CommandContext(ctx, "git", "-C", orch.repoPath, "log",
		"--all", "--format=%H|%an|%ae|%at|%s", "--graph", "--decorate")
	output, err := cmd.Output()
	if err != nil {
		return fmt.Errorf("git log failed: %w", err)
	}

	// Parsear para LFIR
	graph, err := orch.gitParser.Parse(output)
	if err != nil {
		return fmt.Errorf("git parsing failed: %w", err)
	}

	// Mapear para gradientes de coerência se habilitado
	if orch.coherenceMapper != nil {
		if err := orch.coherenceMapper.ProcessLFIRGraph(graph); err != nil {
			// Logar erro mas não falhar o scan
		}
	}

	// Atualizar métricas
	orch.mu.Lock()
	orch.metrics.ScansCompleted++
	orch.metrics.LastScanTime = orch.lastScanTime
	orch.mu.Unlock()

	// Notificar callbacks
	for _, cb := range orch.integrationCallbacks {
		cb(IntegrationEvent{
			EventType: "git_scan_completed",
			ClusterID: orch.repoPath,
			Data: map[string]interface{}{
				"commits_parsed": len(graph.Nodes),
				"scan_time":      orch.lastScanTime,
			},
			Timestamp: time.Now(),
		})
	}

	return nil
}

// StartContinuousScanning inicia loop de scan contínuo do repositório
func (orch *GitIntegrationOrchestrator) StartContinuousScanning(ctx context.Context) {
	ticker := time.NewTicker(orch.scanInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			if err := orch.ScanRepository(ctx); err != nil {
				// Logar erro mas continuar loop
				continue
			}
		}
	}
}

// GetIntegrationMetrics retorna métricas consolidadas da integração Git
func (orch *GitIntegrationOrchestrator) GetIntegrationMetrics() IntegrationMetrics {
	orch.mu.RLock()
	defer orch.mu.RUnlock()

	if orch.coherenceMapper != nil {
		mapperMetrics := orch.coherenceMapper.GetMapperMetrics()
		orch.metrics.CoherenceMetrics = &mapperMetrics
	}

	return orch.metrics
}

// RegisterIntegrationCallback registra callback para eventos de integração
func (orch *GitIntegrationOrchestrator) RegisterIntegrationCallback(
	cb func(IntegrationEvent),
) {
	orch.integrationCallbacks = append(orch.integrationCallbacks, cb)
}
