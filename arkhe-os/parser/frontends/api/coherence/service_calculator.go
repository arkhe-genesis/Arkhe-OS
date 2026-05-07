package coherence

import (
	"arkhe/parser/frontends/api/models"
)

// CalculateServiceCoherence evaluates how "coherent" the API is
// Metrics: Consistency, Security Cover, Resource matching
func CalculateServiceCoherence(api *models.APIInfrastructure) float64 {
	if len(api.Endpoints) == 0 {
		return 0.0
	}

	secureEndpoints := 0
	for _, ep := range api.Endpoints {
		if ep.RequiresAuth {
			secureEndpoints++
		}
	}

	securityRatio := float64(secureEndpoints) / float64(len(api.Endpoints))

	// Simplified formula for demo
	coherence := (securityRatio * 0.5) + 0.5
	return coherence
	"math"

    "arkhe/parser/frontends/api/models"
)

// ServiceMetrics acumula métricas para cálculo de coerência de serviço
type ServiceMetrics struct {
	ContractClarity    float64 // Clareza do contrato de API (0-1)
	ProtocolConsistency float64 // Consistência com protocolo declarado (0-1)
	AuthCoverage       float64 // Cobertura de autenticação (0-1)
	ResilienceAdequacy float64 // Adequação de padrões de resiliência (0-1)
	AmbiguityPenalty   float64 // Penalidade por ambiguidade (0-1, menor é melhor)

	// Detalhes para debugging
	UnderspecifiedParams int
	MissingErrorCodes   int
	ProtocolMismatches  int
	UnauthEndpoints     int
	UnresilientEndpoints int
}

// APIAnalysis acumula métricas para sistema de API completo
type APIAnalysis struct {
	SystemName              string
	Services                map[string]*ServiceMetrics
	AvgContractClarity      float64
	ProtocolConsistency     float64
	AuthCoverage            float64
	ResilienceAdequacy      float64
	DependencyCycles        int
	SinglePointsOfFailure   int

	// Métricas de infraestrutura
	CircuitBreakerCoverage  float64
	RetryPolicyAdequacy     float64
	DataConsistencyScore    float64
	ShardingAdequacy        float64
	ReplicationFactor       float64

	// Contagem de grafo
	TotalNodes              int
	TotalEdges              int
}

// APICoherenceConfig configura pesos para cálculo de coerência de API
type APICoherenceConfig struct {
	ContractClarityWeight    float64 // Peso para clareza de contrato
	ProtocolConsistencyWeight float64 // Peso para consistência de protocolo
	AuthCoverageWeight       float64 // Peso para cobertura de auth
	ResilienceAdequacyWeight float64 // Peso para adequação de resiliência
	AmbiguityPenaltyWeight   float64 // Peso para penalidade de ambiguidade
}

// DefaultAPIConfig retorna configurações padrão
func DefaultAPIConfig() *APICoherenceConfig {
	return &APICoherenceConfig{
		ContractClarityWeight:    0.30,
		ProtocolConsistencyWeight: 0.25,
		AuthCoverageWeight:       0.25,
		ResilienceAdequacyWeight: 0.15,
		AmbiguityPenaltyWeight:   0.05,
	}
}

// CalculateServiceCoherence calcula Φ_C médio para serviços individuais
func CalculateServiceCoherence(services map[string]*ServiceMetrics, cfg *APICoherenceConfig) float64 {
	if len(services) == 0 {
		return 1.0
	}

	sum := 0.0
	for _, metrics := range services {
		score := cfg.ContractClarityWeight*metrics.ContractClarity +
			cfg.ProtocolConsistencyWeight*metrics.ProtocolConsistency +
			cfg.AuthCoverageWeight*metrics.AuthCoverage +
			cfg.ResilienceAdequacyWeight*metrics.ResilienceAdequacy -
			cfg.AmbiguityPenaltyWeight*metrics.AmbiguityPenalty

		sum += math.Max(0.0, math.Min(1.0, score))
	}

	return sum / float64(len(services))
}

