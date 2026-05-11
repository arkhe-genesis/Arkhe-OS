package evolution

import (
	"testing"
	"time"
)

func TestEvolutionOrchestratorInitialization(t *testing.T) {
	config := EvolutionConfig{
		PhiOptimizationConfig: OptimizationConfig{
			MaxIterations:         10,
			MinFitnessImprovement: 0.01,
			EnablePhiRebalance:    true,
			EnableMemoization:     true,
			EnableInlining:        true,
			Seed:                  42,
		},
		SelectionConfig:            map[string]interface{}{"strategy": StrategyTournament},
		FitnessWeights:             map[string]float64{"time": 0.4, "memory": 0.3, "energy": 0.15, "phi": 0.15},
		EnableSemanticVerification: true,
		ProofValidityWindowSec:     3600,
		MetricsCollectionInterval:  1 * time.Second,
		MinSamplesForEvaluation:    10,
		MaxConcurrentEvolutions:    5,
		EvolutionTimeoutSec:        600,
		EnableLogging:              true,
	}

	store := &FunctionSignatureStore{}
	orch, err := NewAutoEvolutionOrchestrator(config, store)
	if err != nil {
		t.Fatalf("Failed to initialize orchestrator: %v", err)
	}
	if orch == nil {
		t.Fatalf("Orchestrator is nil")
	}

	metrics := orch.GetOrchestratorMetrics()
	if metrics.EvolutionsStarted != 0 {
		t.Errorf("Expected 0 evolutions started initially, got %d", metrics.EvolutionsStarted)
	}
}
