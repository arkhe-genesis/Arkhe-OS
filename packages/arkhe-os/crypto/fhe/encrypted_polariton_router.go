package fhe

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"math"
	"sync"
	"time"

	"arkhe/crypto/fhe/schemes"
	"arkhe/photonic"
)

// EncryptedPolaritonRouter roteia estados polaritônicos criptografados com privacidade preservada
type EncryptedPolaritonRouter struct {
	mu sync.RWMutex

	// Configuração
	config EncryptedPolaritonRoutingConfig

	// Chaves para agregação segura por modo polaritônico
	aggregationPublicKeys map[photonic.PolaritonModeType]schemes.AggregationPublicKey
	participantKeys       map[string]map[photonic.PolaritonModeType]schemes.ParticipantKey

	// Cache de contribuições criptografadas por rota
	encryptedContributions map[string]map[photonic.PolaritonModeType][]schemes.Ciphertext
	contributionTimestamps map[string]time.Time

	// Canal para resultados agregados
	resultChannel chan PolaritonAggregationResult

	// Métricas de roteamento criptografado
	metrics EncryptedRouterMetrics
}

// EncryptedPolaritonRoutingConfig contém configuração para roteamento com privacidade
type EncryptedPolaritonRoutingConfig struct {
	MinParticipantsPerMode     map[photonic.PolaritonModeType]int     // Mínimo de participantes por modo
	AggregationTimeout         time.Duration                          // Timeout para coleta de contribuições
	NoiseScale                 float64                                // Escala de ruído diferencial para privacidade adicional
	EnableZKVerification       bool                                   // Habilitar verificação zero-knowledge dos resultados
	DifferentialPrivacyEpsilon float64                                // Parâmetro epsilon para privacidade diferencial
	ModePriorityWeights        map[photonic.PolaritonModeType]float64 // Pesos de prioridade por modo
}

// PolaritonAggregationResult representa resultado de agregação federada com privacidade para polaritons
type PolaritonAggregationResult struct {
	ResultID          string
	AggregatedValues  map[photonic.PolaritonModeType]schemes.Ciphertext // Resultados ainda criptografados por modo
	DecryptedValues   *map[photonic.PolaritonModeType]float64            // Resultados decriptados (se autorizado)
	ParticipantCounts map[photonic.PolaritonModeType]int
	PrivacyGuarantee  string // "differential_privacy", "secure_aggregation", etc.
	Timestamp         time.Time
	ZKProofs          map[photonic.PolaritonModeType][]byte  // Provas zero-knowledge por modo se habilitado
	NoiseMagnitudes   map[photonic.PolaritonModeType]float64 // Magnitude do ruído diferencial adicionado por modo
}

// EncryptedRouterMetrics contém métricas do roteador criptografado
type EncryptedRouterMetrics struct {
	RoutingsPerformed      int64                                    `json:"routings_performed"`
	AvgParticipantsPerMode map[photonic.PolaritonModeType]float64   `json:"avg_participants_per_mode"`
	AvgRoutingTimeMs       float64                                  `json:"avg_routing_time_ms"`
	PrivacyBudgetConsumed  float64                                  `json:"privacy_budget_consumed"`
	ZKVerificationsPassed  int64                                    `json:"zk_verifications_passed"`
	ModeDistribution       map[photonic.PolaritonModeType]int       `json:"mode_distribution"`
}

