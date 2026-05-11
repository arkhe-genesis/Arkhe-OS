package ferris

import (
	"fmt"
	"go/ast"
)

// PyLexer converte tokens Python para uma representação genérica.
type PyLexer struct {
	source []byte
	pos    int
}

// PyParser converte token stream em ast.Node (do Go, reutilizado para Python).
type PyParser struct {
	lexer *PyLexer
}

func (p *PyParser) Parse() ([]ast.Stmt, error) {
	// ex.: "x = 42" → &ast.AssignStmt{...}
	return []ast.Stmt{}, nil
}

type goType struct {
	Name string
}

type TypeInferer struct {
	globals map[string]goType // mapeia nome → tipo Go
}

func (ti *TypeInferer) isBuiltin(expr ast.Expr, name string) bool {
	// Simplificação para fins do esqueleto
	return false
}

func (ti *TypeInferer) inferCall(expr *ast.CallExpr) goType {
	return goType{Name: "interface{}"}
}

func inferFromLiteral(expr *ast.BasicLit) goType {
	return goType{Name: "interface{}"}
}

func (ti *TypeInferer) Infer(expr ast.Expr) goType {
	switch e := expr.(type) {
	case *ast.BasicLit:
		return inferFromLiteral(e)
	case *ast.CallExpr:
		if ti.isBuiltin(e.Fun, "len") {
			return goType{Name: "int"}
		}
		return ti.inferCall(e)
	}
	return goType{Name: "interface{}"}
}

type pyParam struct {
	Name     string
	Inferred goType
}

type pyFuncDef struct {
	Name    string
	Params  []pyParam
	RetType *goType
	Body    []ast.Stmt
}

type CodeGen struct {
	out *fmt.Stringer
}

// Number interface definition
type Number interface {
    Add(other Number) Number
    // ...
}
