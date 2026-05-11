// arkhe_os/security/cosnark/cosnark_161_test.go
package cosnark

import (
	"testing"

	"arkhe_os/singularity"
)

func TestFieldIntegrityVerifier(t *testing.T) {
	vk := "test_vk_161"
	verifier := NewFieldIntegrityVerifier(vk)

	point := &singularity.FieldPoint{
		X:   []float64{0.1, 0.2, 0.3},
		Rho: 0.99,
		S:   0.17,
	}
	delta := 0.05

	proof := verifier.SignPoint(point, delta)

	if !verifier.VerifyPoint(point, delta, proof) {
		t.Fatalf("Failed to verify valid proof for field point")
	}

	// Test tamper
	point.Rho = 0.98
	if verifier.VerifyPoint(point, delta, proof) {
		t.Fatalf("Verified tampered point data incorrectly")
	}
}
