package fhe

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"math/cmplx"
	"sync"
	"time"

	"arkhe/crypto/fhe/schemes"
	"arkhe/photonic"
)

// PolaritonFHEEncryptor criptografa estados polaritônicos para computação homomórfica
type PolaritonFHEEncryptor struct {
	mu sync.RWMutex

	// Chaves e parâmetros FHE por modo polaritônico
	publicKeys  map[photonic.PolaritonModeType]schemes.FHEPublicKey
	privateKeys map[photonic.PolaritonModeType]schemes.FHEPrivateKey
	params      map[photonic.PolaritonModeType]PolaritonFHEParams

	// Cache de ciphertexts para eficiência
	ciphertextCache map[string]schemes.Ciphertext
	cacheTTL        time.Duration

	// Métricas de criptografia
	metrics PolaritonEncryptorMetrics
}

// PolaritonFHEParams contém parâmetros FHE adaptados para modos polaritônicos
type PolaritonFHEParams struct {
	SchemeType             string  // "BFV" para modos discretos, "CKKS" para contínuos
	PolyModulusDegree      int     // Grau do polinômio modular
	CoeffModulusBitSizes   []int   // Tamanhos de bits para coeficientes modulares
	SecurityLevel          int     // Nível de segurança em bits (128/256)
	MaxMultiplicativeDepth int     // Profundidade multiplicativa máxima permitida
	ScalingFactor          float64 // Fator de escala para CKKS (modos contínuos)
	ModeSpecificParams     map[string]interface{} // Parâmetros específicos por modo
}

// PolaritonEncryptorMetrics contém métricas do criptografador polaritônico
type PolaritonEncryptorMetrics struct {
	EncryptionsPerformed     int64   `json:"encryptions_performed"`
	EvaluationsPerformed     int64   `json:"evaluations_performed"`
	AvgEncryptionTimeMs      float64 `json:"avg_encryption_time_ms"`
	TotalCiphertextSizeBytes int64   `json:"total_ciphertext_size_bytes"`
	PrivacyBudgetConsumed    float64 `json:"privacy_budget_consumed"`
	ModeDistribution         map[photonic.PolaritonModeType]int `json:"mode_distribution"`
}

// NewPolaritonFHEEncryptor cria novo criptografador homomórfico para estados polaritônicos
func NewPolaritonFHEEncryptor(
	params map[photonic.PolaritonModeType]PolaritonFHEParams,
) (*PolaritonFHEEncryptor, error) {
	// Validar parâmetros por modo
	for mode, p := range params {
		if err := validatePolaritonFHEParams(mode, p); err != nil {
			return nil, fmt.Errorf("invalid FHE params for mode %s: %w", mode, err)
		}
	}

	encryptor := &PolaritonFHEEncryptor{
		publicKeys:      make(map[photonic.PolaritonModeType]schemes.FHEPublicKey),
		privateKeys:     make(map[photonic.PolaritonModeType]schemes.FHEPrivateKey),
		params:          params,
		ciphertextCache: make(map[string]schemes.Ciphertext),
		cacheTTL:        1 * time.Hour,
		metrics: PolaritonEncryptorMetrics{
			AvgEncryptionTimeMs: 0,
			ModeDistribution:    make(map[photonic.PolaritonModeType]int),
		},
	}

	// Gerar chaves para cada modo polaritônico suportado
	for mode, p := range params {
		pubKey, privKey, err := schemes.GenerateKeyPair(p.SchemeType, p)
		if err != nil {
			return nil, fmt.Errorf("key generation failed for mode %s: %w", mode, err)
		}
		encryptor.publicKeys[mode] = pubKey
		encryptor.privateKeys[mode] = privKey
	}

	return encryptor, nil
}

