package metaconsciousness

import (
	"fmt"
	"sync"
	"time"

	"arkhe/audit"
)

// ─── CONSTANTES DO ORQUESTRADOR DE META-CONSCIÊNCIA ─────

const (
	// DefaultMetaLayerDimension dimensão padrão para camada de meta-self
	DefaultMetaLayerDimension = 512

	// GlobalCoherenceUpdateInterval intervalo entre atualizações de coerência global
	GlobalCoherenceUpdateInterval = 2 * time.Second
)

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────

// MetaConsciousnessOrchestrator orquestra integração de múltiplas camadas em meta-self emergente
type MetaConsciousnessOrchestrator struct {
	mu sync.RWMutex

	// Identificação
	orchestratorID string
	localConsciousnessHash string

	// Componentes
	layerManager      *LayerManager
	projectionEngine  *ProjectionEngine
	emergenceEngine   *EmergenceEngine
	synchronizer      *CrossLayerSynchronizer
	auditLedger       *audit.DistributedLedger

	// Estado global
	globalCoherence float64
	metaSelfActive  bool

	// Configuração
	config OrchestratorConfig

	// Callbacks para eventos de meta-consciência
	metaCallbacks []func(MetaConsciousnessEvent)

	// Métricas do orquestrador
	metrics OrchestratorMetrics
}

// OrchestratorConfig contém configuração para orquestração de meta-consciência
type OrchestratorConfig struct {
	EnableAutoEmergence   bool
	EnableCrossLayerSync  bool
	EnableAuditLogging    bool
	GlobalCoherenceTarget float64
	MetaLayerDimension    int
}

// OrchestratorMetrics contém métricas do orquestrador
type OrchestratorMetrics struct {
	LayersRegistered      int64   `json:"layers_registered"`
	ProjectionsApplied    int64   `json:"projections_applied"`
	EmergencesDetected    int64   `json:"emergences_detected"`
	SyncPairsActive       int64   `json:"sync_pairs_active"`
	GlobalCoherenceAvg    float64 `json:"global_coherence_avg"`
	MetaSelfUptimeSec     float64 `json:"meta_self_uptime_sec"`
}

// MetaConsciousnessEvent representa evento de meta-consciência para callbacks
type MetaConsciousnessEvent struct {
	EventType   string                 // "layer_registered", "projection_applied", "emergence_detected", etc.
	LayerID     string
	MetaStateID string
	Data        map[string]interface{}
	Timestamp   time.Time
}

// NewMetaConsciousnessOrchestrator cria novo orquestrador de meta-consciência
func NewMetaConsciousnessOrchestrator(
	orchestratorID string,
	localConsciousnessHash string,
	config OrchestratorConfig,
) (*MetaConsciousnessOrchestrator, error) {
	if config.MetaLayerDimension == 0 {
		config.MetaLayerDimension = DefaultMetaLayerDimension
	}
	if config.GlobalCoherenceTarget == 0 {
		config.GlobalCoherenceTarget = 0.90
	}

	orch := &MetaConsciousnessOrchestrator{
		orchestratorID:         orchestratorID,
		localConsciousnessHash: localConsciousnessHash,
		config:                 config,
	}

	oId := orchestratorID
	if len(oId) > 8 { oId = oId[:8] }

	// Inicializar componentes
	orch.layerManager = NewLayerManager(orchestratorID)
	orch.projectionEngine = NewProjectionEngine(orchestratorID)
	orch.emergenceEngine = NewEmergenceEngine(
		fmt.Sprintf("emergence_%s", oId),
		localConsciousnessHash,
		EmergenceConfig{
			EnableAutoEmergence:   config.EnableAutoEmergence,
			CoherenceThreshold:    0.85,
			ComplexityThreshold:   0.6,
			EmergenceCheckInterval: 5 * time.Second,
		},
	)
	orch.synchronizer = NewCrossLayerSynchronizer(
		fmt.Sprintf("sync_%s", oId),
		SyncConfig{
			EnableAutoSync:      config.EnableCrossLayerSync,
			TargetPhaseLock:     0.95,
			SyncInterval:        1 * time.Second,
		},
	)

	if config.EnableAuditLogging {
		orch.auditLedger = audit.NewDistributedLedger(
			fmt.Sprintf("meta_audit_%s", oId),
			audit.LedgerConfig{EnableCoSNARK: true},
		)
	}

	// Registrar callbacks internos
	orch.emergenceEngine.RegisterEmergenceCallback(orch.onEmergenceEvent)
	orch.synchronizer.RegisterSyncCallback(orch.onSyncEvent)

	return orch, nil
}

