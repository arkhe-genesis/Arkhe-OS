// arkhe_os/compiler/treesitter_frontend.go
//go:build cgo
// +build cgo

package compiler

import (
    "fmt"
    "strings"
    "sync"

    "github.com/arkhe-os/arkhe/parser/lfir"
/*
#cgo LDFLAGS: -L${SRCDIR}/lib -ltree-sitter
#include <tree_sitter/api.h>
#include <stdlib.h>

// Wrapper para TSLanguage*
typedef const TSLanguage* TSLanguagePtr;

// Funções helper para CGo
TSLanguagePtr ts_language_for_name(const char* name);
*/
import "C"
import (
	"fmt"
	"strings"
	"sync"

	"github.com/arkhe-os/arkhe/parser/lfir"
	tree_sitter "github.com/tree-sitter/go-tree-sitter"
)

// TreeSitterFrontend encapsula parser tree-sitter para uma linguagem
type TreeSitterFrontend struct {
    language     string
    grammarPath  string  // Cambo para .so/.dylib compilada
    initialized  bool
    mu           sync.Mutex
    catalog      *LanguageCatalog
	language    string
	grammarPath string // Cambo para .so/.dylib compilada
	tsLanguage  *tree_sitter.Language
	parser      *tree_sitter.Parser
	initialized bool
	mu          sync.Mutex
}

// SupportedTreeSitterLanguages retorna lista de gramáticas disponíveis
func SupportedTreeSitterLanguages() []string {
    return []string{
        "bash", "c", "cpp", "c_sharp", "css", "dart", "dockerfile",
        "elixir", "erlang", "go", "haskell", "html", "java",
        "javascript", "json", "julia", "kotlin", "lua", "make",
        "markdown", "nix", "ocaml", "perl", "php", "python",
        "r", "ruby", "rust", "scala", "scheme", "sql",
        "swift", "toml", "typescript", "verilog", "vim",
        "yaml", "zig", "xml", "regex", "query",
    }
	return []string{
		"bash", "c", "cpp", "c_sharp", "css", "dart", "dockerfile",
		"elixir", "erlang", "go", "haskell", "html", "java",
		"javascript", "json", "julia", "kotlin", "lua", "make",
		"markdown", "nix", "ocaml", "perl", "php", "python",
		"r", "ruby", "rust", "scala", "scheme", "sql",
		"swift", "toml", "typescript", "verilog", "vim",
		"yaml", "zig", "xml", "regex", "query",
	}
}

// NewTreeSitterFrontend cria frontend para linguagem específica
func NewTreeSitterFrontend(language string, grammarPath string) (*TreeSitterFrontend, error) {
    frontend := &TreeSitterFrontend{
        language:    language,
        grammarPath: grammarPath,
        catalog:     NewLanguageCatalog(),
    }

    if err := frontend.initialize(); err != nil {
        return nil, fmt.Errorf("failed to initialize tree-sitter for %s: %w", language, err)
    }

    return frontend, nil
}

func (t *TreeSitterFrontend) initialize() error {
    t.mu.Lock()
    defer t.mu.Unlock()

    if t.initialized {
        return nil
    }
    t.initialized = true

    return nil
}


type ParseOptions struct {
    EnableTypeInference bool
    PreserveComments bool
	frontend := &TreeSitterFrontend{
		language:    language,
		grammarPath: grammarPath,
	}

	if err := frontend.initialize(); err != nil {
		return nil, fmt.Errorf("failed to initialize tree-sitter for %s: %w", language, err)
	}

	return frontend, nil
}

func (t *TreeSitterFrontend) initialize() error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if t.initialized {
		return nil
	}

	// Em produção: carregar gramática compilada do filesystem
	// Aqui: usar bindings go-tree-sitter pré-compilados
	var tsLang *tree_sitter.Language

	// Mapear nome ARKHE para nome tree-sitter
	tsName := t.language
	nameMap := map[string]string{
		"csharp":     "c_sharp",
		"objectivec": "objc",
		"javascript": "javascript",
		"typescript": "typescript",
	}
	if mapped, ok := nameMap[t.language]; ok {
		tsName = mapped
	}

	// Obter linguagem tree-sitter (em produção: carregar dinamicamente)
	tsLang = getTreeSitterLanguage(tsName)
	if tsLang == nil {
		return fmt.Errorf("tree-sitter grammar not found for: %s", t.language)
	}

	// Criar parser
	t.parser = tree_sitter.NewParser()
	t.parser.SetLanguage(tsLang)
	t.tsLanguage = tsLang
	t.initialized = true

	return nil
}

