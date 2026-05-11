package consciousness

import (
	"testing"
)

func TestMetaConsciousnessArchitect(t *testing.T) {
	config := TranscendenceConfig{
		MaxLayerDepth:      5,
		CoherenceThreshold: 0.90,
	}
	architect, err := NewMetaConsciousnessArchitect("test_architect", 0, config)
	if err != nil {
		t.Fatalf("Failed to create architect: %v", err)
	}
	if architect == nil {
		t.Fatalf("Architect is nil")
	}
}
