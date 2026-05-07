package models

import (
	"fmt"
	"strings"

	"arkhe/parser/lfir"
)

// Tipos de nós LFIR específicos para API/Infraestrutura
const (
	// Serviços e endpoints
	LFIRNodeTypeService          lfir.LFIRNodeType = "api_service"
	LFIRNodeTypeEndpoint         lfir.LFIRNodeType = "api_endpoint"
	LFIRNodeTypeOperation        lfir.LFIRNodeType = "api_operation"
	LFIRNodeTypeParameter        lfir.LFIRNodeType = "api_parameter"
	LFIRNodeTypeResponse         lfir.LFIRNodeType = "api_response"

	// Protocolos
	LFIRNodeTypeREST             lfir.LFIRNodeType = "protocol_rest"
	LFIRNodeTypegRPC             lfir.LFIRNodeType = "protocol_grpc"
	LFIRNodeTypeGraphQL          lfir.LFIRNodeType = "protocol_graphql"
	LFIRNodeTypeWebSocket        lfir.LFIRNodeType = "protocol_websocket"

	// Autenticação
	LFIRNodeTypeAuthScheme       lfir.LFIRNodeType = "auth_scheme"
	LFIRNodeTypeJWT              lfir.LFIRNodeType = "auth_jwt"
	LFIRNodeTypeOAuth2           lfir.LFIRNodeType = "auth_oauth2"
	LFIRNodeTypeAPIKey           lfir.LFIRNodeType = "auth_api_key"

	// Infraestrutura
	LFIRNodeTypeCache            lfir.LFIRNodeType = "infra_cache"
	LFIRNodeTypeQueue            lfir.LFIRNodeType = "infra_queue"
	LFIRNodeTypeStream           lfir.LFIRNodeType = "infra_stream"
	LFIRNodeTypeDatabase         lfir.LFIRNodeType = "infra_database"
	LFIRNodeTypeLoadBalancer     lfir.LFIRNodeType = "infra_load_balancer"
	LFIRNodeTypeCDN              lfir.LFIRNodeType = "infra_cdn"
	LFIRNodeTypeAPIGateway       lfir.LFIRNodeType = "infra_api_gateway"

	// Resiliência
	LFIRNodeTypeCircuitBreaker   lfir.LFIRNodeType = "resilience_circuit_breaker"
	LFIRNodeTypeRetry            lfir.LFIRNodeType = "resilience_retry"
	LFIRNodeTypeTimeout          lfir.LFIRNodeType = "resilience_timeout"
	LFIRNodeTypeBulkhead         lfir.LFIRNodeType = "resilience_bulkhead"
	LFIRNodeTypeRateLimiter      lfir.LFIRNodeType = "resilience_rate_limiter"

	// Dados
	LFIRNodeTypeIndex            lfir.LFIRNodeType = "data_index"
	LFIRNodeTypeShard            lfir.LFIRNodeType = "data_shard"
	LFIRNodeTypeReplica          lfir.LFIRNodeType = "data_replica"

	// Eventos
	LFIRNodeTypeEvent            lfir.LFIRNodeType = "event"
	LFIRNodeTypeWebhook          lfir.LFIRNodeType = "webhook"
	LFIRNodeTypeIdempotency      lfir.LFIRNodeType = "idempotency_key"

	// Alertas
	LFIRNodeTypeAlert            lfir.LFIRNodeType = "api_alert"
	LFIRNodeTypeSPOF             lfir.LFIRNodeType = "single_point_of_failure"
	LFIRNodeTypeDependencyCycle  lfir.LFIRNodeType = "dependency_cycle"
)

// APILFIRBuilder converte modelo de API → grafo LFIR
type APILFIRBuilder struct {
	graph            *lfir.LFIRGraph
	rootID           string
	serviceNodeMap   map[string]string // Service.Name → LFIR node ID
	endpointNodeMap  map[string]string // Endpoint key → LFIR node ID
	componentNodeMap map[string]string // InfrastructureComponent.ID → LFIR node ID
}