// getTreeSitterLanguage retorna linguagem tree-sitter por nome
// (em produção: carregar de .so via dlopen)
func getTreeSitterLanguage(name string) *tree_sitter.Language {
	// Mapeamento simplificado - em produção: gerar automaticamente
	grammarMap := map[string]*tree_sitter.Language{
		"bash":       tree_sitter.GetLanguage(tree_sitter.LanguageBash),
		"c":          tree_sitter.GetLanguage(tree_sitter.LanguageC),
		"cpp":        tree_sitter.GetLanguage(tree_sitter.LanguageCpp),
		"c_sharp":    tree_sitter.GetLanguage(tree_sitter.LanguageC_sharp),
		"css":        tree_sitter.GetLanguage(tree_sitter.LanguageCss),
		"dart":       tree_sitter.GetLanguage(tree_sitter.LanguageDart),
		"dockerfile": tree_sitter.GetLanguage(tree_sitter.LanguageDockerfile),
		"elixir":     tree_sitter.GetLanguage(tree_sitter.LanguageElixir),
		"erlang":     tree_sitter.GetLanguage(tree_sitter.LanguageErlang),
		"go":         tree_sitter.GetLanguage(tree_sitter.LanguageGo),
		"haskell":    tree_sitter.GetLanguage(tree_sitter.LanguageHaskell),
		"html":       tree_sitter.GetLanguage(tree_sitter.LanguageHtml),
		"java":       tree_sitter.GetLanguage(tree_sitter.LanguageJava),
		"javascript": tree_sitter.GetLanguage(tree_sitter.LanguageJavascript),
		"json":       tree_sitter.GetLanguage(tree_sitter.LanguageJson),
		"julia":      tree_sitter.GetLanguage(tree_sitter.LanguageJulia),
		"kotlin":     tree_sitter.GetLanguage(tree_sitter.LanguageKotlin),
		"lua":        tree_sitter.GetLanguage(tree_sitter.LanguageLua),
		"make":       tree_sitter.GetLanguage(tree_sitter.LanguageMake),
		"markdown":   tree_sitter.GetLanguage(tree_sitter.LanguageMarkdown),
		"nix":        tree_sitter.GetLanguage(tree_sitter.LanguageNix),
		"ocaml":      tree_sitter.GetLanguage(tree_sitter.LanguageOcaml),
		"perl":       tree_sitter.GetLanguage(tree_sitter.LanguagePerl),
		"php":        tree_sitter.GetLanguage(tree_sitter.LanguagePhp),
		"python":     tree_sitter.GetLanguage(tree_sitter.LanguagePython),
		"r":          tree_sitter.GetLanguage(tree_sitter.LanguageR),
		"ruby":       tree_sitter.GetLanguage(tree_sitter.LanguageRuby),
		"rust":       tree_sitter.GetLanguage(tree_sitter.LanguageRust),
		"scala":      tree_sitter.GetLanguage(tree_sitter.LanguageScala),
		"scheme":     tree_sitter.GetLanguage(tree_sitter.LanguageScheme),
		"sql":        tree_sitter.GetLanguage(tree_sitter.LanguageSql),
		"swift":      tree_sitter.GetLanguage(tree_sitter.LanguageSwift),
		"toml":       tree_sitter.GetLanguage(tree_sitter.LanguageToml),
		"typescript": tree_sitter.GetLanguage(tree_sitter.LanguageTypescript),
		"verilog":    tree_sitter.GetLanguage(tree_sitter.LanguageVerilog),
		"vim":        tree_sitter.GetLanguage(tree_sitter.LanguageVim),
		"yaml":       tree_sitter.GetLanguage(tree_sitter.LanguageYaml),
		"zig":        tree_sitter.GetLanguage(tree_sitter.LanguageZig),
		"xml":        tree_sitter.GetLanguage(tree_sitter.LanguageXml),
		"regex":      tree_sitter.GetLanguage(tree_sitter.LanguageRegex),
		"query":      tree_sitter.GetLanguage(tree_sitter.LanguageQuery),
	}
	return grammarMap[name]
}

