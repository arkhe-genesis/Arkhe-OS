package frontends

import (
	"strings"
	"sync"
	"time"

	"github.com/arkhe-os/arkhe/parser/lfir"
)

// GooseFrontend parser Goose recipes and config -> LFIR
type GooseFrontend struct {
	mu      sync.Mutex
}

func NewGooseFrontend() *GooseFrontend { return &GooseFrontend{} }

func (g *GooseFrontend) GetLanguage() string { return "goose" }
func (g *GooseFrontend) GetExtensions() []string { return []string{".goosehints", "AGENTS.md", ".ts", ".tsx", ".rs"} }

func (g *GooseFrontend) Parse(source string) (*lfir.LFIRGraph, error) {
	start := time.Now()
	graph := lfir.NewLFIRGraph()

	module := lfir.NewLFIRNode(lfir.LFIRModule, "goose_configuration", "goose")
	graph.AddNode(module)
	graph.RootNodes = append(graph.RootNodes, module.ID)

	lines := strings.Split(source, "\n")
	for i, line := range lines {
		trimmed := strings.TrimSpace(line)

		if trimmed == "" {
			continue
		}

		if strings.HasPrefix(trimmed, "import ") || strings.HasPrefix(trimmed, "use ") {
			node := lfir.NewLFIRNode(lfir.LFIRType, "goose_import", "goose")
			node.Attributes["line"] = i + 1
			node.Attributes["content"] = trimmed
			graph.AddNode(node)
			graph.Link(module.ID, node.ID)
			continue
		}

		if strings.HasPrefix(trimmed, "function ") || strings.HasPrefix(trimmed, "fn ") {
			node := lfir.NewLFIRNode(lfir.LFIRFunction, "goose_function", "goose")
			node.Attributes["line"] = i + 1
			node.Attributes["content"] = trimmed
			graph.AddNode(node)
			graph.Link(module.ID, node.ID)
			continue
		}

		if strings.HasPrefix(trimmed, "#") {
			continue
		}

        // Just basic parsing to map lines to LFIR metadata nodes
        node := lfir.NewLFIRNode(lfir.LFIRMetadata, "goose_rule", "goose")
        node.Attributes["line"] = i + 1
        node.Attributes["content"] = trimmed
        graph.AddNode(node)
        graph.Link(module.ID, node.ID)
	}

	graph.Metrics.ParseTimeMs = float64(time.Since(start).Milliseconds())
	graph.Metrics.TotalNodes = len(graph.Nodes)

	return graph, nil
}
