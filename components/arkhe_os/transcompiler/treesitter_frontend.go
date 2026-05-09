// treesitter_frontend.go — Frontend universal baseado em tree‑sitter
package arkhe

import (
	"fmt"
	"strings"
	"sync"
)

// TreeSitterFrontend encapsula um parser tree‑sitter para uma linguagem
type TreeSitterFrontend struct {
    language     string
    grammarPath  string  // caminho para a gramática compilada (.so/.dylib)
    initialized  bool
    mu           sync.Mutex
}

// SupportedTreeSitterLanguages lista todas as gramáticas disponíveis
func SupportedTreeSitterLanguages() []string {
    return []string{
        "bash", "c", "cpp", "csharp", "css", "dart", "dockerfile",
        "elixir", "erlang", "go", "haskell", "html", "java",
        "javascript", "json", "julia", "kotlin", "lua", "make",
        "markdown", "nix", "ocaml", "perl", "php", "python",
        "r", "ruby", "rust", "scala", "scheme", "sql",
        "swift", "toml", "typescript", "verilog", "vim",
        "yaml", "zig",
    }
}

func NewTreeSitterFrontend(language string) *TreeSitterFrontend {
	return &TreeSitterFrontend{
		language:    language,
		initialized: true, // Mock for now
	}
}

// Parse analisa código fonte usando tree‑sitter
func (t *TreeSitterFrontend) Parse(source string) (*LFIRGraph, error) {
    t.mu.Lock()
    defer t.mu.Unlock()

    if !t.initialized {
        return nil, fmt.Errorf("tree-sitter frontend for %s not initialized", t.language)
    }

    // Em produção, carregaria a gramática compilada e invocaria o parser
    // via CGo ou bindings Go do tree‑sitter
    graph := NewLFIRGraph()
    module := NewLFIRNode(LFIRModule, "main_"+t.language, t.language)
    graph.AddNode(module)
    graph.RootNodes = append(graph.RootNodes, module.ID)

    // Análise estrutural simulada (em produção, usaria a AST do tree‑sitter)
    lines := strings.Split(source, "\n")
    for i, line := range lines {
        trimmed := strings.TrimSpace(line)
        if trimmed == "" || strings.HasPrefix(trimmed, "//") || strings.HasPrefix(trimmed, "#") {
            continue
        }
        node := NewLFIRNode(LFIROperation, trimmed[:min(32, len(trimmed))], t.language)
        node.Attributes["line"] = i + 1
        node.Attributes["raw"] = trimmed
        graph.AddNode(node)
        graph.Link(module.ID, node.ID)
    }

    return graph, nil
}

func (t *TreeSitterFrontend) GetLanguage() string { return t.language }
func (t *TreeSitterFrontend) GetExtensions() []string {
    // Delegate ao catálogo
    return nil // preenchido pelo PolymathParser
}
