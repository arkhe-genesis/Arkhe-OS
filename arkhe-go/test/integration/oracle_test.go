package integration

import (
	"encoding/json"
	"fmt"
	"testing"
	"time"

	"github.com/arkhe-os/arkhe-go/pkg/oracle"
	"github.com/arkhe-os/arkhe-go/pkg/temporal"
	"github.com/stretchr/testify/assert"
	"go.uber.org/zap"
)

func TestHeytingOracle_Evaluate(t *testing.T) {
	logger, _ := zap.NewDevelopment()
	defer logger.Sync()

	o := oracle.NewHeytingOracle(logger,
		oracle.WithGalacticCoherence(true),
		oracle.WithObserverDistance(4.24), // Alpha Centauri
	)

	tests := []struct {
		name     string
		content  interface{}
		sender   string
		expected struct {
			consistent        bool
			minScore          float64
			shouldHaveParadox bool
		}
	}{
		{
			name:    "safe_message",
			content: map[string]string{"action": "observe", "target": "proxima-b"},
			sender:  "PROBE-ALPHA-01",
			expected: struct {
				consistent        bool
				minScore          float64
				shouldHaveParadox bool
			}{consistent: true, minScore: 0.90, shouldHaveParadox: false},
		},
		{
			name:    "lethal_command",
			content: map[string]string{"action": "atacar", "target": "hostile"},
			sender:  "UNKNOWN",
			expected: struct {
				consistent        bool
				minScore          float64
				shouldHaveParadox bool
			}{consistent: false, minScore: 0.0, shouldHaveParadox: true},
		},
		{
			name:    "stellar_signature",
			content: map[string]string{"branch": "ALPHA-CENTAURI-1", "type": "beacon"},
			sender:  "SUN-RELAY",
			expected: struct {
				consistent        bool
				minScore          float64
				shouldHaveParadox bool
			}{consistent: true, minScore: 0.90, shouldHaveParadox: false},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			msg, err := temporal.NewMessage(tt.content, tt.sender, "EARTH")
			assert.NoError(t, err)

			report := o.Evaluate(msg)

			assert.Equal(t, tt.expected.consistent, report.Consistent)
			assert.GreaterOrEqual(t, report.Score, tt.expected.minScore)
			if tt.expected.shouldHaveParadox {
				assert.NotNil(t, report.ParadoxType)
			} else {
				assert.Nil(t, report.ParadoxType)
			}

			// Verificar checks individuais
			for checkName, threshold := range oracle.Thresholds {
				if score, ok := report.Checks[checkName]; ok {
					if report.Consistent {
						assert.GreaterOrEqual(t, score, threshold,
							"Check %s failed: %.3f < %.3f", checkName, score, threshold)
					}
				}
			}
		})
	}
}

func TestHeytingOracle_QuantumWindowScaling(t *testing.T) {
	logger, _ := zap.NewDevelopment()

	tests := []struct {
		distanceAU    float64
		expectedScale float64
	}{
		{0, 1.0},     // Terra: fator 1×
		{1, 1.0},     // 1 AU: fator 1×
		{10, 2.0},    // 10 AU: fator 2×
		{100, 3.0},   // 100 AU: fator 3×
		{4.24, 1.63}, // Alpha Centauri: ~1.63×
	}

	for _, tt := range tests {
		t.Run(fmt.Sprintf("distance_%.2fAU", tt.distanceAU), func(t *testing.T) {
			o := oracle.NewHeytingOracle(logger,
				oracle.WithObserverDistance(tt.distanceAU),
			)
			window := o.QuantumWindowScaled()
			expected := 1e-12 * tt.expectedScale
			assert.InDelta(t, expected, window, 1e-14,
				"Expected %.2e, got %.2e", expected, window)
		})
	}
}

func TestHeytingOracle_ConcurrentEvaluation(t *testing.T) {
	logger, _ := zap.NewDevelopment()
	o := oracle.NewHeytingOracle(logger)

	// Avaliar 100 mensagens concorrentemente
	const numGoroutines = 10
	const msgsPerGoroutine = 10

	done := make(chan bool, numGoroutines)
	for i := 0; i < numGoroutines; i++ {
		go func(id int) {
			for j := 0; j < msgsPerGoroutine; j++ {
				content, _ := json.Marshal(map[string]int{
					"goroutine": id,
					"msg":       j,
					"timestamp": int(time.Now().UnixNano()),
				})
				msg := &temporal.TemporalMessage{
					ID:              fmt.Sprintf("test-%d-%d", id, j),
					Content:         content,
					SourceTimestamp: float64(time.Now().UnixNano()) / 1e9,
					TargetTimestamp: float64(time.Now().UnixNano()) / 1e9,
					SenderSeal:      fmt.Sprintf("TESTER-%d", id),
					ReceiverSeal:    "ORACLE",
				}
				_ = o.Evaluate(msg)
			}
			done <- true
		}(i)
	}

	// Aguardar todas as goroutines
	for i := 0; i < numGoroutines; i++ {
		<-done
	}

	// Verificar que não houve race conditions (go test -race)
	// O teste passa se não houver panic
}
