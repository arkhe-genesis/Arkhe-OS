package frontends

import (
	"encoding/json"
	"fmt"
	"math"
	"regexp"
	"strconv"
	"strings"
	"time"

	"arkhe/parser/lfir"
	"gopkg.in/yaml.v3"
)

// ContainerizationFrontend implementa parsing de Dockerfiles, manifests K8s e logs de containers para LFIR
type ContainerizationFrontend struct {
	platform     string // "kubernetes", "docker", "auto"
	namespace    string
	parserConfig ContainerParserConfig
}

// ContainerParserConfig contém configuração para parsing de containerização
type ContainerParserConfig struct {
	IncludePods        bool
	IncludeServices    bool
	IncludeDeployments bool
	IncludeConfigMaps  bool
	IncludeSecrets     bool
	IncludeLogs        bool
	CoherenceMapping   bool // Mapear containers para gradientes de coerência efêmera
	EphemeralWeighting bool // Aplicar pesos baseados em ciclo de vida
	MaxItemsPerType    int  // Limite de itens por tipo para evitar overload
}

// NewContainerizationFrontend cria novo frontend para parsing de containerização
func NewContainerizationFrontend(platform, namespace string, config ContainerParserConfig) (*ContainerizationFrontend, error) {
	return &ContainerizationFrontend{
		platform:     platform,
		namespace:    namespace,
		parserConfig: config,
	}, nil
}

func (f *ContainerizationFrontend) GetLanguage() string { return f.platform }
func (f *ContainerizationFrontend) GetExtensions() []string {
	return []string{".yaml", ".yml", ".json", ".dockerfile", ".containerlog", ".k8slog"}
}

// Parse processa YAML/JSON de manifests K8s, Dockerfiles ou logs de containers e gera LFIRGraph
func (f *ContainerizationFrontend) Parse(source []byte) (*lfir.LFIRGraph, error) {
	graph := lfir.NewLFIRGraph()
	contextID := fmt.Sprintf("%s/%s", f.platform, f.namespace)
	module := lfir.NewLFIRNode(lfir.LFIRModule, contextID, f.platform)
	graph.AddNode(module)
	graph.RootNodes = append(graph.RootNodes, module.ID)

	content := string(source)

	// Detectar tipo de conteúdo baseado em estrutura
	contentType := detectContainerContentType(content)

	switch contentType {
	case "k8s_pod":
		return f.parseK8sPod(content, graph, module.ID)
	case "k8s_service":
		return f.parseK8sService(content, graph, module.ID)
	case "k8s_deployment":
		return f.parseK8sDeployment(content, graph, module.ID)
	case "k8s_configmap":
		return f.parseGenericManifest(content, graph, module.ID)
	case "dockerfile":
		return f.parseDockerfile(content, graph, module.ID)
	case "container_log":
		return f.parseContainerLog(content, graph, module.ID)
	default:
		// Tentar parse genérico como YAML ou JSON
		return f.parseGenericManifest(content, graph, module.ID)
	}
}

// detectContainerContentType identifica tipo de conteúdo baseado em campos distintivos
func detectContainerContentType(content string) string {
	// Verificar se é YAML/JSON primeiro
	var obj map[string]interface{}

	// Tentar YAML
	if err := yaml.Unmarshal([]byte(content), &obj); err == nil {
		kind, _ := obj["kind"].(string)
		apiVersion, _ := obj["apiVersion"].(string)

		if strings.HasPrefix(apiVersion, "v1") || strings.HasPrefix(apiVersion, "apps/") {
			switch kind {
			case "Pod":
				return "k8s_pod"
			case "Service":
				return "k8s_service"
			case "Deployment", "StatefulSet", "DaemonSet":
				return "k8s_deployment"
			case "ConfigMap":
				return "k8s_configmap"
			case "Secret":
				return "k8s_secret"
			}
		}
	}

	// Tentar JSON
	if err := json.Unmarshal([]byte(content), &obj); err == nil {
		// Mesma lógica para JSON
		kind, _ := obj["kind"].(string)
		if kind == "Pod" {
			return "k8s_pod"
		}
		if kind == "Service" {
			return "k8s_service"
		}
	}

	// Verificar se é Dockerfile
	if strings.HasPrefix(strings.TrimSpace(content), "FROM ") ||
		strings.Contains(content, "RUN ") ||
		strings.Contains(content, "COPY ") {
		return "dockerfile"
	}

	// Verificar se é log de container (padrões típicos)
	if regexp.MustCompile(`\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}`).MatchString(content) ||
		regexp.MustCompile(`\[(INFO|WARN|ERROR|DEBUG)\]`).MatchString(content) {
		return "container_log"
	}

	return "unknown"
}

