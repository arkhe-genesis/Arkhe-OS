package consistency

import (
	"errors"
	"sync"
	"time"

	arkhecore "github.com/arkhe-os/arkhe-go/pkg/core"
	"github.com/arkhe-os/arkhe-go/pkg/consensus"
)

// ============================================================================
// Forward Consistency Checker
// ============================================================================

var (
	ErrCausalViolation   = errors.New("violação de causalidade forward")
	ErrTemporalViolation = errors.New("violação temporal forward")
)

// ForwardCheckConfig configura o forward checker.
type ForwardCheckConfig struct {
	ConsistencyThreshold consensus.Score
	StrictMode          bool
	EnableOracle        bool
}

// ForwardChecker verifica consistência forward (causalidade direta).
type ForwardChecker struct {
	cfg     *ForwardCheckConfig
	oracle  *consensus.ConsistencyOracle
	mu      sync.RWMutex
	history []ForwardRecord
}

// ForwardRecord registra um passo de consistência forward.
type ForwardRecord struct {
	Message     *arkhecore.TemporalMessage
	Score       consensus.Score
	AdjustedW   float64
	Pruned      bool
	PruneReason string
	Timestamp   int64
}

// NewForwardChecker cria um novo forward checker.
func NewForwardChecker(cfg *ForwardCheckConfig) *ForwardChecker {
	if cfg == nil {
		cfg = &ForwardCheckConfig{
			ConsistencyThreshold: consensus.DefaultThresholds().ParadoxFree,
			StrictMode:           false,
			EnableOracle:         true,
		}
	}
	return &ForwardChecker{
		cfg:    cfg,
		oracle: consensus.NewConsistencyOracle(nil),
		history: make([]ForwardRecord, 0),
	}
}

// SetOracleConfigura o oracle no forward checker.
func (fc *ForwardChecker) SetOracle(thresholds *consensus.Thresholds, weights *consensus.CheckWeights) {
	fc.oracle = consensus.NewConsistencyOracle(&consensus.ConsistencyOracleConfig{
		Thresholds: thresholds,
		Weights:    weights,
		StrictMode: fc.cfg.StrictMode,
	})
}

// Check verifica consistência forward de uma mensagem.
func (fc *ForwardChecker) Check(
	msg *arkhecore.TemporalMessage,
	edgeWeight float64,
) (*ForwardRecord, error) {
	fc.mu.Lock()
	defer fc.mu.Unlock()

	record := &ForwardRecord{
		Message:   msg,
		Timestamp: time.Now().UnixNano(),
	}

	if !fc.cfg.EnableOracle {
		// Sem oracle: verificação simples
		record.Score = consensus.ScoreTop
		record.AdjustedW = edgeWeight
		fc.history = append(fc.history, *record)
		return record, nil
	}

	// Avaliar via Oracle
	report := fc.oracle.Evaluate(msg, edgeWeight, nil)

	record.Score = report.Score
	record.AdjustedW = report.AdjustedWeight
	record.Pruned = report.Pruned
	record.PruneReason = report.PruneReason

	// Verificar violação
	if report.Pruned {
		return record, ErrCausalViolation
	}

	// Verificar threshold
	if report.Score < fc.cfg.ConsistencyThreshold {
		return record, ErrTemporalViolation
	}

	fc.history = append(fc.history, *record)

	return record, nil
}

// History retorna o histórico de verificações.
func (fc *ForwardChecker) History() []ForwardRecord {
	fc.mu.RLock()
	defer fc.mu.RUnlock()

	cpy := make([]ForwardRecord, len(fc.history))
	copy(cpy, fc.history)
	return cpy
}

// Reset limpa o histórico.
func (fc *ForwardChecker) Reset() {
	fc.mu.Lock()
	fc.history = fc.history[:0]
	fc.mu.Unlock()
}
