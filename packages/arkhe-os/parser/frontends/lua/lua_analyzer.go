package lua

import (
	"arkhe/parser/frontends/lua/analyzer"
	"arkhe/parser/frontends/lua/ast"
	"arkhe/parser/frontends/lua/lfir"
	arkhelfir "arkhe/parser/lfir"
)

type LuaAnalyzer struct {
	parser *LuaParser
}

func NewLuaAnalyzer(p *LuaParser) *LuaAnalyzer {
	return &LuaAnalyzer{
		parser: p,
	}
}

func (a *LuaAnalyzer) Analyze(root *ast.Node, graph *arkhelfir.LFIRGraph) (*lfir.LuaMetrics, error) {
	metrics := &lfir.LuaMetrics{}

	// Table graph
	tg := analyzer.NewTableGraph()
	tableCount, maxTableDepth := tg.Analyze(root)
	metrics.TableCount = tableCount
	metrics.MaxTableDepth = maxTableDepth
	metrics.AvgNestingDepth = float64(maxTableDepth) / 2.0 // Simplified

	// Coroutine flow
	cf := analyzer.NewCoroutineFlowAnalyzer()
	metrics.CoroutineCount = cf.Analyze(root)

	// Metamethod tracker
	mt := analyzer.NewMetamethodTracker()
	totalMetas, wellDocMetas := mt.Analyze(root)
	metrics.TotalMetamethods = totalMetas
	metrics.WellDocumentedMetas = wellDocMetas

	// Safety checker
	sc := analyzer.NewSafetyChecker()
	unsafeCount, _ := sc.Check(root)
	metrics.UnsafePatternCount = unsafeCount

	// Basic metrics calculation from AST
	var walk func(*ast.Node)
	walk = func(node *ast.Node) {
		if node == nil {
			return
		}
		if node.Type == ast.NodeFunction {
			metrics.FunctionCount++
		}
		if node.Type == ast.NodeLiteral {
			metrics.TotalLiterals++
			if attr, ok := node.Attributes["literal_type"]; ok && attr == "number" {
				if node.Value != "0" && node.Value != "1" {
					metrics.MagicNumberCount++
				}
			}
		}
		if node.Type == ast.NodeIfStmt || node.Type == ast.NodeForStmt || node.Type == ast.NodeWhileStmt || node.Type == ast.NodeRepeatStmt {
			metrics.CyclomaticComplexity++
		}
		for _, child := range node.Children {
			walk(child)
		}
	}
	walk(root)

	// In real impl, we'd count nodes/edges
	metrics.TotalNodes = len(graph.Nodes)
	metrics.TotalEdges = len(graph.Edges)

	return metrics, nil
}
