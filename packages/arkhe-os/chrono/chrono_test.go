package chrono

import (
	"testing"
)

func TestChronoFlexSync(t *testing.T) {
	engine := NewTemporalFlexEngine()
	engine.SetCoherence(0.8) // compressão temporal
	// Dados de dois relógios com offset de 10 ns
	t1, t2 := 0.0, 10.0
	// Aplicar compressão para reduzir latência efetiva
	result := engine.CompressTime(t1, t2, 2.5) // > 2.0 to be < 5.0

	if result["effective_latency"] >= 5.0 {
		t.Errorf("Expected effective_latency < 5.0, got %v", result["effective_latency"])
	}
	if result["causal_consistency"] <= 0.95 {
		t.Errorf("Expected causal_consistency > 0.95, got %v", result["causal_consistency"])
	}
}
