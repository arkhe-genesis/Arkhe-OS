package integration

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"time"

	"arkhe/ai"
	"arkhe/parser/frontends"
)

// ContainerizationIntegrationOrchestrator orquestra parsing de containerização → LFIR → Coerência Efêmera
type ContainerizationIntegrationOrchestrator struct {
	mu sync.RWMutex

	// Componentes
	containerParser *frontends.ContainerizationFrontend
	coherenceMapper *ContainerCoherenceMapper

	// Configuração
	config ContainerizationIntegrationConfig

	// Estado
	monitorPaths   []string             // Diretórios para monitorar (manifests, logs)
	commandPollers map[string]*exec.Cmd // Comandos kubectl/docker em execução
	lastScanTime   time.Time
	scanInterval   time.Duration
	kubeConfigPath string
	dockerEndpoint string

	// Métricas
	metrics IntegrationMetrics

	// Callbacks
	integrationCallbacks []func(IntegrationEvent)
}

// ContainerizationIntegrationConfig contém configuração para integração de containerização
type ContainerizationIntegrationConfig struct {
	ScanIntervalSec      int64
	EnableCoherenceMap   bool
	EnableAutoPromotion  bool // Promover pods com alta coerência efêmera
	CoherenceThreshold   float64
	MonitorManifestPaths []string // Caminhos para manifests YAML/JSON
	MonitorLogPaths      []string // Caminhos para logs de containers
	PollKubectl          bool     // Poll kubectl get pods/services periodicamente
	PollDocker           bool     // Poll docker ps periodicamente
	KubeConfigPath       string   // Caminho para kubeconfig
	DockerEndpoint       string   // Endpoint do Docker daemon
}

type IntegrationMetrics struct {
	ScansCompleted   int64
	FilesScanned     int64
	GraphsProcessed  int64
	CoherenceMetrics *MapperMetrics
}

// NewContainerizationIntegrationOrchestrator cria novo orquestrador de integração de containerização
func NewContainerizationIntegrationOrchestrator(
	config ContainerizationIntegrationConfig,
	gradientChannel *ai.CoherenceGradientChannel,
) (*ContainerizationIntegrationOrchestrator, error) {
	if config.ScanIntervalSec == 0 {
		config.ScanIntervalSec = 180 // 3 minutos padrão para containers (mais dinâmico que VMs)
	}
	if config.CoherenceThreshold == 0 {
		config.CoherenceThreshold = 0.70
	}

	orch := &ContainerizationIntegrationOrchestrator{
		config:         config,
		monitorPaths:   append(config.MonitorManifestPaths, config.MonitorLogPaths...),
		commandPollers: make(map[string]*exec.Cmd),
		scanInterval:   time.Duration(config.ScanIntervalSec) * time.Second,
		kubeConfigPath: config.KubeConfigPath,
		dockerEndpoint: config.DockerEndpoint,
	}

	// Inicializar parser de containerização (auto-detect platform)
	platform := "auto"
	if config.PollKubectl {
		platform = "kubernetes"
	} else if config.PollDocker {
		platform = "docker"
	}

	orch.containerParser, _ = frontends.NewContainerizationFrontend(
		platform,
		"default", // namespace padrão
		frontends.ContainerParserConfig{
			IncludePods:        true,
			IncludeServices:    true,
			IncludeDeployments: true,
			IncludeLogs:        config.MonitorLogPaths != nil,
			CoherenceMapping:   config.EnableCoherenceMap,
			EphemeralWeighting: true,
		},
	)

	// Inicializar mapeador de coerência se habilitado
	if config.EnableCoherenceMap && gradientChannel != nil {
		orch.coherenceMapper = NewContainerCoherenceMapper(
			ContainerCoherenceConfig{
				EnableAutoSubmission:    true,
				WeightPerReplica:        0.01,
				WeightForHealthProbes:   0.03,
				WeightForResourceLimits: 0.02,
				PenaltyForHighErrorRate: 0.05,
				MinCoherenceDelta:       0.01,
				EphemeralDecayFactor:    0.01,
			},
			gradientChannel,
		)
	}

	return orch, nil
}

