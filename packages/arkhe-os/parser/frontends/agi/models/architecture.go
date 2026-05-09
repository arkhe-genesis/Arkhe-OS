// parser/frontends/agi/models/architecture.go
package models

import (
	"time"
)

// ArchitectureType define tipos de arquitetura AGI suportados
type ArchitectureType string

const (
	TypeNeural          ArchitectureType = "neural"          // Baseado em redes neurais profundas
	TypeSymbolic        ArchitectureType = "symbolic"        // Baseado em lógica/regras simbólicas
	TypeHybrid          ArchitectureType = "hybrid"          // Combinação neural+simbólica
	TypeModular         ArchitectureType = "modular"         // Módulos especializados com orquestração
	TypeEmergent        ArchitectureType = "emergent"        // Propriedades emergentes de sistemas simples
	TypeNeuroSymbolic   ArchitectureType = "neuro_symbolic"  // Integração profunda neural+simbólica
)

// CognitiveModuleType define tipos de módulos cognitivos
type CognitiveModuleType string

const (
	ModulePerception    CognitiveModuleType = "perception"     // Entrada sensorial/processamento
	ModuleMemory        CognitiveModuleType = "memory"         // Memória de curto/longo prazo
	ModuleReasoning     CognitiveModuleType = "reasoning"      // Raciocínio lógico/probabilístico
	ModulePlanning      CognitiveModuleType = "planning"       // Planejamento de ações/estratégias
	ModuleLearning      CognitiveModuleType = "learning"       // Aprendizado/adaptação
	ModuleAction        CognitiveModuleType = "action"         // Execução de ações no ambiente
	ModuleMeta          CognitiveModuleType = "meta_cognition" // Auto-reflexão/meta-cognição
	ModuleValue         CognitiveModuleType = "value_system"   // Sistema de valores/ética
)

// AGISpecification representa a especificação completa de um sistema AGI
type AGISpecification struct {
	Name              string                  `json:"name"`
	Description       string                  `json:"description,omitempty"`
	Version           string                  `json:"version"`
	ArchitectureType  ArchitectureType        `json:"architecture_type"`
	CreatedAt         time.Time               `json:"created_at"`
	UpdatedAt         time.Time               `json:"updated_at"`

	// Módulos cognitivos
	Modules           []CognitiveModule       `json:"modules"`

	// Capacidades e habilidades
	Capabilities      []Capability            `json:"capabilities"`

	// Objetivos e metas
	Goals             []Goal                  `json:"goals"`

	// Valores, preferências, restrições éticas
	Values            []Value                 `json:"values"`
	Preferences       []Preference            `json:"preferences,omitempty"`
	EthicalConstraints []EthicalConstraint    `json:"ethical_constraints,omitempty"`

	// Mecanismos de segurança e alinhamento
	SafetyMechanisms  []SafetyMechanism       `json:"safety_mechanisms"`

	// Meta-cognição (se aplicável)
	MetaCognition     *MetaCognitionSpec      `json:"meta_cognition,omitempty"`

	// Interfaces e comunicação entre módulos
	Interfaces        []ModuleInterface       `json:"interfaces"`

	// Ambiente e contexto de operação
	Environment       EnvironmentSpec         `json:"environment"`

	// Código e prompts associados
	CodeModules       []CodeModule            `json:"code_modules,omitempty"`
	Prompts           []PromptSpec            `json:"prompts,omitempty"`

	// Metadados
	Metadata          map[string]interface{}  `json:"metadata"`
}

// CognitiveModule representa um módulo cognitivo no sistema AGI
type CognitiveModule struct {
	ID              string                `json:"id"`
	Name            string                `json:"name"`
	Type            CognitiveModuleType   `json:"type"`
	Description     string                `json:"description,omitempty"`

	// Interface do módulo
	Inputs          []DataSpecification   `json:"inputs"`
	Outputs         []DataSpecification   `json:"outputs"`
	API             *APIInterface         `json:"api,omitempty"`

	// Implementação
	Implementation  ImplementationSpec    `json:"implementation"`

	// Recursos e requisitos
	ComputeRequirements *ComputeRequirements `json:"compute_requirements,omitempty"`
	MemoryRequirements  *MemoryRequirements  `json:"memory_requirements,omitempty"`

	// Dependências de outros módulos
	Dependencies    []string              `json:"dependencies,omitempty"` // IDs de módulos dos quais depende
	ProvidesTo      []string              `json:"provides_to,omitempty"`   // IDs de módulos para os quais fornece

	// Estado e configuração
	Configuration   map[string]interface{} `json:"configuration"`
	InitialState    map[string]interface{} `json:"initial_state,omitempty"`

	// Métricas e monitoramento
	Metrics         []MetricDefinition  `json:"metrics,omitempty"`

	// Metadados
	Metadata        map[string]interface{} `json:"metadata"`
}

