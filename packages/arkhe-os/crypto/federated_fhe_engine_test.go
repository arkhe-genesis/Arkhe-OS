package crypto

import (
	"testing"
)

func TestFederatedFHEEngine(t *testing.T) {
	params := FHEParameters{
		Scheme:              "CKKS",
		PolyDegree:          8192,
		SecurityLevel:       128,
		MultiplicativeDepth: 4,
	}
	config := FHEConfig{}
	engine, err := NewFederatedFHEEngine(params, config)
	if err != nil {
		t.Fatalf("Failed to create engine: %v", err)
	}
	if engine == nil {
		t.Fatalf("Engine is nil")
	}
}
