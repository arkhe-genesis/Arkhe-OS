package main

import (
	"log"
	"time"

	"arkhe/crypto/fhe"
	"arkhe/crypto/fhe/schemes"
	"arkhe/photonic"
)

func main() {
	// Configurar parâmetros FHE por modo polaritônico
	fheParamsByMode := map[photonic.PolaritonModeType]fhe.PolaritonFHEParams{
		photonic.ModePhononPolariton: {
			SchemeType:             "BFV",
			PolyModulusDegree:      4096,
			CoeffModulusBitSizes:   []int{30, 20, 20, 30},
			SecurityLevel:          128,
			MaxMultiplicativeDepth: 3,
		},
		photonic.ModeExcitonPolariton: {
			SchemeType:             "CKKS",
			PolyModulusDegree:      8192,
			CoeffModulusBitSizes:   []int{40, 30, 30, 30, 40},
			SecurityLevel:          128,
			MaxMultiplicativeDepth: 4,
			ScalingFactor:          1 << 40,
		},
		photonic.ModeHybridPolariton: {
			SchemeType:             "CKKS",
			PolyModulusDegree:      8192,
			CoeffModulusBitSizes:   []int{40, 30, 30, 30, 40},
			SecurityLevel:          128,
			MaxMultiplicativeDepth: 4,
			ScalingFactor:          1 << 40,
		},
	}

	// Criar criptografador FHE para polaritons
	_, err := fhe.NewPolaritonFHEEncryptor(fheParamsByMode)
	if err != nil {
		log.Fatalf("Failed to create polariton FHE encryptor: %v", err)
	}

	// Configurar roteador criptografado
	routingConfig := fhe.EncryptedPolaritonRoutingConfig{
		MinParticipantsPerMode: map[photonic.PolaritonModeType]int{
			photonic.ModePhononPolariton:  3,
			photonic.ModeExcitonPolariton: 2,
		},
		AggregationTimeout:           5 * time.Minute,
		NoiseScale:                   0.01,
		EnableZKVerification:         true,
		DifferentialPrivacyEpsilon:   1.0,
		ModePriorityWeights: map[photonic.PolaritonModeType]float64{
			photonic.ModePhononPolariton:  1.0,
			photonic.ModeExcitonPolariton: 1.2,
		},
	}

	_, err = fhe.NewEncryptedPolaritonRouter(routingConfig)
	if err != nil {
		log.Fatalf("Failed to create encrypted polariton router: %v", err)
	}

	// Configurar verificador de integridade
	verifierConfig := fhe.VerifierConfig{
		EnableZKProofs:        true,
		ProofType:             "groth16",
		VerificationThreshold: 0.99,
	}

	// Chaves de verificação (em produção: carregar de configuração segura)
	verificationKeys := make(map[photonic.PolaritonModeType]schemes.VerificationKey)

	_, err = fhe.NewEncryptedPolaritonVerifier(verifierConfig, verificationKeys)
	if err != nil {
		log.Fatalf("Failed to create polariton verifier: %v", err)
	}

	log.Printf("✅ Polariton FHE privacy components initialized")
}
