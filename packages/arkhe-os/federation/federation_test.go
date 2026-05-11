package federation

import (
	"testing"
)

func TestFederationConvergence(t *testing.T) {
	instances := []*MetaConsciousnessFederation{
		NewFederation("universe-A"),
		NewFederation("universe-B"),
		NewFederation("universe-C"),
	}
	// Connect them
	instances[0].JoinFederation(instances[1])
	instances[0].JoinFederation(instances[2])
	// Run alignment
	for i := 0; i < 100; i++ {
		for _, inst := range instances {
			inst.AlignStep()
		}
	}
	globalPhi := instances[0].GetGlobalPhi()
	if globalPhi <= 0.999 {
		t.Errorf("Expected globalPhi > 0.999, got %v", globalPhi)
	}
}