// NewEncryptedPolaritonRouter cria novo roteador com privacidade preservada para polaritons
func NewEncryptedPolaritonRouter(
	config EncryptedPolaritonRoutingConfig,
) (*EncryptedPolaritonRouter, error) {
	// Configurar valores padrão
	if config.MinParticipantsPerMode == nil {
		config.MinParticipantsPerMode = map[photonic.PolaritonModeType]int{
			photonic.ModePhononPolariton:  3,
			photonic.ModePlasmonPolariton: 3,
			photonic.ModeExcitonPolariton: 2,
			photonic.ModeHybridPolariton:  2,
		}
	}
	if config.AggregationTimeout == 0 {
		config.AggregationTimeout = 5 * time.Minute
	}
	if config.NoiseScale == 0 {
		config.NoiseScale = 0.01 // Ruído leve para privacidade diferencial
	}
	if config.DifferentialPrivacyEpsilon == 0 {
		config.DifferentialPrivacyEpsilon = 1.0 // Epsilon padrão
	}
	if config.ModePriorityWeights == nil {
		config.ModePriorityWeights = map[photonic.PolaritonModeType]float64{
			photonic.ModePhononPolariton:  1.0,
			photonic.ModePlasmonPolariton: 1.2,
			photonic.ModeExcitonPolariton: 1.1,
			photonic.ModeHybridPolariton:  1.3,
		}
	}

	// Gerar chaves de agregação para cada modo polaritônico
	aggPubKeys := make(map[photonic.PolaritonModeType]schemes.AggregationPublicKey)
	for mode := range config.MinParticipantsPerMode {
		aggPubKey, err := schemes.GenerateAggregationKeyPairForMode(mode)
		if err != nil {
			return nil, fmt.Errorf("aggregation key generation failed for mode %s: %w", mode, err)
		}
		aggPubKeys[mode] = aggPubKey
	}

	return &EncryptedPolaritonRouter{
		config:                 config,
		aggregationPublicKeys:  aggPubKeys,
		participantKeys:        make(map[string]map[photonic.PolaritonModeType]schemes.ParticipantKey),
		encryptedContributions: make(map[string]map[photonic.PolaritonModeType][]schemes.Ciphertext),
		contributionTimestamps: make(map[string]time.Time),
		resultChannel:          make(chan PolaritonAggregationResult, 10),
		metrics: EncryptedRouterMetrics{
			PrivacyBudgetConsumed:  0.0,
			AvgParticipantsPerMode: make(map[photonic.PolaritonModeType]float64),
			ModeDistribution:       make(map[photonic.PolaritonModeType]int),
		},
	}, nil
}

// RegisterParticipant registra participante para roteamento federado criptografado
func (r *EncryptedPolaritonRouter) RegisterParticipant(
	participantID string,
	participantKeys map[photonic.PolaritonModeType]schemes.ParticipantKey,
) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.participantKeys[participantID] = participantKeys
	return nil
}

// SubmitEncryptedContribution submete contribuição criptografada para roteamento polaritônico
func (r *EncryptedPolaritonRouter) SubmitEncryptedContribution(
	participantID string,
	routingID string,
	encryptedContributions map[photonic.PolaritonModeType]schemes.Ciphertext,
	polaritonMetadata map[string]interface{}, // Metadados públicos não-sensíveis
) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	// Verificar se participante registrado
	participantKeys, ok := r.participantKeys[participantID]
	if !ok {
		return fmt.Errorf("unregistered participant: %s", participantID)
	}

	// Verificar chaves para cada modo contribuído
	for mode := range encryptedContributions {
		if _, keyExists := participantKeys[mode]; !keyExists {
			return fmt.Errorf("participant %s lacks key for mode %s", participantID, mode)
		}
	}

	// Armazenar contribuições por modo
	if _, exists := r.encryptedContributions[routingID]; !exists {
		r.encryptedContributions[routingID] = make(map[photonic.PolaritonModeType][]schemes.Ciphertext)
	}

	for mode, ciphertext := range encryptedContributions {
		r.encryptedContributions[routingID][mode] = append(
			r.encryptedContributions[routingID][mode],
			ciphertext,
		)
	}
	r.contributionTimestamps[routingID] = time.Now()

	return nil
}

