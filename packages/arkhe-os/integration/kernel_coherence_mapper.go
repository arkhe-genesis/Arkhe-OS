// arkhe_os/integration/kernel_coherence_mapper.go
package integration

import (
	"fmt"
	"math"
	"strings"
	"sync"
	"time"

	"arkhe/ai"
	"arkhe/parser/lfir"
)

// KernelCoherenceMapper mapeia elementos do kernel para gradientes de coerência
type KernelCoherenceMapper struct {
	mu sync.RWMutex

	// Configuração
	config KernelCoherenceConfig

	// Cache de elementos processados
	processedElements map[string]bool

	// Canal de gradientes para submissão
	gradientChannel *ai.CoherenceGradientChannel

	// Métricas de mapeamento
	metrics MapperMetrics

	// Modelo de vitalidade modular aprendido
	moduleVitalityModel ModuleVitalityModel
}

// KernelCoherenceConfig contém configuração para mapeamento kernel→Coerência
type KernelCoherenceConfig struct {
	EnableAutoSubmission    bool
	SyscallWeightSuccess    float64 // Peso para syscalls bem-sucedidas
	SyscallWeightError      float64 // Penalidade para syscalls com erro
	ModuleWeightHealthy     float64 // Bonus para módulos saudáveis
	ModuleWeightCritical    float64 // Peso extra para módulos críticos
	MinCoherenceDelta       float64 // Delta mínimo para submissão
	CriticalityThreshold    float64 // Limiar para considerar elemento crítico
}

// ModuleVitalityModel representa modelo aprendido de vitalidade modular
type ModuleVitalityModel struct {
	Trained             bool
	CriticalModules     map[string]bool // Módulos considerados críticos
	DependencyWeights   map[string]float64 // Pesos de dependência por módulo
	LastUpdated         time.Time
}

// MapperMetrics contém métricas do mapeador de kernel
type MapperMetrics struct {
	ElementsProcessed       int64   `json:"elements_processed"`
	SyscallsMapped          int64   `json:"syscalls_mapped"`
	ModulesMapped           int64   `json:"modules_mapped"`
	SymbolsMapped           int64   `json:"symbols_mapped"`
	ConfigsMapped           int64   `json:"configs_mapped"`
	GradientsSubmitted      int64   `json:"gradients_submitted"`
	AvgKernelCoherence      float64 `json:"avg_kernel_coherence"`
	CriticalElementsHealthy int64   `json:"critical_elements_healthy"`
}

// NewKernelCoherenceMapper cria novo mapeador de kernel para coerência
func NewKernelCoherenceMapper(
	config KernelCoherenceConfig,
	gradientChannel *ai.CoherenceGradientChannel,
) *KernelCoherenceMapper {
	if config.SyscallWeightSuccess == 0 {
		config.SyscallWeightSuccess = 0.03
	}
	if config.SyscallWeightError == 0 {
		config.SyscallWeightError = -0.05
	}
	if config.ModuleWeightHealthy == 0 {
		config.ModuleWeightHealthy = 0.02
	}
	if config.ModuleWeightCritical == 0 {
		config.ModuleWeightCritical = 0.04
	}

	return &KernelCoherenceMapper{
		config:            config,
		processedElements: make(map[string]bool),
		gradientChannel:   gradientChannel,
		moduleVitalityModel: ModuleVitalityModel{
			CriticalModules: map[string]bool{
				"ext4": true, "xfs": true, "btrfs": true, // filesystems críticos
				"tcp": true, "udp": true, "ipv4": true, "ipv6": true, // rede crítica
				"usbcore": true, "ehci_hcd": true, "xhci_hcd": true, // USB crítico
				"nvidia": true, "amdgpu": true, "i915": true, // GPU crítica
			},
			DependencyWeights: make(map[string]float64),
		},
	}
}

// ProcessLFIRGraph processa grafo LFIR de kernel e submete elementos como gradientes
func (m *KernelCoherenceMapper) ProcessLFIRGraph(graph *lfir.LFIRGraph) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	elementsSubmitted := 0

	for _, node := range graph.Nodes {
		if node.Attributes["type"] == nil {
			continue
		}

		elementType, ok := node.Attributes["type"].(string)
		if !ok {
			continue
		}

		elementID := node.ID
		if m.processedElements[elementID] {
			continue
		}

		// Calcular gradiente de coerência baseado no tipo de elemento
		var gradient float64
		var metadata map[string]interface{}

		switch elementType {
		case "syscall":
			gradient, metadata = m.computeSyscallCoherenceGradient(node)
			m.metrics.SyscallsMapped++
		case "kernel_module":
			gradient, metadata = m.computeModuleCoherenceGradient(node)
			m.metrics.ModulesMapped++
		case "kernel_symbol":
			gradient, metadata = m.computeSymbolCoherenceGradient(node)
			m.metrics.SymbolsMapped++
		case "kernel_config", "kconfig_option":
			gradient, metadata = m.computeConfigCoherenceGradient(node)
			m.metrics.ConfigsMapped++
		case "initcall":
			gradient, metadata = m.computeInitcallCoherenceGradient(node)
		case "boot_param":
			gradient, metadata = m.computeBootParamCoherenceGradient(node)
		default:
			continue
		}

		// Submeter ao canal de coerência se habilitado e delta significativo
		if m.config.EnableAutoSubmission && math.Abs(gradient) >= m.config.MinCoherenceDelta {
			if err := m.submitGradient(elementID, gradient, metadata); err != nil {
				continue
			}
			elementsSubmitted++
			m.metrics.GradientsSubmitted++
		}

		// Atualizar métricas
		m.metrics.ElementsProcessed++
		m.metrics.AvgKernelCoherence = m.metrics.AvgKernelCoherence*0.99 + math.Abs(gradient)*0.01

		// Detectar elementos críticos saudáveis
		if isCritical, ok := metadata["is_critical"].(bool); ok && isCritical {
			if health, ok := metadata["health_score"].(float64); ok && health > 0.9 {
				m.metrics.CriticalElementsHealthy++
			}
		}

		m.processedElements[elementID] = true
	}

	return nil
}

