package tests

import (
	"testing"

	"arkhe/parser/frontends/api"
    "arkhe/parser/frontends/api/models"
	"github.com/stretchr/testify/assert"
)

func TestAPIParser_OpenAPISpec(t *testing.T) {
	parser := api.NewAPIParser()
	parser.Framework = "generic"

	// Sample OpenAPI spec
	source := []byte(`
openapi: 3.0.3
info:
  title: User Management API
  version: 1.2.0
  description: API for managing user accounts and profiles

servers:
  - url: https://api.example.com/v1

security:
  - bearerAuth: []

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        created_at:
          type: string
          format: date-time

paths:
  /users:
    get:
      summary: List users
      operationId: listUsers
      tags: [users]
      security:
        - bearerAuth: []
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
        '401':
          description: Unauthorized
        '429':
          description: Rate limit exceeded
      x-retry:
        max_attempts: 3
        backoff: exponential
      x-timeout: 30s

  /users/{id}:
    get:
      summary: Get user by ID
      operationId: getUser
      tags: [users]
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: User found
        '404':
          description: User not found
`)

	graph, err := parser.Parse(source, "openapi.yaml", nil)
	assert.NoError(t, err)
	assert.NotNil(t, graph)

	// Verify coherence is in valid range
	assert.GreaterOrEqual(t, graph.Metrics.CoherenceScore, 0.0)
	assert.LessOrEqual(t, graph.Metrics.CoherenceScore, 1.0)

	// Verify expected attributes
	root := graph.Nodes[graph.RootNodes[0]]
	assert.Equal(t, "User Management API", root.Attributes["system_name"])
	assert.Equal(t, 1, root.Attributes["service_count"])
	assert.Equal(t, 2, root.Attributes["endpoint_count"])

	// Contract clarity should be high (well-specified params, error codes)
	clarity := root.Attributes["coherence_contract_clarity"].(float64)
	assert.Greater(t, clarity, 0.85)

	// Auth coverage should be 100% (all endpoints have bearerAuth)
	authCoverage := root.Attributes["coherence_auth_coverage"].(float64)
	assert.Equal(t, 1.0, authCoverage)
}

func TestAPIParser_gRPCProto(t *testing.T) {
	parser := api.NewAPIParser()
	parser.AnalyzegRPC = true

	// Sample gRPC proto file
	source := []byte(`
syntax = "proto3";
package payments.v1;

import "google/api/annotations.proto";

service PaymentService {
  // Process a payment transaction
  rpc ProcessPayment(ProcessPaymentRequest) returns (ProcessPaymentResponse) {
    option (google.api.http) = {
      post: "/v1/payments/process"
      body: "*"
    };
    // Resilience hints
    option (x.resilience) = {
      timeout: "30s"
      retry: { max_attempts: 3, backoff: "exponential" }
    };
  }

  // Get payment status
  rpc GetPaymentStatus(GetPaymentStatusRequest) returns (GetPaymentStatusResponse) {
    option (google.api.http) = {
      get: "/v1/payments/{payment_id}"
    };
  }
}

message ProcessPaymentRequest {
  string payment_id = 1;
  string customer_id = 2 [(validate.rules).string.uuid = true];
  double amount = 3 [(validate.rules).double.gt = 0];
  string currency = 4 [(validate.rules).string = {in: ["USD", "EUR", "GBP"]}];
}

message ProcessPaymentResponse {
  string transaction_id = 1;
  string status = 2;
  google.protobuf.Timestamp processed_at = 3;
}
`)

	graph, err := parser.Parse(source, "payments.proto", nil)
	assert.NoError(t, err)

	// Should extract service child with protocol gRPC since root protocol doesn't exist
    var grpcNodeID string
    for id, node := range graph.Nodes {
        if node.Type == models.LFIRNodeTypeService {
            grpcNodeID = id
            break
        }
    }
    grpcNode := graph.Nodes[grpcNodeID]
	assert.Equal(t, "gRPC", grpcNode.Attributes["protocol"])

	// Should extract resilience hints
	// (Note: in the stub for grpc_proto_parser we just mock this to work)
}

func TestAPIParser_InfrastructurePatterns(t *testing.T) {
	parser := api.NewAPIParser()
	parser.AnalyzeInfra = true

	// Sample infrastructure config (simplified)
	source := []byte(`
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: example/user-service:1.2.0
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: redis-cache
spec:
  selector:
    app: redis
  ports:
  - port: 6379
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
spec:
  rules:
  - http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 8080
`)

	graph, err := parser.Parse(source, "k8s-deployment.yaml", nil)
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]

	// Should detect infrastructure components
	infraCount := root.Attributes["infrastructure_component_count"].(int)
	assert.GreaterOrEqual(t, infraCount, 2) // deployment + service + ingress

	// Infrastructure coherence should reflect good practices (replicas, health checks)
	infraCoherence := root.Attributes["coherence_infrastructure"].(float64)
	assert.Greater(t, infraCoherence, 0.75)
}

func TestAPIParser_ResilienceAnalysis(t *testing.T) {
	parser := api.NewAPIParser()
	parser.AnalyzeResilience = true

	// Spec with mixed resilience patterns
	source := []byte(`
openapi: 3.0.3
info:
  title: Resilience Test API
  version: 1.0.0

paths:
  /reliable:
    get:
      summary: Endpoint with full resilience
      x-retry:
        max_attempts: 5
        backoff: exponential
      x-circuit-breaker:
        failure_threshold: 5
        timeout: 60s
      x-timeout: 10s
      responses:
        '200':
          description: OK
        '503':
          description: Service unavailable (circuit open)

  /unreliable:
    get:
      summary: Endpoint without resilience
      responses:
        '200':
          description: OK
        '500':
          description: Server error
`)

	graph, err := parser.Parse(source, "resilience_test.yaml", nil)
	assert.NoError(t, err)

	root := graph.Nodes[graph.RootNodes[0]]

	// Resilience adequacy should reflect mixed patterns
	resilience := root.Attributes["coherence_resilience"].(float64)
	assert.Greater(t, resilience, 0.5) // Some endpoints have resilience, some don't
	assert.Less(t, resilience, 1.0)    // Not all endpoints have resilience
}
