// ═══════════════════════════════════════════════════════
// ARKHE OS — OpenAPI/Swagger Parser
// ═══════════════════════════════════════════════════════

package formats

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"strings"

	"arkhe/parser/frontends/api/models"
)

// ParseOpenAPI reads a file and converts it to our internal APIInfrastructure model
func ParseOpenAPI(filePath string) (*models.APIInfrastructure, error) {
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("read error: %w", err)
	}

	// Simplified JSON parsing for demonstration
	// In production, use standard go-openapi or kin-openapi libraries
	var raw map[string]interface{}
	if err := json.Unmarshal(data, &raw); err != nil {
		// Try YAML if JSON fails
		return nil, fmt.Errorf("JSON parse error: %w", err)
	}

	api := &models.APIInfrastructure{
		SourceType: "OpenAPI",
		Endpoints:  make([]models.Endpoint, 0),
		Components: make([]models.Component, 0),
	}

	// Extract Info
	if info, ok := raw["info"].(map[string]interface{}); ok {
		if title, ok := info["title"].(string); ok {
			api.Name = title
		}
		if version, ok := info["version"].(string); ok {
			api.Version = version
		}
	}

	// Extract Paths
	if paths, ok := raw["paths"].(map[string]interface{}); ok {
		for pathName, pathData := range paths {
			methods, ok := pathData.(map[string]interface{})
			if !ok {
				continue
			}

			for method, opData := range methods {
				// skip extensions like x-amazon-apigateway-integration
				if strings.HasPrefix(method, "x-") {
					continue
				}

				endpoint := models.Endpoint{
					Path:   pathName,
					Method: strings.ToUpper(method),
				}

				op, ok := opData.(map[string]interface{})
				if !ok {
					continue
				}

				if opId, ok := op["operationId"].(string); ok {
					endpoint.OperationID = opId
				}

				// Basic Security inference
				if security, ok := op["security"]; ok && security != nil {
					endpoint.RequiresAuth = true
				}

				api.Endpoints = append(api.Endpoints, endpoint)
			}
		}
	}

	return api, nil
}

// Stub for Protobuf
func ParseProtobuf(filePath string) (*models.APIInfrastructure, error) {
	return &models.APIInfrastructure{SourceType: "gRPC"}, nil
}

// Stub for GraphQL
func ParseGraphQL(filePath string) (*models.APIInfrastructure, error) {
	return &models.APIInfrastructure{SourceType: "GraphQL"}, nil
}
