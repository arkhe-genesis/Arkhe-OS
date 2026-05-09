// cli/commands/agi_parse.go
package commands

import (
	"fmt"
	"os"
	"path/filepath"

	"arkhe/parser/frontends/agi"
	"arkhe/parser/lfir"
	"github.com/spf13/cobra"
)

var AgiParseCmd = &cobra.Command{
	Use:   "agi-parse --file <spec.yaml|json>",
	Short: "Parse AGI system specifications into LFIR graphs with coherence metrics",
	Long: `Analyze AGI system specifications for architectural coherence, value alignment, and safety robustness.

Supported inputs:
  • YAML or JSON specifications defining values, goals, modules, and safety mechanisms.

Key analyses:
  • Value Alignment: Analyzes instrumental risk and goal conflicts.
  • Architectural Coherence: Analyzes module integration.
  • Safety Robustness: Analyzes verifiable properties and fallback behaviors.

Examples:
  arkhe agi parse --file spec.yaml
  arkhe agi parse --file spec.json --output lfir.json`,
	RunE: runAgiParse,
}

var (
	agiFile    string
	agiOutput  string
	agiVerbose bool
)

func init() {
	AgiParseCmd.Flags().StringVarP(&agiFile, "file", "f", "", "Path to AGI specification file (required)")
	AgiParseCmd.Flags().StringVarP(&agiOutput, "output", "o", "", "Output path for LFIR JSON")
	AgiParseCmd.Flags().BoolVarP(&agiVerbose, "verbose", "v", false, "Verbose output with detailed metrics")
	AgiParseCmd.MarkFlagRequired("file")
}