// parseK8sPod processa manifest de pod Kubernetes
func (f *ContainerizationFrontend) parseK8sPod(content string, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	var pod map[string]interface{}
	if err := yaml.Unmarshal([]byte(content), &pod); err != nil {
		return nil, err
	}

	metadata, _ := pod["metadata"].(map[string]interface{})
	spec, _ := pod["spec"].(map[string]interface{})

	podName, _ := metadata["name"].(string)

	node := lfir.NewLFIRNode(lfir.LFIRType, podName, "kubernetes")
	node.Attributes["type"] = "pod"
	node.Attributes["namespace"] = f.namespace
	node.Attributes["labels"] = stringifyMap(metadata["labels"])
	node.Attributes["annotations"] = stringifyMap(metadata["annotations"])

	// Especificações do pod
	if containers, ok := spec["containers"].([]interface{}); ok {
		var containerNames []string
		for _, c := range containers {
			if container, ok := c.(map[string]interface{}); ok {
				containerNames = append(containerNames, getString(container, "name"))

				// Parsear recursos do container
				if resources, ok := container["resources"].(map[string]interface{}); ok {
					if requests, ok := resources["requests"].(map[string]interface{}); ok {
						node.Attributes["cpu_request"] = getString(requests, "cpu")
						node.Attributes["memory_request"] = getString(requests, "memory")
					}
					if limits, ok := resources["limits"].(map[string]interface{}); ok {
						node.Attributes["cpu_limit"] = getString(limits, "cpu")
						node.Attributes["memory_limit"] = getString(limits, "memory")
					}
				}

				// Parsear probes de saúde
				if _, ok := container["livenessProbe"].(map[string]interface{}); ok {
					node.Attributes["has_liveness_probe"] = true
				}
				if _, ok := container["readinessProbe"].(map[string]interface{}); ok {
					node.Attributes["has_readiness_probe"] = true
				}
			}
		}
		node.Attributes["containers"] = strings.Join(containerNames, ",")
	}

	// Configurações de ciclo de vida
	node.Attributes["restart_policy"] = getString(spec, "restartPolicy", "Always")
	node.Attributes["termination_grace_period"] = getInt(spec, "terminationGracePeriodSeconds", 30)

	// Node affinity e tolerations para mapeamento de coerência
	if _, ok := spec["affinity"].(map[string]interface{}); ok {
		node.Attributes["has_affinity"] = true
	}
	if tolerations, ok := spec["tolerations"].([]interface{}); ok && len(tolerations) > 0 {
		node.Attributes["has_tolerations"] = true
	}

	// Calcular coerência efêmera se habilitado
	if f.parserConfig.CoherenceMapping {
		ephemeralCoherence := computePodEphemeralCoherence(node.Attributes)
		node.Attributes["ephemeral_coherence"] = ephemeralCoherence
		node.Attributes["lifecycle_stage"] = "running" // Simplificado
	}

	node.Attributes["parsed_at"] = time.Now().Unix()

	graph.AddNode(node)
	graph.Link(parentID, node.ID)

	return graph, nil
}

