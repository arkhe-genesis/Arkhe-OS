// tests/api_xml_parser_test.go
package tests

import (
	"os"
	"testing"

	"arkhe/parser/frontends/api"
	"github.com/stretchr/testify/assert"
)

func TestAPIParser_XMLSpec(t *testing.T) {
	parser := api.NewAPIParser()
	parser.Framework = "generic"

	source, err := os.ReadFile("testdata/xml_api_spec.xml")
	assert.NoError(t, err)

	graph, err := parser.Parse(source, "enterprise_payments.xml", nil)
	assert.NoError(t, err)
	assert.NotNil(t, graph)

	root := graph.Nodes[graph.RootNodes[0]]

	// Basic metadata
	assert.Equal(t, "Enterprise Payment Gateway API", root.Attributes["system_name"])
	assert.Equal(t, "2.1.0", root.Attributes["version"])
	assert.Equal(t, 1, root.Attributes["service_count"])
	assert.Equal(t, 2, root.Attributes["endpoint_count"])

	// Security
	authCoverage := root.Attributes["coherence_auth_coverage"].(float64)
	assert.Equal(t, 1.0, authCoverage) // Both endpoints have bearerAuth

	// Resilience patterns detected
	resilience := root.Attributes["coherence_resilience"].(float64)
	assert.Greater(t, resilience, 0.4) // /payments/process has retry + CB

	// Overall coherence
	coherence := graph.Metrics.CoherenceScore
	assert.GreaterOrEqual(t, coherence, 0.0)
	assert.LessOrEqual(t, coherence, 1.0)
	assert.Greater(t, coherence, 0.85) // Well-specified XML spec
}