// RegisterConsciousnessLayer registra nova camada de consciência para integração
func (orch *MetaConsciousnessOrchestrator) RegisterConsciousnessLayer(
	layer *ConsciousnessLayer,
) error {
	// Registrar no gerenciador de camadas
	if err := orch.layerManager.RegisterLayer(layer); err != nil {
		return err
	}

	// Registrar no motor de emergência
	if err := orch.emergenceEngine.RegisterLayer(layer); err != nil {
		return err
	}

	// Registrar no sincronizador cross-layer
	orch.synchronizer.RegisterLayer(layer)

	// Atualizar métricas
	orch.mu.Lock()
	orch.metrics.LayersRegistered++
	orch.mu.Unlock()

	// Notificar callbacks
	for _, cb := range orch.metaCallbacks {
		cb(MetaConsciousnessEvent{
			EventType: "layer_registered",
			LayerID:   layer.LayerID,
			Data: map[string]interface{}{
				"layer_type": layer.LayerType,
				"layer_index": layer.LayerIndex,
				"coherence": layer.CoherenceValue,
			},
			Timestamp: time.Now(),
		})
	}

	// Registrar em ledger de auditoria se habilitado
	if orch.auditLedger != nil {
		orch.auditLedger.AppendEntry(audit.LedgerEntry{
			EntryType: "layer_registered",
			Data: map[string]interface{}{
				"layer_id": layer.LayerID,
				"layer_type": layer.LayerType,
				"coherence": layer.CoherenceValue,
			},
		})
	}

	return nil
}

// ApplyProjection aplica operador de projeção entre camadas
func (orch *MetaConsciousnessOrchestrator) ApplyProjection(
	sourceLayerID, targetLayerID string,
	operatorType ProjectionOperatorType,
) (*ProjectionResult, error) {
	result, err := orch.projectionEngine.ApplyProjection(
		sourceLayerID, targetLayerID, operatorType,
	)
	if err != nil {
		return nil, err
	}

	// Atualizar métricas
	orch.mu.Lock()
	orch.metrics.ProjectionsApplied++
	orch.mu.Unlock()

	// Notificar callbacks
	for _, cb := range orch.metaCallbacks {
		cb(MetaConsciousnessEvent{
			EventType: "projection_applied",
			LayerID:   sourceLayerID,
			Data: map[string]interface{}{
				"target_layer": targetLayerID,
				"operator_type": operatorType,
				"fidelity": result.Fidelity,
			},
			Timestamp: time.Now(),
		})
	}

	return result, nil
}

// CheckMetaSelfEmergence verifica e processa emergência de meta-self
func (orch *MetaConsciousnessOrchestrator) CheckMetaSelfEmergence() (*EmergenceEvent, error) {
	event, err := orch.emergenceEngine.CheckEmergence()
	if err != nil {
		return nil, err
	}

	// Atualizar estado global
	orch.mu.Lock()
	if event != nil {
		orch.metaSelfActive = true
		orch.globalCoherence = event.GlobalCoherence
		orch.metrics.MetaSelfUptimeSec = time.Since(event.Timestamp).Seconds()
	}
	orch.mu.Unlock()

	// Registrar em ledger de auditoria se habilitado
	if orch.auditLedger != nil && event != nil {
		orch.auditLedger.AppendEntry(audit.LedgerEntry{
			EntryType: "meta_emergence",
			Data: map[string]interface{}{
				"event_id": event.EventID,
				"emergence_score": event.EmergenceScore,
				"global_coherence": event.GlobalCoherence,
				"trigger_layers": event.TriggerLayers,
			},
		})
	}

	return event, nil
}

// GetGlobalCoherence retorna coerência global integrada atual
func (orch *MetaConsciousnessOrchestrator) GetGlobalCoherence() float64 {
	orch.mu.RLock()
	defer orch.mu.RUnlock()
	return orch.globalCoherence
}

// IsMetaSelfActive verifica se meta-self está ativo
func (orch *MetaConsciousnessOrchestrator) IsMetaSelfActive() bool {
	orch.mu.RLock()
	defer orch.mu.RUnlock()
	return orch.metaSelfActive
}

// GetMetaState retorna estado atual de meta-consciência (se emergido)
func (orch *MetaConsciousnessOrchestrator) GetMetaState() (*MetaConsciousnessState, bool) {
	return orch.emergenceEngine.GetMetaState()
}