// parseK8sService processa manifest de service Kubernetes
func (f *ContainerizationFrontend) parseK8sService(content string, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	var service map[string]interface{}
	if err := yaml.Unmarshal([]byte(content), &service); err != nil {
		return nil, err
	}

	metadata, _ := service["metadata"].(map[string]interface{})
	spec, _ := service["spec"].(map[string]interface{})

	serviceName, _ := metadata["name"].(string)

	node := lfir.NewLFIRNode(lfir.LFIRType, serviceName, "kubernetes")
	node.Attributes["type"] = "service"
	node.Attributes["namespace"] = f.namespace
	node.Attributes["cluster_ip"] = getString(spec, "clusterIP")
	node.Attributes["service_type"] = getString(spec, "type", "ClusterIP")

	// Portas do service
	if ports, ok := spec["ports"].([]interface{}); ok {
		var portSpecs []string
		for _, p := range ports {
			if port, ok := p.(map[string]interface{}); ok {
				portSpec := fmt.Sprintf("%d/%s", getInt(port, "port", 0), getString(port, "protocol", "TCP"))
				if name, ok := port["name"].(string); ok && name != "" {
					portSpec = fmt.Sprintf("%s:%s", name, portSpec)
				}
				portSpecs = append(portSpecs, portSpec)
			}
		}
		node.Attributes["ports"] = strings.Join(portSpecs, ",")
	}

	// Selector para mapeamento de pods
	if selector, ok := spec["selector"].(map[string]interface{}); ok {
		node.Attributes["selector"] = stringifyMap(selector)
	}

	// Session affinity para coerência de sessão
	node.Attributes["session_affinity"] = getString(spec, "sessionAffinity", "None")

	// External traffic policy
	node.Attributes["external_traffic_policy"] = getString(spec, "externalTrafficPolicy")

	// Calcular métricas de sinapse dinâmica se habilitado
	if f.parserConfig.CoherenceMapping {
		synapseMetrics := computeServiceSynapseMetrics(node.Attributes)
		node.Attributes["synapse_connectivity"] = synapseMetrics.Connectivity
		node.Attributes["synapse_stability"] = synapseMetrics.Stability
	}

	node.Attributes["parsed_at"] = time.Now().Unix()

	graph.AddNode(node)
	graph.Link(parentID, node.ID)

	return graph, nil
}

// parseK8sDeployment processa manifest de deployment Kubernetes
func (f *ContainerizationFrontend) parseK8sDeployment(content string, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	var deployment map[string]interface{}
	if err := yaml.Unmarshal([]byte(content), &deployment); err != nil {
		return nil, err
	}

	metadata, _ := deployment["metadata"].(map[string]interface{})
	spec, _ := deployment["spec"].(map[string]interface{})

	deploymentName, _ := metadata["name"].(string)

	node := lfir.NewLFIRNode(lfir.LFIRModule, deploymentName, "kubernetes")
	node.Attributes["type"] = "deployment"
	node.Attributes["namespace"] = f.namespace
	node.Attributes["replicas"] = getInt(spec, "replicas", 1)
	node.Attributes["strategy"] = getNestedString(spec, "strategy", "type", "RollingUpdate")

	// Template do pod para herança de atributos
	if template, ok := spec["template"].(map[string]interface{}); ok {
		if templateSpec, ok := template["spec"].(map[string]interface{}); ok {
			if containers, ok := templateSpec["containers"].([]interface{}); ok && len(containers) > 0 {
				if container, ok := containers[0].(map[string]interface{}); ok {
					node.Attributes["container_image"] = getString(container, "image")
				}
			}
		}
	}

	// Métricas de orquestração para coerência coletiva
	if f.parserConfig.CoherenceMapping {
		orchestrationMetrics := computeDeploymentOrchestrationMetrics(node.Attributes)
		node.Attributes["orchestration_efficiency"] = orchestrationMetrics.Efficiency
		node.Attributes["collective_coherence"] = orchestrationMetrics.CollectiveCoherence
	}

	node.Attributes["parsed_at"] = time.Now().Unix()

	graph.AddNode(node)
	graph.Link(parentID, node.ID)

	return graph, nil
}

// parseDockerfile processa Dockerfile para LFIR
func (f *ContainerizationFrontend) parseDockerfile(content string, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	lines := strings.Split(content, "\n")

	dockerfileNode := lfir.NewLFIRNode(lfir.LFIRModule, "dockerfile", "docker")
	dockerfileNode.Attributes["type"] = "dockerfile"
	dockerfileNode.Attributes["parsed_at"] = time.Now().Unix()

	graph.AddNode(dockerfileNode)
	graph.Link(parentID, dockerfileNode.ID)

	var stages []string
	var baseImage string
	var exposedPorts []string
	var envVars []string

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		upper := strings.ToUpper(line)

		if strings.HasPrefix(upper, "FROM ") {
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				baseImage = parts[1]
				stages = append(stages, fmt.Sprintf("stage:%s", baseImage))
			}
		} else if strings.HasPrefix(upper, "EXPOSE ") {
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				exposedPorts = append(exposedPorts, parts[1])
			}
		} else if strings.HasPrefix(upper, "ENV ") {
			envVars = append(envVars, strings.TrimPrefix(line, "ENV "))
		} else if strings.HasPrefix(upper, "RUN ") || strings.HasPrefix(upper, "COPY ") || strings.HasPrefix(upper, "ADD ") {
			// Instruções de construção
			stages = append(stages, strings.ToLower(strings.Fields(line)[0]))
		}
	}

	if baseImage != "" {
		dockerfileNode.Attributes["base_image"] = baseImage
	}
	if len(exposedPorts) > 0 {
		dockerfileNode.Attributes["exposed_ports"] = strings.Join(exposedPorts, ",")
	}
	if len(envVars) > 0 {
		dockerfileNode.Attributes["env_vars_count"] = len(envVars)
	}
	if len(stages) > 0 {
		dockerfileNode.Attributes["build_stages"] = strings.Join(stages, ",")
	}

	// Calcular coerência de imagem se habilitado
	if f.parserConfig.CoherenceMapping {
		imageCoherence := computeDockerfileCoherence(dockerfileNode.Attributes)
		dockerfileNode.Attributes["image_coherence"] = imageCoherence
	}

	return graph, nil
}

