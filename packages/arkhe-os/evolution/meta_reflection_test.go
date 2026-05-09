package evolution

import (
	"context"
	"testing"
	"time"

	"arkhe/ai"
)

func TestMetaReflexiveOrchestrator(t *testing.T) {
	federationChannel := ai.NewCoherenceGradientChannel(
		"kernel_federation",
		"arkhe_node_earth_001",
		"kernel_layer",
		nil,
		ai.ChannelConfig{AggregationStrategy: "weighted_average"},
	)
	metaFederationChannel := ai.NewCoherenceGradientChannel(
		"kernel_meta_federation",
		"arkhe_node_earth_001",
		"kernel_meta_reflection",
		nil,
		ai.ChannelConfig{AggregationStrategy: "weighted_average"},
	)

	metaConfig := MetaReflexiveConfig{
		MetaReflectionInterval:  1 * time.Second,
		FederationRoundInterval: 2 * time.Second,
		MinQualityForFederation: 0.1,
		EnableAdaptiveParams:    true,
	}

	orchestrator := NewMetaReflexiveOrchestrator(
		metaConfig,
		federationChannel,
		metaFederationChannel,
	)

	initialMetaParams := MetaReflectionParams{
		ReflectionWindow:         60 * time.Minute,
		InsightValueThreshold:    0.15,
		ConfidenceThreshold:      0.7,
		UtilityWeight:            0.4,
		NoveltyWeight:            0.3,
		ActionableWeight:         0.3,
		FederationLearningRate:   0.01,
		FederationTemperature:    0.5,
		LocalUpdateFrequency:     3,
	}

	err := orchestrator.PromoteKernelToMetaReflexive(
		"test_kernel",
		"6.6.0", "x86_64", "node_1",
		0.85,
		KernelStructuralMetrics{
			Version: "6.6.0", Architecture: "x86_64",
			LoadedModules: 89, CriticalModules: 12,
			SecurityEnabled: 8, SecurityTotal: 8,
		},
		initialMetaParams,
	)
	if err != nil {
		t.Fatalf("Failed to promote kernel: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	orchestrator.StartFederationRounds(ctx)

	time.Sleep(3 * time.Second)

	metrics := orchestrator.GetMetrics()
	if metrics.MetaKernelsManaged != 1 {
		t.Errorf("Expected 1 managed kernel, got %d", metrics.MetaKernelsManaged)
	}
}
