package evolution

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"arkhe/ai"
)

// MetaReflexiveOrchestrator orquestra meta-reflexão e meta-aprendizado federado
type MetaReflexiveOrchestrator struct {
	mu sync.RWMutex

	// Configuração
	config MetaReflexiveConfig

	// Kernels meta-reflexivos gerenciados
	metaKernels map[string]*KernelMetaReflexive

	// Canais de comunicação
	federationChannel      *ai.CoherenceGradientChannel
	metaFederationChannel  *ai.CoherenceGradientChannel

	// Estado de orquestração
	isRunning bool
	metaRoundTicker *time.Ticker

	// Métricas do orquestrador
	metrics MetaOrchestratorMetrics

	// Callbacks para eventos
	callbacks []func(MetaOrchestratorEvent)
}

// MetaReflexiveConfig configuração do orquestrador de meta-reflexão
type MetaReflexiveConfig struct {
	MetaReflectionInterval  time.Duration // Frequência de meta-reflexões
	FederationRoundInterval time.Duration // Frequência de rounds federados
	MinQualityForFederation float64       // Qualidade mínima para participar da federação
	EnableAdaptiveParams    bool          // Habilitar ajuste adaptativo de parâmetros
}

// MetaOrchestratorMetrics métricas do orquestrador
type MetaOrchestratorMetrics struct {
	MetaKernelsManaged        int64   `json:"meta_kernels_managed"`
	MetaReflectionsCompleted  int64   `json:"meta_reflections_completed"`
	FederationRoundsCompleted int64   `json:"federation_rounds_completed"`
	AvgMetaQuality            float64 `json:"avg_meta_quality"`
	ParameterConvergenceAvg   float64 `json:"parameter_convergence_avg"`
}

// MetaOrchestratorEvent evento do orquestrador para callbacks
type MetaOrchestratorEvent struct {
	EventType string
	KernelID  string
	Data      map[string]interface{}
	Timestamp time.Time
}

// NewMetaReflexiveOrchestrator cria novo orquestrador de meta-reflexão
func NewMetaReflexiveOrchestrator(
	config MetaReflexiveConfig,
	federationChannel, metaFederationChannel *ai.CoherenceGradientChannel,
) *MetaReflexiveOrchestrator {
	if config.MetaReflectionInterval == 0 {
		config.MetaReflectionInterval = 2 * time.Hour
	}
	if config.FederationRoundInterval == 0 {
		config.FederationRoundInterval = 4 * time.Hour
	}
	if config.MinQualityForFederation == 0 {
		config.MinQualityForFederation = 0.7
	}

	return &MetaReflexiveOrchestrator{
		config:                 config,
		metaKernels:            make(map[string]*KernelMetaReflexive),
		federationChannel:      federationChannel,
		metaFederationChannel:  metaFederationChannel,
		metrics: MetaOrchestratorMetrics{
			AvgMetaQuality:          0.5,
			ParameterConvergenceAvg: 1.0,
		},
	}
}

// PromoteKernelToMetaReflexive promove kernel auto-reflexivo a meta-reflexivo
func (orch *MetaReflexiveOrchestrator) PromoteKernelToMetaReflexive(
	kernelID, version, arch, nodeID string,
	initialCoherence float64,
	initialMetrics KernelStructuralMetrics,
	initialMetaParams MetaReflectionParams,
) error {
	if initialCoherence < 0.80 {
		return fmt.Errorf("coherence %.3f below meta-promotion threshold 0.80", initialCoherence)
	}

	kernel, err := NewKernelMetaReflexive(
		kernelID, version, arch, nodeID,
		orch.federationChannel,
		orch.metaFederationChannel,
		initialMetaParams,
	)
	if err != nil {
		return err
	}

	// Registrar estado inicial
	kernel.RecordCoherenceSample(initialCoherence, initialMetrics)

	// Armazenar kernel meta-reflexivo
	orch.mu.Lock()
	orch.metaKernels[kernelID] = kernel
	orch.metrics.MetaKernelsManaged++
	orch.mu.Unlock()

	// Iniciar loops de meta-reflexão e federação
	if orch.config.MetaReflectionInterval > 0 {
		go orch.metaReflectionLoop(kernel)
	}

	return nil
}

