package consistency

import (
	"errors"
	"fmt"
	"sync"
	"time"

	arkhecore "github.com/arkhe-os/arkhe-go/pkg/core"
	"github.com/arkhe-os/arkhe-go/pkg/consensus"
)

// ============================================================================
// Backward Consistency Checker
// ============================================================================

var (
	ErrBackwardViolation = errors.New("violação de causalidade backward")
)

// BackwardChecker verifica consistência backward (compatibilidade entre branches).
type BackwardChecker struct {
	threshold  consensus.Score
	history    []BackwardRecord
	mu         sync.RWMutex
}

// BackwardRecord registra uma verificação backward.
type BackwardRecord struct {
	Message        *arkhecore.TemporalMessage
	PrevStateHash  arkhecore.Address
	Score          consensus.Score
	Compatible     bool
	Reason         string
	Timestamp      int64
}

// NewBackwardChecker cria um novo backward checker.
func NewBackwardChecker(threshold consensus.Score) *BackwardChecker {
	if threshold == 0 {
		threshold = consensus.DefaultThresholds().ParadoxFree
	}
	return &BackwardChecker{
		threshold: threshold,
		history:   make([]BackwardRecord, 0),
	}
}

// CheckCompatibility verifica se uma nova mensagem é compatível
// (não contradiz) mensagens em branches existentes.
func (bc *BackwardChecker) CheckCompatibility(
	newMsg *arkhecore.TemporalMessage,
	existingState []arkhecore.Address,
) (*BackwardRecord, error) {
	bc.mu.Lock()
	defer bc.mu.Unlock()

	record := &BackwardRecord{
		Message:   newMsg,
		Timestamp: time.Now().UnixNano(),
	}

	msgHash := newMsg.Hash()

	// Verificar se a mensagem é compatível com estados existentes
	for _, stateHash := range existingState {
		if stateHash == msgHash {
			record.Compatible = true
			record.Reason = "estado já existe"
			bc.history = append(bc.history, *record)
			return record, nil
		}
	}

	// Simulação: verificar score de compatibilidade temporal
	// Em produção: verificar causalidade real
	score := bc.computeBackwardScore(newMsg, existingState)
	record.Score = score

	if score < bc.threshold {
		record.Compatible = false
		record.Reason = fmt.Sprintf(
			"incompatibilidade backward: score %.4f < threshold %.4f",
			score, bc.threshold)
		bc.history = append(bc.history, *record)
		return record, ErrBackwardViolation
	}

	record.Compatible = true
	record.Reason = "compatível"
	bc.history = append(bc.history, *record)

	return record, nil
}

func (bc *BackwardChecker) computeBackwardScore(
	msg *arkhecore.TemporalMessage,
	state []arkhecore.Address,
) consensus.Score {
	// Simplificado: usar heurística baseada em timestamps
	// Produção: deveria verificar Merkle proofs contra o ledger

	if len(state) == 0 {
		return consensus.ScoreTop
	}

	// Verificar temporal ordering
	for _, addr := range state {
		_ = addr // Placeholder: verificar causalidade real
	}

	// Baseado apenas no temporal ordering
	if msg.SourceTimestamp >= 0 && msg.TargetTimestamp >= msg.SourceTimestamp {
		return consensus.ScoreTop
	}

	return consensus.Score(0.5)
}

// MergeStates mescla estados de dois branches compatíveis.
func (bc *BackwardChecker) MergeStates(
	state1, state2 []arkhecore.Address,
) ([]arkhecore.Address, error) {
	bc.mu.Lock()
	defer bc.mu.Unlock()

	merged := make(map[arkhecore.Address]bool)
	for _, addr := range state1 {
		merged[addr] = true
	}
	for _, addr := range state2 {
		merged[addr] = true
	}

	result := make([]arkhecore.Address, 0, len(merged))
	for addr := range merged {
		result = append(result, addr)
	}

	return result, nil
}