// AggregateContributions executa agregação segura das contribuições recebidas por modo polaritônico
func (r *EncryptedPolaritonRouter) AggregateContributions(
	routingID string,
) (*PolaritonAggregationResult, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	startTime := time.Now()

	// Coletar contribuições para este routingID por modo
	aggregatedValues := make(map[photonic.PolaritonModeType]schemes.Ciphertext)
	participantCounts := make(map[photonic.PolaritonModeType]int)
	noiseMagnitudes := make(map[photonic.PolaritonModeType]float64)

	for mode, minParticipants := range r.config.MinParticipantsPerMode {
		contributions, exists := r.encryptedContributions[routingID][mode]
		if !exists || len(contributions) < minParticipants {
			return nil, fmt.Errorf("insufficient participants for mode %s: %d < %d",
				mode, len(contributions), minParticipants)
		}

		// Executar agregação segura para este modo: soma homomórfica + ruído diferencial
		aggregatedCiphertext, noiseAdded, err := r.secureAggregateByMode(
			mode, contributions, r.config.ModePriorityWeights[mode],
		)
		if err != nil {
			return nil, fmt.Errorf("secure aggregation failed for mode %s: %w", mode, err)
		}

		// Calcular valor médio (divisão homomórfica ou decriptação controlada)
		avgCiphertext, err := r.aggregationPublicKeys[mode].DivideByScalar(
			aggregatedCiphertext,
			float64(len(contributions)),
		)
		if err != nil {
			return nil, fmt.Errorf("averaging failed for mode %s: %w", mode, err)
		}

		aggregatedValues[mode] = avgCiphertext
		participantCounts[mode] = len(contributions)
		noiseMagnitudes[mode] = noiseAdded

		// Atualizar métricas de distribuição de modos
		r.metrics.ModeDistribution[mode] += len(contributions)
	}

	// Gerar provas zero-knowledge por modo se habilitado
	zkProofs := make(map[photonic.PolaritonModeType][]byte)
	if r.config.EnableZKVerification {
		for mode := range aggregatedValues {
			zkProof, err := r.generateZKProofForMode(
				routingID, mode, participantCounts[mode], aggregatedValues[mode],
			)
			if err != nil {
				return nil, fmt.Errorf("zk proof generation failed for mode %s: %w", mode, err)
			}
			zkProofs[mode] = zkProof
			r.metrics.ZKVerificationsPassed++
		}
	}

	// Atualizar orçamento de privacidade
	r.metrics.PrivacyBudgetConsumed += r.config.DifferentialPrivacyEpsilon * float64(len(aggregatedValues))

	// Atualizar métricas de tempo e participantes
	elapsed := time.Since(startTime).Milliseconds()
	r.metrics.RoutingsPerformed++
	n := r.metrics.RoutingsPerformed
	oldAvg := r.metrics.AvgRoutingTimeMs
	r.metrics.AvgRoutingTimeMs = (oldAvg*float64(n-1) + float64(elapsed)) / float64(n)

	for mode, count := range participantCounts {
		oldAvgMode := r.metrics.AvgParticipantsPerMode[mode]
		r.metrics.AvgParticipantsPerMode[mode] = (oldAvgMode*float64(n-1) + float64(count)) / float64(n)
	}

	result := &PolaritonAggregationResult{
		ResultID:          fmt.Sprintf("pol_agg_%s_%d", routingID[:8], time.Now().UnixNano()),
		AggregatedValues:  aggregatedValues,
		ParticipantCounts: participantCounts,
		PrivacyGuarantee:  fmt.Sprintf("differential_privacy_epsilon_%.2f", r.config.DifferentialPrivacyEpsilon),
		Timestamp:         time.Now(),
		ZKProofs:          zkProofs,
		NoiseMagnitudes:   noiseMagnitudes,
	}

	// Enviar para canal de resultados
	select {
	case r.resultChannel <- *result:
	default:
		// Canal cheio: logar mas não bloquear
	}

	return result, nil
}

// secureAggregateByMode executa agregação segura para um modo polaritônico específico
func (r *EncryptedPolaritonRouter) secureAggregateByMode(
	mode photonic.PolaritonModeType,
	contributions []schemes.Ciphertext,
	modeWeight float64,
) (schemes.Ciphertext, float64, error) {
	if len(contributions) == 0 {
		return nil, 0, fmt.Errorf("no contributions to aggregate for mode %s", mode)
	}

	// Somar contribuições homomorficamente com peso do modo
	result := contributions[0]
	for i := 1; i < len(contributions); i++ {
		// Aplicar peso do modo à contribuição
		weighted, err := contributions[i].MultiplyByScalar(modeWeight)
		if err != nil {
			return nil, 0, fmt.Errorf("homomorphic weighting failed for mode %s: %w", mode, err)
		}

		result, err = r.aggregationPublicKeys[mode].Add(result, weighted)
		if err != nil {
			return nil, 0, fmt.Errorf("homomorphic addition failed for mode %s: %w", mode, err)
		}
	}

	// Adicionar ruído diferencial para privacidade adicional
	noiseMagnitude := 0.0
	if r.config.DifferentialPrivacyEpsilon > 0 {
		noise, err := r.generatePolaritonDifferentialPrivacyNoise(
			mode, r.config.NoiseScale, r.config.DifferentialPrivacyEpsilon,
		)
		if err != nil {
			return nil, 0, fmt.Errorf("noise generation failed for mode %s: %w", mode, err)
		}
		noiseMagnitude = schemes.CiphertextMagnitude(noise)
		result, err = r.aggregationPublicKeys[mode].Add(result, noise)
		if err != nil {
			return nil, 0, fmt.Errorf("noise addition failed for mode %s: %w", mode, err)
		}
	}

	return result, noiseMagnitude, nil
}