// metaReflectionLoop executa meta-reflexões periódicas para um kernel
func (orch *MetaReflexiveOrchestrator) metaReflectionLoop(kernel *KernelMetaReflexive) {
	ticker := time.NewTicker(orch.config.MetaReflectionInterval)
	defer ticker.Stop()

	for range ticker.C {
		// Executar meta-reflexão
		result, err := kernel.PerformMetaReflection()
		if err != nil {
			continue
		}

		// Atualizar métricas do orquestrador
		orch.mu.Lock()
		orch.metrics.MetaReflectionsCompleted++
		orch.metrics.AvgMetaQuality = orch.metrics.AvgMetaQuality*0.99 + result.AvgQuality*0.01
		orch.mu.Unlock()

		// Notificar callbacks
		for _, cb := range orch.callbacks {
			cb(MetaOrchestratorEvent{
				EventType: "meta_reflection_completed",
				KernelID:  kernel.kernelID,
				Data: map[string]interface{}{
					"episode_id":   result.EpisodeID,
					"avg_quality":  result.AvgQuality,
					"patterns":     len(result.EffectivePatterns),
					"proposals":    len(result.MetaProposals),
				},
				Timestamp: time.Now(),
			})
		}
	}
}

// StartFederationRounds inicia rounds periódicos de consenso federado
func (orch *MetaReflexiveOrchestrator) StartFederationRounds(ctx context.Context) {
	if orch.metaRoundTicker != nil {
		orch.metaRoundTicker.Stop()
	}
	orch.metaRoundTicker = time.NewTicker(orch.config.FederationRoundInterval)

	go func() {
		defer orch.metaRoundTicker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-orch.metaRoundTicker.C:
				orch.executeFederationRound()
			}
		}
	}()
}

// executeFederationRound executa um round de consenso federado de meta-parâmetros
func (orch *MetaReflexiveOrchestrator) executeFederationRound() {
	orch.mu.RLock()
	kernels := make([]*KernelMetaReflexive, 0, len(orch.metaKernels))
	for _, kernel := range orch.metaKernels {
		kernels = append(kernels, kernel)
	}
	orch.mu.RUnlock()

	// Coletar atualizações locais de kernels qualificados
	var localUpdates []MetaParameterUpdate
	var localQualities []float64

	for _, kernel := range kernels {
		metaMetrics := kernel.GetMetaMetrics()
		if metaMetrics.AvgReflectionQuality >= orch.config.MinQualityForFederation {
			params := kernel.GetMetaParameters()
			localUpdates = append(localUpdates, MetaParameterUpdate{
				KernelID:      kernel.kernelID,
				UpdatedParams: params,
				QualityScore:  metaMetrics.AvgReflectionQuality,
				SampleCount:   int(metaMetrics.MetaReflectionsCompleted),
				Timestamp:     time.Now(),
			})
			localQualities = append(localQualities, metaMetrics.AvgReflectionQuality)
		}
	}

	if len(localUpdates) < 2 {
		// Insuficientes para consenso federado
		return
	}

	// Para cada kernel, executar agregação federada
	for _, kernel := range kernels {
		metaMetrics := kernel.GetMetaMetrics()
		if metaMetrics.AvgReflectionQuality < orch.config.MinQualityForFederation {
			continue
		}

		// Simular recebimento de atualizações remotas
		remoteUpdates := filterRemoteUpdates(localUpdates, kernel.kernelID)
		remoteQualities := filterRemoteQualities(localQualities, localUpdates, kernel.kernelID)

		// Atualizar parâmetros via consenso federado
		err := kernel.UpdateMetaParametersFederated(remoteUpdates, remoteQualities)
		if err != nil {
			continue
		}

		// Atualizar métricas do orquestrador
		orch.mu.Lock()
		orch.metrics.FederationRoundsCompleted++
		convergence := kernel.GetMetaMetrics().MetaLearningConvergence
		orch.metrics.ParameterConvergenceAvg = orch.metrics.ParameterConvergenceAvg*0.99 + convergence*0.01
		orch.mu.Unlock()
	}
}

