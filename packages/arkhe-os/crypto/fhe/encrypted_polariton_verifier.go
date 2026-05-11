package fhe

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"sync"

	"arkhe/crypto/fhe/schemes"
	"arkhe/photonic"
)

// EncryptedPolaritonVerifier verifica integridade de estados polaritônicos criptografados sem decifrar
type EncryptedPolaritonVerifier struct {
	mu sync.RWMutex

	// Chaves de verificação por modo polaritônico
	verificationKeys map[photonic.PolaritonModeType]schemes.VerificationKey

	// Circuitos zk-SNARK pré-compilados por tipo de verificação
	zkCircuits map[string]map[photonic.PolaritonModeType]schemes.ZKCircuit

	// Configuração de verificação
	config VerifierConfig

	// Métricas de verificação
	metrics VerifierMetrics
}

// VerifierConfig contém configuração para verificação criptográfica
type VerifierConfig struct {
	EnableZKProofs        bool                                    // Habilitar provas zero-knowledge
	ProofType             string                                  // "groth16", "plonk", "bulletproofs"
	VerificationThreshold float64                                 // Threshold mínimo para aceitação de prova
	ModeSpecificChecks    map[photonic.PolaritonModeType][]string // Checks específicos por modo
}

// VerifierMetrics contém métricas do verificador
type VerifierMetrics struct {
	VerificationsPerformed int64                              `json:"verifications_performed"`
	ZKProofsVerified       int64                              `json:"zk_proofs_verified"`
	VerificationFailures   int64                              `json:"verification_failures"`
	AvgVerificationTimeMs  float64                            `json:"avg_verification_time_ms"`
	ModeDistribution       map[photonic.PolaritonModeType]int `json:"mode_distribution"`
}

// NewEncryptedPolaritonVerifier cria novo verificador para estados polaritônicos criptografados
func NewEncryptedPolaritonVerifier(
	config VerifierConfig,
	verificationKeys map[photonic.PolaritonModeType]schemes.VerificationKey,
) (*EncryptedPolaritonVerifier, error) {
	if config.ProofType == "" {
		config.ProofType = "groth16"
	}
	if config.VerificationThreshold == 0 {
		config.VerificationThreshold = 0.99
	}

	verifier := &EncryptedPolaritonVerifier{
		verificationKeys: verificationKeys,
		zkCircuits:       make(map[string]map[photonic.PolaritonModeType]schemes.ZKCircuit),
		config:           config,
		metrics: VerifierMetrics{
			ModeDistribution: make(map[photonic.PolaritonModeType]int),
		},
	}

	// Compilar circuitos zk-SNARK padrão para verificações comuns
	if err := verifier.compileDefaultZKCircuits(); err != nil {
		return nil, fmt.Errorf("failed to compile default zk circuits: %w", err)
	}

	return verifier, nil
}

// compileDefaultZKCircuits compila circuitos zk-SNARK para verificações padrão
func (v *EncryptedPolaritonVerifier) compileDefaultZKCircuits() error {
	// Verificações comuns para estados polaritônicos
	checks := []string{
		"coherence_preservation", // Verificar que coerência foi preservada
		"compression_integrity",  // Verificar que compressão não corrompeu dados
		"mode_consistency",       // Verificar consistência entre modos
		"crystal_params_valid",   // Verificar parâmetros do cristal
	}

	for _, check := range checks {
		v.zkCircuits[check] = make(map[photonic.PolaritonModeType]schemes.ZKCircuit)
		for mode := range v.verificationKeys {
			// Compilar circuito para este check e modo
			circuit, err := schemes.CompileZKCircuitForPolaritonCheck(check, string(mode), v.config.ProofType)
			if err != nil {
				return fmt.Errorf("circuit compilation failed for %s/%s: %w", check, mode, err)
			}
			v.zkCircuits[check][mode] = circuit
		}
	}

	return nil
}

// VerifyIntegrity verifica integridade de estado polaritônico criptografado sem decifrar
func (v *EncryptedPolaritonVerifier) VerifyIntegrity(
	encryptedState *EncryptedPolaritonState,
	checkType string,
	publicInputs map[string]interface{},
) (bool, error) {
	v.mu.RLock()
	defer v.mu.RUnlock()

	if !v.config.EnableZKProofs {
		return false, fmt.Errorf("zk proofs not enabled in verifier config")
	}

	// Verificar cada modo polaritônico presente
	allValid := true

	for mode, ciphertext := range encryptedState.EncryptedComponents {
		// Recuperar circuito zk para este check e modo
		circuit, exists := v.zkCircuits[checkType][mode]
		if !exists {
			return false, fmt.Errorf("no zk circuit registered for check %s on mode %s", checkType, mode)
		}

		// Gerar prova zero-knowledge (em produção: prover externo geraria a prova)
		// Aqui: simular verificação de prova existente
		proof, err := v.simulateZKProofGeneration(ciphertext, circuit, publicInputs)
		if err != nil {
			return false, fmt.Errorf("proof generation failed for mode %s: %w", mode, err)
		}

		// Verificar prova
		verified, err := circuit.Verify(proof, publicInputs)
		if err != nil {
			return false, fmt.Errorf("proof verification failed for mode %s: %w", mode, err)
		}

		if !verified {
			allValid = false
			v.metrics.VerificationFailures++
		}

		v.metrics.ModeDistribution[mode]++
	}

	// Atualizar métricas
	v.metrics.VerificationsPerformed++
	if allValid {
		v.metrics.ZKProofsVerified++
	}

	return allValid, nil
}

// VerifyCoherencePreservation verifica especificamente preservação de coerência
func (v *EncryptedPolaritonVerifier) VerifyCoherencePreservation(
	encryptedState *EncryptedPolaritonState,
	expectedCoherence float64,
	tolerance float64,
) (bool, error) {
	publicInputs := map[string]interface{}{
		"expected_coherence": expectedCoherence,
		"tolerance":          tolerance,
		"verification_type":  "coherence_preservation",
	}

	return v.VerifyIntegrity(encryptedState, "coherence_preservation", publicInputs)
}

// VerifyCompressionIntegrity verifica que compressão não corrompeu dados essenciais
func (v *EncryptedPolaritonVerifier) VerifyCompressionIntegrity(
	encryptedState *EncryptedPolaritonState,
	originalHash string,
) (bool, error) {
	publicInputs := map[string]interface{}{
		"original_hash":     originalHash,
		"verification_type": "compression_integrity",
	}

	return v.VerifyIntegrity(encryptedState, "compression_integrity", publicInputs)
}

// simulateZKProofGeneration simula geração de prova zk (em produção: usar prover real)
func (v *EncryptedPolaritonVerifier) simulateZKProofGeneration(
	ciphertext schemes.Ciphertext,
	circuit schemes.ZKCircuit,
	publicInputs map[string]interface{},
) ([]byte, error) {
	// Em produção: chamar prover zk-SNARK real com witness privado
	// Aqui: retornar prova simulada baseada em hash do ciphertext
	proofData := fmt.Sprintf("%x:%v", hashCiphertextVerifier(ciphertext), publicInputs)
	return schemes.SimulateZKProof(proofData, circuit, v.config.ProofType)
}

// GetVerifierMetrics retorna métricas consolidadas do verificador
func (v *EncryptedPolaritonVerifier) GetVerifierMetrics() VerifierMetrics {
	v.mu.RLock()
	defer v.mu.RUnlock()
	return v.metrics
}

// Helper functions
func hashCiphertextVerifier(ct schemes.Ciphertext) []byte {
	data, _ := json.Marshal(ct)
	sum := sha256.Sum256(data)
	return sum[:]
}
