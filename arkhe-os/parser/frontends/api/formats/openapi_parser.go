package formats

import (
	"encoding/json"
	"fmt"
	"strings"

	"arkhe/parser/frontends/api/models"
	"gopkg.in/yaml.v3"
)

// ParseOpenAPI parseia especificação OpenAPI 3.x em modelo canônico
func ParseOpenAPI(source []byte) (*models.APISpecification, error) {
	// Tentar YAML primeiro, fallback para JSON
	var doc map[string]interface{}

	errYaml := yaml.Unmarshal(source, &doc)
	if errYaml != nil {
		errJson := json.Unmarshal(source, &doc)
		if errJson != nil {
			return nil, fmt.Errorf("failed to parse OpenAPI: YAML error (%v), JSON error (%v)", errYaml, errJson)
		}
	}

	spec := &models.APISpecification{
		Name:        extractString(doc, "info", "title"),
		Version:     extractString(doc, "info", "version"),
		Description: extractString(doc, "info", "description"),
		Services:    make([]models.Service, 0),
	}

	// Extrair servers (base URLs)
	servers := extractArray(doc, "servers")
	for _, server := range servers {
		if serverMap, ok := server.(map[string]interface{}); ok {
			spec.BaseURLs = append(spec.BaseURLs, extractString(serverMap, "url", ""))
		}
	}

	// Extrair componentes de segurança
	securitySchemes := extractMap(doc, "components", "securitySchemes")
	spec.AuthSchemes = parseAuthSchemes(securitySchemes)

	// Extrair paths → endpoints
	paths := extractMap(doc, "paths")
	endpoints, err := parseOpenAPIPaths(paths, spec.AuthSchemes)
	if err != nil {
		return nil, fmt.Errorf("failed to parse endpoints: %w", err)
	}

	// Agrupar endpoints por serviço (heurística: por tag ou prefixo de path)
	spec.Services = groupEndpointsByService(endpoints, doc)

	// Extrair componentes reutilizáveis (schemas, parameters, etc.)
	spec.Schemas = parseSchemas(extractMap(doc, "components", "schemas"))

	return spec, nil
}

// parseOpenAPIPaths converte seção "paths" do OpenAPI em lista de endpoints
func parseOpenAPIPaths(paths map[string]interface{}, authSchemes []models.AuthScheme) ([]models.Endpoint, error) {
	var endpoints []models.Endpoint

	for path, methods := range paths {
		methodMap, ok := methods.(map[string]interface{})
		if !ok {
			continue
		}

		for method, operation := range methodMap {
			// Ignorar chaves que não são métodos HTTP
			if !isValidHTTPMethod(method) {
				continue
			}

			opMap, ok := operation.(map[string]interface{})
			if !ok {
				continue
			}

			endpoint := models.Endpoint{
				Path:        path,
				Method:      strings.ToUpper(method),
				OperationID: extractString(opMap, "operationId", ""),
				Summary:     extractString(opMap, "summary", ""),
				Description: extractString(opMap, "description", ""),
				Tags:        extractStringArray(opMap, "tags"),
			}

			// Extrair parâmetros
			endpoint.Parameters = parseParameters(extractArray(opMap, "parameters"))

			// Extrair request body
			if requestBody, ok := opMap["requestBody"].(map[string]interface{}); ok {
				endpoint.RequestBody = parseRequestBody(requestBody)
			}

			// Extrair respostas
			endpoint.Responses = parseResponses(extractMap(opMap, "responses"))

			// Extrair segurança específica do endpoint
			endpoint.Security = parseEndpointSecurity(extractArray(opMap, "security"), authSchemes)

			// Extrair padrões de resiliência (via extensions x-)
			endpoint.Resilience = parseResilienceHints(opMap)

			endpoints = append(endpoints, endpoint)
		}
	}

	return endpoints, nil
}