func NewAPILFIRBuilder(graph *lfir.LFIRGraph, rootID string) *APILFIRBuilder {
	return &APILFIRBuilder{
		graph:            graph,
		rootID:           rootID,
		serviceNodeMap:   make(map[string]string),
		endpointNodeMap:  make(map[string]string),
		componentNodeMap: make(map[string]string),
	}
}

// Build converte especificação de API para LFIR
func (b *APILFIRBuilder) Build(spec *APISpecification) error {
	// Criar nó raiz do sistema de API
	systemNode := lfir.NewLFIRNode(lfir.LFIRNodeTypeModule,
		fmt.Sprintf("api_system_%s", spec.Name), "api")
	systemNode.Attributes["name"] = spec.Name
	systemNode.Attributes["version"] = spec.Version
	systemNode.Attributes["service_count"] = len(spec.Services)
	systemNode.Attributes["endpoint_count"] = countEndpointsInSpec(spec)
	b.graph.AddNode(systemNode)
	b.graph.Link(b.rootID, systemNode.ID)

	// Criar nós de serviços
	for _, service := range spec.Services {
		serviceNode := b.createServiceNode(service)
		b.graph.AddNode(serviceNode)
		b.graph.Link(systemNode.ID, serviceNode.ID)
		b.serviceNodeMap[service.Name] = serviceNode.ID
	}

	// Criar nós de endpoints e operações
	for _, service := range spec.Services {
		serviceNodeID := b.serviceNodeMap[service.Name]
		for _, endpoint := range service.Endpoints {
			endpointNode := b.createEndpointNode(endpoint, service.Protocol)
			b.graph.AddNode(endpointNode)
			b.graph.Link(serviceNodeID, endpointNode.ID)
			b.endpointNodeMap[endpointKey(endpoint)] = endpointNode.ID

			// Adicionar parâmetros como filhos
			for _, param := range endpoint.Parameters {
				paramNode := b.createParameterNode(param)
				b.graph.AddNode(paramNode)
				b.graph.Link(endpointNode.ID, paramNode.ID)
			}

			// Adicionar respostas como filhos
			for _, resp := range endpoint.Responses {
				respNode := b.createResponseNode(resp)
				b.graph.AddNode(respNode)
				b.graph.Link(endpointNode.ID, respNode.ID)
			}
		}
	}

	// Criar nós de esquemas de autenticação
	for _, auth := range spec.AuthSchemes {
		authNode := b.createAuthNode(auth)
		b.graph.AddNode(authNode)
		b.graph.Link(systemNode.ID, authNode.ID)

		// Link para endpoints que usam este auth
		for _, service := range spec.Services {
			for _, endpoint := range service.Endpoints {
				if usesAuthScheme(endpoint, auth.Name) {
					if epNodeID, exists := b.endpointNodeMap[endpointKey(endpoint)]; exists {
						b.graph.Link(authNode.ID, epNodeID)
					}
				}
			}
		}
	}

	// Criar nós de componentes de infraestrutura
	if spec.Infrastructure != nil {
		for _, comp := range spec.Infrastructure.Components {
			compNode := b.createInfrastructureNode(comp)
			b.graph.AddNode(compNode)
			b.graph.Link(systemNode.ID, compNode.ID)
			b.componentNodeMap[comp.ID] = compNode.ID

			// Link para serviços que usam este componente
			for _, targetID := range comp.ConnectsTo {
				if targetNodeID, exists := b.serviceNodeMap[targetID]; exists {
					b.graph.Link(compNode.ID, targetNodeID)
				}
			}
		}
	}

	// Criar arestas de dependência entre serviços
	b.addServiceDependencies(spec.Services)

	// Criar alertas para problemas detectados
	b.addAlerts(spec)

	return nil
}

