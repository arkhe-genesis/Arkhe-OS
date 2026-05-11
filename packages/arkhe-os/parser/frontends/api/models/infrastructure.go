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
// InfrastructureSpec representa a configuração de infraestrutura de um sistema de API
type InfrastructureSpec struct {
	Components []InfrastructureComponent `json:"components"`
	Network    NetworkConfig            `json:"network,omitempty"`
	Security   SecurityConfig           `json:"security,omitempty"`
	Monitoring MonitoringConfig         `json:"monitoring,omitempty"`
}

// InfrastructureComponent representa um componente de infraestrutura
type InfrastructureComponent struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        ComponentType          `json:"type"`
	Description string                 `json:"description,omitempty"`

	// Configuração específica por tipo
	Config      map[string]interface{} `json:"config"`

	// Conectividade
	ConnectsTo  []string               `json:"connects_to,omitempty"` // IDs de outros componentes
	ExposedPorts []int                 `json:"exposed_ports,omitempty"`

	// Recursos
	Resources   ResourceRequirements   `json:"resources,omitempty"`

	// Resiliência
	Replicas    int                    `json:"replicas,omitempty"`
	HealthCheck *HealthCheckConfig     `json:"health_check,omitempty"`

	// Metadados
	Metadata    map[string]interface{} `json:"metadata"`
}

// ComponentType define tipos de componentes de infraestrutura
type ComponentType string

const (
	// Compute
	TypeService       ComponentType = "service"        // Microserviço/API
	TypeFunction      ComponentType = "function"       // Serverless function
	TypeWorker        ComponentType = "worker"         // Background worker

	// Data
	TypeDatabase      ComponentType = "database"       // Banco de dados
	TypeCache         ComponentType = "cache"          // Cache (Redis, Memcached)
	TypeSearch        ComponentType = "search"         // Search engine (Elasticsearch)
	TypeObjectStore   ComponentType = "object_store"   // S3-compatible storage

	// Messaging
	TypeQueue         ComponentType = "queue"          // Message queue (RabbitMQ, SQS)
	TypeStream        ComponentType = "stream"         // Event stream (Kafka, Kinesis)
	TypeWebhook       ComponentType = "webhook"        // Webhook endpoint/receiver

	// Network
	TypeLoadBalancer  ComponentType = "load_balancer"  // LB (ALB, NGINX, HAProxy)
	TypeAPIGateway    ComponentType = "api_gateway"    // API Gateway (Kong, Apigee)
	TypeCDN           ComponentType = "cdn"            // Content Delivery Network
	TypeServiceMesh   ComponentType = "service_mesh"   // Istio, Linkerd

	// Security
	TypeAuthServer    ComponentType = "auth_server"    // OAuth2/OIDC provider
	TypeWAF           ComponentType = "waf"            // Web Application Firewall
	TypeSecretsStore  ComponentType = "secrets_store"  // Vault, AWS Secrets Manager

	// Observability
	TypeMetrics       ComponentType = "metrics"        // Prometheus, Datadog
	TypeLogs          ComponentType = "logs"           // ELK, Loki
	TypeTracing       ComponentType = "tracing"        // Jaeger, Zipkin
	TypeAlerting      ComponentType = "alerting"       // Alertmanager, PagerDuty
    TypeCircuitBreaker ComponentType = "circuit_breaker"
    TypeRateLimiter    ComponentType = "rate_limiter"
)

// ResourceRequirements especifica requisitos de recursos
type ResourceRequirements struct {
	CPU          string `json:"cpu,omitempty"`           // "500m", "2"
	Memory       string `json:"memory,omitempty"`        // "512Mi", "4Gi"
	Storage      string `json:"storage,omitempty"`       // "10Gi"
	NetworkBandwidth string `json:"network_bandwidth,omitempty"` // "1Gbps"
}

// HealthCheckConfig especifica configuração de health check
type HealthCheckConfig struct {
	Endpoint        string        `json:"endpoint"`
	Interval        string        `json:"interval"`          // "30s"
	Timeout         string        `json:"timeout"`           // "5s"
	HealthyThreshold int          `json:"healthy_threshold"` // 2
	UnhealthyThreshold int        `json:"unhealthy_threshold"` // 3
}

