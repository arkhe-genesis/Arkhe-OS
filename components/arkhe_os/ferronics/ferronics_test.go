package ferronics

import (
	"testing"
	"time"
	"math"
)

func TestFerronicCPU(t *testing.T) {
	cpuConfig := CPUConfig{
		ClockFrequencyHz:       1.0e9,
		PipelineDepth:          16,
		MemoryDomainCount:      10,
		LogicGateCount:         10,
		EnergyEfficiencyTarget: 1.0e-21,
	}
	cpu, err := NewFerronicCPU("test_cpu", cpuConfig)
	if err != nil {
		t.Fatalf("Failed to create CPU: %v", err)
	}

	program := &FerronicProgram{
		ProgramID: "test_prog",
		Instructions: []*FerronicInstruction{
			{Operation: "LOAD", Operands: []string{"mem_0"}, Destination: "reg_A"},
		},
	}
	if err := cpu.LoadProgram(program); err != nil {
		t.Fatalf("Failed to load program: %v", err)
	}

	if err := cpu.Run(10); err != nil {
		t.Fatalf("Run failed: %v", err)
	}
}

func TestFerronMeshNetwork(t *testing.T) {
	meshConfig := MeshConfig{
		EnableAutoHandover:    true,
		HandoverThresholdHigh: 25.0,
		HandoverThresholdLow:  15.0,
		MaxNodesPerMesh:       10,
		PredictionHorizon:     100 * time.Millisecond,
	}
	mesh, err := NewFerronMeshNetwork("test_mesh", meshConfig)
	if err != nil {
		t.Fatalf("Failed to create mesh: %v", err)
	}
	if mesh == nil {
		t.Fatal("Mesh is nil")
	}
}

func TestMagnonFerronCoupler(t *testing.T) {
	couplerConfig := CouplerConfig{
		EnableQuantumMode:       true,
		TargetCoherenceTransfer: 0.95,
		EnergyEfficiencyMode:    true,
	}
	coupler, err := NewMagnonFerronCoupler("test_coupler", "BiFeO3", couplerConfig)
	if err != nil {
		t.Fatalf("Failed to create coupler: %v", err)
	}
	magnonInput := &MagnonState{
		StateID:       "mag1",
		SpinAmplitude: 0.8,
		SpinPhase:     0.0,
		Frequency:     1.0e12,
		Coherence:     0.99,
	}
	ferronInput := &FerronState{
		StateID:   "fer1",
		Amplitude: 0.7,
		Phase:     math.Pi / 4,
		Coherence: 0.98,
	}

	_, err = coupler.ExecuteHybridGate("XOR_ME", magnonInput, ferronInput)
	if err != nil {
		t.Fatalf("Failed to execute hybrid gate: %v", err)
	}
}
