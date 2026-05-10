// parser/frontends/lua/lfir/lua_nodes.go
package lfir

import (
	"fmt"
	"strings"

	"arkhe/parser/frontends/lua/ast"
	arkhelfir "arkhe/parser/lfir"
)

// Lua-specific LFIR node types
const (
	LFIRNodeTypeLuaFunction   arkhelfir.LFIRNodeType = "lua_function"
	LFIRNodeTypeLuaTable      arkhelfir.LFIRNodeType = "lua_table"
	LFIRNodeTypeLuaCoroutine  arkhelfir.LFIRNodeType = "lua_coroutine"
	LFIRNodeTypeLuaMetamethod arkhelfir.LFIRNodeType = "lua_metamethod"
	LFIRNodeTypeLuaCAPI       arkhelfir.LFIRNodeType = "lua_c_api"
)

// LuaLFIRBuilder converte AST Lua → grafo LFIR
type LuaLFIRBuilder struct {
	graph    *arkhelfir.LFIRGraph
	parentID string
	nodeMap  map[*ast.Node]string // AST node → LFIR node ID
}

func NewLuaLFIRBuilder(graph *arkhelfir.LFIRGraph, parentID string) *LuaLFIRBuilder {
	return &LuaLFIRBuilder{
		graph:    graph,
		parentID: parentID,
		nodeMap:  make(map[*ast.Node]string),
	}
}

// Build converte AST Lua para LFIR
func (b *LuaLFIRBuilder) Build(astRoot *ast.Node) error {
	return b.buildNode(astRoot, b.parentID)
}

func (b *LuaLFIRBuilder) buildNode(astNode *ast.Node, parentID string) error {
	if astNode == nil {
		return nil
	}

	// Criar nó LFIR correspondente
	lfirNode := b.astToLFIR(astNode)
	if lfirNode == nil {
		// Skip nodes that don't map to LFIR
		return nil
	}

	b.graph.AddNode(lfirNode)
	b.nodeMap[astNode] = lfirNode.ID

	// Link com parent
	if parentID != "" {
		b.graph.Link(parentID, lfirNode.ID)
	}

	// Recursivamente processar children
	for _, child := range astNode.Children {
		if err := b.buildNode(child, lfirNode.ID); err != nil {
			return err
		}
	}

	// Adicionar arestas semânticas específicas de Lua
	b.addLuaSemanticEdges(astNode, lfirNode)

	return nil
}

// astToLFIR mapeia tipos de nó AST para tipos LFIR
func (b *LuaLFIRBuilder) astToLFIR(astNode *ast.Node) *arkhelfir.LFIRNode {
	switch astNode.Type {
	case ast.NodeFunction:
		name := ""
		if astNode.Value != nil {
			name = astNode.Value.(string)
		}
		node := arkhelfir.NewLFIRNode(LFIRNodeTypeLuaFunction,
			fmt.Sprintf("fn_%s_%p", name, astNode), "lua")
		if name != "" {
			node.Attributes["name"] = name
		}
		if params, ok := astNode.Attributes["params"].([]string); ok {
			node.Attributes["param_count"] = len(params)
		}
		node.Attributes["body_lines"] = astNode.Attributes["body_lines"]
		return node

	case ast.NodeTable:
		node := arkhelfir.NewLFIRNode(LFIRNodeTypeLuaTable,
			fmt.Sprintf("table_%p", astNode), "lua")
		node.Attributes["field_count"] = astNode.Attributes["field_count"]
		node.Attributes["array_style"] = astNode.Attributes["array_style"]
		return node

	case ast.NodeCoroutine:
		node := arkhelfir.NewLFIRNode(LFIRNodeTypeLuaCoroutine,
			fmt.Sprintf("coro_%p", astNode), "lua")
		node.Attributes["created_at_line"] = astNode.Line
		return node

	case ast.NodeMetamethod:
		metaName := ""
		if astNode.Value != nil {
			metaName = astNode.Value.(string)
		}
		node := arkhelfir.NewLFIRNode(LFIRNodeTypeLuaMetamethod,
			fmt.Sprintf("meta_%s_%p", metaName, astNode), "lua")
		node.Attributes["metamethod_name"] = metaName
		node.Attributes["has_side_effects"] = astNode.Attributes["side_effects"]
		return node

	case ast.NodeCallExpr:
		// Detectar chamadas à C API do Lua
		if len(astNode.Children) > 0 {
			if callee, ok := astNode.Children[0].Value.(string); ok {
				if isLuaCAPI(callee) {
					node := arkhelfir.NewLFIRNode(LFIRNodeTypeLuaCAPI,
						fmt.Sprintf("capi_%s_%p", callee, astNode), "lua")
					node.Attributes["capi_function"] = callee
					return node
				}
			}
		}
		// Chamada de função Lua normal
		node := arkhelfir.NewLFIRNode(arkhelfir.LFIRNodeTypeCall,
			fmt.Sprintf("call_%p", astNode), "lua")
		return node

	default:
		// Mapeamento genérico para outros tipos
		node := arkhelfir.NewLFIRNode(arkhelfir.LFIRNodeTypeExpr,
			fmt.Sprintf("%s_%p", astNode.Type, astNode), "lua")
		node.Attributes["ast_type"] = string(astNode.Type)
		if astNode.Value != nil {
			node.Attributes["value"] = astNode.Value
		}
		return node
	}
}

// addLuaSemanticEdges adiciona arestas que capturam semântica Lua
func (b *LuaLFIRBuilder) addLuaSemanticEdges(astNode *ast.Node, lfirNode *arkhelfir.LFIRNode) {
	switch astNode.Type {
	case ast.NodeTable:
		// Conectar campos da tabela ao nó da tabela
		for _, field := range astNode.Children {
			if field.Type == ast.NodeTableField {
				if keyNode, ok := field.Attributes["key"].(*ast.Node); ok {
					if keyLFIR, exists := b.nodeMap[keyNode]; exists {
						b.graph.Link(lfirNode.ID, keyLFIR)
					}
				} else if keyStr, ok := field.Attributes["key"].(string); ok {
					// Fallback for string keys
					// we can't easily link to a non-existent AST node, but we could create one
					keyNode := arkhelfir.NewLFIRNode(arkhelfir.LFIRNodeTypeExpr, fmt.Sprintf("key_%s_%p", keyStr, field), "lua")
					keyNode.Attributes["value"] = keyStr
					b.graph.AddNode(keyNode)
					b.graph.Link(lfirNode.ID, keyNode.ID)
				}
				// Conectar valor do campo
				if len(field.Children) > 0 {
					if valLFIR, exists := b.nodeMap[field.Children[0]]; exists {
						b.graph.Link(lfirNode.ID, valLFIR)
					}
				}
			}
		}

	case ast.NodeCallExpr:
		// Conectar função chamada aos argumentos
		if len(astNode.Children) >= 2 {
			funcNode := astNode.Children[0]
			if funcLFIR, exists := b.nodeMap[funcNode]; exists {
				for _, arg := range astNode.Children[1:] {
					if argLFIR, exists := b.nodeMap[arg]; exists {
						b.graph.Link(funcLFIR, argLFIR)
					}
				}
			}
		}
	}
}

// isLuaCAPI detecta funções da C API do Lua
func isLuaCAPI(name string) bool {
	prefixes := []string{
		"lua_", "luaL_", "lua_push", "lua_get", "lua_set",
		"lua_call", "lua_pcall", "lua_newtable", "lua_createtable",
	}
	for _, prefix := range prefixes {
		if strings.HasPrefix(name, prefix) {
			return true
		}
	}
	return false
}
