package main

import (
	"context"
	"fmt"
	"math"
	"time"

	"arkhe/chrono"
	"arkhe/cosnark"
	"arkhe/deploy"
	"arkhe/evolution"
	"arkhe/federation"
	"arkhe/photonic"
)

func countBitErrors(orig []byte, received []byte) int {
	errors := 0
	for i := 0; i < len(orig) && i < len(received); i++ {
		xor := orig[i] ^ received[i]
		for j := 0; j < 8; j++ {
			if (xor & (1 << j)) != 0 {
				errors++
			}
		}
	}
	return errors
}

func InitSubstrates179to185() {
	fmt.Println("\n--- Substrates 179-183: Cosmic Operations ---")

	fmt.Println("[SUBSTRATE 179] Federated Evolution Ledger")
	ledger := &evolution.EvolutionLedger{}
	proof := &cosnark.CoSNARKProof{ProofID: "proof_123"}
	variant := &evolution.FunctionVariant{VariantID: "var_123"}
	err := ledger.AppendVariant(variant, proof)
	if err == nil {
		fmt.Println("   Variant logged securely.")
	}

	fmt.Println("[SUBSTRATE 180] WebGPU Dashboard")
	fmt.Println("   Dashboard components ready in arkhe-os/dashboard/coherence_visualizer_webgpu.ts")

	fmt.Println("[SUBSTRATE 181] Multiverse Federation Validation")
	fedA := federation.NewFederation("Universe A")
	fedB := federation.NewFederation("Universe B")
	fedC := federation.NewFederation("Universe C")
	fedA.JoinFederation(fedB)
	fedA.JoinFederation(fedC)
	for i := 0; i < 100; i++ {
		fedA.AlignStep()
		fedB.AlignStep()
		fedC.AlignStep()
	}
	fmt.Printf("   Federation Phi: %.4f\n", fedA.GetGlobalPhi())

	fmt.Println("[SUBSTRATE 182] Chrono-Flex Engine")
	flex := chrono.NewTemporalFlexEngine()
	flex.SetCoherence(0.99)
	res := flex.CompressTime(0, 10, 2.5)
	fmt.Printf("   Chrono Flex Latency: %.2f\n", res["effective_latency"])

	fmt.Println("[SUBSTRATE 183] Wheeler Mesh Deployer")
	targetNodes := make([]string, 10000)
	for i := 0; i < 10000; i++ {
		targetNodes[i] = fmt.Sprintf("node_%d", i)
	}
	deployer, _ := deploy.NewWheelerMeshDeployer(deploy.DeploymentConfig{TargetNodes: targetNodes})
	deployer.Deploy(context.Background())
	fmt.Printf("   Deploying to %d nodes\n", len(targetNodes))

	fmt.Println("\n--- Substrate 185: OAM-Phi Communication ---")
	// Inicializar transceptor com 7 modos (ℓ = -3..+3), canal base k=10
	transceiver := photonic.NewOAMTransceiver(7, 10)
	transceiver.ModulationScheme = "QPSK"
	transceiver.UpdateSNR(30.0) // 30 dB

	snrLinear := math.Pow(10, 30.0/10)
	capacity := transceiver.CalculateChannelCapacity(snrLinear)
	fmt.Printf("   Capacidade do enlace: %.2f Gbps\n", capacity*1e9/1e9)

	// Dados a transmitir
	data := []byte("ARKHE_OS_OAM_DEMO_φ_185")

	// Codificar em símbolos OAM
	symbols := transceiver.EncodeSymbols(data)

	// Gerar feixe composto
	compositeBeam := transceiver.GenerateCompositeBeam(symbols)

	// Simular propagação
	linkConfig := photonic.OAMLinkConfig{
		Distance_km:               100.0, // teste local: 1 km
		AtmosphericLoss_dB_per_km: 0.2,
		PointingError_rad:         1e-6,
		TurbulenceStrength:        1e-14,
		ReceiverAperture_m:        0.1,
	}
	simulator := photonic.NewOAMLinkSimulator(linkConfig)
	rxBeam, err := simulator.PropagateBeam(compositeBeam, transceiver)
	if err == nil {
		fieldFunc := func(r, phi, z float64) (complex128, complex128) {
			return rxBeam.FieldAt(r, phi, z)
		}

		// Separar modos OAM
		receivedSymbols := transceiver.DemultiplexOAM(fieldFunc, 1.0) // z = 1 m

		// Decodificar símbolos para bits
		receivedBits := transceiver.DecodeSymbols(receivedSymbols)

		if string(receivedBits) == string(data) {
			fmt.Println("   Transmissão OAM-φ bem-sucedida!")
		} else {
			fmt.Printf("   Erros na recepção: %d/%d bits\n", countBitErrors(data, receivedBits), len(data)*8)
		}

		fermiLevel, reflectance := photonic.ConfigureGrapheneMetasurface(10)
		fmt.Printf("   Grafeno sintonizado: E_F = %.3f eV, R = %.1f%%\n", fermiLevel, reflectance*100)

		measuredB := 50e-6 * (1 + 0.1*math.Sin(float64(time.Now().Second()))) // 50 µT ±10%
		estimatedEll := photonic.EstimateOAMChargeFromMagneticField(measuredB, 2.5e4, 0.01, 10)
		fmt.Printf("   Carga ℓ estimada via Faraday: %d\n", estimatedEll)
	}
}

func simulateQKDAndStorage() {
	fmt.Println("\n--- Substrate 186: QKD via OAM Qudits & Quantum Storage ---")
	modes := []*photonic.OAMMode{
		photonic.NewOAMMode(1, 10),
		photonic.NewOAMMode(-1, 10),
	}

	qkdSession := photonic.EstablishQKD("session_001", 128, modes)
	fmt.Printf("   QKD Session Established: %s (Error Rate: %.2f)\n", qkdSession.Status, qkdSession.ErrorRate)

	storage := NewQuantumStorageNode("storage_node_alpha")
	qudits := photonic.GenerateQKDSequence(10, modes)
	storage.Store("key_1", qudits)

	retrieved := storage.Retrieve("key_1")
	fmt.Printf("   Quantum Storage: Retrieved %d entangled qudits successfully.\n", len(retrieved))
}