// EncryptPolaritonState criptografa estado polaritônico para computação homomórfica
func (e *PolaritonFHEEncryptor) EncryptPolaritonState(
	polaritonState *photonic.CompressedAPIState,
	sensitivityLevel string, // "public", "confidential", "private"
) (*EncryptedPolaritonState, error) {
	startTime := time.Now()
	e.mu.Lock()
	defer e.mu.Unlock()

	// Extrair componentes do estado polaritônico por modo
	modeComponents := extractPolaritonModeComponents(polaritonState, sensitivityLevel)

	// Criptografar componentes baseado no modo polaritônico
	encryptedComponents := make(map[photonic.PolaritonModeType]schemes.Ciphertext)
	for mode, component := range modeComponents {
		// Selecionar esquema FHE apropriado para o modo
		schemeType := e.params[mode].SchemeType

		// Converter valor para formato apropriado para FHE do modo
		plaintext, err := polaritonValueToPlaintext(component, schemeType, mode)
		if err != nil {
			return nil, fmt.Errorf("plaintext conversion failed for mode %s: %w", mode, err)
		}

		// Criptografar com FHE do modo
		publicKey := e.publicKeys[mode]
		ciphertext, err := publicKey.Encrypt(plaintext)
		if err != nil {
			return nil, fmt.Errorf("encryption failed for mode %s: %w", mode, err)
		}

		encryptedComponents[mode] = ciphertext

		// Cache para reuso
		cacheKey := fmt.Sprintf("%s:%s:%x", polaritonState.StateID, mode, hashPolaritonValue(component))
		e.ciphertextCache[cacheKey] = ciphertext

		// Atualizar métricas de distribuição de modos
		e.metrics.ModeDistribution[mode]++
	}

	// Componentes não-sensíveis permanecem em claro para eficiência
	nonSensitiveComponents := filterNonSensitivePolaritonComponents(polaritonState, sensitivityLevel)

	// Atualizar métricas
	elapsed := time.Since(startTime).Milliseconds()
	e.metrics.EncryptionsPerformed++
	n := e.metrics.EncryptionsPerformed
	oldAvg := e.metrics.AvgEncryptionTimeMs
	e.metrics.AvgEncryptionTimeMs = (oldAvg*float64(n-1) + float64(elapsed)) / float64(n)

	return &EncryptedPolaritonState{
		StateID:             polaritonState.StateID,
		EncryptionLevel:     sensitivityLevel,
		EncryptedComponents: encryptedComponents,
		PlainTextComponents: nonSensitiveComponents,
		CiphertextBlob:      serializePolaritonCiphertexts(encryptedComponents),
		Timestamp:           time.Now(),
		CrystalParams:       polaritonState.CrystalParams,
	}, nil
}

// extractPolaritonModeComponents extrai componentes do estado polaritônico por modo
func extractPolaritonModeComponents(
	state *photonic.CompressedAPIState,
	sensitivityLevel string,
) map[photonic.PolaritonModeType][]complex128 {
	components := make(map[photonic.PolaritonModeType][]complex128)

	// Separar componentes do estado comprimido por tipo de modo polaritônico
	// Simplificação: dividir vetor de estado em segmentos por modo
	stateVec := state.CompressedState
	segmentSize := len(stateVec) / 4 // 4 modos principais

	if segmentSize == 0 {
		return components
	}

	components[photonic.ModePhononPolariton] = stateVec[0:segmentSize]
	components[photonic.ModePlasmonPolariton] = stateVec[segmentSize : 2*segmentSize]
	components[photonic.ModeExcitonPolariton] = stateVec[2*segmentSize : 3*segmentSize]
	components[photonic.ModeHybridPolariton] = stateVec[3*segmentSize:]

	// Aplicar filtragem baseada em nível de sensibilidade
	if sensitivityLevel == "private" {
		// Para nível privado: criptografar todos os componentes
		return components
	} else if sensitivityLevel == "confidential" {
		// Para confidencial: criptografar apenas modos de alta sensibilidade
		delete(components, photonic.ModePhononPolariton) // Modo menos sensível em claro
	}
	// Para público: apenas metadados em claro, estados sempre criptografados

	return components
}

// polaritonValueToPlaintext converte valor polaritônico para plaintext FHE
func polaritonValueToPlaintext(
	value []complex128,
	schemeType string,
	mode photonic.PolaritonModeType,
) (schemes.Plaintext, error) {
	// Converter vetor complexo para formato apropriado para FHE
	switch schemeType {
	case "CKKS":
		// Para modos contínuos (exciton, hybrid): usar CKKS com scaling
		scaledValues := make([]float64, len(value))
		for i, c := range value {
			// Usar magnitude como valor real, fase como metadado
			scaledValues[i] = cmplx.Abs(c) * 1e6 // Scaling para precisão
		}
		return schemes.NewCKKSPlaintext(scaledValues...), nil

	case "BFV":
		// Para modos discretos (phonon, plasmon): usar BFV para inteiros
		intValues := make([]int64, len(value))
		for i, c := range value {
			// Quantizar amplitude para inteiro
			intValues[i] = int64(cmplx.Abs(c) * 1e9)
		}
		return schemes.NewBFVPlaintext(intValues...), nil

	default:
		return nil, fmt.Errorf("unsupported scheme type %s for mode %s", schemeType, mode)
	}
}

// EvaluateCoherenceHomomorphically computa coerência sobre estado polaritônico criptografado
func (e *PolaritonFHEEncryptor) EvaluateCoherenceHomomorphically(
	encryptedState *EncryptedPolaritonState,
	coherenceFunction string, // "photonic_coherence", "compression_fidelity", "mode_matching"
	mode photonic.PolaritonModeType,
) (schemes.Ciphertext, error) {
	e.mu.RLock()
	defer e.mu.RUnlock()

	// Recuperar ciphertext do modo especificado
	ciphertext, exists := encryptedState.EncryptedComponents[mode]
	if !exists {
		return nil, fmt.Errorf("no encrypted component for mode %s", mode)
	}

	// Avaliar função de coerência homomorficamente
	// Nota: em produção, compilar função para circuito FHE específico do modo
	result, err := e.publicKeys[mode].Evaluate(coherenceFunction, ciphertext)
	if err != nil {
		return nil, fmt.Errorf("homomorphic evaluation failed for mode %s: %w", mode, err)
	}

	e.metrics.EvaluationsPerformed++
	return result, nil
}

