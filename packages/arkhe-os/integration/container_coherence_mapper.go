package integration

import (
	"math"
	"strings"
	"sync"
	"time"

	"arkhe/ai"
	"arkhe/parser/lfir"
)

// ContainerCoherenceMapper mapea containers e pods para gradientes de coerência efêmera
type ContainerCoherenceMapper struct {
	mu sync.RWMutex

	// Configuração
	config ContainerCoherenceConfig

	// Cache de containers processados
	processedContainers map[string]bool

	// Canal de gradientes para submissão
	gradientChannel *ai.CoherenceGradientChannel

	// Métricas de mapeamento
	metrics MapperMetrics

	// Modelo de coerência efêmera aprendido
	ephemeralCoherenceModel EphemeralCoherenceModel
}

// ContainerCoherenceConfig contém configuração para mapeamento container→Coerência
type ContainerCoherenceConfig struct {
	EnableAutoSubmission    bool
	WeightPerReplica        float64 // Peso por réplica em deployment
	WeightForHealthProbes   float64 // Bonus por probes de saúde
	WeightForResourceLimits float64 // Peso por limites de recursos definidos
	PenaltyForHighErrorRate float64 // Penalidade por alta taxa de erros em logs
	MinCoherenceDelta       float64 // Delta mínimo para submissão
	EphemeralDecayFactor    float64 // Fator de decaimento por idade do pod
}

// EphemeralCoherenceModel representa modelo aprendido de coerência efêmera
type EphemeralCoherenceModel struct {
	Trained            bool
	PlatformEfficiency map[string]float64 // kubernetes: 0.92, docker: 0.88, etc.
	AveragePodLifetime time.Duration      // Tempo médio de vida de pods
	LastUpdated        time.Time
}

// MapperMetrics contém métricas do mapeador de containers
type MapperMetrics struct {
	ContainersProcessed   int64   `json:"containers_processed"`
	PodsProcessed         int64   `json:"pods_processed"`
	ServicesProcessed     int64   `json:"services_processed"`
	GradientsSubmitted    int64   `json:"gradients_submitted"`
	AvgEphemeralCoherence float64 `json:"avg_ephemeral_coherence"`
	HighErrorRateDetected int64   `json:"high_error_rate_detected"`
	HealthyPodsPromoted   int64   `json:"healthy_pods_promoted"`
}

// NewContainerCoherenceMapper cria novo mapeador de containers para coerência efêmera
func NewContainerCoherenceMapper(
	config ContainerCoherenceConfig,
	gradientChannel *ai.CoherenceGradientChannel,
) *ContainerCoherenceMapper {
	if config.WeightPerReplica == 0 {
		config.WeightPerReplica = 0.01
	}
	if config.WeightForHealthProbes == 0 {
		config.WeightForHealthProbes = 0.03
	}
	if config.WeightForResourceLimits == 0 {
		config.WeightForResourceLimits = 0.02
	}
	if config.PenaltyForHighErrorRate == 0 {
		config.PenaltyForHighErrorRate = 0.05
	}
	if config.EphemeralDecayFactor == 0 {
		config.EphemeralDecayFactor = 0.01
	}

	return &ContainerCoherenceMapper{
		config:              config,
		processedContainers: make(map[string]bool),
		gradientChannel:     gradientChannel,
		ephemeralCoherenceModel: EphemeralCoherenceModel{
			PlatformEfficiency: map[string]float64{
				"kubernetes": 0.92,
				"docker":     0.88,
				"nomad":      0.85,
			},
			AveragePodLifetime: 30 * time.Minute,
		},
	}
}

