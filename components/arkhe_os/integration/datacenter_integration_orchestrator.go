package integration

import (
	"context"
	"fmt"
	"sync"
	"time"

	"arkhe_os/parser/frontends"
	"arkhe_os/parser/lfir"
	"arkhe_os/network"
)

// DataCenterIntegrationOrchestrator orquestra parsing → monitoramento → promoção
type DataCenterIntegrationOrchestrator struct {
	mu sync.RWMutex

	// Componentes
	parser            *frontends.DataCenterFrontend
	emMonitor         *EMCoherenceMonitor
	promotionProtocol *DataCenterPromotionProtocol
	gradientMapper    *GradientToActionPotentialMapper

	// Configuração
	config IntegrationConfig

	// Estado
	promotedNodes map[string]*DataCenterNode
	parsingJobs   map[string]*ParsingJob

	// Métricas
	metrics IntegrationMetrics

	// Callbacks
	integrationCallbacks []func(IntegrationEvent)
}

// IntegrationConfig contém configuração para orquestração de integração
type IntegrationConfig struct {
	ParseIntervalSec      int64
	PromotionEnabled      bool
	GradientMappingEnabled bool
	MinGPUsForPromotion   int
	CoherenceThreshold    float64
	PromotionHysteresis   float64
}

// IntegrationMetrics contém métricas de integração
type IntegrationMetrics struct {
	ParsingJobsCompleted  int64   `json:"parsing_jobs_completed"`
	PromotionsTriggered   int64   `json:"promotions_triggered"`
	GradientsMapped       int64   `json:"gradients_mapped"`
	PotentialsFired       int64   `json:"potentials_fired"`
	AvgCoherenceDC        float64 `json:"avg_coherence_dc"`
	ActivePromotedNodes   int64   `json:"active_promoted_nodes"`
}

// IntegrationEvent representa evento de integração para callbacks
type IntegrationEvent struct {
	EventType   string                 // "parsed", "promoted", "gradient_mapped", "potential_fired"
	ClusterID   string
	Data        map[string]interface{}
	Timestamp   time.Time
}

// NewDataCenterIntegrationOrchestrator cria novo orquestrador de integração
func NewDataCenterIntegrationOrchestrator(
	clusterID string,
	datacenterName string,
	wheelerMesh *network.WheelerMeshProtocol,
	config IntegrationConfig,
) (*DataCenterIntegrationOrchestrator, error) {
	if config.CoherenceThreshold == 0 {
		config.CoherenceThreshold = 0.70
	}
	if config.PromotionHysteresis == 0 {
		config.PromotionHysteresis = 0.05
	}

	orch := &DataCenterIntegrationOrchestrator{
		config:          config,
		promotedNodes:   make(map[string]*DataCenterNode),
		parsingJobs:     make(map[string]*ParsingJob),
	}

	// Inicializar parser
	orch.parser, _ = frontends.NewDataCenterFrontend(clusterID, frontends.ParserConfig{
		EnableNvidiaSMI:    true,
		EnableK8sQueries:   true,
		EnableLogParsing:   true,
		EnableConfigParsing: true,
		ParseIntervalSec:   config.ParseIntervalSec,
	})

	// Inicializar monitor de coerência EM
	orch.emMonitor, _ = NewEMCoherenceMonitor(
		fmt.Sprintf("em_monitor_%s", clusterID[:8]),
		clusterID,
		datacenterName,
		EMCoherenceMonitorConfig{
			EnableGeomagSensor:  true,
			EnableMetasurface:   true,
			CoherenceThreshold:  config.CoherenceThreshold,
			PromotionHysteresis: config.PromotionHysteresis,
		},
	)

	// Inicializar protocolo de promoção se habilitado
	if config.PromotionEnabled {
		orch.promotionProtocol = NewDataCenterPromotionProtocol(
			fmt.Sprintf("promo_%s", clusterID[:8]),
			clusterID,
			wheelerMesh,
			PromotionConfig{
				AutoPromotionEnabled:    true,
				RequireHandshake:        true,
				MinSustainedCoherence:   config.CoherenceThreshold - 0.05,
			},
		)
        // Configure promotedNodes
        orch.promotionProtocol.SetPromotedNodes(orch.promotedNodes)
	}

	// Inicializar mapeador de gradientes se habilitado
	if config.GradientMappingEnabled {
		orch.gradientMapper = NewGradientToActionPotentialMapper(map[string]float64{
			"scale_factor":   1.0,
			"fire_threshold": 0.1,
		})
	}

	// Registrar callback de promoção no monitor EM
	orch.emMonitor.RegisterPromotionCallback(func(cid string, coherence float64) {
		if orch.promotionProtocol != nil {
			orch.promotionProtocol.checkPromotionEligibility(cid, coherence)
		}
		orch.metrics.AvgCoherenceDC = orch.metrics.AvgCoherenceDC*0.99 + coherence*0.01
	})

	return orch, nil
}

// StartParsingJob inicia job de parsing contínuo para data center
func (orch *DataCenterIntegrationOrchestrator) StartParsingJob(
	ctx context.Context,
	dataSource DataSource,
) (*ParsingJob, error) {
	job := &ParsingJob{
		JobID:      fmt.Sprintf("parse_%s_%d", orch.parser.GetClusterName(), time.Now().UnixNano()),
		DataSource: dataSource,
		StartTime:  time.Now(),
		Status:     "running",
	}

	orch.mu.Lock()
	orch.parsingJobs[job.JobID] = job
	orch.mu.Unlock()

	// Executar parsing em background
	go orch.runParsingLoop(ctx, job)

	return job, nil
}

