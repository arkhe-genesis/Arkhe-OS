// parser/frontends/api/models/api_spec.go
package models

type AuthType string

const (
	AuthTypeHTTP   AuthType = "http"
	AuthTypeAPIKey AuthType = "apiKey"
	AuthTypeOAuth2 AuthType = "oauth2"
	AuthTypeOIDC   AuthType = "openIdConnect"
	AuthTypeUnknown AuthType = "unknown"
)

type APISpecification struct {
	Name        string
	Version     string
	Description string
	BaseURLs    []string
	AuthSchemes []AuthScheme
	Services    []Service
}

type AuthScheme struct {
	Name         string
	Type         AuthType
	Scheme       string
	BearerFormat string
}

type Service struct {
	Name      string
	Endpoints []Endpoint
}

type Endpoint struct {
	Path        string
	Method      string
	OperationID string
	Summary     string
	Tags        []string
	Security    []EndpointSecurity
	Parameters  []Parameter
	RequestBody RequestBody
	Responses   []Response
	Resilience  ResilienceConfig
}

type EndpointSecurity struct {
	SchemeName string
}

type Parameter struct {
	Name        string
	In          string
	Required    bool
	Description string
	Schema      Schema
}

type Schema struct {
	Type string
}

type RequestBody struct {
	Required bool
}

type Response struct {
	StatusCode  string
	Description string
}

type ResilienceConfig struct {
	Retry          *RetryPolicy
	CircuitBreaker *CircuitBreakerConfig
	Timeout        string
	Idempotency    *IdempotencyConfig
}

type RetryPolicy struct {
	MaxAttempts int
	Backoff     string
}

type CircuitBreakerConfig struct {
	FailureThreshold int
	Timeout          string
}

type IdempotencyConfig struct {
	Enabled     bool
	KeyLocation string
	KeyName     string
	TTL         string
}
