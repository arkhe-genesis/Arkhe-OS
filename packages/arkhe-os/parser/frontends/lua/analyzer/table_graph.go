package analyzer

import (
	"arkhe/parser/frontends/lua/ast"
)

type TableGraph struct {}

func NewTableGraph() *TableGraph {
	return &TableGraph{}
}

func (t *TableGraph) Analyze(root *ast.Node) (int, int) {
	tableCount := 0
	maxDepth := 0

	var walk func(*ast.Node, int)
	walk = func(node *ast.Node, depth int) {
		if node == nil {
			return
		}
		if node.Type == ast.NodeTable {
			tableCount++
			if depth > maxDepth {
				maxDepth = depth
			}
			for _, child := range node.Children {
				walk(child, depth+1)
			}
		} else {
			for _, child := range node.Children {
				walk(child, depth)
			}
		}
	}

	walk(root, 1)
	return tableCount, maxDepth
}