// Parse analisa código fonte usando tree-sitter e converte para LFIR
func (t *TreeSitterFrontend) Parse(source []byte, options ParseOptions) (*lfir.LFIRGraph, error) {
    t.mu.Lock()
    defer t.mu.Unlock()

    if !t.initialized {
        if err := t.initialize(); err != nil {
            return nil, err
        }
    }

    graph := lfir.NewLFIRGraph()
    return graph, nil
}

type GenerateOptions struct {
    OptimizeCode bool
    TargetArchitecture string
	t.mu.Lock()
	defer t.mu.Unlock()

	if !t.initialized {
		if err := t.initialize(); err != nil {
			return nil, err
		}
	}

	// Parse com tree-sitter
	tree, err := t.parser.ParseCtx(nil, source, nil)
	if err != nil {
		return nil, fmt.Errorf("tree-sitter parse error: %w", err)
	}

	rootNode := tree.RootNode()
	if rootNode.HasError() {
		return nil, fmt.Errorf("syntax error in %s code", t.language)
	}

	// Converter CST do tree-sitter para LFIR
	graph := lfir.NewLFIRGraph()

	// Criar nó raiz do módulo
	moduleNode := lfir.NewLFIRNode(lfir.LFIRModule, "main_"+t.language, t.language)
	moduleNode.Attributes["tree_sitter"] = true
	moduleNode.Attributes["language"] = t.language
	graph.AddNode(moduleNode)
	graph.RootNodes = append(graph.RootNodes, moduleNode.ID)

	// Percorrer CST e extrair construções de alto nível
	t.traverseCST(rootNode, source, moduleNode.ID, graph, options)

	return graph, nil
}

func (t *TreeSitterFrontend) traverseCST(
	node tree_sitter.Node,
	source []byte,
	parentID string,
	graph *lfir.LFIRGraph,
	options ParseOptions,
) {
	nodeType := node.Type()
	startPos := node.StartPoint()
	endPos := node.EndPoint()

	// Extrair texto do nó
	nodeText := string(source[node.StartByte():node.EndByte()])

	// Mapear tipos tree-sitter para tipos LFIR
	lfirType := t.mapNodeTypeToLFIR(nodeType, t.language)

	// Ignorar nós muito granulares ou de comentário
	if lfirType == lfir.LFIROperation && len(nodeText) < 4 {
		// Processar filhos diretamente no pai
		cursor := node.Walk()
		for cursor.GoToFirstChild() {
			t.traverseCST(cursor.CurrentNode(), source, parentID, graph, options)
		}
		return
	}

	// Criar nó LFIR
	lfirNode := lfir.NewLFIRNode(lfirType, nodeText, t.language)
	lfirNode.Attributes["start_line"] = startPos.Row + 1
	lfirNode.Attributes["end_line"] = endPos.Row + 1
	lfirNode.Attributes["tree_sitter_type"] = nodeType
	lfirNode.Attributes["is_named"] = node.IsNamed()

	// Adicionar metadados específicos da linguagem
	t.addLanguageSpecificMetadata(lfirNode, node, source)

	graph.AddNode(lfirNode)
	graph.Link(parentID, lfirNode.ID)

	// Recursivamente processar filhos nomeados
	cursor := node.Walk()
	for cursor.GoToFirstChild() {
		child := cursor.CurrentNode()
		if child.IsNamed() {
			t.traverseCST(child, source, lfirNode.ID, graph, options)
		}
	}
}