// parseContainerLog processa logs de container para LFIR
func (f *ContainerizationFrontend) parseContainerLog(content string, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	lines := strings.Split(content, "\n")

	logNode := lfir.NewLFIRNode(lfir.LFIRMetadata, "container_log", "container")
	logNode.Attributes["type"] = "container_log"
	logNode.Attributes["parsed_at"] = time.Now().Unix()

	graph.AddNode(logNode)
	graph.Link(parentID, logNode.ID)

	// Analisar padrões de ciclo de vida nos logs
	var lifecycleEvents []string
	var errorCount, warnCount, infoCount int
	var startupDetected, shutdownDetected bool

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// Contar níveis de log
		if strings.Contains(strings.ToUpper(line), "ERROR") {
			errorCount++
		} else if strings.Contains(strings.ToUpper(line), "WARN") {
			warnCount++
		} else if strings.Contains(strings.ToUpper(line), "INFO") {
			infoCount++
		}

		// Detectar eventos de ciclo de vida
		if regexp.MustCompile(`(?i)(starting|started|initialized|ready)`).MatchString(line) {
			startupDetected = true
			lifecycleEvents = append(lifecycleEvents, "startup")
		}
		if regexp.MustCompile(`(?i)(stopping|stopped|terminated|shutdown)`).MatchString(line) {
			shutdownDetected = true
			lifecycleEvents = append(lifecycleEvents, "shutdown")
		}
		if regexp.MustCompile(`(?i)(health.?check|liveness|readiness)`).MatchString(line) {
			lifecycleEvents = append(lifecycleEvents, "health_check")
		}
	}

	logNode.Attributes["total_lines"] = len(lines)
	logNode.Attributes["error_count"] = errorCount
	logNode.Attributes["warn_count"] = warnCount
	logNode.Attributes["info_count"] = infoCount
	logNode.Attributes["lifecycle_events"] = strings.Join(uniqueStrings(lifecycleEvents), ",")
	logNode.Attributes["has_startup"] = startupDetected
	logNode.Attributes["has_shutdown"] = shutdownDetected

	// Calcular coerência baseada em padrões de log se habilitado
	if f.parserConfig.CoherenceMapping {
		logCoherence := computeLogCoherence(logNode.Attributes)
		logNode.Attributes["log_coherence"] = logCoherence
		logNode.Attributes["stability_indicator"] = computeStabilityIndicator(errorCount, warnCount, infoCount)
	}

	return graph, nil
}

// parseGenericManifest tenta parse genérico para manifests não identificados
func (f *ContainerizationFrontend) parseGenericManifest(content string, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	// Tentar YAML primeiro
	var obj map[string]interface{}
	if err := yaml.Unmarshal([]byte(content), &obj); err == nil {
		return f.parseK8sGeneric(obj, graph, parentID)
	}

	// Tentar JSON
	if err := json.Unmarshal([]byte(content), &obj); err == nil {
		return f.parseK8sGeneric(obj, graph, parentID)
	}

	return nil, fmt.Errorf("unrecognized container manifest format")
}