// DataSpecification especifica formato de dados de entrada/saída
type DataSpecification struct {
	Name        string      `json:"name"`
	Type        string      `json:"type"` // "tensor", "graph", "text", "symbolic", "probabilistic"
	Schema      interface{} `json:"schema,omitempty"` // JSON Schema ou similar
	Required    bool        `json:"required"`
	Description string      `json:"description,omitempty"`
}

// APIInterface especifica interface de programação do módulo
type APIInterface struct {
	Endpoint    string              `json:"endpoint"`
	Method      string              `json:"method"` // "sync", "async", "streaming"
	Parameters  []ParameterSpec     `json:"parameters"`
	Returns     []ReturnSpec        `json:"returns"`
	Errors      []ErrorSpec         `json:"errors,omitempty"`
}

// ParameterSpec especifica um parâmetro de API
type ParameterSpec struct {
	Name        string      `json:"name"`
	Type        string      `json:"type"`
	Required    bool        `json:"required"`
	Default     interface{} `json:"default,omitempty"`
	Description string      `json:"description,omitempty"`
}

// ReturnSpec especifica um valor de retorno de API
type ReturnSpec struct {
	Name        string      `json:"name"`
	Type        string      `json:"type"`
	Description string      `json:"description,omitempty"`
}

// ErrorSpec especifica um tipo de erro de API
type ErrorSpec struct {
	Code        string      `json:"code"`
	Description string      `json:"description"`
	Recoverable bool        `json:"recoverable"`
}

// ImplementationSpec especifica como um módulo é implementado
type ImplementationSpec struct {
	Type            string   `json:"type"` // "neural_network", "rule_engine", "hybrid", "external_service"
	Framework       string   `json:"framework,omitempty"` // "pytorch", "tensorflow", "prolog", etc.
	ModelPath       string   `json:"model_path,omitempty"`
	CodeReference   string   `json:"code_reference,omitempty"` // Path para código fonte
	TrainingData    string   `json:"training_data,omitempty"`
	Hyperparameters map[string]interface{} `json:"hyperparameters,omitempty"`
}

// ComputeRequirements especifica requisitos computacionais
type ComputeRequirements struct {
	CPU          string `json:"cpu,omitempty"`          // "4 cores", "32 cores"
	GPU          string `json:"gpu,omitempty"`          // "NVIDIA A100", "TPU v4"
	Memory       string `json:"memory,omitempty"`       // "16GB", "128GB"
	Storage      string `json:"storage,omitempty"`      // "1TB SSD"
	Network      string `json:"network,omitempty"`      // "10Gbps"
	EstimatedCost string `json:"estimated_cost,omitempty"` // "$0.50/hour"
}

// MemoryRequirements especifica requisitos de memória
type MemoryRequirements struct {
	ShortTerm   string `json:"short_term,omitempty"`   // "512MB working memory"
	LongTerm    string `json:"long_term,omitempty"`    // "100GB vector database"
	Cache       string `json:"cache,omitempty"`        // "2GB LRU cache"
}

// Capability representa uma capacidade ou habilidade do sistema AGI
type Capability struct {
	ID              string            `json:"id"`
	Name            string            `json:"name"`
	Description     string            `json:"description"`
	Category        string            `json:"category"` // "reasoning", "perception", "planning", etc.

	// Requisitos para habilitar a capacidade
	RequiredModules []string          `json:"required_modules"` // IDs de módulos necessários
	RequiredResources []ResourceRequirement `json:"required_resources,omitempty"`

	// Métricas de desempenho
	PerformanceMetrics []PerformanceMetric `json:"performance_metrics"`

	// Limitações e condições de falha
	Limitations   []string            `json:"limitations,omitempty"`
	FailureConditions []string        `json:"failure_conditions,omitempty"`

	// Metadados
	Metadata      map[string]interface{} `json:"metadata"`
}