func (b *APILFIRBuilder) createServiceNode(service Service) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeService,
		fmt.Sprintf("service_%s", service.Name), "api")

	node.Attributes["name"] = service.Name
	node.Attributes["protocol"] = service.Protocol
	node.Attributes["version"] = service.Version
	node.Attributes["endpoint_count"] = len(service.Endpoints)
	node.Attributes["base_url"] = service.BaseURL

	if service.Description != "" {
		node.Attributes["description"] = service.Description
	}

	// Adicionar métricas de contrato se disponíveis
	if service.ContractMetrics != nil {
		node.Attributes["contract_clarity"] = service.ContractMetrics.Clarity
		node.Attributes["completeness"] = service.ContractMetrics.Completeness
	}

	return node
}

func (b *APILFIRBuilder) createEndpointNode(endpoint Endpoint, protocol string) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeEndpoint,
		fmt.Sprintf("endpoint_%s_%s", endpoint.Method, endpoint.Path), "api")

	node.Attributes["path"] = endpoint.Path
	node.Attributes["method"] = endpoint.Method
	node.Attributes["operation_id"] = endpoint.OperationID
	node.Attributes["summary"] = endpoint.Summary

	if len(endpoint.Tags) > 0 {
		node.Attributes["tags"] = endpoint.Tags
	}

	if len(endpoint.Security) > 0 {
		authNames := make([]string, len(endpoint.Security))
		for i, s := range endpoint.Security {
			authNames[i] = s.SchemeName
        }
		node.Attributes["auth_required"] = authNames
	}

	// Adicionar dicas de resiliência
	if endpoint.Resilience.Timeout != "" {
		node.Attributes["timeout"] = endpoint.Resilience.Timeout
	}
	if endpoint.Resilience.Retry != nil {
		node.Attributes["retry_max_attempts"] = endpoint.Resilience.Retry.MaxAttempts
	}
	if endpoint.Resilience.CircuitBreaker != nil {
		node.Attributes["circuit_breaker"] = true
	}

	return node
}

func (b *APILFIRBuilder) createParameterNode(param Parameter) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeParameter,
		fmt.Sprintf("param_%s_%s", param.In, param.Name), "api")

	node.Attributes["name"] = param.Name
	node.Attributes["in"] = param.In
	node.Attributes["required"] = param.Required
	node.Attributes["type"] = param.Schema.Type

	if param.Description != "" {
		node.Attributes["description"] = param.Description
	}

	return node
}

func (b *APILFIRBuilder) createResponseNode(resp Response) *lfir.LFIRNode {
	node := lfir.NewLFIRNode(LFIRNodeTypeResponse,
		fmt.Sprintf("response_%s", resp.StatusCode), "api")

	node.Attributes["status_code"] = resp.StatusCode
	node.Attributes["description"] = resp.Description

	if len(resp.Content) > 0 {
		contentTypes := make([]string, 0, len(resp.Content))
		for ct := range resp.Content {
			contentTypes = append(contentTypes, ct)
        }
		node.Attributes["content_types"] = contentTypes
	}

	return node
}

func (b *APILFIRBuilder) createAuthNode(auth AuthScheme) *lfir.LFIRNode {
	nodeType := LFIRNodeTypeAuthScheme
	switch auth.Type {
	case AuthTypeJWT:
		nodeType = LFIRNodeTypeJWT
	case AuthTypeOAuth2:
		nodeType = LFIRNodeTypeOAuth2
	case AuthTypeAPIKey:
		nodeType = LFIRNodeTypeAPIKey
	}

	node := lfir.NewLFIRNode(nodeType,
		fmt.Sprintf("auth_%s", auth.Name), "api")

	node.Attributes["name"] = auth.Name
	node.Attributes["type"] = string(auth.Type)
	node.Attributes["description"] = auth.Description

	if auth.Scheme != "" {
		node.Attributes["scheme"] = auth.Scheme
	}
	if auth.In != "" {
		node.Attributes["location"] = auth.In
	}
	if auth.ParamName != "" {
		node.Attributes["param_name"] = auth.ParamName
	}

	return node
}

