// parser/frontends/lua/analyzer/safety_checker.go
package analyzer

import (
	"arkhe/parser/frontends/lua/ast"
)

// SafetyChecker detecta anti-patterns de segurança em código Lua
type SafetyChecker struct {
	UnsafePatterns map[string]bool
	GlobalVars     map[string]bool // Variáveis globais declaradas
}

// NewSafetyChecker cria verificador com padrões padrão
func NewSafetyChecker() *SafetyChecker {
	return &SafetyChecker{
		UnsafePatterns: map[string]bool{
			"loadstring": true, // Execução dinâmica de código
			"load":       true,
			"getfenv":    true, // Manipulação de ambiente (Lua 5.1)
			"setfenv":    true,
			"debug":      true, // Acesso à biblioteca debug
			"collectgarbage": true, // Uso explícito pode indicar má gestão de memória
		},
		GlobalVars: make(map[string]bool),
	}
}

// Check analisa AST e retorna contagem de padrões inseguros
func (sc *SafetyChecker) Check(root *ast.Node) (unsafeCount int, details []string) {
	sc.walkAST(root, func(node *ast.Node) {
		// Verificar chamadas a funções inseguras
		if node.Type == ast.NodeCallExpr && len(node.Children) > 0 {
			// Handle cases where the callee is an identifier
			if node.Children[0].Type == ast.NodeIdentifier {
				if callee, ok := node.Children[0].Value.(string); ok {
					if sc.UnsafePatterns[callee] {
						unsafeCount++
						details = append(details,
							"unsafe_call:"+callee)
					}
				}
			}
			// Handle cases where callee is index expression (e.g. debug.getinfo)
			if node.Children[0].Type == ast.NodeIndexExpr && len(node.Children[0].Children) > 0 {
				if callee, ok := node.Children[0].Children[0].Value.(string); ok {
					if sc.UnsafePatterns[callee] {
						unsafeCount++
						details = append(details,
							"unsafe_call:"+callee)
					}
				}
			}
		}

		// Verificar acesso a globais não declarados (modo strict)
		if node.Type == ast.NodeIdentifier {
			if name, ok := node.Value.(string); ok {
				if !isLuaBuiltin(name) && !sc.GlobalVars[name] {
					// Em modo strict, isso seria um erro
					// Aqui apenas registramos para métrica de clareza
				}
			}
		}

		// Verificar metatables com side effects perigosos
		if node.Type == ast.NodeMetamethod {
			if metaName, ok := node.Value.(string); ok {
				if metaName == "__index" || metaName == "__newindex" {
					if hasSideEffects(node) {
						unsafeCount++
						details = append(details,
							"unsafe_metamethod:"+metaName)
					}
				}
			}
		}
	})
	return
}

// walkAST percorre AST chamando callback para cada nó
func (sc *SafetyChecker) walkAST(node *ast.Node, callback func(*ast.Node)) {
	if node == nil {
		return
	}
	callback(node)
	for _, child := range node.Children {
		sc.walkAST(child, callback)
	}
}

// isLuaBuiltin verifica se nome é builtin do Lua
func isLuaBuiltin(name string) bool {
	builtins := map[string]bool{
		// Funções globais Lua 5.4
		"assert": true, "collectgarbage": true, "dofile": true, "error": true, "getmetatable": true,
		"ipairs": true, "load": true, "loadfile": true, "next": true, "pairs": true, "pcall": true, "print": true,
		"rawequal": true, "rawget": true, "rawlen": true, "rawset": true, "select": true, "setmetatable": true,
		"tonumber": true, "tostring": true, "type": true, "xpcall": true,
		// Bibliotecas padrão
		"_G": true, "_VERSION": true, "coroutine": true, "table": true, "string": true, "math": true,
		"utf8": true, "io": true, "os": true, "debug": true, "package": true,
	}
	return builtins[name]
}

// hasSideEffects detecta se um metamétodo tem efeitos colaterais perigosos
func hasSideEffects(node *ast.Node) bool {
	// Heurística simplificada: verificar se o corpo contém
	// chamadas a funções inseguras ou modificações de estado global
	hasUnsafe := false
	walkFunctions(node, func(fn *ast.Node) {
		for _, child := range fn.Children {
			if child.Type == ast.NodeCallExpr {
				if child.Children[0].Type == ast.NodeIdentifier {
					if callee, ok := child.Children[0].Value.(string); ok {
						if isDangerousForMetamethod(callee) {
							hasUnsafe = true
						}
					}
				}
			}
		}
	})
	return hasUnsafe
}

func isDangerousForMetamethod(name string) bool {
	dangerous := map[string]bool{
		"loadstring": true, "load": true, "setfenv": true,
		"rawset": true, // Modificação direta de tabelas
		"error": true,
	}
	return dangerous[name]
}

func walkFunctions(node *ast.Node, callback func(*ast.Node)) {
	if node == nil {
		return
	}
	if node.Type == ast.NodeFunction {
		callback(node)
	}
	for _, child := range node.Children {
		walkFunctions(child, callback)
	}
}
