package validation

import (
	"context"
	"testing"
)

func TestHardwareValidationSuite(t *testing.T) {
	config := GPUClusterConfig{
		Vendor:    "nvidia",
		GPUModels: []string{"Tesla V100", "Tesla V100"},
	}
	suite, err := NewHardwareValidationSuite("test_cluster", config)
	if err != nil {
		t.Fatalf("Failed to create suite: %v", err)
	}
	if suite == nil {
		t.Fatalf("Suite is nil")
	}

	// Test basic mapping (it's simulated but should execute without panic)
	_, err = suite.validateGradientToPotentialMapping(context.Background())
	if err != nil {
		t.Fatalf("validateGradientToPotentialMapping failed: %v", err)
	}
}