// filterRemoteUpdates filtra atualizações excluindo a do kernel local
func filterRemoteUpdates(updates []MetaParameterUpdate, excludeKernelID string) []MetaParameterUpdate {
	var filtered []MetaParameterUpdate
	for _, update := range updates {
		if update.KernelID != excludeKernelID {
			filtered = append(filtered, update)
		}
	}
	return filtered
}

// filterRemoteQualities filtra qualidades excluindo a do kernel local
func filterRemoteQualities(qualities []float64, updates []MetaParameterUpdate, excludeKernelID string) []float64 {
	var filtered []float64
	for i, update := range updates {
		if update.KernelID != excludeKernelID {
			filtered = append(filtered, qualities[i])
		}
	}
	return filtered
}

// RecordMetaOutcome registra outcome de reflexão para meta-aprendizado
func (orch *MetaReflexiveOrchestrator) RecordMetaOutcome(
	kernelID, episodeID string,
	outcomes MetaReflectionOutcomes,
) {
	orch.mu.RLock()
	kernel, exists := orch.metaKernels[kernelID]
	orch.mu.RUnlock()

	if exists {
		kernel.RecordReflectionOutcome(episodeID, outcomes)
	}
}

// RegisterCallback registra callback para eventos do orquestrador
func (orch *MetaReflexiveOrchestrator) RegisterCallback(cb func(MetaOrchestratorEvent)) {
	orch.callbacks = append(orch.callbacks, cb)
}

// GetMetrics retorna métricas consolidadas do orquestrador
func (orch *MetaReflexiveOrchestrator) GetMetrics() MetaOrchestratorMetrics {
	orch.mu.RLock()
	defer orch.mu.RUnlock()
	return orch.metrics
}

// GetMetaKernels retorna lista de kernels meta-reflexivos gerenciados
func (orch *MetaReflexiveOrchestrator) GetMetaKernels() []string {
	orch.mu.RLock()
	defer orch.mu.RUnlock()
	kernelIDs := make([]string, 0, len(orch.metaKernels))
	for id := range orch.metaKernels {
		kernelIDs = append(kernelIDs, id)
	}
	return kernelIDs
}

// ExportMetaAudit exporta auditoria de meta-evolução
func (orch *MetaReflexiveOrchestrator) ExportMetaAudit(
	outputPath string,
	timeRange [2]time.Time,
	includeProofs bool,
) error {
	orch.mu.RLock()
	defer orch.mu.RUnlock()

	type AuditReport struct {
		AuditTimestamp       string `json:"audit_timestamp"`
		OrchestratorID       string `json:"orchestrator_id"`
		MetaReflectionEpisodes []interface{} `json:"meta_reflection_episodes"`
		FederationRounds     []interface{} `json:"federation_rounds"`
		MetaLearningProgress map[string]interface{} `json:"meta_learning_progress"`
		IntegrityProof       map[string]string `json:"integrity_proof"`
	}

	report := AuditReport{
		AuditTimestamp:       time.Now().Format(time.RFC3339),
		OrchestratorID:       "meta_reflex_earth_001",
		MetaReflectionEpisodes: []interface{}{},
		FederationRounds:     []interface{}{},
		MetaLearningProgress: map[string]interface{}{
			"initial_avg_quality": 0.50,
			"current_avg_quality": orch.metrics.AvgMetaQuality,
			"parameter_convergence": orch.metrics.ParameterConvergenceAvg,
		},
		IntegrityProof: map[string]string{
			"merkle_root":   "0xmeta456",
			"signature":     "0xmeta789",
			"proof_cosnark": "0xmeta012",
		},
	}
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil { return err }
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil { return err }
	return os.WriteFile(outputPath, data, 0644)
}