func (b *APILFIRBuilder) createInfrastructureNode(comp InfrastructureComponent) *lfir.LFIRNode {
	nodeType := mapComponentTypeToLFIR(comp.Type)

	node := lfir.NewLFIRNode(nodeType,
		fmt.Sprintf("infra_%s", comp.ID), "api")

	node.Attributes["id"] = comp.ID
	node.Attributes["name"] = comp.Name
	node.Attributes["type"] = string(comp.Type)
	node.Attributes["description"] = comp.Description

	if comp.Replicas > 1 {
		node.Attributes["replicas"] = comp.Replicas
	}
	if comp.HealthCheck != nil {
		node.Attributes["health_check_endpoint"] = comp.HealthCheck.Endpoint
	}

	// Adicionar configuração específica por tipo
	b.addInfrastructureConfig(node, comp)

	return node
}

func (b *APILFIRBuilder) addInfrastructureConfig(node *lfir.LFIRNode, comp InfrastructureComponent) {
	switch comp.Type {
	case TypeCache:
		if pattern, ok := comp.Config["pattern"].(map[string]interface{}); ok {
			node.Attributes["cache_pattern"] = extractString(pattern, "type", "")
			node.Attributes["cache_ttl"] = extractString(pattern, "ttl", "")
        }
	case TypeQueue:
		if pattern, ok := comp.Config["pattern"].(map[string]interface{}); ok {
			node.Attributes["queue_type"] = extractString(pattern, "type", "")
			node.Attributes["delivery_guarantee"] = extractString(pattern, "delivery_guarantee", "")
        }
	case TypeStream:
		if cfg, ok := comp.Config["event_stream"].(map[string]interface{}); ok {
			node.Attributes["topic"] = extractString(cfg, "topic", "")
			node.Attributes["partitions"] = extractFloat(cfg, "partitions", 1)
        }
	case TypeDatabase:
		if strategy, ok := comp.Config["data_strategy"].(map[string]interface{}); ok {
			node.Attributes["consistency_model"] = extractString(strategy, "consistency_model", "")
			if sharding, ok := strategy["sharding"].(map[string]interface{}); ok {
				node.Attributes["sharding_strategy"] = extractString(sharding, "strategy", "")
            }
        }
	case TypeLoadBalancer:
		if cfg, ok := comp.Config["lb_config"].(map[string]interface{}); ok {
			node.Attributes["algorithm"] = extractString(cfg, "algorithm", "round_robin")
			node.Attributes["health_check"] = extractBool(cfg, "health_check", true)
        }
	case TypeCircuitBreaker:
		if cfg, ok := comp.Config["circuit_breaker"].(map[string]interface{}); ok {
			node.Attributes["failure_threshold"] = extractFloat(cfg, "failure_threshold", 5)
			node.Attributes["timeout"] = extractString(cfg, "timeout", "30s")
        }
	}
}

func (b *APILFIRBuilder) addServiceDependencies(services []Service) {
	// Detectar dependências por análise de paths/URLs (heurística)
	for _, sourceSvc := range services {
		sourceNodeID := b.serviceNodeMap[sourceSvc.Name]
        for _, targetSvc := range services {
            if targetSvc.Name == sourceSvc.Name {
                continue
            }

            // Se há dependência declarada ou inferida
            if hasDependency(sourceSvc, targetSvc) {
                depNode := lfir.NewLFIRNode(lfir.LFIRNodeTypeDependency,
                    fmt.Sprintf("dep_%s_%s", sourceSvc.Name, targetSvc.Name), "api")
                depNode.Attributes["type"] = "calls"
                b.graph.AddNode(depNode)
                b.graph.Link(sourceNodeID, depNode.ID)
                b.graph.Link(depNode.ID, b.serviceNodeMap[targetSvc.Name])
            }
        }
	}
}

