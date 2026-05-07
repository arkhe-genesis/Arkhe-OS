// ═══════════════════════════════════════════════════════
// ARKHE OS — CLI: API Parse Command
// ═══════════════════════════════════════════════════════

package commands

import (
	"context"
	"fmt"
	"log"

	"arkhe.os/parser/frontends/api"
)

// RunAPIParse executes the api-parse command
func RunAPIParse(sourceFile string, enableMetrics bool) error {
	log.Printf("Starting API parsing for: %s", sourceFile)

	options := api.APIParserOptions{
		EnableCoherenceMetrics: enableMetrics,
		InferSecuritySchemas:   true,
	}

	parser := api.NewAPIFrontend(options)

	node, err := parser.Parse(context.Background(), sourceFile)
	if err != nil {
		return fmt.Errorf("parsing failed: %w", err)
	}

	log.Printf("Successfully parsed API into LFIR. Root Node: %s, Children: %d", node.Name, len(node.Children))
	return nil
}