// ProcessLFIRGraph processa grafo LFIR de containerização e submete containers como gradientes
func (m *ContainerCoherenceMapper) ProcessLFIRGraph(graph *lfir.LFIRGraph) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	containersSubmitted := 0

	for _, node := range graph.Nodes {
		if node.Attributes["type"] == nil {
			continue
		}

		resourceType, ok := node.Attributes["type"].(string)
		if !ok {
			continue
		}

		containerID := node.ID
		if m.processedContainers[containerID] {
			continue
		}

		// Calcular gradiente de coerência baseado no tipo de recurso
		var gradient float64
		var metadata map[string]interface{}

		switch resourceType {
		case "pod":
			gradient, metadata = m.computePodCoherenceGradient(node)
			m.metrics.PodsProcessed++
		case "service":
			gradient, metadata = m.computeServiceCoherenceGradient(node)
			m.metrics.ServicesProcessed++
		case "deployment":
			gradient, metadata = m.computeDeploymentCoherenceGradient(node)
		case "dockerfile":
			gradient, metadata = m.computeDockerfileCoherenceGradient(node)
		case "container_log":
			gradient, metadata = m.computeLogCoherenceGradient(node)
		default:
			continue
		}

		// Submeter ao canal de coerência se habilitado e delta significativo
		if m.config.EnableAutoSubmission && math.Abs(gradient) >= m.config.MinCoherenceDelta {
			if err := m.submitGradient(containerID, gradient, metadata); err != nil {
				continue
			}
			containersSubmitted++
			m.metrics.GradientsSubmitted++
		}

		// Atualizar métricas
		m.metrics.ContainersProcessed++
		m.metrics.AvgEphemeralCoherence = m.metrics.AvgEphemeralCoherence*0.99 + math.Abs(gradient)*0.01

		// Detectar pods com alta taxa de erro
		if errorRate, ok := metadata["error_rate"].(float64); ok && errorRate > 0.1 {
			m.metrics.HighErrorRateDetected++
		}

		// Detectar pods saudáveis para promoção
		if coherence, ok := metadata["ephemeral_coherence"].(float64); ok && coherence > 0.8 {
			m.metrics.HealthyPodsPromoted++
		}

		m.processedContainers[containerID] = true
	}

	return nil
}

// computePodCoherenceGradient calcula contribuição de coerência de um pod
func (m *ContainerCoherenceMapper) computePodCoherenceGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"resource_type": "pod",
		"pod_name":      node.Name,
		"namespace":     node.Attributes["namespace"],
	}

	// Coerência efêmera base
	baseCoherence := 0.65
	if estimated, ok := node.Attributes["ephemeral_coherence"].(float64); ok {
		baseCoherence = estimated
	}

	// Bonus por probes de saúde
	if hasLiveness, ok := node.Attributes["has_liveness_probe"].(bool); ok && hasLiveness {
		gradient += m.config.WeightForHealthProbes
	}
	if hasReadiness, ok := node.Attributes["has_readiness_probe"].(bool); ok && hasReadiness {
		gradient += m.config.WeightForHealthProbes * 0.5
	}

	// Bonus por limites de recursos bem definidos
	if _, hasCPU := node.Attributes["cpu_request"]; hasCPU {
		gradient += m.config.WeightForResourceLimits
	}
	if _, hasMem := node.Attributes["memory_request"]; hasMem {
		gradient += m.config.WeightForResourceLimits * 0.5
	}

	// Penalidade por alta taxa de erros em logs associados
	if errorRate, ok := node.Attributes["error_rate"].(float64); ok {
		if errorRate > 0.1 {
			gradient -= m.config.PenaltyForHighErrorRate
		}
	}

	// Fator de decaimento efêmero baseado em idade
	if ageMinutes, ok := node.Attributes["age_minutes"].(float64); ok {
		decay := math.Exp(-m.config.EphemeralDecayFactor * ageMinutes)
		gradient *= decay
		metadata["ephemeral_decay"] = decay
	}

	// Ajuste por eficiência do orquestrador
	if platform, ok := node.Attributes["platform"].(string); ok {
		if efficiency, exists := m.ephemeralCoherenceModel.PlatformEfficiency[platform]; exists {
			gradient *= efficiency
			metadata["platform_efficiency"] = efficiency
		}
	}

	metadata["ephemeral_coherence"] = baseCoherence + gradient
	metadata["coherence_sign"] = "positive"
	if gradient < 0 {
		metadata["coherence_sign"] = "negative"
	}

	return gradient, metadata
}

// computeServiceCoherenceGradient calcula contribuição de coerência de um service
func (m *ContainerCoherenceMapper) computeServiceCoherenceGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"resource_type": "service",
		"service_name":  node.Name,
		"namespace":     node.Attributes["namespace"],
	}

	// Services atuam como sinapses: conectividade é chave
	if connectivity, ok := node.Attributes["synapse_connectivity"].(float64); ok {
		gradient += connectivity * 0.05
	}

	// Bonus por estabilidade de sessão
	if stability, ok := node.Attributes["synapse_stability"].(float64); ok {
		gradient += stability * 0.03
	}

	// Bonus por tipo de service mais robusto
	if serviceType, ok := node.Attributes["service_type"].(string); ok {
		switch serviceType {
		case "LoadBalancer":
			gradient += 0.02
		case "ClusterIP":
			gradient += 0.01
		}
	}

	metadata["coherence_delta"] = gradient
	metadata["coherence_sign"] = "positive"
	if gradient < 0 {
		metadata["coherence_sign"] = "negative"
	}

	return gradient, metadata
}