// computeSyscallCoherenceGradient calcula contribuição de coerência de uma syscall
func (m *KernelCoherenceMapper) computeSyscallCoherenceGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"element_type": "syscall",
		"syscall_name": node.Attributes["name"],
	}

	// Syscalls críticas recebem peso extra
	syscallName, _ := node.Attributes["name"].(string)
	criticalSyscalls := map[string]bool{
		"read": true, "write": true, "open": true, "close": true,
		"fork": true, "execve": true, "exit": true, "wait4": true,
		"socket": true, "connect": true, "bind": true, "listen": true,
		"mmap": true, "munmap": true, "brk": true,
	}
	if criticalSyscalls[syscallName] {
		metadata["is_critical"] = true
		gradient += m.config.ModuleWeightCritical * 0.5
	}

	// Bonus por número de argumentos (complexidade gerenciada)
	if nargs, ok := node.Attributes["nargs"].(string); ok {
		var n int
		if _, err := fmt.Sscanf(nargs, "%d", &n); err == nil && n > 0 {
			gradient += 0.005 * float64(n) // Complexidade bem gerenciada = positivo
		}
	}

	// Penalidade por syscalls depreciadas ou perigosas
	dangerousSyscalls := map[string]bool{
		"get_kernel_syms": true, "query_module": true, "sysfs": true,
	}
	if dangerousSyscalls[syscallName] {
		gradient -= 0.02
		metadata["warning"] = "deprecated_or_dangerous"
	}

	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// computeModuleCoherenceGradient calcula contribuição de coerência de um módulo
func (m *KernelCoherenceMapper) computeModuleCoherenceGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"element_type": "kernel_module",
		"module_name":  node.Name,
	}

	modName := node.Name

	// Verificar se é módulo crítico
	if m.moduleVitalityModel.CriticalModules[modName] {
		metadata["is_critical"] = true
		gradient += m.config.ModuleWeightCritical
	}

	// Bonus por módulo saudável (sem dependências problemáticas)
	if deps, ok := node.Attributes["dependencies"].(string); ok && deps != "" {
		depList := strings.Split(deps, ",")
		healthyDeps := 0
		for _, dep := range depList {
			dep = strings.TrimSpace(dep)
			if dep != "" && !strings.HasPrefix(dep, "[") {
				healthyDeps++
			}
		}
		if healthyDeps == len(depList) {
			gradient += m.config.ModuleWeightHealthy
			metadata["health_score"] = 0.95
		} else {
			metadata["health_score"] = 0.7
		}
	} else {
		// Módulo sem dependências = mais isolado = potencialmente mais estável
		gradient += m.config.ModuleWeightHealthy * 0.5
		metadata["health_score"] = 0.85
	}

	// Penalidade por módulos grandes (potencial de complexidade excessiva)
	if sizeStr, ok := node.Attributes["size"].(string); ok {
		var size int
		if _, err := fmt.Sscanf(sizeStr, "%d", &size); err == nil && size > 1000000 {
			gradient -= 0.01 // Módulos >1MB podem indicar complexidade excessiva
		}
	}

	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// computeSymbolCoherenceGradient calcula contribuição de coerência de um símbolo
func (m *KernelCoherenceMapper) computeSymbolCoherenceGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"element_type": "kernel_symbol",
		"symbol_name":  node.Name,
	}

	// Símbolos de texto (código executável) recebem peso maior
	if symType, ok := node.Attributes["symbol_type"].(string); ok {
		switch symType {
		case "T", "t": // Texto global/local
			gradient += 0.005
			metadata["symbol_category"] = "executable"
		case "D", "d", "B", "b": // Dados
			gradient += 0.002
			metadata["symbol_category"] = "data"
		case "U": // Não definido (referência externa)
			// Neutro: pode ser dependência legítima
			metadata["symbol_category"] = "external_ref"
		default:
			metadata["symbol_category"] = "other"
		}
	}

	// Símbolos com nomes que indicam criticidade
	symbolName := node.Name
	if strings.Contains(symbolName, "init") || strings.Contains(symbolName, "setup") {
		gradient += 0.003 // Funções de inicialização são importantes
	}
	if strings.Contains(symbolName, "error") || strings.Contains(symbolName, "fail") {
		gradient -= 0.002 // Símbolos de erro podem indicar pontos de falha
	}

	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// computeConfigCoherenceGradient calcula contribuição de coerência de uma opção de configuração