func runAgiParse(cmd *cobra.Command, args []string) error {
var agiParseCmd = &cobra.Command{
	Use:   "parse --file <agi_spec.yaml> [--framework <langchain|autogen>]",
	Short: "Parse AGI system specifications into LFIR graphs with coherence metrics",
	Long: `Analyze AGI architectures for cognitive coherence, value alignment, and safety robustness.

Supported formats:
  • YAML/JSON AGI specifications
  • Markdown specs with embedded code/prompts
  • Python/JS files with AGI spec annotations
  • LLM prompt collections with system architecture

Key analyses:
  • Module integration: interface clarity, dependency cycles, communication protocols
  • Goal consistency: conflict detection, criteria measurability, priority alignment
  • Value alignment: preference transitivity, contradiction detection, instrumental convergence risks
  • Safety robustness: formal verifiability, redundancy, corrigibility, interruptibility
  • Meta-cognition: uncertainty calibration, self-model accuracy, reflection loops
  • Emergence detection: phase transitions, capability jumps, goal drift risks

Examples:
  arkhe agi parse --file aligned_assistant.yaml
  arkhe agi parse --file agent.py --framework langchain --verify-safety
  arkhe agi parse --file spec.md --detect-emergence --output lfir.json`,
	RunE: runAGIParse,
}

var (
	agiFile           string
	agiFramework      string
	agiVerifySafety   bool
	agiDetectEmergence bool
	agiOutput         string
	agiVerbose        bool
)

func init() {
	agiParseCmd.Flags().StringVarP(&agiFile, "file", "f", "", "Path to AGI specification file (required)")
	agiParseCmd.Flags().StringVarP(&agiFramework, "framework", "k", "generic", "AGI framework: langchain, autogen, llm_orchestration, generic")
	agiParseCmd.Flags().BoolVar(&agiVerifySafety, "verify-safety", true, "Verify safety properties formally")
	agiParseCmd.Flags().BoolVar(&agiDetectEmergence, "detect-emergence", true, "Detect potential emergence risks")
	agiParseCmd.Flags().StringVarP(&agiOutput, "output", "o", "", "Output path for LFIR JSON")
	agiParseCmd.Flags().BoolVarP(&agiVerbose, "verbose", "v", false, "Verbose output with detailed metrics")
	agiParseCmd.MarkFlagRequired("file")
}

func runAGIParse(cmd *cobra.Command, args []string) error {
	if agiFile == "" {
		return fmt.Errorf("--file is required")
	}

	// Read file
	source, err := os.ReadFile(agiFile)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	parser := agi.NewAGIParser()

	// Configure parser
	parser := agi.NewAGIParser()
	parser.Framework = agiFramework
	parser.VerifySafety = agiVerifySafety
	parser.DetectEmergence = agiDetectEmergence

	// Parse
	graph, err := parser.Parse(source, filepath.Base(agiFile), nil)
	if err != nil {
		return fmt.Errorf("parse failed: %w", err)
	}

	if agiVerbose {
		fmt.Printf("🧠 ARKHE AGI Analysis — %s\n", filepath.Base(agiFile))
		fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
		printAgiStats(graph)
	}

	// Verbose output
	if agiVerbose {
		fmt.Printf("🧠 ARKHE AGI Analysis — %s\n", filepath.Base(agiFile))
		fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
		printAGIStats(graph)
	}

	// Save output
	if agiOutput != "" {
		if err := graph.ToJSONFile(agiOutput); err != nil {
			return fmt.Errorf("failed to write output: %w", err)
		}
		fmt.Printf("✅ LFIR graph saved to %s\n", agiOutput)
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
	fmt.Printf("• Φ_C (AGI System Coherence) = %.2f %s\n", coherence, status)

	root := graph.Nodes[graph.RootNodes[0]]
	if emergenceRisks, ok := root.Attributes["emergence_risks"].(int); ok && emergenceRisks > 0 {
		fmt.Printf("⚠️  %d emergence risk(s) detected\n", emergenceRisks)
	}
	if conflictingGoals, ok := root.Attributes["conflicting_goals"].(int); ok && conflictingGoals > 0 {
		fmt.Printf("⚠️  Conflicting goals detected in specification\n")
	}
	if valueContradictions, ok := root.Attributes["value_contradictions"].(int); ok && valueContradictions > 0 {
		fmt.Printf("⚠️  %d unresolved value contradiction(s) found\n", valueContradictions)
	// Component breakdown
	root := graph.Nodes[graph.RootNodes[0]]
	fmt.Printf("\nComponent Scores:\n")
	fmt.Printf("  • Architecture: %.2f\n", root.Attributes["coherence_architecture"])
	fmt.Printf("  • Alignment: %.2f\n", root.Attributes["coherence_alignment"])
	fmt.Printf("  • Safety: %.2f\n", root.Attributes["coherence_safety"])
	fmt.Printf("  • Module Integration: %.2f\n", root.Attributes["coherence_module_integration"])
	fmt.Printf("  • Goal Consistency: %.2f\n", root.Attributes["coherence_goal_consistency"])
	fmt.Printf("  • Value Alignment: %.2f\n", root.Attributes["coherence_value_alignment"])
	fmt.Printf("  • Safety Robustness: %.2f\n", root.Attributes["coherence_safety_robustness"])

	// Alerts
	if conflicts, ok := root.Attributes["conflicting_goals"].(int); ok && conflicts > 0 {
		fmt.Printf("\n⚠️  %d conflicting goal pair(s) detected\n", conflicts)
	}
	if contradictions, ok := root.Attributes["value_contradictions"].(int); ok && contradictions > 0 {
		fmt.Printf("⚠️  %d value contradiction(s) found\n", contradictions)
	}
	if risks, ok := root.Attributes["high_risk_emergence"].(int); ok && risks > 0 {
		fmt.Printf("🔴 %d high-risk emergence scenario(s) detected — review recommended\n", risks)
	}
	if unverified, ok := root.Attributes["safety_verification_results"].([]interface{}); ok {
		unverifiedCount := countUnverifiedInResults(unverified)
		if unverifiedCount > 0 {
			fmt.Printf("⚠️  %d safety property/ies could not be formally verified\n", unverifiedCount)
		}
	}

	return nil
}

func printAgiStats(graph *lfir.LFIRGraph) {
	root := graph.Nodes[graph.RootNodes[0]]

	fmt.Printf("• System Name: %s\n", root.Attributes["system_name"])
	fmt.Printf("• Architecture: %s\n", root.Attributes["architecture_type"])
	fmt.Printf("• Modules: %d\n", root.Attributes["module_count"])
	fmt.Printf("• Goals: %d\n", root.Attributes["goal_count"])
	fmt.Printf("• Values: %d\n", root.Attributes["value_count"])
	fmt.Printf("• Safety Mechanisms: %d\n", root.Attributes["safety_mechanism_count"])

	if root.Attributes["coherence_architecture"] != nil {
		fmt.Printf("\nCoherence Components:\n")
		fmt.Printf("  • Architecture: %.2f\n", root.Attributes["coherence_architecture"])
		fmt.Printf("  • Alignment: %.2f\n", root.Attributes["coherence_alignment"])
		fmt.Printf("  • Safety: %.2f\n", root.Attributes["coherence_safety"])

		if metaCog := root.Attributes["coherence_meta_cognition"]; metaCog != nil {
			fmt.Printf("  • Meta-Cognition: %.2f\n", metaCog)
		}
	}
func printAGIStats(graph *lfir.LFIRGraph) {
	root := graph.Nodes[graph.RootNodes[0]]

	fmt.Printf("• Sistema: %s (%s)\n", root.Attributes["system_name"], root.Attributes["architecture_type"])
	fmt.Printf("• Módulos cognitivos: %d\n", root.Attributes["module_count"])
	fmt.Printf("• Capacidades: %d\n", root.Attributes["capability_count"])
	fmt.Printf("• Objetivos: %d\n", root.Attributes["goal_count"])
	fmt.Printf("• Valores/Restrições: %d\n", root.Attributes["value_count"])
	fmt.Printf("• Mecanismos de segurança: %d\n", root.Attributes["safety_mechanism_count"])

	if metaScore, ok := root.Attributes["coherence_meta_cognition"].(float64); ok && metaScore > 0 {
		fmt.Printf("• Meta-cognição: %.2f\n", metaScore)
	}
}

func countUnverifiedInResults(results []interface{}) int {
	count := 0
	for _, r := range results {
		if result, ok := r.(map[string]interface{}); ok {
			if verified, ok := result["verified"].(bool); ok && !verified {
				count++
			}
		}
	}
	return count
}