// computeDeploymentCoherenceGradient calcula contribuição de coerência de um deployment
func (m *ContainerCoherenceMapper) computeDeploymentCoherenceGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"resource_type":   "deployment",
		"deployment_name": node.Name,
		"namespace":       node.Attributes["namespace"],
	}

	// Bonus por múltiplas réplicas (resiliência)
	if replicas, ok := node.Attributes["replicas"].(int); ok {
		gradient += m.config.WeightPerReplica * float64(replicas)
		metadata["replica_bonus"] = m.config.WeightPerReplica * float64(replicas)
	}

	// Bonus por estratégia de rollout eficiente
	if strategy, ok := node.Attributes["strategy"].(string); ok {
		switch strategy {
		case "RollingUpdate":
			gradient += 0.02
		case "BlueGreen":
			gradient += 0.03
		}
	}

	// Coerência coletiva do deployment
	if collectiveCoherence, ok := node.Attributes["collective_coherence"].(float64); ok {
		gradient += collectiveCoherence * 0.02
	}

	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// computeDockerfileCoherenceGradient calcula contribuição de coerência de um Dockerfile
func (m *ContainerCoherenceMapper) computeDockerfileCoherenceGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"resource_type": "dockerfile",
	}

	// Imagens bem construídas contribuem para coerência do ecossistema
	if imageCoherence, ok := node.Attributes["image_coherence"].(float64); ok {
		gradient += imageCoherence * 0.01
	}

	// Bonus por base image mínima
	if baseImage, ok := node.Attributes["base_image"].(string); ok {
		if strings.Contains(baseImage, "alpine") || strings.Contains(baseImage, "distroless") {
			gradient += 0.01
		}
	}

	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// computeLogCoherenceGradient calcula contribuição de coerência de logs de container
func (m *ContainerCoherenceMapper) computeLogCoherenceGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"resource_type": "container_log",
	}

	// Logs estáveis contribuem positivamente
	if stability, ok := node.Attributes["stability_indicator"].(string); ok {
		switch stability {
		case "stable":
			gradient += 0.02
		case "moderate":
			gradient += 0.005
		case "unstable":
			gradient -= 0.02
		}
	}

	// Penalidade por alta taxa de erros
	if errorCount, ok := node.Attributes["error_count"].(int); ok {
		if totalLines, ok := node.Attributes["total_lines"].(int); ok && totalLines > 0 {
			errorRate := float64(errorCount) / float64(totalLines)
			metadata["error_rate"] = errorRate
			if errorRate > 0.1 {
				gradient -= m.config.PenaltyForHighErrorRate
			}
		}
	}

	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// submitGradient submete gradiente de coerência efêmera ao canal
func (m *ContainerCoherenceMapper) submitGradient(
	containerID string,
	coherenceDelta float64,
	metadata map[string]interface{},
) error {
	// Preparar metadados para o gradiente
	gradientMetadata := map[string]interface{}{
		"source":           "containerization_layer",
		"container_id":     containerID,
		"timestamp":        time.Now().Unix(),
		"coherence_sign":   metadata["coherence_sign"],
		"ephemeral_factor": true,
	}
	for k, v := range metadata {
		gradientMetadata[k] = v
	}

	// Converter delta de coerência para vetor de gradiente
	gradientVector := []float64{coherenceDelta}

	// Calcular "coerência" do container como confiança na contribuição efêmera
	coherenceValue := 0.6 + 0.4*math.Abs(coherenceDelta) // Faixa mais baixa para efêmeros

	// Submeter ao canal
	_, err := m.gradientChannel.SubmitLocalGradient(
		gradientVector,
		coherenceValue,
		0.7, // distância conceitual maior para infraestrutura efêmera
		1,   // sample count
		0.0, // loss value (N/A para containers)
		gradientMetadata,
	)

	return err
}

// GetMapperMetrics retorna métricas consolidadas do mapeador de containers
func (m *ContainerCoherenceMapper) GetMapperMetrics() MapperMetrics {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.metrics
}