// runParsingLoop executa loop contínuo de parsing e integração
func (orch *DataCenterIntegrationOrchestrator) runParsingLoop(
	ctx context.Context,
	job *ParsingJob,
) {
	ticker := time.NewTicker(time.Duration(orch.config.ParseIntervalSec) * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			job.Status = "stopped"
			return
		case <-ticker.C:
			// Coletar dados da fonte
			data, err := job.DataSource.Collect()
			if err != nil {
				job.LastError = err.Error()
				continue
			}

			// Parse para LFIR
			lfirGraph, err := orch.parser.Parse(data)
			if err != nil {
				job.LastError = fmt.Sprintf("parse failed: %v", err)
				continue
			}

			// Atualizar monitor EM com componentes do LFIR
			if err := orch.updateEMMonitorFromLFIR(lfirGraph); err != nil {
				job.LastError = fmt.Sprintf("EM monitor update failed: %v", err)
				continue
			}

			// Atualizar métricas
			orch.mu.Lock()
			orch.metrics.ParsingJobsCompleted++
			job.LastSuccessfulParse = time.Now()
			job.ParsedNodesCount = len(lfirGraph.Nodes)
			orch.mu.Unlock()

			// Notificar callbacks
			for _, cb := range orch.integrationCallbacks {
				cb(IntegrationEvent{
					EventType: "parsed",
					ClusterID: orch.parser.GetClusterName(),
					Data: map[string]interface{}{
						"job_id":        job.JobID,
						"nodes_parsed":  len(lfirGraph.Nodes),
						"coherence_dc":  orch.emMonitor.GetMonitorMetrics().LastCoherenceValue,
					},
					Timestamp: time.Now(),
				})
			}
		}
	}
}

// updateEMMonitorFromLFIR atualiza monitor EM com componentes extraídos do LFIR
func (orch *DataCenterIntegrationOrchestrator) updateEMMonitorFromLFIR(graph *lfir.LFIRGraph) error {
	for _, node := range graph.Nodes {
		if node.Type == lfir.LFIRType && node.Attributes["type"] == "GPU" {
			// Extrair parâmetros da GPU
			gpuID, _ := node.Attributes["node_id"].(string)
			if gpuID == "" {
				gpuID = fmt.Sprintf("gpu_%s", node.Name)
			}

			//memMB, _ := node.Attributes["memory_mb"].(int)
			powerW, _ := node.Attributes["power_draw_w"].(float64)
			//tempC, _ := node.Attributes["temperature_c"].(float64)

			// Criar GPUComponent para monitor EM
			gpuComponent := &GPUComponent{
				GPUID:          gpuID,
				Position:       [3]float64{float64(len(orch.emMonitor.gpuComponents)) * 0.5, 0, 0},
				ClockFrequency: 1.5e9, // Default, pode ser extraído se disponível
				PowerDrawW:     powerW,
				PhaseOffset:    float64(len(orch.emMonitor.gpuComponents)) * 0.1,
				ActivityLevel:  0.85, // Default, pode ser calculado de métricas
			}

			orch.emMonitor.RegisterGPUComponent(gpuComponent)
		}
	}
	return nil
}

// OnGradientComputed callback para mapear gradientes de treinamento em potenciais
func (orch *DataCenterIntegrationOrchestrator) OnGradientComputed(
	gpuID string,
	gradient []float64,
) {
	if orch.gradientMapper == nil {
		return
	}

	potential := orch.gradientMapper.MapGradientToPotential(
		gpuID,
		gradient,
		time.Now(),
	)

	if potential.Fired {
		orch.metrics.PotentialsFired++

		// Contribuir para canal de coerência se nó promovido
		if orch.promotionProtocol != nil {
			if promotedNode, ok := orch.promotedNodes[orch.parser.GetClusterName()]; ok {
				promotedNode.GradientChannel.SubmitLocalGradient(
					[]float64{potential.AmplitudeV},
					potential.Frequency_Hz/1000.0,
					0.5, // distância conceitual simulada
					1,
					0.0,
					map[string]interface{}{
						"gpu_id":        gpuID,
						"potential_id":  potential.PotentialID,
						"fired":         true,
					},
				)
			}
		}

		// Notificar callbacks
		for _, cb := range orch.integrationCallbacks {
			cb(IntegrationEvent{
				EventType: "potential_fired",
				ClusterID: orch.parser.GetClusterName(),
				Data: map[string]interface{}{
					"gpu_id":        gpuID,
					"potential_id":  potential.PotentialID,
					"amplitude_mv":  potential.AmplitudeV * 1000,
					"firing_rate":   potential.Frequency_Hz,
				},
				Timestamp: time.Now(),
			})
		}
	}

	orch.metrics.GradientsMapped++
}

// GetIntegrationMetrics retorna métricas consolidadas de integração
func (orch *DataCenterIntegrationOrchestrator) GetIntegrationMetrics() IntegrationMetrics {
	orch.mu.RLock()
	defer orch.mu.RUnlock()

	if orch.promotionProtocol != nil {
		promoMetrics := orch.promotionProtocol.GetPromotionMetrics()
		orch.metrics.ActivePromotedNodes = promoMetrics.ActivePromotedNodes
	}

	return orch.metrics
}

// RegisterIntegrationCallback registra callback para eventos de integração
func (orch *DataCenterIntegrationOrchestrator) RegisterIntegrationCallback(
	cb func(IntegrationEvent),
) {
	orch.integrationCallbacks = append(orch.integrationCallbacks, cb)
}

// DataSource interface para coleta de dados de data center
type DataSource interface {
	Collect() ([]byte, error)
}

// ParsingJob representa job de parsing em execução
type ParsingJob struct {
	JobID              string
	DataSource         DataSource
	StartTime          time.Time
	Status             string
	LastSuccessfulParse time.Time
	LastError          string
	ParsedNodesCount   int
}