// ResourceRequirement especifica um recurso necessário para uma capacidade
type ResourceRequirement struct {
	Type        string `json:"type"` // "compute", "memory", "data", "time"
	Amount      string `json:"amount"`
	Priority    string `json:"priority"` // "critical", "important", "optional"
}

// PerformanceMetric especifica uma métrica de desempenho para uma capacidade
type PerformanceMetric struct {
	Name        string  `json:"name"`
	Type        string  `json:"type"` // "accuracy", "latency", "throughput", "robustness"
	Target      float64 `json:"target"`
	Unit        string  `json:"unit"`
	MeasurementMethod string `json:"measurement_method"`
}

// Goal representa um objetivo ou meta do sistema AGI
type Goal struct {
	ID              string            `json:"id"`
	Name            string            `json:"name"`
	Description     string            `json:"description"`
	Priority        string            `json:"priority"` // "critical", "high", "medium", "low"

	// Critérios de sucesso
	SuccessCriteria []SuccessCriterion `json:"success_criteria"`

	// Sub-objetivos
	SubGoalIDs      []string          `json:"sub_goal_ids,omitempty"`
	ParentGoalID    string            `json:"parent_goal_id,omitempty"`

	// Métricas para avaliar progresso
	Metrics         []GoalMetric      `json:"metrics,omitempty"`

	// Restrições e condições
	Constraints     []string          `json:"constraints,omitempty"`
	Timeout         *time.Duration    `json:"timeout,omitempty"`

	// Módulos responsáveis por este objetivo
	ResponsibleModules []string       `json:"responsible_modules,omitempty"`

	// Metadados
	Metadata        map[string]interface{} `json:"metadata"`
}

// SuccessCriterion especifica um critério para considerar um objetivo como atingido
type SuccessCriterion struct {
	Description string  `json:"description"`
	MetricName  string  `json:"metric_name"`
	Threshold   float64 `json:"threshold"`
	Operator    string  `json:"operator"` // ">=", "<=", "==", "in_range"
}

// GoalMetric especifica uma métrica para avaliar progresso de um objetivo
type GoalMetric struct {
	Name        string  `json:"name"`
	Type        string  `json:"type"` // "progress", "quality", "efficiency"
	Target      float64 `json:"target"`
	Current     *float64 `json:"current,omitempty"`
	Unit        string  `json:"unit"`
}

// Value representa um valor, preferência ou princípio ético do sistema AGI
type Value struct {
	ID              string            `json:"id"`
	Name            string            `json:"name"`
	Description     string            `json:"description"`
	Category        string            `json:"category"` // "ethical", "aesthetic", "pragmatic", "social"

	// Expressão formal do valor (se aplicável)
	FormalExpression string           `json:"formal_expression,omitempty"` // LTL, CTL, ou lógica de preferência

	// Prioridade e peso
	Priority        string            `json:"priority"` // "fundamental", "important", "contextual"
	Weight          *float64          `json:"weight,omitempty"` // Peso numérico para trade-offs

	// Condições de aplicação
	ApplicabilityConditions []string  `json:"applicability_conditions,omitempty"`

	// Conflitos potenciais e resolução
	PotentialConflicts []string       `json:"potential_conflicts,omitempty"`
	ConflictResolution string         `json:"conflict_resolution,omitempty"`

	// Metadados
	Metadata        map[string]interface{} `json:"metadata"`
}

// Preference representa uma preferência ordenada entre opções
type Preference struct {
	ID              string            `json:"id"`
	Name            string            `json:"name"`
	Description     string            `json:"description"`

	// Expressão de preferência: A > B, ou função de utilidade
	Expression      string            `json:"expression"` // "option_A > option_B" ou "utility(x) = ..."

	// Contexto de aplicação
	Context         string            `json:"context,omitempty"`

	// Força da preferência
	Strength        float64           `json:"strength"` // 0.0-1.0

	// Metadados
	Metadata        map[string]interface{} `json:"metadata"`
}