// NetworkConfig representa configuração de rede
type NetworkConfig struct {
	VPC             string   `json:"vpc,omitempty"`
	Subnets         []string `json:"subnets,omitempty"`
	SecurityGroups  []string `json:"security_groups,omitempty"`
	AllowedCIDRs    []string `json:"allowed_cidrs,omitempty"`
	TLSVersion      string   `json:"tls_version,omitempty"` // "1.2", "1.3"
}

// SecurityConfig representa configuração de segurança
type SecurityConfig struct {
	EncryptionAtRest    bool     `json:"encryption_at_rest"`
	EncryptionInTransit bool     `json:"encryption_in_transit"`
	SecretsManagement   string   `json:"secrets_management,omitempty"` // "vault", "aws_secrets"
	AuditLogging        bool     `json:"audit_logging"`
	Compliance          []string `json:"compliance,omitempty"` // "GDPR", "PCI-DSS", "HIPAA"
}

// MonitoringConfig representa configuração de observabilidade
type MonitoringConfig struct {
	MetricsEnabled    bool              `json:"metrics_enabled"`
	LogsEnabled       bool              `json:"logs_enabled"`
	TracingEnabled    bool              `json:"tracing_enabled"`
	AlertRules        []AlertRule       `json:"alert_rules,omitempty"`
	Dashboards        []string          `json:"dashboards,omitempty"` // Dashboard IDs/names
}

// AlertRule representa uma regra de alerta
type AlertRule struct {
	Name        string            `json:"name"`
	Condition   string            `json:"condition"` // PromQL, CloudWatch metric filter, etc.
	Severity    string            `json:"severity"`  // "critical", "warning", "info"
	Notification []string         `json:"notification"` // ["slack:channel", "pagerduty"]
}

// CachePattern representa padrão de uso de cache
type CachePattern struct {
	Type           string `json:"type"` // "read-through", "write-through", "write-behind", "cache-aside"
	TTL            string `json:"ttl,omitempty"`
	Invalidation   string `json:"invalidation,omitempty"` // "time-based", "event-based", "manual"
	KeyStrategy    string `json:"key_strategy,omitempty"`
}

// QueuePattern representa padrão de uso de fila
type QueuePattern struct {
	Type            string `json:"type"` // "work_queue", "pub_sub", "priority_queue", "delay_queue"
	DeliveryGuarantee string `json:"delivery_guarantee"` // "at-most-once", "at-least-once", "exactly-once"
	DeadLetterQueue string `json:"dead_letter_queue,omitempty"`
	RetryPolicy     *RetryPolicy `json:"retry_policy,omitempty"`
}

// EventStreamingConfig representa configuração de streaming de eventos
type EventStreamingConfig struct {
	Topic           string            `json:"topic"`
	Partitions      int               `json:"partitions,omitempty"`
	ReplicationFactor int             `json:"replication_factor,omitempty"`
	SchemaRegistry  string            `json:"schema_registry,omitempty"` // URL do schema registry
	Serialization   string            `json:"serialization"` // "json", "avro", "protobuf"
	Retention       string            `json:"retention,omitempty"` // "7d", "infinite"
}

// ResilienceConfig representa configuração de resiliência
type ResilienceConfig struct {
	CircuitBreaker *CircuitBreakerConfig `json:"circuit_breaker,omitempty"`
	Retry          *RetryPolicy          `json:"retry,omitempty"`
	Timeout        string                `json:"timeout,omitempty"`
	Bulkhead       *BulkheadConfig       `json:"bulkhead,omitempty"`
	RateLimiter    *RateLimitConfig      `json:"rate_limiter,omitempty"`
}

// CircuitBreakerConfig representa configuração de circuit breaker
type CircuitBreakerConfig struct {
	FailureThreshold    int    `json:"failure_threshold"`
	SuccessThreshold    int    `json:"success_threshold"`
	Timeout             string `json:"timeout"`
	HalfOpenMaxRequests int    `json:"half_open_max_requests,omitempty"`
    RecoveryTimeout     string `json:"recovery_timeout,omitempty"`
}