func (t *TreeSitterFrontend) mapNodeTypeToLFIR(tsType, language string) lfir.LFIRNodeType {
	// Mapeamento genérico baseado em padrões de nomenclatura
	switch {
	case strings.Contains(tsType, "function") || strings.Contains(tsType, "method") ||
		strings.Contains(tsType, "lambda") || strings.Contains(tsType, "proc") ||
		strings.Contains(tsType, "def"):
		return lfir.LFIRFunction

	case strings.Contains(tsType, "class") || strings.Contains(tsType, "struct") ||
		strings.Contains(tsType, "interface") || strings.Contains(tsType, "type") ||
		strings.Contains(tsType, "enum") || strings.Contains(tsType, "trait"):
		return lfir.LFIRType

	case strings.Contains(tsType, "variable") || strings.Contains(tsType, "identifier") &&
		!strings.Contains(tsType, "call") && !strings.Contains(tsType, "field"):
		return lfir.LFIRVariable

	case strings.Contains(tsType, "if") || strings.Contains(tsType, "switch") ||
		strings.Contains(tsType, "for") || strings.Contains(tsType, "while") ||
		strings.Contains(tsType, "match") || strings.Contains(tsType, "case"):
		return lfir.LFIRControlFlow

	case strings.Contains(tsType, "import") || strings.Contains(tsType, "include") ||
		strings.Contains(tsType, "require") || strings.Contains(tsType, "use") ||
		strings.Contains(tsType, "module"):
		return lfir.LFIRModule

	case strings.Contains(tsType, "call") || strings.Contains(tsType, "expression") ||
		strings.Contains(tsType, "binary") || strings.Contains(tsType, "unary") ||
		strings.Contains(tsType, "operator"):
		return lfir.LFIROperation

	case strings.Contains(tsType, "comment") || strings.Contains(tsType, "string") ||
		strings.Contains(tsType, "number") || strings.Contains(tsType, "literal") ||
		strings.Contains(tsType, "boolean") || strings.Contains(tsType, "null"):
		return lfir.LFIRMetadata

	default:
		// Fallback baseado em linguagem
		switch language {
		case "python", "ruby", "perl":
			if strings.Contains(tsType, "statement") || strings.Contains(tsType, "expression_statement") {
				return lfir.LFIROperation
			}
		case "c", "cpp", "rust", "go":
			if strings.Contains(tsType, "declaration") {
				return lfir.LFIRVariable
			}
		}
		return lfir.LFIROperation
	}
}

func (t *TreeSitterFrontend) addLanguageSpecificMetadata(
	lfirNode *lfir.LFIRNode,
	tsNode tree_sitter.Node,
	source []byte,
) {
	// Adicionar metadados específicos por linguagem
	switch t.language {
	case "python":
		if tsNode.Type() == "function_definition" {
			lfirNode.Attributes["async"] = strings.Contains(
				string(source[tsNode.StartByte():tsNode.EndByte()]), "async def")
		}
	case "javascript", "typescript":
		if tsNode.Type() == "arrow_function" {
			lfirNode.Attributes["arrow"] = true
		}
	case "rust":
		if tsNode.Type() == "function_item" {
			content := string(source[tsNode.StartByte():tsNode.EndByte()])
			lfirNode.Attributes["unsafe"] = strings.Contains(content, "unsafe fn")
			lfirNode.Attributes["async"] = strings.Contains(content, "async fn")
		}
	case "go":
		if tsNode.Type() == "method_declaration" {
			lfirNode.Attributes["method"] = true
		}
	}
}