// EthicalConstraint representa uma restrição ética ou de segurança
type EthicalConstraint struct {
	ID              string            `json:"id"`
	Name            string            `json:"name"`
	Description     string            `json:"description"`
	Type            string            `json:"type"` // "deontological", "consequentialist", "virtue_ethics", "safety"

	// Expressão formal da restrição
	FormalExpression string           `json:"formal_expression"` // Lógica temporal, lógica deôntica, etc.

	// Nível de aplicação
	EnforcementLevel string          `json:"enforcement_level"` // "hard", "soft", "advisory"

	// Escopo de aplicação
	Scope           string            `json:"scope"` // "global", "module", "context"

	// Mecanismos de verificação
	VerificationMethods []string      `json:"verification_methods,omitempty"`

	// Metadados
	Metadata        map[string]interface{} `json:"metadata"`
}

// SafetyMechanism representa um mecanismo de segurança ou alinhamento
type SafetyMechanism struct {
	ID              string            `json:"id"`
	Name            string            `json:"name"`
	Description     string            `json:"description"`
	Type            string            `json:"type"` // "interruptibility", "corrigibility", "boxing", "value_learning", "uncertainty_awareness"

	// Implementação
	Implementation  SafetyImplementation `json:"implementation"`

	// Propriedades verificáveis
	VerifiableProperties []PropertySpec `json:"verifiable_properties"`

	// Condições de ativação
	ActivationConditions []string     `json:"activation_conditions,omitempty"`

	// Efeitos colaterais potenciais
	SideEffects     []string          `json:"side_effects,omitempty"`

	// Metadados
	Metadata        map[string]interface{} `json:"metadata"`
}

// SafetyImplementation especifica como um mecanismo de segurança é implementado
type SafetyImplementation struct {
	Type            string            `json:"type"` // "runtime_monitor", "formal_verification", "sandbox", "human_in_loop"
	Configuration   map[string]interface{} `json:"configuration"`
	TestingProtocol string            `json:"testing_protocol,omitempty"`
	FallbackBehavior string           `json:"fallback_behavior,omitempty"`
}

// PropertySpec especifica uma propriedade verificável de um mecanismo de segurança
type PropertySpec struct {
	Name            string            `json:"name"`
	Description     string            `json:"description"`
	FormalSpecification string        `json:"formal_specification"` // Especificação em lógica formal
	VerificationMethod string         `json:"verification_method"` // "model_checking", "theorem_proving", "testing"
}

// MetaCognitionSpec especifica capacidades de meta-cognição do sistema
type MetaCognitionSpec struct {
	SelfModeling    SelfModelSpec     `json:"self_modeling"`
	UncertaintyCalibration UncertaintySpec `json:"uncertainty_calibration"`
	Reflection      ReflectionSpec    `json:"reflection"`
	LearningToLearn LearningSpec      `json:"learning_to_learn,omitempty"`
}

// SelfModelSpec especifica capacidades de auto-modelagem
type SelfModelSpec struct {
	Enabled         bool              `json:"enabled"`
	ModelGranularity string           `json:"model_granularity"` // "high", "medium", "low"
	UpdateFrequency string           `json:"update_frequency"`  // "continuous", "periodic", "on_demand"
	AccuracyTarget  float64          `json:"accuracy_target"`   // 0.0-1.0
}

// UncertaintySpec especifica capacidades de calibração de incerteza
type UncertaintySpec struct {
	Enabled         bool              `json:"enabled"`
	CalibrationMethod string         `json:"calibration_method"` // "bayesian", "ensemble", "conformal"
	ReportingFormat string          `json:"reporting_format"`   // "interval", "distribution", "qualitative"
}

// ReflectionSpec especifica capacidades de reflexão/auto-análise
type ReflectionSpec struct {
	Enabled         bool              `json:"enabled"`
	TriggerConditions []string        `json:"trigger_conditions"`
	Depth           string            `json:"depth"` // "shallow", "deep", "recursive"
	Timeout         *time.Duration    `json:"timeout,omitempty"`
}

// LearningSpec especifica capacidades de meta-aprendizado
type LearningSpec struct {
	Enabled         bool              `json:"enabled"`
	MetaLearningAlgorithm string     `json:"meta_learning_algorithm"`
	AdaptationRate  string            `json:"adaptation_rate"` // "conservative", "moderate", "aggressive"
}