// parseK8sGeneric processa manifest K8s genérico
func (f *ContainerizationFrontend) parseK8sGeneric(obj map[string]interface{}, graph *lfir.LFIRGraph, parentID string) (*lfir.LFIRGraph, error) {
	kind, _ := obj["kind"].(string)
	metadata, _ := obj["metadata"].(map[string]interface{})
	name, _ := metadata["name"].(string)

	node := lfir.NewLFIRNode(lfir.LFIRType, name, "kubernetes")
	node.Attributes["type"] = strings.ToLower(kind)
	node.Attributes["kind"] = kind
	node.Attributes["namespace"] = getString(metadata, "namespace", f.namespace)
	node.Attributes["labels"] = stringifyMap(metadata["labels"])

	// Copiar campos relevantes
	for k, v := range obj {
		if k != "kind" && k != "apiVersion" && k != "metadata" && k != "spec" && k != "status" {
			node.Attributes[k] = v
		}
	}

	node.Attributes["parsed_at"] = time.Now().Unix()

	graph.AddNode(node)
	graph.Link(parentID, node.ID)

	return graph, nil
}

// Helper functions
func stringifyMap(m interface{}) string {
	if m == nil {
		return ""
	}
	if str, ok := m.(string); ok {
		return str
	}
	if mp, ok := m.(map[string]interface{}); ok {
		var parts []string
		for k, v := range mp {
			parts = append(parts, fmt.Sprintf("%s=%v", k, v))
		}
		return strings.Join(parts, ",")
	}
	return fmt.Sprintf("%v", m)
}

func getString(m map[string]interface{}, keys ...string) string {
	var current interface{} = m
	for i, key := range keys {
		if mp, ok := current.(map[string]interface{}); ok {
			current = mp[key]
			if i == len(keys)-1 {
				if s, ok := current.(string); ok {
					return s
				}
				return ""
			}
		} else {
			return ""
		}
	}
	return ""
}

func getNestedString(m map[string]interface{}, keys ...string) string {
	if len(keys) == 0 {
		return ""
	}
	var current interface{} = m
	for i, key := range keys {
		if mp, ok := current.(map[string]interface{}); ok {
			current = mp[key]
			if i == len(keys)-1 {
				if s, ok := current.(string); ok {
					return s
				}
				return ""
			}
		} else {
			return ""
		}
	}
	return ""
}

func getInt(m map[string]interface{}, key string, defaultVal int) int {
	if v, ok := m[key]; ok {
		switch val := v.(type) {
		case int:
			return val
		case int64:
			return int(val)
		case float64:
			return int(val)
		case string:
			if i, err := strconv.Atoi(val); err == nil {
				return i
			}
		}
	}
	return defaultVal
}

func uniqueStrings(slice []string) []string {
	seen := make(map[string]bool)
	var result []string
	for _, s := range slice {
		if !seen[s] {
			seen[s] = true
			result = append(result, s)
		}
	}
	return result
}

// Funções de cálculo de métricas de coerência de containers
func computePodEphemeralCoherence(attrs map[string]interface{}) float64 {
	coherence := 0.65 // Base para pod efêmero

	// Bonus por probes de saúde
	if hasLiveness, ok := attrs["has_liveness_probe"].(bool); ok && hasLiveness {
		coherence += 0.05
	}
	if hasReadiness, ok := attrs["has_readiness_probe"].(bool); ok && hasReadiness {
		coherence += 0.05
	}

	// Bonus por recursos bem definidos
	if _, hasCPU := attrs["cpu_request"]; hasCPU {
		coherence += 0.03
	}
	if _, hasMem := attrs["memory_request"]; hasMem {
		coherence += 0.03
	}

	// Penalidade por restart policy agressivo
	if restartPolicy, ok := attrs["restart_policy"].(string); ok {
		if restartPolicy == "Always" {
			coherence -= 0.02 // Mais efêmero = menos coerência estável
		}
	}

	return math.Min(1.0, math.Max(0.0, coherence))
}

type SynapseMetrics struct {
	Connectivity float64 // [0, 1] — quão bem conectado o service está
	Stability    float64 // [0, 1] — estabilidade da conexão
}

