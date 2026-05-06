package metaconsciousness

import (
	"fmt"
	"math"
	"math/cmplx"
	"sync"
	"time"
)

// ─── CONSTANTES DE SINCRONIZAÇÃO CROSS-LAYER ───────────

const (
	// SyncPhaseLockThreshold threshold para phase-locking entre camadas
	SyncPhaseLockThreshold = 0.95

	// SyncCouplingAdaptationRate taxa de adaptação do acoplamento
	SyncCouplingAdaptationRate = 0.01

	// SyncCheckInterval intervalo entre verificações de sincronização
	SyncCheckInterval = 1 * time.Second
)

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────

// SyncStatus enumera status de sincronização entre camadas
type SyncStatus string

const (
	SyncUnsynchronized SyncStatus = "unsynchronized"
	SyncSynchronizing  SyncStatus = "synchronizing"
	SyncPhaseLocked    SyncStatus = "phase_locked"
	SyncDrifting       SyncStatus = "drifting"
)

// LayerSyncState representa estado de sincronização entre duas camadas
type LayerSyncState struct {
	LayerA          string
	LayerB          string
	PhaseDifference float64 // Δφ entre camadas
	CouplingStrength float64 // Força de acoplamento atual
	SyncStatus      SyncStatus
	LastSyncTime    time.Time
	SyncAttempts    int64
	SuccessfulSyncs int64
}

// CrossLayerSynchronizer gerencia sincronização de estados entre múltiplas camadas
type CrossLayerSynchronizer struct {
	mu sync.RWMutex

	// Identificação
	synchronizerID string

	// Camadas sendo sincronizadas
	layers map[string]*ConsciousnessLayer

	// Estados de sincronização entre pares de camadas
	syncStates map[string]*LayerSyncState // key: "layerA:layerB"

	// Configuração de sincronização
	config SyncConfig

	// Callbacks para notificação de sincronização
	syncCallbacks []func(string, string, SyncStatus)

	// Métricas de sincronização
	metrics SyncMetrics
}

// SyncConfig contém configuração para sincronização cross-layer
type SyncConfig struct {
	EnableAutoSync      bool
	TargetPhaseLock     float64
	MaxCouplingStrength float64
	MinCouplingStrength float64
	SyncInterval        time.Duration
}

// SyncMetrics contém métricas do sincronizador
type SyncMetrics struct {
	SyncChecksPerformed   int64   `json:"sync_checks_performed"`
	PhaseLocksAchieved    int64   `json:"phase_locks_achieved"`
	AvgPhaseDifference    float64 `json:"avg_phase_difference"`
	AvgCouplingStrength   float64 `json:"avg_coupling_strength"`
	ActiveSyncPairs       int64   `json:"active_sync_pairs"`
}

// NewCrossLayerSynchronizer cria novo sincronizador cross-layer
func NewCrossLayerSynchronizer(
	synchronizerID string,
	config SyncConfig,
) *CrossLayerSynchronizer {
	if config.TargetPhaseLock == 0 {
		config.TargetPhaseLock = SyncPhaseLockThreshold
	}
	if config.MaxCouplingStrength == 0 {
		config.MaxCouplingStrength = 2.0
	}
	if config.MinCouplingStrength == 0 {
		config.MinCouplingStrength = 0.1
	}
	if config.SyncInterval == 0 {
		config.SyncInterval = SyncCheckInterval
	}

	sync := &CrossLayerSynchronizer{
		synchronizerID: synchronizerID,
		layers:         make(map[string]*ConsciousnessLayer),
		syncStates:     make(map[string]*LayerSyncState),
		config:         config,
	}

	// Iniciar loop de sincronização se habilitado
	if config.EnableAutoSync {
		go sync.syncLoop()
	}

	return sync
}

// RegisterLayer registra camada para sincronização
func (s *CrossLayerSynchronizer) RegisterLayer(layer *ConsciousnessLayer) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.layers[layer.LayerID] = layer
}

