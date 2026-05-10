// cli/commands/lua_parse.go
package commands

import (
	"fmt"
	"os"
	"path/filepath"

	"arkhe/parser/frontends/lua"
	"arkhe/parser/lfir"
	"github.com/spf13/cobra"
)

var luaParseCmd = &cobra.Command{
	Use:   "parse --file <path.lua>",
	Short: "Parse Lua scripts into LFIR graphs with coherence metrics",
	Long: `Analyze Lua code for coherence, safety, and extensibility.

Supported features:
  • Table graph analysis with cycle detection
  • Coroutine flow tracking
  • Metamethod safety checking
  • C API binding mapping
  • Anti-pattern detection (loadstring, getfenv, etc.)

Examples:
  arkhe lua parse --file game_logic.lua
  arkhe lua parse --file config.lua --strict`,
	RunE: runLuaParse,
}

var (
	luaFile     string
	luaStrict   bool
	luaOutput   string
	luaVerbose  bool
)

func init() {
	luaParseCmd.Flags().StringVarP(&luaFile, "file", "f", "", "Path to Lua file (required)")
	luaParseCmd.Flags().BoolVarP(&luaStrict, "strict", "s", false, "Strict mode: flag undeclared globals")
	luaParseCmd.Flags().StringVarP(&luaOutput, "output", "o", "", "Output path for LFIR JSON")
	luaParseCmd.Flags().BoolVarP(&luaVerbose, "verbose", "v", false, "Verbose output with details")
	luaParseCmd.MarkFlagRequired("file")
}

func runLuaParse(cmd *cobra.Command, args []string) error {
	if luaFile == "" {
		return fmt.Errorf("--file is required")
	}

	// Read file
	source, err := os.ReadFile(luaFile)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	// Configure parser
	parser := lua.NewLuaParser()
	parser.StrictMode = luaStrict
	parser.DetectPatterns = true

	// Parse
	graph, err := parser.Parse(source, filepath.Base(luaFile), nil)
	if err != nil {
		return fmt.Errorf("parse failed: %w", err)
	}

	// Verbose output
	if luaVerbose {
		fmt.Printf("🌙 ARKHE Lua Analysis — %s\n", filepath.Base(luaFile))
		fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
		printLuaStats(graph)
	}

	// Save output
	if luaOutput != "" {
		if err := graph.ToJSONFile(luaOutput); err != nil {
			return fmt.Errorf("failed to write output: %w", err)
		}
		fmt.Printf("✅ LFIR graph saved to %s\n", luaOutput)
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
	fmt.Printf("• Φ_C = %.2f %s\n", coherence, status)

	// Safety warnings
	root := graph.Nodes[graph.RootNodes[0]]
	if unsafe, ok := root.Attributes["unsafe_patterns"].(int); ok && unsafe > 0 {
		fmt.Printf("⚠️  %d unsafe patterns detected (loadstring, getfenv, etc.)\n", unsafe)
	}

	return nil
}

func printLuaStats(graph *lfir.LFIRGraph) {
	root := graph.Nodes[graph.RootNodes[0]]

	fmt.Printf("• Linhas: %d\n", root.Attributes["line_count"])
	fmt.Printf("• Funções: %d\n", root.Attributes["function_count"])
	fmt.Printf("• Tabelas: %d\n", root.Attributes["table_count"])
	fmt.Printf("• Corrotinas: %d\n", root.Attributes["coroutine_count"])
	fmt.Printf("• Complexidade ciclomática: %d\n", root.Attributes["cyclomatic_complexity"])
	fmt.Printf("• Profundidade máxima de tabelas: %d\n", root.Attributes["max_table_depth"])

	if root.Attributes["coherence_clarity"] != nil {
		fmt.Printf("• Clareza: %.2f\n", root.Attributes["coherence_clarity"])
		fmt.Printf("• Extensibilidade: %.2f\n", root.Attributes["coherence_extensibility"])
		fmt.Printf("• Segurança: %.2f\n", root.Attributes["coherence_safety"])
	}
}
