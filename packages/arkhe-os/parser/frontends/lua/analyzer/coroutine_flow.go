package analyzer

import (
	"arkhe/parser/frontends/lua/ast"
)

type CoroutineFlowAnalyzer struct {}

func NewCoroutineFlowAnalyzer() *CoroutineFlowAnalyzer {
	return &CoroutineFlowAnalyzer{}
}

func (c *CoroutineFlowAnalyzer) Analyze(root *ast.Node) int {
	coroCount := 0

	var walk func(*ast.Node)
	walk = func(node *ast.Node) {
		if node == nil {
			return
		}
		if node.Type == ast.NodeCallExpr && len(node.Children) > 0 && node.Children[0].Type == ast.NodeIndexExpr {
			if len(node.Children[0].Children) > 1 {
				if obj, ok := node.Children[0].Children[0].Value.(string); ok && obj == "coroutine" {
					if method, ok := node.Children[0].Children[1].Value.(string); ok && method == "create" {
						coroCount++
					}
				}
			}
		}
		for _, child := range node.Children {
			walk(child)
		}
	}
	walk(root)
	return coroCount
}