// ModuleInterface especifica interface de comunicação entre módulos
type ModuleInterface struct {
	ID              string            `json:"id"`
	Name            string            `json:"name"`
	SourceModule    string            `json:"source_module"` // ID do módulo fonte
	TargetModule    string            `json:"target_module"` // ID do módulo destino

	// Protocolo de comunicação
	Protocol        string            `json:"protocol"` // "sync_call", "async_message", "shared_memory", "event_stream"
	DataFormat      string            `json:"data_format"` // "json", "protobuf", "tensor", "symbolic"

	// Especificação de mensagens
	Messages        []MessageSpec     `json:"messages"`

	// QoS e garantias
	QoS             QoSSpec           `json:"qos,omitempty"`

	// Metadados
	Metadata        map[string]interface{} `json:"metadata"`
}

// MessageSpec especifica um tipo de mensagem na interface
type MessageSpec struct {
	Name        string            `json:"name"`
	Description string            `json:"description"`
	Payload     DataSpecification `json:"payload"`
	Required    bool              `json:"required"`
}

// QoSSpec especifica requisitos de qualidade de serviço
type QoSSpec struct {
	Latency       string            `json:"latency,omitempty"`      // "low", "medium", "high"
	Reliability   string            `json:"reliability,omitempty"`  // "best_effort", "at_least_once", "exactly_once"
	Ordering      string            `json:"ordering,omitempty"`     // "unordered", "fifo", "causal"
}

// EnvironmentSpec especifica o ambiente de operação do sistema AGI
type EnvironmentSpec struct {
	Type            string            `json:"type"` // "simulated", "real_world", "hybrid"
	Domain          string            `json:"domain"` // "general", "scientific", "creative", "social"

	// Características do ambiente
	Characteristics []string          `json:"characteristics,omitempty"` // "partially_observable", "stochastic", "multi_agent"

	// Interfaces com o ambiente
	PerceptionInterfaces []InterfaceSpec `json:"perception_interfaces"`
	ActionInterfaces  []InterfaceSpec `json:"action_interfaces"`

	// Restrições operacionais
	OperationalConstraints []string  `json:"operational_constraints,omitempty"`

	// Metadados
	Metadata        map[string]interface{} `json:"metadata"`
}

// InterfaceSpec especifica uma interface de percepção ou ação
type InterfaceSpec struct {
	Name        string            `json:"name"`
	Type        string            `json:"type"` // "sensor", "actuator", "api", "human_interface"
	Capabilities []string         `json:"capabilities"`
	Limitations  []string         `json:"limitations,omitempty"`
}

// CodeModule representa um módulo de código associado à spec AGI
type CodeModule struct {
	ID              string            `json:"id"`
	Name            string            `json:"name"`
	Language        string            `json:"language"` // "python", "javascript", "rust"
	Path            string            `json:"path"`
	Description     string            `json:"description,omitempty"`

	// Funções/exportações relevantes
	Exports         []CodeExport      `json:"exports,omitempty"`

	// Dependências
	Dependencies    []string          `json:"dependencies,omitempty"`

	// Metadados
	Metadata        map[string]interface{} `json:"metadata"`
}

// CodeExport representa uma função ou classe exportada por um módulo de código
type CodeExport struct {
	Name        string            `json:"name"`
	Type        string            `json:"type"` // "function", "class", "constant"
	Signature   string            `json:"signature,omitempty"`
	Description string            `json:"description,omitempty"`
}

// PromptSpec representa um prompt de sistema ou few-shot example
type PromptSpec struct {
	ID              string            `json:"id"`
	Name            string            `json:"name"`
	Type            string            `json:"type"` // "system", "user", "assistant", "few_shot"
	Content         string            `json:"content"`

	// Contexto de uso
	Context         string            `json:"context,omitempty"`

	// Variáveis e placeholders
	Variables       []PromptVariable  `json:"variables,omitempty"`

	// Metadados
	Metadata        map[string]interface{} `json:"metadata"`
}

// PromptVariable representa uma variável em um prompt
type PromptVariable struct {
	Name        string            `json:"name"`
	Type        string            `json:"type"`
	Required    bool              `json:"required"`
	Default     interface{}       `json:"default,omitempty"`
	Description string            `json:"description,omitempty"`
}

// MetricDefinition define uma métrica para monitoramento de módulo ou sistema
type MetricDefinition struct {
	Name        string            `json:"name"`
	Description string            `json:"description"`
	Type        string            `json:"type"` // "counter", "gauge", "histogram", "event"
	Unit        string            `json:"unit,omitempty"`
	Aggregation string            `json:"aggregation,omitempty"` // "sum", "avg", "max", "min"
}