func (b *APILFIRBuilder) addAlerts(spec *APISpecification) {
	// Alertar sobre endpoints sem autenticação em serviços sensíveis
	for _, service := range spec.Services {
		if isSensitiveService(service) {
			for _, endpoint := range service.Endpoints {
				if len(endpoint.Security) == 0 {
					alert := lfir.NewLFIRNode(LFIRNodeTypeAlert,
						fmt.Sprintf("alert_no_auth_%s_%s", service.Name, endpointKey(endpoint)), "api")
					alert.Attributes["type"] = "missing_auth"
					alert.Attributes["severity"] = "high"
					alert.Attributes["endpoint"] = fmt.Sprintf("%s %s", endpoint.Method, endpoint.Path)
					b.graph.AddNode(alert)
					b.graph.Link(b.rootID, alert.ID)
                }
            }
		}
	}

	// Alertar sobre single points of failure
	// (implementação futura: integrar com dependency_graph analysis)
}

// Helpers
func endpointKey(ep Endpoint) string {
	return fmt.Sprintf("%s:%s", ep.Method, ep.Path)
}

func usesAuthScheme(endpoint Endpoint, authName string) bool {
	for _, sec := range endpoint.Security {
		if sec.SchemeName == authName {
			return true
        }
	}
	return false
}

func mapComponentTypeToLFIR(compType ComponentType) lfir.LFIRNodeType {
	switch compType {
	case TypeCache:
		return LFIRNodeTypeCache
	case TypeQueue:
		return LFIRNodeTypeQueue
	case TypeStream:
		return LFIRNodeTypeStream
	case TypeDatabase:
		return LFIRNodeTypeDatabase
	case TypeLoadBalancer:
		return LFIRNodeTypeLoadBalancer
	case TypeCDN:
		return LFIRNodeTypeCDN
	case TypeAPIGateway:
		return LFIRNodeTypeAPIGateway
	case TypeCircuitBreaker:
		return LFIRNodeTypeCircuitBreaker
	case TypeRateLimiter:
		return LFIRNodeTypeRateLimiter
	default:
		return lfir.LFIRNodeTypeComponent
	}
}

func countEndpointsInSpec(spec *APISpecification) int {
	count := 0
	for _, s := range spec.Services {
		count += len(s.Endpoints)
	}
	return count
}

func isSensitiveService(service Service) bool {
	// Heurística: serviços com paths sensíveis ou tags
	sensitivePaths := []string{"/admin", "/user", "/auth", "/payment", "/internal"}
	sensitiveTags := []string{"admin", "internal", "sensitive"}

	for _, ep := range service.Endpoints {
		for _, sensitive := range sensitivePaths {
			if strings.Contains(ep.Path, sensitive) {
				return true
            }
        }
	}
	for _, tag := range service.Tags {
		for _, sensitive := range sensitiveTags {
			if strings.EqualFold(tag, sensitive) {
				return true
            }
        }
	}
	return false
}

func hasDependency(source, target Service) bool {
	// Heurística simplificada: verificar se source chama target por nome em endpoints
	// Em produção: analisar service mesh config, código, ou traces
	for _, ep := range source.Endpoints {
		if strings.Contains(ep.Description, target.Name) ||
		   strings.Contains(strings.ToLower(ep.Path), strings.ToLower(target.Name)) {
			return true
        }
	}
	return false
}

// Helpers de extração (reutilizados de openapi_parser.go)
func extractString(m map[string]interface{}, key string, defaultVal string) string {
	if val, ok := m[key].(string); ok {
		return val
	}
	return defaultVal
}

func extractBool(m map[string]interface{}, key string, defaultVal bool) bool {
	if val, ok := m[key].(bool); ok {
		return val
	}
	return defaultVal
}

func extractFloat(m map[string]interface{}, key string, defaultVal float64) float64 {
	if val, ok := m[key].(float64); ok {
		return val
	}
	return defaultVal
}