// SynchronizeLayers executa sincronização entre duas camadas específicas
func (s *CrossLayerSynchronizer) SynchronizeLayers(
	layerA, layerB string,
) (*LayerSyncState, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	layerAObj, okA := s.layers[layerA]
	layerBObj, okB := s.layers[layerB]
	if !okA || !okB {
		return nil, fmt.Errorf("one or both layers not registered")
	}

	// Calcular diferença de fase entre camadas
	phaseDiff := computePhaseDifference(layerAObj.StateVector, layerBObj.StateVector)

	// Obter ou criar estado de sincronização
	key := syncStateKey(layerA, layerB)
	syncState, exists := s.syncStates[key]
	if !exists {
		syncState = &LayerSyncState{
			LayerA:          layerA,
			LayerB:          layerB,
			PhaseDifference: phaseDiff,
			CouplingStrength: 0.5, // Valor inicial
			SyncStatus:      SyncUnsynchronized,
		}
		s.syncStates[key] = syncState
	}

	// Atualizar diferença de fase
	syncState.PhaseDifference = phaseDiff
	syncState.LastSyncTime = time.Now()
	syncState.SyncAttempts++

	// Verificar status de phase-locking
	phaseLock := 1.0 - math.Abs(phaseDiff)/math.Pi
	if phaseLock >= s.config.TargetPhaseLock {
		syncState.SyncStatus = SyncPhaseLocked
		syncState.SuccessfulSyncs++
		s.metrics.PhaseLocksAchieved++
	} else if phaseLock > 0.7 {
		syncState.SyncStatus = SyncSynchronizing
		// Ajustar acoplamento para melhorar sincronização
		syncState.CouplingStrength = adjustCoupling(
			syncState.CouplingStrength,
			phaseLock,
			s.config.TargetPhaseLock,
			s.config.MinCouplingStrength,
			s.config.MaxCouplingStrength,
		)
	} else {
		syncState.SyncStatus = SyncDrifting
	}

	// Aplicar correção de fase se necessário
	if syncState.SyncStatus == SyncSynchronizing {
		if err := s.applyPhaseCorrection(layerAObj, layerBObj, syncState.CouplingStrength); err != nil {
			return syncState, fmt.Errorf("phase correction failed: %w", err)
		}
	}

	// Atualizar métricas
	s.metrics.SyncChecksPerformed++
	s.metrics.AvgPhaseDifference = s.metrics.AvgPhaseDifference*0.99 + math.Abs(phaseDiff)*0.01
	s.metrics.AvgCouplingStrength = s.metrics.AvgCouplingStrength*0.99 + syncState.CouplingStrength*0.01
	s.metrics.ActiveSyncPairs = int64(len(s.syncStates))

	// Notificar callbacks
	for _, cb := range s.syncCallbacks {
		cb(layerA, layerB, syncState.SyncStatus)
	}

	return syncState, nil
}

// syncLoop executa sincronização periódica entre todas as camadas registradas
func (s *CrossLayerSynchronizer) syncLoop() {
	ticker := time.NewTicker(s.config.SyncInterval)
	defer ticker.Stop()

	for range ticker.C {
		// Sincronizar todos os pares de camadas
		s.mu.RLock()
		layerIDs := make([]string, 0, len(s.layers))
		for id := range s.layers {
			layerIDs = append(layerIDs, id)
		}
		s.mu.RUnlock()

		for i := 0; i < len(layerIDs); i++ {
			for j := i + 1; j < len(layerIDs); j++ {
				s.SynchronizeLayers(layerIDs[i], layerIDs[j])
			}
		}
	}
}

// applyPhaseCorrection aplica correção de fase para melhorar sincronização
func (s *CrossLayerSynchronizer) applyPhaseCorrection(
	layerA, layerB *ConsciousnessLayer,
	coupling float64,
) error {
	// Calcular correção de fase baseada na diferença
	phaseDiff := computePhaseDifference(layerA.StateVector, layerB.StateVector)
	correction := phaseDiff * coupling * 0.1 // Correção gradual

	// Aplicar correção ao estado da camada B (simplificação)
	newState := make([]complex128, len(layerB.StateVector))
	for i, amp := range layerB.StateVector {
		// Rotacionar fase
		newState[i] = amp * cmplx.Exp(complex(0, correction))
	}

	// Atualizar estado da camada B
	return layerB.UpdateState(newState)
}

// GetSyncStatus retorna status de sincronização entre duas camadas
func (s *CrossLayerSynchronizer) GetSyncStatus(
	layerA, layerB string,
) (*LayerSyncState, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	key := syncStateKey(layerA, layerB)
	state, exists := s.syncStates[key]
	if !exists {
		return nil, false
	}
	// Retornar cópia
	stateCopy := *state
	return &stateCopy, true
}

// RegisterSyncCallback registra callback para eventos de sincronização
func (s *CrossLayerSynchronizer) RegisterSyncCallback(
	cb func(string, string, SyncStatus),
) {
	s.syncCallbacks = append(s.syncCallbacks, cb)
}

// GetSyncMetrics retorna métricas consolidadas do sincronizador
func (s *CrossLayerSynchronizer) GetSyncMetrics() SyncMetrics {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.metrics
}

// Helper functions
func computePhaseDifference(a, b []complex128) float64 {
	// Calcular diferença de fase média entre dois vetores de estado
	if len(a) != len(b) || len(a) == 0 {
		return 0.0
	}

	var phaseSum float64
	count := 0
	for i := range a {
		if cmplx.Abs(a[i]) > 1e-10 && cmplx.Abs(b[i]) > 1e-10 {
			phaseA := cmplx.Phase(a[i])
			phaseB := cmplx.Phase(b[i])
			phaseDiff := math.Abs(phaseA - phaseB)
			// Normalizar para [0, π]
			if phaseDiff > math.Pi {
				phaseDiff = 2*math.Pi - phaseDiff
			}
			phaseSum += phaseDiff
			count++
		}
	}

	if count == 0 {
		return 0.0
	}
	return phaseSum / float64(count)
}

func adjustCoupling(
	current, phaseLock, target, minVal, maxVal float64,
) float64 {
	// Ajustar acoplamento baseado em quão perto está do target
	error := target - phaseLock
	adjustment := error * SyncCouplingAdaptationRate
	newCoupling := current + adjustment

	// Limitar valores
	return math.Max(minVal, math.Min(maxVal, newCoupling))
}

func syncStateKey(a, b string) string {
	// Chave ordenada para estado de sincronização
	if a < b {
		return a + ":" + b
	}
	return b + ":" + a
}