// ScanContainerizationFiles executa scan de manifests e logs de containerização
func (orch *ContainerizationIntegrationOrchestrator) ScanContainerizationFiles(ctx context.Context) error {
	orch.mu.Lock()
	orch.lastScanTime = time.Now()
	orch.mu.Unlock()

	filesScanned := 0
	graphsProcessed := 0

	// Scan de arquivos de manifest e log
	for _, path := range orch.monitorPaths {
		info, err := os.Stat(path)
		if err != nil {
			continue
		}

		var files []string
		if info.IsDir() {
			// Listar arquivos YAML, JSON e log no diretório
			entries, err := os.ReadDir(path)
			if err != nil {
				continue
			}
			for _, entry := range entries {
				ext := filepath.Ext(entry.Name())
				if ext == ".yaml" || ext == ".yml" || ext == ".json" || ext == ".log" {
					files = append(files, filepath.Join(path, entry.Name()))
				}
			}
		} else {
			files = []string{path}
		}

		for _, file := range files {
			content, err := os.ReadFile(file)
			if err != nil {
				continue
			}

			graph, err := orch.containerParser.Parse(content)
			if err != nil {
				continue
			}

			filesScanned++
			graphsProcessed++

			if orch.coherenceMapper != nil {
				if err := orch.coherenceMapper.ProcessLFIRGraph(graph); err != nil {
					// Logar erro mas não falhar o scan
				}
			}
		}
	}

	// Poll kubectl se habilitado
	if orch.config.PollKubectl && orch.config.KubeConfigPath != "" {
		// Obter pods
		if output, err := exec.CommandContext(ctx, "kubectl",
			"--kubeconfig", orch.config.KubeConfigPath,
			"get", "pods", "-n", "default", "-o", "yaml").Output(); err == nil {
			graph, err := orch.containerParser.Parse(output)
			if err == nil {
				graphsProcessed++
				if orch.coherenceMapper != nil {
					orch.coherenceMapper.ProcessLFIRGraph(graph)
				}
			}
		}

		// Obter services
		if output, err := exec.CommandContext(ctx, "kubectl",
			"--kubeconfig", orch.config.KubeConfigPath,
			"get", "services", "-n", "default", "-o", "yaml").Output(); err == nil {
			graph, err := orch.containerParser.Parse(output)
			if err == nil {
				graphsProcessed++
				if orch.coherenceMapper != nil {
					orch.coherenceMapper.ProcessLFIRGraph(graph)
				}
			}
		}
	}

	// Poll docker se habilitado
	if orch.config.PollDocker && orch.config.DockerEndpoint != "" {
		if output, err := exec.CommandContext(ctx, "docker",
			"-H", orch.config.DockerEndpoint,
			"ps", "--format", "{{.Names}}|{{.Image}}|{{.Status}}").Output(); err == nil {
			// Converter output do docker para formato parseável
			graph, err := orch.containerParser.Parse(output)
			if err == nil {
				graphsProcessed++
				if orch.coherenceMapper != nil {
					orch.coherenceMapper.ProcessLFIRGraph(graph)
				}
			}
		}
	}

	// Atualizar métricas
	orch.mu.Lock()
	orch.metrics.ScansCompleted++
	orch.metrics.FilesScanned += int64(filesScanned)
	orch.metrics.GraphsProcessed += int64(graphsProcessed)
	orch.mu.Unlock()

	// Notificar callbacks
	for _, cb := range orch.integrationCallbacks {
		cb(IntegrationEvent{
			EventType: "containerization_scan_completed",
			ClusterID: fmt.Sprintf("%s/%s", orch.containerParser.GetLanguage(), "default"),
			Data: map[string]interface{}{
				"files_scanned":    filesScanned,
				"graphs_processed": graphsProcessed,
				"scan_time":        orch.lastScanTime,
				"platform":         orch.containerParser.GetLanguage(),
			},
			Timestamp: time.Now(),
		})
	}

	return nil
}

// StartContinuousScanning inicia loop de scan contínuo de containerização
func (orch *ContainerizationIntegrationOrchestrator) StartContinuousScanning(ctx context.Context) {
	ticker := time.NewTicker(orch.scanInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			if err := orch.ScanContainerizationFiles(ctx); err != nil {
				// Logar erro mas continuar loop
				continue
			}
		}
	}
}

// GetIntegrationMetrics retorna métricas consolidadas da integração de containerização
func (orch *ContainerizationIntegrationOrchestrator) GetIntegrationMetrics() IntegrationMetrics {
	orch.mu.RLock()
	defer orch.mu.RUnlock()

	if orch.coherenceMapper != nil {
		mapperMetrics := orch.coherenceMapper.GetMapperMetrics()
		orch.metrics.CoherenceMetrics = &mapperMetrics
	}

	return orch.metrics
}

// RegisterIntegrationCallback registra callback para eventos de integração
func (orch *ContainerizationIntegrationOrchestrator) RegisterIntegrationCallback(
	cb func(IntegrationEvent),
) {
	orch.integrationCallbacks = append(orch.integrationCallbacks, cb)
}
