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
}
