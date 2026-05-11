// cli/commands/game_parse.go
package commands

import (
	"fmt"
	"os"
	"path/filepath"

	"arkhe_os/parser/frontends"
	"arkhe_os/parser/lfir"
	"github.com/spf13/cobra"
)

var gameParseCmd = &cobra.Command{
	Use:   "parse --file <path> --engine <unity|steam>",
	Short: "Parse Unity scenes or Steam manifests into LFIR graphs",
	Long: `Analyze game development artifacts and calculate coherence scores.

Supported engines:
  unity  - Parse .prefab, .unity, .asset files
  steam  - Parse .vdf, .acf, .manifest files

Examples:
  arkhe game parse --file MainMenu.unity --engine unity
  arkhe game parse --file appmanifest_123456.acf --engine steam`,
	RunE: runGameParse,
}

var (
	parseFile    string
	parseEngine  string
	parseOutput  string
	parseVerbose bool
)

func init() {
	gameParseCmd.Flags().StringVarP(&parseFile, "file", "f", "", "Path to game artifact file (required)")
	gameParseCmd.Flags().StringVarP(&parseEngine, "engine", "e", "", "Game engine: unity or steam (required)")
	gameParseCmd.Flags().StringVarP(&parseOutput, "output", "o", "", "Output path for LFIR graph JSON")
	gameParseCmd.Flags().BoolVarP(&parseVerbose, "verbose", "v", false, "Verbose output")
	gameParseCmd.MarkFlagRequired("file")
	gameParseCmd.MarkFlagRequired("engine")
}

// Dummy interface for Parser to compile if it's not exported globally
type Parser interface {
	Parse(source []byte, filename string, metadata map[string]interface{}) (*lfir.LFIRGraph, error)
}

func runGameParse(cmd *cobra.Command, args []string) error {
	if parseFile == "" || parseEngine == "" {
		return fmt.Errorf("--file and --engine are required")
	}

	// Read file
	source, err := os.ReadFile(parseFile)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	// Select parser based on engine
	var p Parser
	switch parseEngine {
	case "unity":
		p = frontends.NewUnityPrefabParser()
	case "steam":
		p = frontends.NewSteamVDFParser()
	default:
		return fmt.Errorf("unsupported engine: %s (supported: unity, steam)", parseEngine)
	}

	// Parse
	graph, err := p.Parse(source, filepath.Base(parseFile), nil)
	if err != nil {
		return fmt.Errorf("parse failed: %w", err)
	}

	// Output results
	if parseVerbose {
		fmt.Printf("🎮 ARKHE.D %s Analysis — %s\n", parseEngine, filepath.Base(parseFile))
		fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

		if parseEngine == "unity" {
			printUnityStats(graph)
		} else {
			printSteamStats(graph)
		}
	}

	// Print coherence summary

	rootNodeID := graph.RootNodes[0]
	var root *lfir.LFIRNode
	if n, ok := graph.Nodes[rootNodeID]; ok {
		root = n
	} else {
		for _, n := range graph.Nodes {
			if n.ID == rootNodeID {
				root = n
				break
			}
		}
	}

	coherence := 0.0
	if root != nil {
		if c, ok := root.Attributes["coherence_score"].(float64); ok {
			coherence = c
		}
	}

	status := "✅"
	if coherence < 0.7 {
		status = "⚠️"
	}
	if coherence < 0.5 {
		status = "❌"
	}
	fmt.Printf("• Φ_C = %.2f %s\n", coherence, status)

	return nil
}

func printUnityStats(graph *lfir.LFIRGraph) {
	rootNodeID := graph.RootNodes[0]
	var node *lfir.LFIRNode
	if n, ok := graph.Nodes[rootNodeID]; ok {
		node = n
	} else {
		for _, n := range graph.Nodes {
			if n.ID == rootNodeID {
				node = n
				break
			}
		}
	}

	if node == nil {
		return
	}

	fmt.Printf("• GameObjects: %d (ativos: %d)\n",
		node.Attributes["total_gameobjects"],
		node.Attributes["active_gameobjects"])
	fmt.Printf("• Componentes: %d scripts, %d renderers\n",
		node.Attributes["script_count"],
		node.Attributes["renderer_count"])

	if missing, ok := node.Attributes["missing_references"].(int); ok && missing > 0 {
		fmt.Printf("• Referências quebradas: %d ⚠️\n", missing)
	}

	if drawCalls, ok := node.Attributes["estimated_draw_calls"].(int); ok {
		fmt.Printf("• Draw calls estimadas: %d\n", drawCalls)
	}

	fmt.Printf("• Utilização: %.2f\n", node.Attributes["coherence_utilization"])
	fmt.Printf("• Integridade: %.2f\n", node.Attributes["coherence_integrity"])
	fmt.Printf("• Performance: %.2f\n", node.Attributes["coherence_performance"])
}

func printSteamStats(graph *lfir.LFIRGraph) {
	rootNodeID := graph.RootNodes[0]
	var node *lfir.LFIRNode
	if n, ok := graph.Nodes[rootNodeID]; ok {
		node = n
	} else {
		for _, n := range graph.Nodes {
			if n.ID == rootNodeID {
				node = n
				break
			}
		}
	}

	if node == nil {
		return
	}

	fmt.Printf("• App ID: %s\n", node.Attributes["app_id"])
	fmt.Printf("• Depots: %d\n", node.Attributes["depot_count"])
	fmt.Printf("• Tamanho total: %.2f GB\n", node.Attributes["total_size_gb"])
	fmt.Printf("• Arquivos: %d\n", node.Attributes["file_count"])

	if achCount, ok := node.Attributes["achievement_count"].(int); ok && achCount > 0 {
		fmt.Printf("• Achievements: %d\n", achCount)
	}

	if missing, ok := node.Attributes["missing_files"].(int); ok && missing > 0 {
		fmt.Printf("• Arquivos faltantes: %d ⚠️\n", missing)
	}

	if rate, ok := node.Attributes["build_success_rate"].(float64); ok {
		fmt.Printf("• Taxa de sucesso de builds: %.1f%%\n", rate*100)
	}
}
