package analyzer

import (
	"arkhe/parser/frontends/lua/ast"
)

type MetamethodTracker struct {}

func NewMetamethodTracker() *MetamethodTracker {
	return &MetamethodTracker{}
}

func (m *MetamethodTracker) Analyze(root *ast.Node) (int, int) {
	totalMetas := 0
	wellDocMetas := 0

	var walk func(*ast.Node)
	walk = func(node *ast.Node) {
		if node == nil {
			return
		}
		if node.Type == ast.NodeMetamethod {
			totalMetas++
			if !hasSideEffects(node) {
				wellDocMetas++
			}
		} else if node.Type == ast.NodeTableField {
			// Check if key is string and starts with __
			if keyNode, ok := node.Attributes["key"].(*ast.Node); ok {
				if keyStr, ok := keyNode.Value.(string); ok && len(keyStr) > 2 && keyStr[:2] == "__" {
					totalMetas++
					if !hasSideEffects(node) {
						wellDocMetas++
					}
					// Also mark it as metamethod to help safety checker
					node.Type = ast.NodeMetamethod
					node.Value = keyStr
				}
			} else if keyStr, ok := node.Attributes["key"].(string); ok && len(keyStr) > 2 && keyStr[:2] == "__" {
				// Handle fallback if parser stores keys directly as string instead of *ast.Node
				totalMetas++
				if !hasSideEffects(node) {
					wellDocMetas++
				}
				node.Type = ast.NodeMetamethod
				node.Value = keyStr
			} else if len(node.Children) > 0 && node.Children[0].Type == ast.NodeIdentifier {
			    // Array style with implicit string key that might be a metamethod name
			    if keyStr, ok := node.Children[0].Value.(string); ok && len(keyStr) > 2 && keyStr[:2] == "__" {
			        totalMetas++
					if !hasSideEffects(node) {
						wellDocMetas++
					}
					node.Type = ast.NodeMetamethod
					node.Value = keyStr
			    }
			}
		} else if node.Type == ast.NodeFunction {
			// Check if function name is a metamethod (e.g. Entity:__tostring)
			if name, ok := node.Value.(string); ok && len(name) > 2 {
			    isMetamethod := name[:2] == "__"
			    if !isMetamethod && len(name) >= 10 && name[len(name)-10:] == "__tostring" {
			        isMetamethod = true
			    }
			    if !isMetamethod && len(name) >= 7 && name[len(name)-7:] == "__index" {
			        isMetamethod = true
			    }
			    if !isMetamethod && len(name) >= 10 && name[len(name)-10:] == "__newindex" {
			        isMetamethod = true
			    }

			    if isMetamethod {
				    totalMetas++
				    if !hasSideEffects(node) {
					    wellDocMetas++
				    }
				    node.Type = ast.NodeMetamethod
				}
			}
		}

		for _, child := range node.Children {
			walk(child)
		}
	}
	walk(root)
	return totalMetas, wellDocMetas
}