// RetryPolicy representa política de retry
type RetryPolicy struct {
	MaxAttempts      int     `json:"max_attempts"`
	InitialBackoff   string  `json:"initial_backoff"` // "100ms"
	MaxBackoff       string  `json:"max_backoff"`     // "30s"
	BackoffMultiplier float64 `json:"backoff_multiplier,omitempty"` // 2.0
	RetryableErrors  []string `json:"retryable_errors,omitempty"`  // HTTP status codes, error types
    Backoff          string  `json:"backoff,omitempty"`
}

// BulkheadConfig representa configuração de bulkhead (isolamento de recursos)
type BulkheadConfig struct {
	MaxConcurrentCalls int `json:"max_concurrent_calls"`
	MaxWaitDuration    string `json:"max_wait_duration,omitempty"`
}

// RateLimitConfig representa configuração de rate limiting
type RateLimitConfig struct {
	Strategy      string `json:"strategy"` // "fixed_window", "sliding_window", "token_bucket", "leaky_bucket"
	RequestsPer   int    `json:"requests_per"`
	Period        string `json:"period"` // "second", "minute", "hour"
	BurstSize     int    `json:"burst_size,omitempty"`
	Scope         string `json:"scope"` // "global", "per_user", "per_ip", "per_api_key"
}

// DataStrategy representa estratégia de dados distribuídos
type DataStrategy struct {
	ConsistencyModel string   `json:"consistency_model"` // "strong", "eventual", "causal", "session"
	Sharding         *ShardingConfig `json:"sharding,omitempty"`
	Replication      *ReplicationConfig `json:"replication,omitempty"`
	Indexing         []IndexConfig `json:"indexing,omitempty"`
}

// ShardingConfig representa configuração de sharding
type ShardingConfig struct {
	Strategy    string   `json:"strategy"` // "hash", "range", "geo", "directory"
	Key         string   `json:"key"`      // Field usado para sharding
	NumShards   int      `json:"num_shards,omitempty"`
	RebalanceOnScale bool `json:"rebalance_on_scale,omitempty"`
}

// ReplicationConfig representa configuração de replicação
type ReplicationConfig struct {
	Strategy      string   `json:"strategy"` // "leader-follower", "multi-leader", "leaderless"
	ReplicationFactor int  `json:"replication_factor"`
	SyncMode      string   `json:"sync_mode"` // "sync", "async", "semi-sync"
	ReadPreference string `json:"read_preference,omitempty"` // "primary", "secondary", "nearest"
}

// IndexConfig representa configuração de índice
type IndexConfig struct {
	Field     string   `json:"field"`
	Type      string   `json:"type"` // "btree", "hash", "fulltext", "geospatial", "composite"
	Unique    bool     `json:"unique,omitempty"`
	Options   map[string]interface{} `json:"options,omitempty"`
}

// WebhookConfig representa configuração de webhook
type WebhookConfig struct {
	URL                 string            `json:"url"`
	Events              []string          `json:"events"` // Event types this webhook subscribes to
	Secret              string            `json:"secret,omitempty"` // For signature verification
	RetryPolicy         *RetryPolicy      `json:"retry_policy,omitempty"`
	Timeout             string            `json:"timeout,omitempty"`
	ContentType         string            `json:"content_type"` // "application/json", "application/x-www-form-urlencoded"
	SignatureHeader     string            `json:"signature_header,omitempty"` // "X-Webhook-Signature"
}

// IdempotencyConfig representa configuração de idempotência
type IdempotencyConfig struct {
	Enabled         bool     `json:"enabled"`
	KeyLocation     string   `json:"key_location"` // "header", "query_param", "body_field"
	KeyName         string   `json:"key_name"`     // Name of the idempotency key
	TTL             string   `json:"ttl,omitempty"` // How long to keep idempotency records
	ConflictBehavior string  `json:"conflict_behavior"` // "return_cached", "return_error", "reprocess"
}