// DecryptCoherenceResult decripta resultado de computação homomórfica polaritônica
func (e *PolaritonFHEEncryptor) DecryptCoherenceResult(
	ciphertext schemes.Ciphertext,
	mode photonic.PolaritonModeType,
) (float64, error) {
	e.mu.RLock()
	defer e.mu.RUnlock()

	privateKey := e.privateKeys[mode]
	plaintext, err := privateKey.Decrypt(ciphertext)
	if err != nil {
		return 0, fmt.Errorf("decryption failed for mode %s: %w", mode, err)
	}

	// Converter plaintext para float64 baseado no esquema do modo
	result, err := polaritonPlaintextToFloat64(plaintext, e.params[mode].SchemeType)
	if err != nil {
		return 0, fmt.Errorf("plaintext conversion failed: %w", err)
	}

	return result, nil
}

// Helper functions
func validatePolaritonFHEParams(
	mode photonic.PolaritonModeType,
	params PolaritonFHEParams,
) error {
	if params.PolyModulusDegree < 1024 || params.PolyModulusDegree > 65536 {
		return fmt.Errorf("invalid PolyModulusDegree: %d", params.PolyModulusDegree)
	}
	if params.SecurityLevel != 128 && params.SecurityLevel != 256 {
		return fmt.Errorf("invalid SecurityLevel: %d (must be 128 or 256)", params.SecurityLevel)
	}

	// Validações específicas por modo
	switch mode {
	case photonic.ModePhononPolariton, photonic.ModePlasmonPolariton:
		if params.SchemeType != "BFV" {
			return fmt.Errorf("mode %s requires BFV scheme for discrete values", mode)
		}
	case photonic.ModeExcitonPolariton, photonic.ModeHybridPolariton:
		if params.SchemeType != "CKKS" {
			return fmt.Errorf("mode %s requires CKKS scheme for continuous values", mode)
		}
	}

	return nil
}

func filterNonSensitivePolaritonComponents(
	state *photonic.CompressedAPIState,
	sensitivityLevel string,
) map[string]interface{} {
	components := make(map[string]interface{})

	// Metadados sempre públicos
	components["state_id"] = state.StateID
	components["compression_factor"] = state.CompressionFactor
	components["fidelity"] = state.Fidelity
	components["crystal_material"] = state.CrystalParams.Material

	// Componentes condicionais baseado em sensibilidade
	if sensitivityLevel != "private" {
		components["photonic_coherence"] = state.PhotonicCoherence
		components["timestamp"] = state.Timestamp.Unix()
	}

	return components
}

func hashPolaritonValue(value []complex128) []byte {
	// Hash simplificado de vetor complexo para cache key
	data := make([]byte, len(value)*16)
	for i, c := range value {
		for j := 0; j < 8; j++ {
			data[i*16+j] = byte(real(c) * 1e10)
			data[i*16+8+j] = byte(imag(c) * 1e10)
		}
	}
	sum := sha256.Sum256(data)
	return sum[:]
}

func serializePolaritonCiphertexts(
	ciphertexts map[photonic.PolaritonModeType]schemes.Ciphertext,
) []byte {
	// Serialização simplificada - em produção: usar formato binário eficiente
	data, _ := json.Marshal(ciphertexts)
	return data
}

func polaritonPlaintextToFloat64(
	plaintext schemes.Plaintext,
	schemeType string,
) (float64, error) {
	// Converter plaintext FHE para float64 baseado no esquema
	switch schemeType {
	case "CKKS":
		if pt, ok := plaintext.(*schemes.CKKSPlaintext); ok {
			// Retornar média dos valores para coerência agregada
			values := pt.Values()
			var sum float64
			for _, v := range values {
				sum += v
			}
			if len(values) > 0 {
				return sum / float64(len(values)) / 1e6, nil // Desescalar
			}
		}
	case "BFV":
		if pt, ok := plaintext.(*schemes.BFVPlaintext); ok {
			// Converter inteiro quantizado para float
			return float64(pt.Value()) / 1e9, nil
		}
	}
	return 0, fmt.Errorf("unsupported plaintext type for scheme %s", schemeType)
}

// EncryptedPolaritonState representa estado polaritônico criptografado
type EncryptedPolaritonState struct {
	StateID             string
	EncryptionLevel     string
	EncryptedComponents map[photonic.PolaritonModeType]schemes.Ciphertext
	PlainTextComponents map[string]interface{}
	CiphertextBlob      []byte
	Timestamp           time.Time
	CrystalParams       photonic.CrystalParameters
}

// GetEncryptorMetrics retorna métricas do criptografador polaritônico
func (e *PolaritonFHEEncryptor) GetEncryptorMetrics() PolaritonEncryptorMetrics {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return e.metrics
}
