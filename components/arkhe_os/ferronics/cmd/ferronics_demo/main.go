package main

import (
	"fmt"
	"log"
	"math"
	"os"
	"path/filepath"
	"time"

	"arkhe_os/ferronics"
)

func main() {
	fmt.Println("🔬🛰️🧲🌐 ARKHE OS — SUBSTRATOS 200-203: ARQUITETURA FERRÔNICA AVANÇADA")

	// 1. Inicializar CPU Ferrônica
	fmt.Println("\n--- 1. Inicializar CPU Ferrônica ---")
	cpuConfig := ferronics.CPUConfig{
		ClockFrequencyHz:       1.0e9, // 1 GHz
		PipelineDepth:          16,
		MemoryDomainCount:      256,
		LogicGateCount:         64,
		EnergyEfficiencyTarget: 1.0e-21, // J/op alvo
	}
	cpu, err := ferronics.NewFerronicCPU("ferron_cpu_001", cpuConfig)
	if err != nil {
		log.Fatalf("CPU initialization failed: %v", err)
	}

	program := &ferronics.FerronicProgram{
		ProgramID: "demo_program",
		Instructions: []*ferronics.FerronicInstruction{
			{Operation: "LOAD", Operands: []string{"mem_0"}, Destination: "reg_A"},
			{Operation: "LOAD", Operands: []string{"mem_1"}, Destination: "reg_B"},
			{Operation: "XOR", Operands: []string{"reg_A", "reg_B"}, Destination: "reg_C"},
			{Operation: "STORE", Operands: []string{"reg_C"}, Destination: "mem_out"},
		},
	}
	if err := cpu.LoadProgram(program); err != nil {
		log.Fatalf("Program load failed: %v", err)
	}

	if err := cpu.Run(100); err != nil {
		log.Printf("⚠️ Execution warning: %v", err)
	}

	metrics := cpu.GetCPUMetrics()
	fmt.Printf("⚡ CPU metrics: %d instr, %.1f ps/gate, %.1e J/instr\n",
		metrics.InstructionsExecuted,
		metrics.AvgGateDelayPs,
		metrics.EnergyPerInstruction)

	// 2. Implantar Rede THz com Handover Automático
	fmt.Println("\n--- 2. Implantar Rede THz com Handover Automático ---")
	meshConfig := ferronics.MeshConfig{
		EnableAutoHandover:    true,
		HandoverThresholdHigh: 25.0,
		HandoverThresholdLow:  15.0,
		MaxNodesPerMesh:       20,
		PredictionHorizon:     500 * time.Millisecond,
	}
	mesh, err := ferronics.NewFerronMeshNetwork("station_mesh_001", meshConfig)
	if err != nil {
		log.Fatalf("Mesh initialization failed: %v", err)
	}

	crystals := []*ferronics.CrystalNode{
		{NodeID: "crystal_alpha", Position: [3]float64{0, 0, 0}, Status: "active"},
		{NodeID: "crystal_beta", Position: [3]float64{10, 0, 0}, Status: "active"},
		{NodeID: "crystal_gamma", Position: [3]float64{5, 8.66, 0}, Status: "active"}, // triângulo equilátero
	}
	for _, crystal := range crystals {
		transceiver, _ := ferronics.NewFerronTransceiver("BaTiO3", ferronics.FerronConfig{
			EnableTHzComm:   true,
			CoherenceTarget: 0.98,
		})
		crystal.FerronTransceiver = transceiver

		if err := mesh.RegisterCrystalNode(crystal); err != nil {
			log.Printf("⚠️ Failed to register %s: %v", crystal.NodeID, err)
		}
	}

	if _, err := mesh.EstablishLink("crystal_alpha", "crystal_beta"); err != nil {
		log.Printf("⚠️ Link alpha-beta failed: %v", err)
	}
	if _, err := mesh.EstablishLink("crystal_alpha", "crystal_gamma"); err != nil {
		log.Printf("⚠️ Link alpha-gamma failed: %v", err)
	}

	handoverID, err := mesh.SendWithHandover("crystal_alpha", []byte("ferron_mesh_demo"), 0.9)
	if err != nil {
		log.Printf("⚠️ Send failed: %v", err)
	} else {
		fmt.Printf("📡 Data sent via handover: %s\n", handoverID)
	}

	meshMetrics := mesh.GetMeshMetrics()
	fmt.Printf("🌐 Mesh metrics: %d nodes, %d links, %d handovers completed\n",
		meshMetrics.ActiveNodes, meshMetrics.ActiveLinks, meshMetrics.HandoversCompleted)

	// 3. Executar Porta Lógica Híbrida Magnon-Ferron
	fmt.Println("\n--- 3. Executar Porta Lógica Híbrida Magnon-Ferron ---")
	couplerConfig := ferronics.CouplerConfig{
		EnableQuantumMode:       true,
		TargetCoherenceTransfer: 0.95,
		EnergyEfficiencyMode:    true,
	}
	coupler, err := ferronics.NewMagnonFerronCoupler("hybrid_coupler_001", "BiFeO3", couplerConfig)
	if err != nil {
		log.Fatalf("Coupler initialization failed: %v", err)
	}

	magnonInput := &ferronics.MagnonState{
		StateID:       "magnon_in_001",
		SpinAmplitude: 0.8,
		SpinPhase:     0.0,
		Frequency:     1.0e12, // 1 THz
		Coherence:     0.99,
	}
	ferronInput := &ferronics.FerronState{
		StateID:   "ferron_in_001",
		Amplitude: 0.7,
		Phase:     math.Pi / 4,
		Coherence: 0.98,
	}

	output, err := coupler.ExecuteHybridGate("XOR_ME", magnonInput, ferronInput)
	if err != nil {
		log.Fatalf("Hybrid gate execution failed: %v", err)
	}

	switch out := output.(type) {
	case *ferronics.FerronState:
		fmt.Printf("🔀 XOR_ME output: amplitude=%.3f, phase=%.3f rad, coherence=%.3f\n",
			out.Amplitude, out.Phase, out.Coherence)
	case map[string]interface{}:
		if entangled, ok := out["entangled"].(bool); ok && entangled {
			fmt.Printf("🔗 Entangled pair created successfully\n")
		}
	}

	couplerMetrics := coupler.GetCouplerMetrics()
	fmt.Printf("🧲 Coupler metrics: %d operations, %.3f coherence transfer, %.1e J/op\n",
		couplerMetrics.CouplingsPerformed,
		couplerMetrics.AvgCoherenceTransfer,
		couplerMetrics.EnergyPerCoupling)

	// 4. Gerar Bindings Multi-Linguagem e Exportar Pacote
	fmt.Println("\n--- 4. Gerar Bindings Multi-Linguagem e Exportar Pacote ---")
	generator, err := ferronics.NewMultiLangGenerator("./ferronics_bindings")
	if err != nil {
		log.Fatalf("Generator initialization failed: %v", err)
	}

	targetLanguages := []ferronics.LanguageTarget{
		ferronics.LangPython,
		ferronics.LangRust,
	}
	results := generator.GenerateBindings(targetLanguages)

	for lang, result := range results {
		if result.Status == "success" {
			fmt.Printf("✅ %s bindings: %s\n", lang, result.OutputPath)
		} else {
			fmt.Printf("❌ %s bindings failed: %v\n", lang, result.Errors)
		}
	}

	packagePath, err := generator.ExportPackage("pypi")
	if err != nil {
		log.Printf("⚠️ Package export failed: %v", err)
	} else {
		fmt.Printf("📦 Package exported to: %s\n", packagePath)
	}

	docsPath := filepath.Join(generator.OutputDir(), "docs")
	if err := os.MkdirAll(docsPath, 0755); err == nil {
		apiRef := ferronics.GenerateAPIReference(generator.Specs())
		os.WriteFile(filepath.Join(docsPath, "API_REFERENCE.md"), []byte(apiRef), 0644)
		fmt.Printf("📚 API reference generated: %s\n", filepath.Join(docsPath, "API_REFERENCE.md"))
	}
}