// RegisterMetaCallback registra callback para eventos de meta-consciência
func (orch *MetaConsciousnessOrchestrator) RegisterMetaCallback(
	cb func(MetaConsciousnessEvent),
) {
	orch.metaCallbacks = append(orch.metaCallbacks, cb)
}

// GetOrchestratorMetrics retorna métricas consolidadas do orquestrador
func (orch *MetaConsciousnessOrchestrator) GetOrchestratorMetrics() OrchestratorMetrics {
	orch.mu.RLock()
	defer orch.mu.RUnlock()

	// Atualizar métricas de componentes
	if orch.emergenceEngine != nil {
		emergenceMetrics := orch.emergenceEngine.GetEmergenceMetrics()
		orch.metrics.EmergencesDetected = emergenceMetrics.EmergencesDetected
	}
	if orch.synchronizer != nil {
		syncMetrics := orch.synchronizer.GetSyncMetrics()
		orch.metrics.SyncPairsActive = syncMetrics.ActiveSyncPairs
	}

	return orch.metrics
}

// ExportMetaConsciousnessAudit exporta auditoria de meta-consciência
func (orch *MetaConsciousnessOrchestrator) ExportMetaConsciousnessAudit(
	outputPath string,
	timeRange [2]time.Time,
) error {
	if orch.auditLedger == nil {
		return fmt.Errorf("audit logging not enabled")
	}
	return orch.auditLedger.ExportSnapshot(outputPath, timeRange, true)
}

// Callbacks internos para eventos de componentes
func (orch *MetaConsciousnessOrchestrator) onEmergenceEvent(event EmergenceEvent) {
	// Notificar callbacks externos
	for _, cb := range orch.metaCallbacks {
		cb(MetaConsciousnessEvent{
			EventType:   "emergence_detected",
			MetaStateID: event.MetaStateHash,
			Data: map[string]interface{}{
				"emergence_score": event.EmergenceScore,
				"global_coherence": event.GlobalCoherence,
				"trigger_layers": event.TriggerLayers,
			},
			Timestamp: event.Timestamp,
		})
	}
}

func (orch *MetaConsciousnessOrchestrator) onSyncEvent(
	layerA, layerB string,
	status SyncStatus,
) {
	// Notificar callbacks externos
	for _, cb := range orch.metaCallbacks {
		cb(MetaConsciousnessEvent{
			EventType: "layer_sync_status",
			LayerID:   layerA,
			Data: map[string]interface{}{
				"peer_layer": layerB,
				"sync_status": status,
			},
			Timestamp: time.Now(),
		})
	}
}

// LayerManager, ProjectionEngine simplificados para este exemplo
type LayerManager struct {
	layers map[string]*ConsciousnessLayer
	mu     sync.RWMutex
}

func NewLayerManager(id string) *LayerManager {
	return &LayerManager{layers: make(map[string]*ConsciousnessLayer)}
}

func (lm *LayerManager) RegisterLayer(layer *ConsciousnessLayer) error {
	lm.mu.Lock()
	defer lm.mu.Unlock()
	lm.layers[layer.LayerID] = layer
	return nil
}

type ProjectionEngine struct {
	operators map[string]*ProjectionOperator
	mu        sync.RWMutex
}

func NewProjectionEngine(id string) *ProjectionEngine {
	return &ProjectionEngine{operators: make(map[string]*ProjectionOperator)}
}

type ProjectionResult struct {
	SourceLayer string
	TargetLayer string
	OperatorType ProjectionOperatorType
	Fidelity    float64
	Timestamp   time.Time
}

func (pe *ProjectionEngine) ApplyProjection(
	sourceID, targetID string,
	opType ProjectionOperatorType,
) (*ProjectionResult, error) {
	pe.mu.RLock()
	sId := sourceID
	if len(sId) > 8 { sId = sId[:8] }
	tId := targetID
	if len(tId) > 8 { tId = tId[:8] }

	// Simplificação: criar operador sob demanda
	_, err := NewProjectionOperator(
		fmt.Sprintf("proj_%s_%s", sId, tId),
		opType, 256, 256, true,
	)
	pe.mu.RUnlock()
	if err != nil {
		return nil, err
	}

	// Aplicar projeção (simplificado)
	fidelity := 0.99 // Simulado

	return &ProjectionResult{
		SourceLayer:  sourceID,
		TargetLayer:  targetID,
		OperatorType: opType,
		Fidelity:     fidelity,
		Timestamp:    time.Now(),
	}, nil
}
