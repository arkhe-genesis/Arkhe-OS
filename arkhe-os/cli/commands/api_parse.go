package commands

import (
	"fmt"
	"os"
	"path/filepath"

	"arkhe/parser/frontends/api"
    "arkhe/parser/lfir"
	"github.com/spf13/cobra"
)

var apiParseCmd = &cobra.Command{
	Use:   "parse --file <openapi.yaml|service.proto|infra.tf> [--framework <express|spring|fastapi>]",
	Short: "Parse API specs and infrastructure configs into LFIR graphs with coherence metrics",
	Long: `Analyze API architectures and infrastructure patterns for coherence, resilience, and best practices.

Supported formats:
  • OpenAPI/Swagger (YAML/JSON) for REST APIs
  • Protocol Buffers (.proto) for gRPC services
  • AsyncAPI for event-driven architectures
  • Terraform/Kubernetes configs for infrastructure
  • Annotated source code (Express, Spring, FastAPI)

Key analyses:
  • Contract clarity: parameter specs, error codes, examples
  • Protocol consistency: REST/gRPC/GraphQL alignment
  • Auth coverage: endpoints with/without authentication
  • Resilience patterns: circuit breakers, retries, timeouts
  • Infrastructure patterns: cache, queue, CDN, load balancing
  • Data strategies: sharding, replication, consistency models
  • Dependency analysis: cycles, single points of failure

Examples:
  arkhe api parse --file openapi.yaml
  arkhe api parse --file service.proto --framework spring
  arkhe api parse --file k8s-deployment.yaml --analyze-infra
  arkhe api parse --file main.py --framework fastapi --output lfir.json`,
	RunE: runAPIParse,
}

var (
	apiFile           string
	apiFramework      string
	apiAnalyzeInfra   bool
	apiAnalyzeResilience bool
	apiOutput         string
	apiVerbose        bool
)

func init() {
	apiParseCmd.Flags().StringVarP(&apiFile, "file", "f", "", "Path to API/infra spec file (required)")
	apiParseCmd.Flags().StringVarP(&apiFramework, "framework", "k", "generic", "Framework: express, spring, fastapi, generic")
	apiParseCmd.Flags().BoolVar(&apiAnalyzeInfra, "analyze-infra", true, "Analyze infrastructure patterns")
	apiParseCmd.Flags().BoolVar(&apiAnalyzeResilience, "analyze-resilience", true, "Analyze resilience patterns")
	apiParseCmd.Flags().StringVarP(&apiOutput, "output", "o", "", "Output path for LFIR JSON")
	apiParseCmd.Flags().BoolVarP(&apiVerbose, "verbose", "v", false, "Verbose output with detailed metrics")
	apiParseCmd.MarkFlagRequired("file")

    // Supondo que a gente tem um rootCmd onde a gente adiciona "api"
    // No contexto real, precisaríamos de `apiCmd` onde `apiParseCmd` é adicionado
}

func GetAPIParseCmd() *cobra.Command {
    return apiParseCmd
}

func runAPIParse(cmd *cobra.Command, args []string) error {
	if apiFile == "" {
		return fmt.Errorf("--file is required")
	}

	// Read file
	source, err := os.ReadFile(apiFile)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	// Configure parser
	parser := api.NewAPIParser()
	parser.Framework = apiFramework
	parser.AnalyzeInfra = apiAnalyzeInfra
	parser.AnalyzeResilience = apiAnalyzeResilience

	// Parse
	graph, err := parser.Parse(source, filepath.Base(apiFile), nil)
	if err != nil {
		return fmt.Errorf("parse failed: %w", err)
	}

	// Verbose output
	if apiVerbose {
		fmt.Printf("🌐 ARKHE API Analysis — %s\n", filepath.Base(apiFile))
		fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
		printAPIStats(graph)
	}

	// Save output
	if apiOutput != "" {
		if err := graph.ToJSONFile(apiOutput); err != nil {
			return fmt.Errorf("failed to write output: %w", err)
		}
		fmt.Printf("✅ LFIR graph saved to %s\n", apiOutput)
	}

	// Coherence summary
	coherence := graph.Metrics.CoherenceScore
	status := "✅"
	if coherence < 0.7 {
		status = "⚠️"
	}
	if coherence < 0.5 {
		status = "❌"
	}
	fmt.Printf("• Φ_C (API System Coherence) = %.2f %s\n", coherence, status)

	// Component breakdown
	root := graph.Nodes[graph.RootNodes[0]]
	fmt.Printf("\nComponent Scores:\n")
	fmt.Printf("  • Contract Clarity: %.2f\n", root.Attributes["coherence_contract_clarity"])
	fmt.Printf("  • Protocol Consistency: %.2f\n", root.Attributes["coherence_protocol_consistency"])
	fmt.Printf("  • Auth Coverage: %.2f\n", root.Attributes["coherence_auth_coverage"])
	fmt.Printf("  • Resilience Adequacy: %.2f\n", root.Attributes["coherence_resilience"])

	// Alerts
	if cycles, ok := root.Attributes["dependency_cycles"].(int); ok && cycles > 0 {
		fmt.Printf("\n⚠️  %d dependency cycle(s) detected — review service dependencies\n", cycles)
	}
	if spof, ok := root.Attributes["single_points_of_failure"].(int); ok && spof > 0 {
		fmt.Printf("⚠️  %d single point(s) of failure identified\n", spof)
	}
	if unauth, ok := root.Attributes["unauth_sensitive_endpoints"].(int); ok && unauth > 0 {
		fmt.Printf("🔴 %d sensitive endpoint(s) without authentication\n", unauth)
	}

	return nil
}

func printAPIStats(graph *lfir.LFIRGraph) {
	root := graph.Nodes[graph.RootNodes[0]]

	fmt.Printf("• Sistema: %v (v%v)\n", root.Attributes["system_name"], root.Attributes["version"])
	fmt.Printf("• Serviços: %v\n", root.Attributes["service_count"])
	fmt.Printf("• Endpoints: %v\n", root.Attributes["endpoint_count"])
	fmt.Printf("• Protocolos: %v\n", root.Attributes["protocol_count"])

	if infraCount, ok := root.Attributes["infrastructure_component_count"].(int); ok && infraCount > 0 {
		fmt.Printf("• Componentes de Infra: %d\n", infraCount)
	}

	if root.Attributes["dependency_cycles"] != nil {
		fmt.Printf("• Ciclos de Dependência: %v\n", root.Attributes["dependency_cycles"])
	}
}