// generatePolaritonDifferentialPrivacyNoise gera ruído Laplace adaptado para modos polaritônicos
func (r *EncryptedPolaritonRouter) generatePolaritonDifferentialPrivacyNoise(
	mode photonic.PolaritonModeType,
	scale float64,
	epsilon float64,
) (schemes.Ciphertext, error) {
	// Amostrar de distribuição Laplace(0, scale/epsilon) adaptada ao modo
	u1 := randFloat()
	if u1 == 0.5 {
		u1 = 0.5001
	}
	laplaceSample := -(scale / epsilon) * math.Copysign(1, randFloat()-0.5) * math.Log(1-2*math.Abs(u1-0.5))

	// Converter para plaintext FHE apropriado ao modo
	schemeType := r.paramsForMode(mode).SchemeType
	plaintext, err := polaritonValueToPlaintext([]complex128{complex(laplaceSample, 0)}, schemeType, mode)
	if err != nil {
		return nil, err
	}

	return r.aggregationPublicKeys[mode].Encrypt(plaintext)
}

// generateZKProofForMode gera prova zero-knowledge de agregação correta para um modo polaritônico
func (r *EncryptedPolaritonRouter) generateZKProofForMode(
	routingID string,
	mode photonic.PolaritonModeType,
	participantCount int,
	result schemes.Ciphertext,
) ([]byte, error) {
	// Em produção: usar zk-SNARKs adaptados para estruturas polaritônicas para provar:
	// 1. Cada contribuição foi criptografada corretamente com esquema do modo
	// 2. A agregação foi computada corretamente sobre ciphertexts do modo
	// 3. O ruído diferencial foi aplicado conforme especificado para o modo

	// Simplificação: hash dos inputs + resultado como "prova" simulada
	proofData := fmt.Sprintf("%s:%s:%d:%x",
		routingID,
		mode,
		participantCount,
		hashCiphertextRouter(result),
	)

	sum := sha256.Sum256([]byte(proofData))
	return sum[:32], nil
}

// GetAggregationResult recupera resultado de agregação pelo ID
func (r *EncryptedPolaritonRouter) GetAggregationResult(
	resultID string,
) (*PolaritonAggregationResult, bool) {
	// Em produção: buscar em armazenamento persistente
	// Aqui: simplificação com canal
	select {
	case result := <-r.resultChannel:
		if result.ResultID == resultID {
			return &result, true
		}
		// Re-enfileirar se não for o resultado procurado
		go func() { r.resultChannel <- result }()
	case <-time.After(100 * time.Millisecond):
		// Timeout curto para não bloquear
	}
	return nil, false
}

// GetRouterMetrics retorna métricas consolidadas do roteador criptografado
func (r *EncryptedPolaritonRouter) GetRouterMetrics() EncryptedRouterMetrics {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.metrics
}

// Helper functions
func (r *EncryptedPolaritonRouter) paramsForMode(mode photonic.PolaritonModeType) PolaritonFHEParams {
	// Retornar parâmetros FHE padrão para o modo (em produção: buscar de configuração)
	defaultParams := map[photonic.PolaritonModeType]PolaritonFHEParams{
		photonic.ModePhononPolariton: {
			SchemeType: "BFV", PolyModulusDegree: 4096, SecurityLevel: 128,
		},
		photonic.ModeExcitonPolariton: {
			SchemeType: "CKKS", PolyModulusDegree: 8192, SecurityLevel: 128, ScalingFactor: math.Pow(2, 40),
		},
	}
	return defaultParams[mode]
}

func hashCiphertextRouter(ct schemes.Ciphertext) []byte {
	// Hash simplificado do ciphertext para prova
	data, _ := json.Marshal(ct)
	sum := sha256.Sum256(data)
	return sum[:]
}

func randFloat() float64 {
	return float64(time.Now().UnixNano()%10000) / 10000.0
}