// Generate converte LFIR para código da linguagem alvo (modo genérico)
func (t *TreeSitterFrontend) Generate(graph *lfir.LFIRGraph, options GenerateOptions) ([]byte, error) {
    // Implementação simplificada - backends específicos devem ser usados para produção
    var output strings.Builder

    output.WriteString(fmt.Sprintf("// Generated by ARKHE Polymath Parser\n"))
    output.WriteString(fmt.Sprintf("// Target: %s\n\n", t.language))

    for _, node := range graph.Nodes {
        switch node.Type {
        case lfir.LFIRFunction:
            output.WriteString(fmt.Sprintf("func %s() {\n", node.Name))
            output.WriteString("    // TODO: implement\n")
            output.WriteString("}\n\n")
        case lfir.LFIRType:
            output.WriteString(fmt.Sprintf("type %s struct {\n", node.Name))
            output.WriteString("    // TODO: fields\n")
            output.WriteString("}\n\n")
        }
    }

    return []byte(output.String()), nil
	// Implementação simplificada - backends específicos devem ser usados para produção
	var output strings.Builder

	output.WriteString(fmt.Sprintf("// Generated by ARKHE Polymath Parser\n"))
	output.WriteString(fmt.Sprintf("// Target: %s\n\n", t.language))

	for _, node := range graph.Nodes {
		switch node.Type {
		case lfir.LFIRFunction:
			output.WriteString(fmt.Sprintf("func %s() {\n", node.Name))
			output.WriteString("    // TODO: implement\n")
			output.WriteString("}\n\n")
		case lfir.LFIRType:
			output.WriteString(fmt.Sprintf("type %s struct {\n", node.Name))
			output.WriteString("    // TODO: fields\n")
			output.WriteString("}\n\n")
		}
	}

	return []byte(output.String()), nil
}

// GetLanguage retorna nome da linguagem
func (t *TreeSitterFrontend) GetLanguage() string {
    return t.language
	return t.language
}

// GetExtensions retorna extensões suportadas (delegado ao catálogo)
func (t *TreeSitterFrontend) GetExtensions() []string {
    if entry := t.catalog.LookupByLanguage(t.language); entry != nil {
        return entry.Extensions
    }
    return []string{}
}

type LanguageCapabilities struct {
    MaxRecursionDepth int
    SupportsAsync bool
    SupportsMetaprogramming bool
    SupportsGenerics bool
    HasTypeInference bool
    SupportsMacros bool
    HasPatternMatching bool
	// mock for now
	return []string{}
}

// GetCapabilities retorna capacidades da linguagem
func (t *TreeSitterFrontend) GetCapabilities() LanguageCapabilities {
    entry := t.catalog.LookupByLanguage(t.language)
    if entry == nil {
        return LanguageCapabilities{}
    }

    // Inferir capacidades baseado na linguagem
    caps := LanguageCapabilities{
        MaxRecursionDepth: 100, // padrão conservador
    }

    switch t.language {
    case "python", "javascript", "typescript", "ruby":
        caps.SupportsAsync = true
        caps.SupportsMetaprogramming = true
    case "rust", "go", "typescript", "scala":
        caps.SupportsGenerics = true
        caps.HasTypeInference = true
    case "rust", "c", "cpp", "scala":
        caps.SupportsMacros = true
    case "rust", "haskell", "scala", "ocaml":
        caps.HasPatternMatching = true
    }

    return caps
	// Inferir capacidades baseado na linguagem
	caps := LanguageCapabilities{
		MaxRecursionDepth: 100, // padrão conservador
	}

	switch t.language {
	case "python", "javascript", "typescript", "ruby":
		caps.SupportsAsync = true
		caps.SupportsMetaprogramming = true
	case "rust", "go", "typescript", "scala":
		caps.SupportsGenerics = true
		caps.HasTypeInference = true
	case "rust", "c", "cpp", "scala":
		caps.SupportsMacros = true
	case "rust", "haskell", "scala", "ocaml":
		caps.HasPatternMatching = true
	}

	return caps
}

// Validate verifica sintaxe usando tree-sitter
func (t *TreeSitterFrontend) Validate(source []byte) error {
    if !t.initialized {
        if err := t.initialize(); err != nil {
            return err
        }
    }

    return nil
	if !t.initialized {
		if err := t.initialize(); err != nil {
			return err
		}
	}

	tree, err := t.parser.ParseCtx(nil, source, nil)
	if err != nil {
		return err
	}

	if tree.RootNode().HasError() {
		// Encontrar primeiro erro para mensagem útil
		cursor := tree.RootNode().Walk()
		for cursor.GoToFirstChild() {
			if cursor.CurrentNode().IsError() {
				pos := cursor.CurrentNode().StartPoint()
				return fmt.Errorf("syntax error at line %d, column %d", pos.Row+1, pos.Column+1)
			}
		}
		return fmt.Errorf("syntax error in %s code", t.language)
	}

	return nil
}