func (m *KernelCoherenceMapper) computeConfigCoherenceGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"element_type": "kernel_config",
		"config_name":  node.Name,
	}

	configName := node.Name
	configValue, _ := node.Attributes["value"].(string)

	// Opções de segurança habilitadas = positivo
	securityConfigs := map[string]bool{
		"CONFIG_SECURITY": true,
		"CONFIG_SECURITY_YAMA": true,
		"CONFIG_SECURITY_APPARMOR": true,
		"CONFIG_SECURITY_SELINUX": true,
		"CONFIG_STRICT_DEVMEM": true,
		"CONFIG_RANDOMIZE_BASE": true,
	}
	if securityConfigs[configName] && configValue == "y" {
		gradient += 0.02
		metadata["security_enhancement"] = true
	}

	// Opções de debugging desabilitadas em produção = positivo
	debugConfigs := map[string]bool{
		"CONFIG_DEBUG_KERNEL": true,
		"CONFIG_DEBUG_SPINLOCK": true,
		"CONFIG_DEBUG_ATOMIC_SLEEP": true,
	}
	if debugConfigs[configName] && configValue == "n" {
		gradient += 0.01
		metadata["production_optimized"] = true
	}

	// Opções críticas desabilitadas = negativo
	criticalConfigs := map[string]bool{
		"CONFIG_BLOCK": true,
		"CONFIG_NET": true,
		"CONFIG_UNIX": true,
	}
	if criticalConfigs[configName] && configValue == "n" {
		gradient -= 0.03
		metadata["critical_feature_disabled"] = true
	}

	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// computeInitcallCoherenceGradient calcula contribuição de coerência de um initcall
func (m *KernelCoherenceMapper) computeInitcallCoherenceGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"element_type": "initcall",
		"initcall_name": node.Name,
	}

	// Initcalls em níveis iniciais são mais críticos
	if level, ok := node.Attributes["level"].(string); ok {
		if strings.Contains(level, "early") || strings.Contains(level, "pure") {
			gradient += 0.01 // Inicialização precoce bem-sucedida = positivo
			metadata["init_criticality"] = "high"
		}
	}

	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// computeBootParamCoherenceGradient calcula contribuição de coerência de um parâmetro de boot
func (m *KernelCoherenceMapper) computeBootParamCoherenceGradient(node *lfir.LFIRNode) (float64, map[string]interface{}) {
	gradient := 0.0
	metadata := map[string]interface{}{
		"element_type": "boot_param",
		"param_name":   node.Name,
	}

	paramName := node.Name
	paramValue, _ := node.Attributes["value"].(string)

	// Parâmetros que melhoram segurança = positivo
	secureParams := map[string][]string{
		"slub_debug": {"P", "F", "Z"}, // Proteção de memória
		"init_on_alloc": {"1"},
		"init_on_free": {"1"},
		"randomize_va_space": {"2"},
	}
	if values, ok := secureParams[paramName]; ok {
		for _, valid := range values {
			if paramValue == valid {
				gradient += 0.015
				metadata["security_enhancement"] = true
				break
			}
		}
	}

	// Parâmetros que desabilitam recursos importantes = negativo
	disablingParams := map[string]bool{
		"noapic": true, "nolapic": true, "acpi=off": true,
	}
	if disablingParams[paramName+"="+paramValue] {
		gradient -= 0.02
		metadata["feature_disabled"] = true
	}

	metadata["coherence_delta"] = gradient
	return gradient, metadata
}

// submitGradient submete gradiente de coerência do kernel ao canal
func (m *KernelCoherenceMapper) submitGradient(
	elementID string,
	coherenceDelta float64,
	metadata map[string]interface{},
) error {
	// Preparar metadados para o gradiente
	gradientMetadata := map[string]interface{}{
		"source":        "kernel_layer",
		"element_id":    elementID,
		"timestamp":     time.Now().Unix(),
		"coherence_sign": "positive",
	}
	if coherenceDelta < 0 {
		gradientMetadata["coherence_sign"] = "negative"
	}
	for k, v := range metadata {
		gradientMetadata[k] = v
	}

	// Converter delta de coerência para vetor de gradiente
	gradientVector := []float64{coherenceDelta}

	// Calcular "coerência" do elemento como confiança na contribuição
	coherenceValue := 0.75 + 0.25*math.Abs(coherenceDelta) // Kernel tem baseline mais alta

	// Submeter ao canal
	_, err := m.gradientChannel.SubmitLocalGradient(
		gradientVector,
		coherenceValue,
		0.4, // distância conceitual menor para kernel (mais fundamental)
		1,   // sample count
		0.0, // loss value
		gradientMetadata,
	)

	return err
}

// GetMapperMetrics retorna métricas consolidadas do mapeador de kernel
func (m *KernelCoherenceMapper) GetMapperMetrics() MapperMetrics {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.metrics
}
