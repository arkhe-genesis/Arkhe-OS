package models

type APISpecification struct {
	Name           string
	Version        string
	Description    string
	BaseURLs       []string
	Services       []Service
	AuthSchemes    []AuthScheme
	Schemas        map[string]Schema
	Infrastructure *InfrastructureSpec
}

type Service struct {
	Name            string
	Protocol        string
	Version         string
	Description     string
	BaseURL         string
	Endpoints       []Endpoint
	Tags            []string
	ContractMetrics *ContractMetrics
}

type Endpoint struct {
	Path        string
	Method      string
	OperationID string
	Summary     string
	Description string
	Tags        []string
	Parameters  []Parameter
	RequestBody *RequestBody
	Responses   []Response
	Security    []SecurityRequirement
	Resilience  ResilienceHints
}

type Parameter struct {
	Name        string
	In          string
	Required    bool
	Description string
	Schema      Schema
}

type RequestBody struct {
    // ...
}

type Response struct {
	StatusCode  string
	Description string
	Content     map[string]MediaType
}

type MediaType struct {
    // ...
}

type Schema struct {
	Type        string
	Format      string
	Description string
	Example     interface{}
}

type SecurityRequirement struct {
    SchemeName string
}

type ResilienceHints struct {
	Retry          *RetryPolicy
	Timeout        string
	CircuitBreaker *CircuitBreakerConfig
}

type ContractMetrics struct {
	Clarity      float64
	Completeness float64
}
