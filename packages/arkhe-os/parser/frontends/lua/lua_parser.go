// parser/frontends/lua/lua_parser.go
package lua

import (
	"fmt"
	"path/filepath"
	"time"

	"arkhe/parser/frontends/lua/ast"
	"arkhe/parser/frontends/lua/lfir"
	arkhelfir "arkhe/parser/lfir"
)

// LuaParser implementa Parser para arquivos Lua (.lua, .luac)
type LuaParser struct {
	ParseBytecode   bool   // Tentar parsear bytecode .luac
	MaxTableDepth   int    // Limite de aninhamento de tabelas para coerência
	StrictMode      bool   // Rejeitar acesso a globais não declarados
	DetectPatterns  bool   // Detectar anti-patterns de segurança
}

// NewLuaParser cria parser com configurações padrão
func NewLuaParser() *LuaParser {
	return &LuaParser{
		ParseBytecode:  true,
		MaxTableDepth:  10,
		StrictMode:     false,
		DetectPatterns: true,
	}
}

func (p *LuaParser) GetLanguage() string { return "lua" }

func (p *LuaParser) GetExtensions() []string {
	return []string{".lua", ".luac"}
}

// Parse é o método principal
func (p *LuaParser) Parse(source []byte, filename string, metadata map[string]interface{}) (*arkhelfir.LFIRGraph, error) {
	graph := arkhelfir.NewLFIRGraph()
	root := arkhelfir.NewLFIRNode(
		arkhelfir.LFIRNodeTypeModule,
		fmt.Sprintf("lua_script_%s_%d", filepath.Base(filename), time.Now().Unix()),
		"lua",
	)
	graph.AddNode(root)
	graph.RootNodes = append(graph.RootNodes, root.ID)

	// Detectar formato: source Lua ou bytecode
	if p.ParseBytecode && isLuaBytecode(source) {
		return p.parseBytecode(source, graph, root.ID, filename)
	}

	// Parse source Lua
	astRoot, err := ast.Parse(source, filename)
	if err != nil {
		return nil, fmt.Errorf("falha ao parsear AST Lua: %w", err)
	}

	// Converter AST → LFIR
	lfirBuilder := lfir.NewLuaLFIRBuilder(graph, root.ID)
	if err := lfirBuilder.Build(astRoot); err != nil {
		return nil, fmt.Errorf("falha ao construir LFIR: %w", err)
	}

	// Analisar semântica específica de Lua
	analyzer := NewLuaAnalyzer(p)
	metrics, err := analyzer.Analyze(astRoot, graph)
	if err != nil {
		return nil, fmt.Errorf("falha na análise semântica: %w", err)
	}

	// Calcular coerência
	coherence := lfir.CalculateLuaCoherence(metrics, p.getConfig())

	// Atualizar root com métricas
	root.Attributes["filename"] = filename
	root.Attributes["line_count"] = metrics.LineCount
	root.Attributes["function_count"] = metrics.FunctionCount
	root.Attributes["table_count"] = metrics.TableCount
	root.Attributes["coroutine_count"] = metrics.CoroutineCount
	root.Attributes["cyclomatic_complexity"] = metrics.CyclomaticComplexity
	root.Attributes["max_table_depth"] = metrics.MaxTableDepth
	root.Attributes["unsafe_patterns"] = metrics.UnsafePatternCount
	root.Attributes["coherence_score"] = coherence
	root.Attributes["coherence_clarity"] = metrics.ClarityScore
	root.Attributes["coherence_extensibility"] = metrics.ExtensibilityScore
	root.Attributes["coherence_safety"] = metrics.SafetyScore

	graph.Metrics.CoherenceScore = coherence
	graph.Metrics.NodeCount = metrics.TotalNodes
	graph.Metrics.EdgeCount = metrics.TotalEdges

	return graph, nil
}

// isLuaBytecode detecta magic number de bytecode Lua (0x1B 0x4C 0x75 0x61)
func isLuaBytecode(source []byte) bool {
	if len(source) < 4 {
		return false
	}
	return source[0] == 0x1B && source[1] == 0x4C &&
		source[2] == 0x75 && source[3] == 0x61
}

// parseBytecode processa arquivos .luac (implementação futura)
func (p *LuaParser) parseBytecode(source []byte, graph *arkhelfir.LFIRGraph, parentID, filename string) (*arkhelfir.LFIRGraph, error) {
	// Placeholder: bytecode parsing requer deserialização do formato Lua
	// Implementação completa exigiria portar o descompilador de Lua para Go
	root := graph.Nodes[parentID]
	root.Attributes["format"] = "lua_bytecode"
	root.Attributes["bytecode_size"] = len(source)
	root.Attributes["coherence_score"] = 0.7 // Baseline conservativa
	root.Attributes["note"] = "bytecode parsing not fully implemented"
	graph.Metrics.CoherenceScore = 0.7
	return graph, nil
}

// getConfig retorna configuração para cálculo de coerência
func (p *LuaParser) getConfig() *lfir.LuaCoherenceConfig {
	return &lfir.LuaCoherenceConfig{
		ClarityWeight:       0.35,
		ExtensibilityWeight: 0.30,
		SafetyWeight:        0.25,
		ComplexityPenalty:   0.10,
		MaxTableDepth:       p.MaxTableDepth,
		StrictMode:          p.StrictMode,
	}
}
