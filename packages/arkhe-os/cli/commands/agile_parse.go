// cli/commands/agile_parse.go
package commands

import (
	"fmt"
	"os"
	"path/filepath"

	"arkhe/parser/frontends/agile"
	"arkhe/parser/lfir"
	"github.com/spf13/cobra"
)

var agileParseCmd = &cobra.Command{
	Use:   "parse --file <export.json> --tool <jira|trello|azure|github> --methodology <scrum|kanban>",
	Short: "Parse Scrum/Kanban artifacts into LFIR graphs with process coherence metrics",
	Long: `Analyze agile project management data for process health and flow coherence.

Supported tools:
  jira     - Jira Cloud/Server JSON exports
  trello   - Trello board JSON exports
  azure    - Azure DevOps work item exports
  github   - GitHub Projects data
  linear   - Linear.app exports
  generic  - Auto-detect from file structure

Methodologies:
  scrum    - Sprint-based analysis with velocity, commitment accuracy
  kanban   - Flow-based analysis with CFD, WIP limits, cycle time

Examples:
  arkhe agile parse --file sprint_report.json --tool jira --methodology scrum
  arkhe agile parse --file board_export.csv --tool trello --methodology kanban --detect-bottlenecks`,
	RunE: runAgileParse,
}

var (
	agileFile         string
	agileTool         string
	agileMethodology  string
	agileOutput       string
	agileVerbose      bool
	detectBottlenecks bool
	analyzeRetros     bool
)

func init() {
	agileParseCmd.Flags().StringVarP(&agileFile, "file", "f", "", "Path to agile export file (required)")
	agileParseCmd.Flags().StringVarP(&agileTool, "tool", "t", "generic", "Tool type: jira, trello, azure, github, linear, generic")
	agileParseCmd.Flags().StringVarP(&agileMethodology, "methodology", "m", "kanban", "Methodology: scrum or kanban")
	agileParseCmd.Flags().StringVarP(&agileOutput, "output", "o", "", "Output path for LFIR JSON")
	agileParseCmd.Flags().BoolVarP(&agileVerbose, "verbose", "v", false, "Verbose output with detailed metrics")
	agileParseCmd.Flags().BoolVar(&detectBottlenecks, "detect-bottlenecks", true, "Detect bottlenecks via CFD analysis")
	agileParseCmd.Flags().BoolVar(&analyzeRetros, "analyze-retros", true, "Analyze retrospective sentiment")
	agileParseCmd.MarkFlagRequired("file")
}

func runAgileParse(cmd *cobra.Command, args []string) error {
	if agileFile == "" {
		return fmt.Errorf("--file is required")
	}

	// Validate methodology
	if agileMethodology != "scrum" && agileMethodology != "kanban" {
		return fmt.Errorf("--methodology must be 'scrum' or 'kanban'")
	}

	// Read file
	source, err := os.ReadFile(agileFile)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	// Configure parser
	parser := agile.NewAgileParser()
	parser.ToolType = agileTool
	parser.Methodology = agileMethodology
	parser.DetectBottlenecks = detectBottlenecks
	parser.AnalyzeRetros = analyzeRetros

	// Parse
	graph, err := parser.Parse(source, filepath.Base(agileFile), nil)
	if err != nil {
		return fmt.Errorf("parse failed: %w", err)
	}

	// Verbose output
	if agileVerbose {
		fmt.Printf("📋 ARKHE Agile Analysis — %s (%s)\n", filepath.Base(agileFile), agileMethodology)
		fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
		printAgileStats(graph, agileMethodology)
	}

	// Save output
	if agileOutput != "" {
		if err := graph.ToJSONFile(agileOutput); err != nil {
			return fmt.Errorf("failed to write output: %w", err)
		}
		fmt.Printf("✅ LFIR graph saved to %s\n", agileOutput)
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
	fmt.Printf("• Φ_C (Process Coherence) = %.2f %s\n", coherence, status)

	// Methodology-specific insights
	root := graph.Nodes[graph.RootNodes[0]]
	if agileMethodology == "kanban" {
		if bottleneckCount, ok := root.Attributes["bottleneck_count"].(int); ok && bottleneckCount > 0 {
			fmt.Printf("⚠️  %d bottleneck(s) detected in workflow\n", bottleneckCount)
		}
		if wipExceeded, ok := root.Attributes["wip_exceeded"].(bool); ok && wipExceeded {
			fmt.Printf("⚠️  WIP limit exceeded in one or more columns\n")
		}
	} else { // scrum
		if commitmentAcc, ok := root.Attributes["commitment_accuracy"].(float64); ok && commitmentAcc < 0.8 {
			fmt.Printf("⚠️  Sprint commitment accuracy low: %.1f%%\n", commitmentAcc*100)
		}
		if scopeCreep, ok := root.Attributes["scope_creep_ratio"].(float64); ok && scopeCreep > 0.2 {
			fmt.Printf("⚠️  High scope creep during sprint: %.1f%%\n", scopeCreep*100)
		}
	}

	// Team health indicator
	if sentiment, ok := root.Attributes["retro_sentiment"].(map[string]interface{}); ok {
		if score, ok := sentiment["score"].(float64); ok {
			if score < -0.3 {
				fmt.Printf("🔴 Team sentiment concerning: %.2f\n", score)
			} else if score > 0.3 {
				fmt.Printf("🟢 Team sentiment positive: %.2f\n", score)
			}
		}
	}

	return nil
}

func printAgileStats(graph *lfir.LFIRGraph, methodology string) {
	root := graph.Nodes[graph.RootNodes[0]]

	fmt.Printf("• Ferramenta: %s\n", root.Attributes["tool_type"])
	fmt.Printf("• Metodologia: %s\n", root.Attributes["methodology"])
	fmt.Printf("• Total de itens: %d\n", root.Attributes["total_items"])
	fmt.Printf("• Itens concluídos: %d\n", root.Attributes["completed_items"])

	if methodology == "kanban" {
		fmt.Printf("• Cycle time médio: %.1f dias\n", root.Attributes["avg_cycle_time_days"])
		fmt.Printf("• Lead time médio: %.1f dias\n", root.Attributes["avg_lead_time_days"])
		fmt.Printf("• Eficiência de fluxo: %.1f%%\n", root.Attributes["flow_efficiency"].(float64)*100)
	} else { // scrum
		if vs, ok := root.Attributes["velocity_stability"].(float64); ok {
			fmt.Printf("• Estabilidade de velocidade: %.2f\n", vs)
		}
		if ca, ok := root.Attributes["commitment_accuracy"].(float64); ok {
			fmt.Printf("• Acurácia de compromisso: %.1f%%\n", ca*100)
		}
	}

	fmt.Printf("• Score de qualidade: %.2f\n", root.Attributes["quality_score"])
	if wr, ok := root.Attributes["waste_ratio"].(float64); ok {
		fmt.Printf("• Razão de desperdício: %.1f%%\n", wr*100)
	}

	if root.Attributes["coherence_flow"] != nil {
		fmt.Printf("\nComponentes de Φ_C:\n")
		fmt.Printf("  • Fluxo: %.2f\n", root.Attributes["coherence_flow"])
		fmt.Printf("  • Previsibilidade: %.2f\n", root.Attributes["coherence_predictability"])
		fmt.Printf("  • Qualidade: %.2f\n", root.Attributes["coherence_quality"])
	}
}