// parseAuthSchemes extrai esquemas de autenticação de OpenAPI
func parseAuthSchemes(schemes map[string]interface{}) []models.AuthScheme {
	var authSchemes []models.AuthScheme

	for name, scheme := range schemes {
		schemeMap, ok := scheme.(map[string]interface{})
		if !ok {
			continue
		}

		authType := extractString(schemeMap, "type", "")
		authScheme := models.AuthScheme{
			Name:        name,
			Type:        mapOpenAPIAuthType(authType),
			Description: extractString(schemeMap, "description", ""),
		}

		switch authType {
		case "http":
			authScheme.Scheme = extractString(schemeMap, "scheme", "")
			authScheme.BearerFormat = extractString(schemeMap, "bearerFormat", "")
		case "apiKey":
			authScheme.In = extractString(schemeMap, "in", "")
			authScheme.ParamName = extractString(schemeMap, "name", "")
		case "oauth2":
			authScheme.Flows = parseOAuthFlows(extractMap(schemeMap, "flows"))
		case "openIdConnect":
			authScheme.OpenIDConnectURL = extractString(schemeMap, "openIdConnectUrl", "")
		}

		authSchemes = append(authSchemes, authScheme)
	}

	return authSchemes
}

// mapOpenAPIAuthType mapeia tipo OpenAPI para tipo canônico
func mapOpenAPIAuthType(openapiType string) models.AuthType {
	switch openapiType {
	case "http":
		return models.AuthTypeHTTP
	case "apiKey":
		return models.AuthTypeAPIKey
	case "oauth2":
		return models.AuthTypeOAuth2
	case "openIdConnect":
		return models.AuthTypeOIDC
	default:
		return models.AuthTypeUnknown
	}
}

// parseParameters extrai parâmetros de endpoint
func parseParameters(params []interface{}) []models.Parameter {
	var parameters []models.Parameter

	for _, param := range params {
		paramMap, ok := param.(map[string]interface{})
		if !ok {
			continue
		}

		p := models.Parameter{
			Name:        extractString(paramMap, "name", ""),
			In:          extractString(paramMap, "in", ""), // path, query, header, cookie
			Required:    extractBool(paramMap, "required", false),
			Description: extractString(paramMap, "description", ""),
		}

		// Extrair schema do parâmetro
		if schema, ok := paramMap["schema"].(map[string]interface{}); ok {
			p.Schema = parseSchema(schema)
		}

		parameters = append(parameters, p)
	}

	return parameters
}

// parseSchema extrai schema JSON de parâmetro ou response
func parseSchema(schema map[string]interface{}) models.Schema {
	return models.Schema{
		Type:        extractString(schema, "type", ""),
		Format:      extractString(schema, "format", ""),
		Description: extractString(schema, "description", ""),
		Example:     schema["example"],
		// ... extrair mais campos conforme necessário
	}
}

// parseResponses extrai definições de resposta
func parseResponses(responses map[string]interface{}) []models.Response {
	var respList []models.Response

	for code, resp := range responses {
		respMap, ok := resp.(map[string]interface{})
		if !ok {
			continue
		}

		r := models.Response{
			StatusCode:  code,
			Description: extractString(respMap, "description", ""),
		}

		// Extrair content/schema da resposta
		if content, ok := respMap["content"].(map[string]interface{}); ok {
			r.Content = parseContent(content)
		}

		respList = append(respList, r)
	}

	return respList
}

// parseResilienceHints extrai dicas de resiliência de extensions OpenAPI (x-)
func parseResilienceHints(opMap map[string]interface{}) models.ResilienceHints {
	hints := models.ResilienceHints{}

	// Extrair extensions x-resilience-* ou x-retry, x-timeout, etc.
	if retry, ok := opMap["x-retry"].(map[string]interface{}); ok {
		hints.Retry = &models.RetryPolicy{
			MaxAttempts: int(extractFloat(retry, "max_attempts", 3)),
			Backoff:     extractString(retry, "backoff", "exponential"),
		}
	}

	if timeout, ok := opMap["x-timeout"].(string); ok {
		hints.Timeout = timeout
	}

	if circuitBreaker, ok := opMap["x-circuit-breaker"].(map[string]interface{}); ok {
		hints.CircuitBreaker = &models.CircuitBreakerConfig{
			FailureThreshold: int(extractFloat(circuitBreaker, "failure_threshold", 5)),
			RecoveryTimeout:  extractString(circuitBreaker, "recovery_timeout", "30s"),
		}
	}

	return hints
}