// CalculateSystemCoherence calcula Φ_C para sistema de API completo
func CalculateSystemCoherence(spec *models.APISpecification, analysis *APIAnalysis, cfg *APICoherenceConfig) float64 {
	// Coerência de serviço média
	serviceCoherence := CalculateServiceCoherence(analysis.Services, cfg)

	// Fatores de sistema distribuído
	cycleFactor := math.Exp(-0.5 * float64(analysis.DependencyCycles))
	spofFactor := 1.0 - float64(analysis.SinglePointsOfFailure)/math.Max(1, float64(len(spec.Services)))

	// Fatores de infraestrutura
	infraFactor := 1.0
	if spec.Infrastructure != nil {
		// Penalizar por baixa cobertura de circuit breaker em serviços críticos
		cbPenalty := 0.0
		if analysis.CircuitBreakerCoverage < 0.8 {
			cbPenalty = (0.8 - analysis.CircuitBreakerCoverage) * 0.2
		}
		infraFactor = 1.0 - cbPenalty
	}

	// Combinação
	systemCoherence := serviceCoherence * cycleFactor * spofFactor * infraFactor

	return math.Max(0.0, math.Min(1.0, systemCoherence))
}

// CalculateInfrastructureCoherence calcula Φ_C para componentes de infraestrutura
func CalculateInfrastructureCoherence(infra *models.InfrastructureSpec, cfg *APICoherenceConfig) float64 {
	if infra == nil || len(infra.Components) == 0 {
		return 0.5 // Neutro se sem infra definida
	}

	// Calcular adequação de padrões por tipo de componente
	patternScores := make(map[models.ComponentType]float64)

	for _, comp := range infra.Components {
		score := calculateComponentCoherence(comp)
		patternScores[comp.Type] = math.Max(patternScores[comp.Type], score)
	}

	// Média ponderada por criticidade
	weightedSum := 0.0
	totalWeight := 0.0

	for compType, score := range patternScores {
		weight := getComponentCriticality(compType)
		weightedSum += weight * score
		totalWeight += weight
	}

	if totalWeight == 0 {
		return 0.5
	}

	return weightedSum / totalWeight
}

func calculateComponentCoherence(comp models.InfrastructureComponent) float64 {
	score := 1.0

	// Penalizar por falta de health check em componentes críticos
	if isCriticalComponent(comp.Type) && comp.HealthCheck == nil {
		score -= 0.2
	}

	// Penalizar por réplicas insuficientes em componentes stateful
	if isStatefulComponent(comp.Type) && comp.Replicas < 2 {
		score -= 0.15
	}

	// Verificar configuração específica por tipo
	switch comp.Type {
	case models.TypeCache:
		if pattern, ok := comp.Config["pattern"].(map[string]interface{}); ok {
			if pattern["type"] == nil {
				score -= 0.1 // Pattern de cache não especificado
			}
		}
	case models.TypeQueue:
		if pattern, ok := comp.Config["pattern"].(map[string]interface{}); ok {
			if pattern["delivery_guarantee"] == nil {
				score -= 0.1 // Garantia de entrega não especificada
			}
		}
	case models.TypeDatabase:
		if strategy, ok := comp.Config["data_strategy"].(map[string]interface{}); ok {
			if strategy["consistency_model"] == nil {
				score -= 0.15 // Modelo de consistência não especificado
			}
		}
	case models.TypeCircuitBreaker:
		if cfg, ok := comp.Config["circuit_breaker"].(map[string]interface{}); ok {
			if cfg["failure_threshold"] == nil || cfg["timeout"] == nil {
				score -= 0.1 // Configuração incompleta
			}
		}
	}

	return math.Max(0.0, math.Min(1.0, score))
}

func isCriticalComponent(compType models.ComponentType) bool {
	critical := map[models.ComponentType]bool{
		models.TypeDatabase: true, models.TypeAuthServer: true, models.TypeAPIGateway: true,
		models.TypeLoadBalancer: true, models.TypeServiceMesh: true,
	}
	return critical[compType]
}

func isStatefulComponent(compType models.ComponentType) bool {
	stateful := map[models.ComponentType]bool{
		models.TypeDatabase: true, models.TypeCache: true, models.TypeQueue: true, models.TypeStream: true,
	}
	return stateful[compType]
}

func getComponentCriticality(compType models.ComponentType) float64 {
	criticality := map[models.ComponentType]float64{
		models.TypeDatabase: 1.0, models.TypeAuthServer: 1.0, models.TypeAPIGateway: 0.9,
		models.TypeLoadBalancer: 0.9, models.TypeServiceMesh: 0.8, models.TypeCache: 0.7,
		models.TypeQueue: 0.7, models.TypeStream: 0.7, models.TypeCDN: 0.5,
		models.TypeMetrics: 0.4, models.TypeLogs: 0.4, models.TypeTracing: 0.4,
	}
	if crit, ok := criticality[compType]; ok {
		return crit
	}
	return 0.5
}
