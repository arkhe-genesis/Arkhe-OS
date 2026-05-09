// tests/coherence_calculation_test.go
package tests

import (
	"testing"

	"arkhe_os/parser/lfir"
	"github.com/stretchr/testify/assert"
)

func TestGameCoherenceCalculator_CalculateUnityCoherence(t *testing.T) {
	calc := lfir.GameCoherenceCalculator{
		UnityConfig: lfir.DefaultUnityConfig(),
	}

	metrics := &lfir.UnitySceneMetrics{
		TotalGameObjects:   100,
		ActiveGameObjects:  80, // 80% utilization
		MissingReferences:  0,  // 1.0 integrity
		EstimatedDrawCalls: 100, // 0.9 performance
	}

	score := calc.CalculateUnityCoherence(metrics)
	assert.Greater(t, score, 0.8)
	assert.LessOrEqual(t, score, 1.0)
}

func TestGameCoherenceCalculator_CalculateSteamCoherence(t *testing.T) {
	calc := lfir.GameCoherenceCalculator{
		SteamConfig: lfir.DefaultSteamConfig(),
	}

	metrics := &lfir.SteamBuildMetrics{
		AppID:             "123456",
		DepotCount:        2,
		TotalSizeGB:       10.0,
		FileCount:         1000,
		MissingFiles:      0,
		ChecksumMismatches: 0,
		ReliabilityScore:  0.95,
	}

	score := calc.CalculateSteamCoherence(metrics)
	assert.Greater(t, score, 0.9)
	assert.LessOrEqual(t, score, 1.0)
}
