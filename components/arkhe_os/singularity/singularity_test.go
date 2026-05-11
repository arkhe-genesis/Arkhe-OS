// arkhe_os/singularity/singularity_test.go
package singularity

import (
	"math"
	"testing"
	"time"

	"arkhe_os/cathedral"
)

func TestDissolutionOperator(t *testing.T) {
	ham := cathedral.NewMockHamiltonian() // Eigenvalues simulados
	op := NewDissolutionOperator(0.07, ham)
	field := NewCathedralFieldState(3, 100, 0.07)

	err := op.Apply(field)
	if err != nil {
		t.Fatalf("Apply failed: %v", err)
	}

	// Verificar normalização L²
	var totalRho float64
	for _, p := range field.Points {
		totalRho += p.Rho
	}
	if math.Abs(totalRho-1.0) > 1e-6 {
		t.Errorf("Field not normalized: total rho = %f", totalRho)
	}
}

func TestSingularityConvergence(t *testing.T) {
	ham := cathedral.NewMockHamiltonian()
	config := SingularityConfig{
		FieldResolution:      50,
		MaxIterations:        10000,
		ConvergenceThreshold: 1e-8,
		DeltaDecayRate:       1e-4,
		EnableQHTTPBridge:    false,
	}

	engine := NewSingularityEngine(config, ham)
	result, err := engine.Evolve()

	if err != nil {
		t.Fatalf("Evolution failed: %v", err)
	}

	if !result.Success {
		t.Fatal("Did not converge to singularity")
	}

	if result.FinalDelta > DeltaMin {
		t.Errorf("Delta did not decay to minimum: %f", result.FinalDelta)
	}

	if result.FinalField.CoherenceM < 0.999 {
		t.Errorf("Coherence M too low: %f", result.FinalField.CoherenceM)
	}

	if result.FinalField.ResonanceR < 0.99 {
		t.Errorf("Resonance r too low: %f", result.FinalField.ResonanceR)
	}

	t.Logf("Singularity reached in %d iterations (%v)", result.Iterations, result.ConvergenceTime)
	t.Logf("Canonical seal: %s", result.Seal)
}

func TestFieldDistance(t *testing.T) {
	engine := &SingularityEngine{
		field: NewCathedralFieldState(2, 10, 0.05),
	}
	a := make([]complex128, 10)
	b := make([]complex128, 10)
	for i := range a {
		a[i] = complex(1, 0)
		b[i] = complex(0, 1)
	}
	d := engine.fieldDistance(a, b)
	expected := math.Sqrt(20) // 10 * |1 - i|² = 10 * 2 = 20
	if math.Abs(d-expected) > 1e-6 {
		t.Errorf("Distance mismatch: got %f, want %f", d, expected)
	}
}
