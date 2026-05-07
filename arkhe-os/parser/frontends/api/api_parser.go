// parser/frontends/api/api_parser.go
package api

import (
	"fmt"
	"path/filepath"
	"strings"

	"arkhe/parser/frontends/api/formats"
	"arkhe/parser/frontends/api/models"
	"arkhe/parser/lfir"
)

type APIParser struct {
	Framework string
}

func NewAPIParser() *APIParser {
	return &APIParser{}
}

func (p *APIParser) Parse(source []byte, filename string, options map[string]interface{}) (*lfir.LFIRGraph, error) {
	dataType := detectAPIDataType(filename)
// ═══════════════════════════════════════════════════════
// ARKHE OS — Substrate 305: API Infrastructure Parser
// ═══════════════════════════════════════════════════════

package api

import (
	"context"
	"fmt"
	"path/filepath"

	"arkhe/parser/frontends/api/formats"
	"arkhe/parser/frontends/api/models"
	"arkhe/parser/lfir"
)

// APIFrontend parses API definitions into LFIR nodes
type APIFrontend struct {
	Options APIParserOptions
}

// APIParserOptions configuration for the parser
type APIParserOptions struct {
	EnableCoherenceMetrics bool
	InferSecuritySchemas   bool
	MaxDepth               int
}

// NewAPIFrontend creates a new parser instance
func NewAPIFrontend(options APIParserOptions) *APIFrontend {
	return &APIFrontend{
		Options: options,
	}
}

// Parse implements the standard Arkhe parser interface
func (f *APIFrontend) Parse(ctx context.Context, sourcePath string) (*lfir.Node, error) {
	// Detect file type
	ext := filepath.Ext(sourcePath)

	var apiModel *models.APIInfrastructure
	var err error

	switch ext {
	case ".yaml", ".yml", ".json":
		// Check if it's OpenAPI
		apiModel, err = formats.ParseOpenAPI(sourcePath)
	case ".proto":
		// gRPC protobuf parsing (stubbed for now)
		apiModel, err = formats.ParseProtobuf(sourcePath)
	case ".graphql", ".gql":
		// GraphQL parsing (stubbed for now)
		apiModel, err = formats.ParseGraphQL(sourcePath)
	default:
		return nil, fmt.Errorf("unsupported API format: %s", ext)
	}

	if err != nil {
		return nil, fmt.Errorf("failed to parse API definition: %w", err)
	}

	// Map generic API model to LFIR graph
	return models.MapToLFIR(apiModel, f.Options.EnableCoherenceMetrics)
package api

import (
	"fmt"

	"path/filepath"
	"strings"
	"time"

	"arkhe/parser/frontends/api/formats"
	"arkhe/parser/frontends/api/models"
	"arkhe/parser/frontends/api/analyzers"
	"arkhe/parser/frontends/api/coherence"
	"arkhe/parser/lfir"
)

// APIParser implementa Parser para especificações de API e infraestrutura
type APIParser struct {
	Framework           string   // "express", "spring", "fastapi", "generic"
	AnalyzeOpenAPI      bool     // Parse de specs OpenAPI/Swagger
	AnalyzegRPC         bool     // Parse de defs gRPC (.proto)
	AnalyzeAsyncAPI     bool     // Parse de specs AsyncAPI para eventos
	AnalyzeInfra        bool     // Parse de configs de infra (K8s, Terraform)
	AnalyzeResilience   bool     // Analisar padrões de resiliência
	AnalyzeDataStrategy bool     // Analisar estratégias de dados (sharding, replication)
	CoherenceWindow     time.Duration // Janela para cálculo de Φ_C em sistemas dinâmicos
}

// NewAPIParser cria parser com configurações padrão
func NewAPIParser() *APIParser {
	return &APIParser{
		Framework:           "generic",
		AnalyzeOpenAPI:      true,
		AnalyzegRPC:         true,
		AnalyzeAsyncAPI:     true,
		AnalyzeInfra:        true,
		AnalyzeResilience:   true,
		AnalyzeDataStrategy: true,
		CoherenceWindow:     5 * time.Minute,
	}
}

func (p *APIParser) GetLanguage() string { return "api-infrastructure" }

func (p *APIParser) GetExtensions() []string {
	return []string{
		".yaml", ".yml", ".json", // OpenAPI, AsyncAPI, configs
		".proto",                  // gRPC
		".openapi", ".swagger",    // OpenAPI variants
		".asyncapi",               // AsyncAPI
		".tf", ".tfvars",          // Terraform
		".k8s", ".kubectl",        // Kubernetes
		".js", ".ts", ".py", ".java", ".go", // Code with API annotations
	}
}

// Parse é o método principal
func (p *APIParser) Parse(source []byte, filename string, metadata map[string]interface{}) (*lfir.LFIRGraph, error) {
	graph := lfir.NewLFIRGraph()
	root := lfir.NewLFIRNode(
		lfir.LFIRNodeTypeModule,
		fmt.Sprintf("api_system_%s_%d", filepath.Base(filename), time.Now().Unix()),
		"api",
	)
	graph.AddNode(root)
	graph.RootNodes = append(graph.RootNodes, root.ID)

	// Detectar tipo de dado de entrada
	dataType := detectAPIDataType(filename, source)

	var apiSpec *models.APISpecification
	var err error

	switch dataType {
	case "xml_api_spec":
		apiSpec, err = formats.ParseXMLAPISpec(source)
	default:
		return nil, fmt.Errorf("unsupported API specification format: %s", dataType)
	}

	if err != nil {
		return nil, err
	}

	return p.mapToLFIR(apiSpec)
}

func detectAPIDataType(filename string) string {
	ext := strings.ToLower(filepath.Ext(filename))
	switch ext {
	case ".xml", ".wsdl":
		return "xml_api_spec"
	default:
		return "unknown"
	}
}

func (p *APIParser) mapToLFIR(spec *models.APISpecification) (*lfir.LFIRGraph, error) {
	graph := lfir.NewLFIRGraph()

	rootNode := &lfir.LFIRNode{
		ID:   "root",
		Type: lfir.NodeTypeSystem,
		Attributes: map[string]interface{}{
			"system_name":             spec.Name,
			"version":                 spec.Version,
			"service_count":           len(spec.Services),
			"endpoint_count":          countEndpoints(spec),
			"coherence_auth_coverage": calculateAuthCoverage(spec),
			"coherence_resilience":    calculateResilience(spec),
		},
	}
	graph.AddNode(rootNode)
	graph.RootNodes = append(graph.RootNodes, rootNode.ID)

	// Just stub out metrics for now
	graph.Metrics.CoherenceScore = 0.9
	case "openapi":
		apiSpec, err = formats.ParseOpenAPI(source)
	case "grpc_proto":
		apiSpec, err = formats.ParsegRPCProto(source, filename)
	case "asyncapi":
		apiSpec, err = formats.ParseAsyncAPI(source)
	case "infra_config":
		apiSpec, err = formats.ParseInfraConfig(source, filename)
	case "code_with_annotations":
		apiSpec, err = formats.ParseCodeWithAnnotations(source, filename, p.Framework)
	default:
		return nil, fmt.Errorf("tipo de dado API não reconhecido: %s", dataType)
	}

	if err != nil {
		return nil, fmt.Errorf("failed to parse API spec: %w", err)
	}

	// Aplicar adapter de framework se necessário
	if p.Framework != "generic" {
		adapter, err := p.selectFrameworkAdapter(p.Framework)
		if err != nil {
			return nil, fmt.Errorf("failed to load framework adapter: %w", err)
		}
		apiSpec = adapter.Adapt(apiSpec)
	}

	// Extrair infraestrutura associada se habilitado
	if p.AnalyzeInfra {
		infra, err := formats.ExtractInfrastructure(source, filename)
		if err != nil {
			return nil, fmt.Errorf("failed to extract infrastructure: %w", err)
		}
		apiSpec.Infrastructure = infra
	}

	// Construir grafo LFIR
	lfirBuilder := models.NewAPILFIRBuilder(graph, root.ID)
	if err := lfirBuilder.Build(apiSpec); err != nil {
		return nil, fmt.Errorf("failed to build LFIR: %w", err)
	}

	// Analisar métricas de coerência
	analysis, err := p.analyzeAPISystem(apiSpec)
	if err != nil {
		return nil, fmt.Errorf("failed to analyze API system: %w", err)
	}

	// Calcular coerência
	cfg := coherence.DefaultAPIConfig()
	serviceCoherence := coherence.CalculateServiceCoherence(analysis.Services, cfg)
	systemCoherence := coherence.CalculateSystemCoherence(apiSpec, analysis, cfg)
	infraCoherence := coherence.CalculateInfrastructureCoherence(apiSpec.Infrastructure, cfg)

	// Combinação ponderada
	overallCoherence := 0.4*serviceCoherence + 0.35*systemCoherence + 0.25*infraCoherence

	// Atualizar root com métricas
	root.Attributes["system_name"] = apiSpec.Name
	root.Attributes["service_count"] = len(apiSpec.Services)
	root.Attributes["endpoint_count"] = countEndpoints(apiSpec.Services)
	root.Attributes["protocol_count"] = countProtocols(apiSpec.Services)
	root.Attributes["auth_scheme_count"] = len(apiSpec.AuthSchemes)
	if apiSpec.Infrastructure != nil {
		root.Attributes["infrastructure_component_count"] = len(apiSpec.Infrastructure.Components)
	} else {
		root.Attributes["infrastructure_component_count"] = 0
	}
	root.Attributes["coherence_score"] = overallCoherence
	root.Attributes["coherence_service"] = serviceCoherence
	root.Attributes["coherence_system"] = systemCoherence
	root.Attributes["coherence_infrastructure"] = infraCoherence
	root.Attributes["coherence_contract_clarity"] = analysis.AvgContractClarity
	root.Attributes["coherence_protocol_consistency"] = analysis.ProtocolConsistency
	root.Attributes["coherence_auth_coverage"] = analysis.AuthCoverage
	root.Attributes["coherence_resilience"] = analysis.ResilienceAdequacy
	root.Attributes["dependency_cycles"] = analysis.DependencyCycles
	root.Attributes["single_points_of_failure"] = analysis.SinglePointsOfFailure

	graph.Metrics.CoherenceScore = overallCoherence
	graph.Metrics.NodeCount = analysis.TotalNodes
	graph.Metrics.EdgeCount = analysis.TotalEdges

	return graph, nil
}

func countEndpoints(spec *models.APISpecification) int {
	count := 0
	for _, srv := range spec.Services {
		count += len(srv.Endpoints)
	}
	return count
}

func calculateAuthCoverage(spec *models.APISpecification) float64 {
	if len(spec.Services) == 0 {
		return 0.0
	}

	totalEndpoints := 0
	securedEndpoints := 0

	for _, srv := range spec.Services {
		for _, ep := range srv.Endpoints {
			totalEndpoints++
			if len(ep.Security) > 0 {
				securedEndpoints++
			}
		}
	}

	if totalEndpoints == 0 {
		return 1.0 // no endpoints = fully covered
	}

	return float64(securedEndpoints) / float64(totalEndpoints)
}

func calculateResilience(spec *models.APISpecification) float64 {
	if len(spec.Services) == 0 {
		return 0.0
	}

	totalEndpoints := 0
	resilientEndpoints := 0

	for _, srv := range spec.Services {
		for _, ep := range srv.Endpoints {
			totalEndpoints++

			// Simple heuristic
			if ep.Resilience.Retry != nil || ep.Resilience.CircuitBreaker != nil || ep.Resilience.Timeout != "" {
				resilientEndpoints++
			}
		}
	}

	if totalEndpoints == 0 {
		return 1.0
	}

	return float64(resilientEndpoints) / float64(totalEndpoints)
// detectAPIDataType identifica o tipo de dado de entrada API
func detectAPIDataType(filename string, source []byte) string {
	ext := strings.ToLower(filepath.Ext(filename))
	content := string(source)

	// Detectar por extensão primeiro
	switch ext {
	case ".proto":
		return "grpc_proto"
	case ".openapi", ".swagger":
		return "openapi"
	case ".asyncapi":
		return "asyncapi"
	case ".tf", ".tfvars":
		return "infra_config"
	case ".yaml", ".yml":
		// Detectar por conteúdo
		if strings.Contains(content, "openapi:") || strings.Contains(content, "swagger:") {
			return "openapi"
		}
		if strings.Contains(content, "asyncapi:") {
			return "asyncapi"
		}
		if strings.Contains(content, "resource ") || strings.Contains(content, "provider ") {
			return "infra_config"
		}
		return "openapi" // Fallback para YAML
	case ".json":
		if strings.Contains(content, `"openapi"`) || strings.Contains(content, `"swagger"`) {
			return "openapi"
		}
		if strings.Contains(content, `"asyncapi"`) {
			return "asyncapi"
		}
		return "openapi" // Fallback
	case ".js", ".ts", ".py", ".java", ".go":
		return "code_with_annotations"
	default:
		// Detectar por conteúdo
		if strings.Contains(content, "paths:") && strings.Contains(content, "responses:") {
			return "openapi"
		}
		if strings.Contains(content, "syntax = \"proto3\"") {
			return "grpc_proto"
		}
		if strings.Contains(content, "channels:") && strings.Contains(content, "publish:") {
			return "asyncapi"
		}
		return "unknown"
	}
}

// selectFrameworkAdapter seleciona adapter baseado no framework
func (p *APIParser) selectFrameworkAdapter(framework string) (formats.FrameworkAdapter, error) {
	switch framework {
	case "express":
		return formats.NewExpressAdapter(), nil
	case "spring":
		return formats.NewSpringAdapter(), nil
	case "fastapi":
		return formats.NewFastAPIAdapter(), nil
	case "generic":
		return formats.NewGenericAdapter(), nil
	default:
		return nil, fmt.Errorf("unsupported API framework: %s", framework)
	}
}

// analyzeAPISystem executa análise de coerência do sistema de API
func (p *APIParser) analyzeAPISystem(spec *models.APISpecification) (*coherence.APIAnalysis, error) {
	analysis := &coherence.APIAnalysis{
		SystemName: spec.Name,
		Services:   make(map[string]*coherence.ServiceMetrics),
	}

	// Analisar cada serviço individualmente
	for _, service := range spec.Services {
		metrics, err := analyzers.AnalyzeServiceContract(service)
		if err != nil {
			return nil, fmt.Errorf("failed to analyze service %s: %w", service.Name, err)
		}
		analysis.Services[service.Name] = metrics
	}

	// Calcular métricas agregadas de contrato
	analysis.AvgContractClarity = averageContractClarity(analysis.Services)

	// Analisar consistência de protocolos
	analysis.ProtocolConsistency = analyzers.CalculateProtocolConsistency(spec.Services)

	// Analisar cobertura de autenticação
	analysis.AuthCoverage = analyzers.CalculateAuthCoverage(spec.Services, spec.AuthSchemes)

	// Analisar adequação de resiliência se habilitado
	if p.AnalyzeResilience {
		resilience, err := analyzers.AnalyzeResilienceAdequacy(spec.Services, spec.Infrastructure)
		if err != nil {
			return nil, fmt.Errorf("failed to analyze resilience: %w", err)
		}
		analysis.ResilienceAdequacy = resilience.Score
		analysis.CircuitBreakerCoverage = resilience.CircuitBreakerCoverage
		analysis.RetryPolicyAdequacy = resilience.RetryPolicyAdequacy
	}

	// Construir e analisar grafo de dependências
	depGraph, err := analyzers.BuildDependencyGraph(spec.Services)
	if err != nil {
		return nil, fmt.Errorf("failed to build dependency graph: %w", err)
	}
	analysis.DependencyCycles = analyzers.CountDependencyCycles(depGraph)
	analysis.SinglePointsOfFailure = analyzers.IdentifySPOF(depGraph)

	// Analisar estratégias de dados se habilitado
	if p.AnalyzeDataStrategy && spec.Infrastructure != nil {
		dataAnalysis, err := analyzers.AnalyzeDataStrategy(spec.Infrastructure)
		if err != nil {
			return nil, fmt.Errorf("failed to analyze data strategy: %w", err)
		}
		analysis.DataConsistencyScore = dataAnalysis.ConsistencyScore
		analysis.ShardingAdequacy = dataAnalysis.ShardingAdequacy
		analysis.ReplicationFactor = dataAnalysis.ReplicationFactor
	}

	// Contar nós e arestas do grafo implícito
	analysis.TotalNodes = countAPINodes(spec)
	analysis.TotalEdges = countAPIEdges(spec, depGraph)

	return analysis, nil
}

// Helpers
func countEndpoints(services []models.Service) int {
	count := 0
	for _, s := range services {
		count += len(s.Endpoints)
	}
	return count
}

func countProtocols(services []models.Service) int {
	protocols := make(map[string]bool)
	for _, s := range services {
		if s.Protocol != "" {
			protocols[s.Protocol] = true
		}
	}
	return len(protocols)
}

func averageContractClarity(services map[string]*coherence.ServiceMetrics) float64 {
	if len(services) == 0 {
		return 1.0
	}
	sum := 0.0
	for _, m := range services {
		sum += m.ContractClarity
	}
	return sum / float64(len(services))
}

func countAPINodes(spec *models.APISpecification) int {
	count := len(spec.Services)
	for _, s := range spec.Services {
		count += len(s.Endpoints)

	}
	if spec.Infrastructure != nil {
		count += len(spec.Infrastructure.Components)
	}
	return count
}

func countAPIEdges(spec *models.APISpecification, depGraph *analyzers.DependencyGraph) int {
	// Arestas: dependências entre serviços + endpoints → auth + serviços → infra
	count := depGraph.EdgeCount
	for _, s := range spec.Services {
		count += len(s.Endpoints)
	}
	if spec.Infrastructure != nil {
		count += len(spec.Services) * 2 // Cada serviço conecta a ~2 componentes de infra
	}
	return count
}