// groupEndpointsByService agrupa endpoints por serviço usando heurísticas
func groupEndpointsByService(endpoints []models.Endpoint, doc map[string]interface{}) []models.Service {
	// Heurística 1: Agrupar por tag
	tagGroups := make(map[string][]models.Endpoint)
	for _, ep := range endpoints {
		if len(ep.Tags) > 0 {
			tag := ep.Tags[0] // Usar primeira tag como agrupador
			tagGroups[tag] = append(tagGroups[tag], ep)
		} else {
			// Fallback: agrupar por prefixo de path
			prefix := extractPathPrefix(ep.Path)
			tagGroups[prefix] = append(tagGroups[prefix], ep)
		}
	}

	// Converter grupos em serviços
	var services []models.Service
	for tagName, eps := range tagGroups {
		service := models.Service{
			Name:      tagName,
			Protocol:  "REST",
			Endpoints: eps,
		}
		services = append(services, service)
	}

	return services
}

// Helpers de extração
func extractString(m map[string]interface{}, keys ...string) string {
	current := m
	for i, key := range keys {
		if i == len(keys)-1 {
			if val, ok := current[key].(string); ok {
				return val
			}
			return ""
		}
		if next, ok := current[key].(map[string]interface{}); ok {
			current = next
		} else {
			return ""
		}
	}
	return ""
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
	// Also attempt type assertion to int and float32 and convert to float64
	if val, ok := m[key].(int); ok {
		return float64(val)
	}
	if val, ok := m[key].(float32); ok {
		return float64(val)
	}
	return defaultVal
}

func extractArray(m map[string]interface{}, keys ...string) []interface{} {
	current := m
	for i, key := range keys {
		if i == len(keys)-1 {
			if val, ok := current[key].([]interface{}); ok {
				return val
			}
			return nil
		}
		if next, ok := current[key].(map[string]interface{}); ok {
			current = next
		} else {
			return nil
		}
	}
	return nil
}

func extractMap(m map[string]interface{}, keys ...string) map[string]interface{} {
	current := m
	for i, key := range keys {
		if i == len(keys)-1 {
			if val, ok := current[key].(map[string]interface{}); ok {
				return val
			}
			return nil
		}
		if next, ok := current[key].(map[string]interface{}); ok {
			current = next
		} else {
			return nil
		}
	}
	return nil
}

func extractStringArray(m map[string]interface{}, key string) []string {
	if arr, ok := m[key].([]interface{}); ok {
		var result []string
		for _, item := range arr {
			if str, ok := item.(string); ok {
				result = append(result, str)
			}
		}
		return result
	}
	return nil
}

func isValidHTTPMethod(method string) bool {
	valid := map[string]bool{
		"get": true, "post": true, "put": true, "patch": true,
		"delete": true, "head": true, "options": true, "trace": true,
	}
	return valid[strings.ToLower(method)]
}

func extractPathPrefix(path string) string {
	// Extrair primeiro segmento do path como prefixo
	// /users/{id}/posts → users
	parts := strings.Split(strings.Trim(path, "/"), "/")
	if len(parts) > 0 && parts[0] != "" {
		return parts[0]
	}
	return "default"
}

// TODO: Implement parseRequestBody, parseEndpointSecurity, parseSchemas, parseOAuthFlows, parseContent
func parseRequestBody(body map[string]interface{}) *models.RequestBody {
    return &models.RequestBody{}
}

func parseEndpointSecurity(security []interface{}, schemes []models.AuthScheme) []models.SecurityRequirement {
    var reqs []models.SecurityRequirement
    for _, sec := range security {
        if secMap, ok := sec.(map[string]interface{}); ok {
            for schemeName, _ := range secMap {
                reqs = append(reqs, models.SecurityRequirement{SchemeName: schemeName})
            }
        }
    }
    return reqs
}

func parseSchemas(schemas map[string]interface{}) map[string]models.Schema {
    return make(map[string]models.Schema)
}

func parseOAuthFlows(flows map[string]interface{}) map[string]interface{} {
    return make(map[string]interface{})
}

func parseContent(content map[string]interface{}) map[string]models.MediaType {
    res := make(map[string]models.MediaType)
    for k := range content {
        res[k] = models.MediaType{}
    }
    return res
}
