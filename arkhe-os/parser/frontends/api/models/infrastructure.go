package models

// APIInfrastructure represents the canonical state of an API
type APIInfrastructure struct {
	Name       string
	Version    string
	SourceType string // "OpenAPI", "gRPC", "GraphQL", etc.
	Endpoints  []Endpoint
	Components []Component
}

// Endpoint represents an API route or method
type Endpoint struct {
	Path         string
	Method       string
	OperationID  string
	RequiresAuth bool
	LatencyBudget int // ms
}

// Component represents schemas, security schemes, etc.
type Component struct {
	Name string
	Type string
}