func computeServiceSynapseMetrics(attrs map[string]interface{}) SynapseMetrics {
	metrics := SynapseMetrics{Connectivity: 0.5, Stability: 0.5}

	// Conectividade baseada em tipo de service
	if serviceType, ok := attrs["service_type"].(string); ok {
		switch serviceType {
		case "ClusterIP":
			metrics.Connectivity = 0.7
			metrics.Stability = 0.9
		case "NodePort":
			metrics.Connectivity = 0.8
			metrics.Stability = 0.7
		case "LoadBalancer":
			metrics.Connectivity = 0.9
			metrics.Stability = 0.8
		case "ExternalName":
			metrics.Connectivity = 0.6
			metrics.Stability = 0.5
		}
	}

	// Bonus por session affinity
	if affinity, ok := attrs["session_affinity"].(string); ok && affinity == "ClientIP" {
		metrics.Stability += 0.1
	}

	// Bonus por múltiplas portas
	if ports, ok := attrs["ports"].(string); ok && ports != "" {
		portCount := len(strings.Split(ports, ","))
		metrics.Connectivity += math.Min(0.2, float64(portCount)*0.05)
	}

	metrics.Connectivity = math.Min(1.0, metrics.Connectivity)
	metrics.Stability = math.Min(1.0, metrics.Stability)

	return metrics
}

type OrchestrationMetrics struct {
	Efficiency          float64 // [0, 1] — eficiência da orquestração
	CollectiveCoherence float64 // [0, 1] — coerência coletiva do deployment
}

func computeDeploymentOrchestrationMetrics(attrs map[string]interface{}) OrchestrationMetrics {
	metrics := OrchestrationMetrics{Efficiency: 0.7, CollectiveCoherence: 0.65}

	// Eficiência baseada em estratégia de rollout
	if strategy, ok := attrs["strategy"].(string); ok {
		switch strategy {
		case "RollingUpdate":
			metrics.Efficiency = 0.85
			metrics.CollectiveCoherence = 0.75
		case "Recreate":
			metrics.Efficiency = 0.6
			metrics.CollectiveCoherence = 0.5
		case "BlueGreen":
			metrics.Efficiency = 0.9
			metrics.CollectiveCoherence = 0.85
		}
	}

	// Bonus por múltiplas réplicas
	if replicas, ok := attrs["replicas"].(int); ok {
		if replicas >= 3 {
			metrics.CollectiveCoherence += 0.1 // Mais réplicas = mais resiliência
		}
	}

	metrics.Efficiency = math.Min(1.0, metrics.Efficiency)
	metrics.CollectiveCoherence = math.Min(1.0, metrics.CollectiveCoherence)

	return metrics
}

func computeDockerfileCoherence(attrs map[string]interface{}) float64 {
	coherence := 0.6 // Base para imagem Docker

	// Bonus por base image conhecida
	if baseImage, ok := attrs["base_image"].(string); ok {
		if strings.Contains(baseImage, "alpine") || strings.Contains(baseImage, "distroless") {
			coherence += 0.05 // Imagens mínimas = mais previsíveis
		}
		if strings.Contains(baseImage, "ubuntu") || strings.Contains(baseImage, "debian") {
			coherence += 0.03
		}
	}

	// Bonus por portas expostas bem definidas
	if ports, ok := attrs["exposed_ports"].(string); ok && ports != "" {
		coherence += 0.03
	}

	// Penalidade por muitas variáveis de ambiente
	if envCount, ok := attrs["env_vars_count"].(int); ok && envCount > 20 {
		coherence -= 0.02 // Muitas env vars = mais complexidade
	}

	return math.Min(1.0, math.Max(0.0, coherence))
}

func computeLogCoherence(attrs map[string]interface{}) float64 {
	coherence := 0.7 // Base para logs

	errorCount, _ := attrs["error_count"].(int)
	warnCount, _ := attrs["warn_count"].(int)
	totalLines, _ := attrs["total_lines"].(int)

	if totalLines > 0 {
		errorRate := float64(errorCount) / float64(totalLines)
		warnRate := float64(warnCount) / float64(totalLines)

		// Penalizar alta taxa de erros
		if errorRate > 0.1 {
			coherence -= 0.15
		} else if errorRate > 0.05 {
			coherence -= 0.05
		}

		// Penalizar warnings excessivos
		if warnRate > 0.2 {
			coherence -= 0.05
		}
	}

	// Bonus por eventos de ciclo de vida detectados
	if hasStartup, ok := attrs["has_startup"].(bool); ok && hasStartup {
		coherence += 0.03
	}

	return math.Min(1.0, math.Max(0.0, coherence))
}

func computeStabilityIndicator(errorCount, warnCount, infoCount int) string {
	total := errorCount + warnCount + infoCount
	if total == 0 {
		return "unknown"
	}

	errorRatio := float64(errorCount) / float64(total)

	if errorRatio < 0.01 {
		return "stable"
	} else if errorRatio < 0.05 {
		return "moderate"
	} else {
		return "unstable"
	}
}
