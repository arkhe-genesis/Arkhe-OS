// parser/frontends/lua/ast/parser.go
package ast

import (
	"fmt"
	"strings"
	"unicode"
)

// NodeType define tipos de nós na AST Lua
type NodeType string

const (
	NodeChunk         NodeType = "chunk"
	NodeFunction      NodeType = "function"
	NodeTable         NodeType = "table"
	NodeTableField    NodeType = "table_field"
	NodeAssignment    NodeType = "assignment"
	NodeLocalDecl     NodeType = "local_decl"
	NodeIfStmt        NodeType = "if"
	NodeWhileStmt     NodeType = "while"
	NodeForStmt       NodeType = "for"
	NodeRepeatStmt    NodeType = "repeat"
	NodeBreakStmt     NodeType = "break"
	NodeReturnStmt    NodeType = "return"
	NodeCallExpr      NodeType = "call"
	NodeIndexExpr     NodeType = "index"
	NodeBinaryExpr    NodeType = "binary_op"
	NodeUnaryExpr     NodeType = "unary_op"
	NodeLiteral       NodeType = "literal"
	NodeIdentifier    NodeType = "identifier"
	NodeCoroutine     NodeType = "coroutine"
	NodeMetamethod    NodeType = "metamethod"
)

// Node representa um nó na AST Lua
type Node struct {
	Type       NodeType
	Value      interface{}
	Children   []*Node
	Attributes map[string]interface{}
	Line       int
	Column     int
}

// Parser implementa parser recursivo-descendente para Lua 5.4
type Parser struct {
	source   []byte
	pos      int
	line     int
	column   int
	filename string
	errors   []error
}

// Parse analisa source Lua e retorna AST
func Parse(source []byte, filename string) (*Node, error) {
	p := &Parser{
		source:   source,
		filename: filename,
		line:     1,
		column:   1,
	}
	return p.parseChunk()
}

func (p *Parser) isEOF() bool {
	return p.pos >= len(p.source)
}

// parseChunk parseia um chunk Lua (bloco de código)
func (p *Parser) parseChunk() (*Node, error) {
	chunk := &Node{
		Type:       NodeChunk,
		Attributes: make(map[string]interface{}),
		Line:       p.line,
		Column:     p.column,
	}

	p.skipWhitespace()

	// Parse statements until EOF or 'end'
	for !p.isEOF() && !p.match("end") {
		stmt, err := p.parseStatement()
		if err != nil {
			return nil, err
		}
		if stmt != nil {
			chunk.Children = append(chunk.Children, stmt)
		}
		p.skipWhitespace()
	}

	return chunk, nil
}

// parseStatement parseia uma declaração Lua
func (p *Parser) parseStatement() (*Node, error) {
	p.skipWhitespace()

	// Keywords que iniciam statements
	switch {
	case p.match("function"):
		return p.parseFunction()
	case p.match("local"):
		return p.parseLocal()
	case p.match("if"):
		return p.parseIf()
	case p.match("while"):
		return p.parseWhile()
	case p.match("for"):
		return p.parseFor()
	case p.match("repeat"):
		return p.parseRepeat()
	case p.match("return"):
		return p.parseReturn()
	case p.match("break"):
		return &Node{Type: NodeBreakStmt, Line: p.line, Column: p.column}, nil
	default:
		// Assignment ou chamada de função
		return p.parseAssignmentOrCall()
	}
}

func (p *Parser) parseLocal() (*Node, error) {
	// Stub para local decl
	p.skipWhitespace()
	if p.match("function") {
		return p.parseFunction()
	}
	return p.parseAssignmentOrCall()
}

func (p *Parser) parseIf() (*Node, error) {
	return &Node{Type: NodeIfStmt, Line: p.line, Column: p.column}, nil
}

func (p *Parser) parseWhile() (*Node, error) {
	return &Node{Type: NodeWhileStmt, Line: p.line, Column: p.column}, nil
}

func (p *Parser) parseFor() (*Node, error) {
	return &Node{Type: NodeForStmt, Line: p.line, Column: p.column}, nil
}

func (p *Parser) parseRepeat() (*Node, error) {
	return &Node{Type: NodeRepeatStmt, Line: p.line, Column: p.column}, nil
}

func (p *Parser) parseReturn() (*Node, error) {
	return &Node{Type: NodeReturnStmt, Line: p.line, Column: p.column}, nil
}

// parseFunction parseia uma declaração de função
func (p *Parser) parseFunction() (*Node, error) {
	fn := &Node{
		Type:       NodeFunction,
		Attributes: make(map[string]interface{}),
		Line:       p.line,
		Column:     p.column,
	}

	// Nome da função (opcional para funções anônimas)
	p.skipWhitespace()

		// In Lua, function can be followed by an identifier chain like `function Entity:__tostring()`
		// `peekIdentifier()` might return "" for keywords, but we might want to capture keywords as part of name or normal idents
		// but since we peek without isLuaKeyword logic inside the loop, we bypass it here.

		ident := ""
		p.skipWhitespace()
		start := p.pos
		for p.pos < len(p.source) && isIdentifierChar(p.source[p.pos]) {
			p.pos++
		}
		if p.pos > start {
			ident = string(p.source[start:p.pos])
		}
		p.pos = start // rewind

		if ident != "" && ident != "function" {
			nameParts := []string{p.parseIdentifierWithoutKeywordCheck()}
		for {
		    p.skipWhitespace()
		    if p.match(".") {
				    nameParts = append(nameParts, p.parseIdentifierWithoutKeywordCheck())
		    } else if p.match(":") {
				    nameParts = append(nameParts, p.parseIdentifierWithoutKeywordCheck())
			} else {
			    break
			}
		}
		fn.Value = strings.Join(nameParts, ".")
		fn.Attributes["name"] = fn.Value
	}

	// Parâmetros
	p.expect("(")
	params := p.parseParamList()
	fn.Attributes["params"] = params
	p.expect(")")

	// Corpo da função
	body, err := p.parseChunk()
	if err != nil {
		return nil, err
	}
	fn.Children = append(fn.Children, body)
	fn.Attributes["body_lines"] = body.Line - fn.Line

	return fn, nil
}

func (p *Parser) parseParamList() []string {
	var params []string
	p.skipWhitespace()
	for !p.match(")") && !p.isEOF() {
		if ident := p.peekIdentifier(); ident != "" {
			params = append(params, p.parseIdentifier())
		} else if p.match("...") {
			params = append(params, "...")
		} else {
			// Skip other tokens for simplified parsing
			p.pos++
		}
		p.skipWhitespace()
		if p.match(",") {
			p.skipWhitespace()
		} else {
			break
		}
	}
	return params
}

func (p *Parser) parseArgList() []*Node {
	var args []*Node
	p.skipWhitespace()
	for !p.match(")") && !p.isEOF() {
		expr, err := p.parseExpression()
		if err == nil && expr != nil {
			args = append(args, expr)
		} else {
			p.pos++
		}
		p.skipWhitespace()
		if p.match(",") {
			p.skipWhitespace()
		} else {
			break
		}
	}
	p.expect(")")
	return args
}

func (p *Parser) parseAssignmentOrCall() (*Node, error) {
	// Fallback to reading an expression then trying to assign
	expr, err := p.parseExpression()
	if err != nil {
		// Just skip a line to recover for simplistic parsing
		for !p.isEOF() && p.source[p.pos] != '\n' {
			p.pos++
		}
		return nil, nil
	}

	p.skipWhitespace()
	if p.match("=") {
		assign := &Node{Type: NodeAssignment, Line: p.line, Column: p.column}
		assign.Children = append(assign.Children, expr)
		val, _ := p.parseExpression()
		if val != nil {
			assign.Children = append(assign.Children, val)
		}
		return assign, nil
	}
	return expr, nil
}

// parseTable parseia uma tabela Lua { ... }
func (p *Parser) parseTable() (*Node, error) {
	table := &Node{
		Type:       NodeTable,
		Attributes: make(map[string]interface{}),
		Line:       p.line,
		Column:     p.column,
	}

	p.expect("{")
	p.skipWhitespace()

	fieldCount := 0
	for !p.match("}") && !p.isEOF() {
		field, err := p.parseTableField()
		if err != nil {
			// Recover
			p.pos++
			continue
		}
		if field != nil {
			table.Children = append(table.Children, field)
			fieldCount++
		}
		p.skipWhitespace()
		if p.match(",") || p.match(";") {
			p.skipWhitespace()
		}
	}
	// we matched } or hit EOF

	table.Attributes["field_count"] = fieldCount
	if fieldCount > 0 && table.Children[0].Attributes["key"] == nil {
		table.Attributes["array_style"] = true
	} else {
		table.Attributes["array_style"] = false
	}
	return table, nil
}

// parseTableField parseia um campo de tabela: [key] = value ou value
func (p *Parser) parseTableField() (*Node, error) {
	field := &Node{
		Type:       NodeTableField,
		Attributes: make(map[string]interface{}),
		Line:       p.line,
		Column:     p.column,
	}

	// [expr] = value (chave explícita)
	if p.match("[") {
		key, err := p.parseExpression()
		if err != nil {
			return nil, err
		}
		p.expect("]")
		p.expect("=")
		field.Attributes["key"] = key
		field.Attributes["key_type"] = "explicit"
	} else if ident := p.peekIdentifier(); ident != "" && p.peekNextNonSpace() == '=' {
		// name = value (chave por nome)
		key := p.parseIdentifier()
		p.expect("=")
			keyNode := &Node{Type: NodeLiteral, Value: key, Attributes: map[string]interface{}{"literal_type": "string"}}
			field.Attributes["key"] = keyNode
		field.Attributes["key_type"] = "named"
		} else if ident := p.peekIdentifier(); ident != "" && (p.peekNextNonSpace() == ',' || p.peekNextNonSpace() == '}' || p.peekNextNonSpace() == ';') {
		    // Implicit named key / value just mapped as value array style
		} else if ident := p.peekIdentifier(); ident != "" {
			// maybe implicit function declaration in table or just a string key value... we'll try to just parse expression
		}
	// else: array-style (chave numérica implícita)

	value, err := p.parseExpression()
	if err != nil {
		return nil, err
	}
	field.Children = append(field.Children, value)

	return field, nil
}

// parseExpression parseia uma expressão Lua (simplificado)
func (p *Parser) parseExpression() (*Node, error) {
	p.skipWhitespace()

	// Literais
	if p.matchNumber() {
		return &Node{
			Type:  NodeLiteral,
			Value: p.parseNumber(),
			Attributes: map[string]interface{}{"literal_type": "number"},
			Line: p.line, Column: p.column,
		}, nil
	}
	if p.matchString() {
		return &Node{
			Type:  NodeLiteral,
			Value: p.parseString(),
			Attributes: map[string]interface{}{"literal_type": "string"},
			Line: p.line, Column: p.column,
		}, nil
	}

	// Identificadores
	if ident := p.peekIdentifier(); ident != "" {
		identNode := &Node{
			Type:  NodeIdentifier,
			Value: p.parseIdentifier(),
			Line:  p.line, Column: p.column,
		}

		// Verificar se é chamada de função: ident(...)
		if p.match("(") {
			call := &Node{Type: NodeCallExpr, Line: p.line, Column: p.column}
			call.Children = append(call.Children, identNode)
			args := p.parseArgList()
			call.Children = append(call.Children, args...)
			return call, nil
		}

		// Verificar se é indexação: ident[...] ou ident.field
		if p.match("[") || p.match(".") {
			index := &Node{Type: NodeIndexExpr, Line: p.line, Column: p.column}
			index.Children = append(index.Children, identNode)
			if p.match("[") {
				key, _ := p.parseExpression()
				index.Children = append(index.Children, key)
				p.expect("]")
			} else if p.match(".") {
				field := p.parseIdentifier()
				fieldNode := &Node{Type: NodeLiteral, Value: field, Attributes: map[string]interface{}{"literal_type": "string"}}
				index.Children = append(index.Children, fieldNode)
			}

			// Detect function calls like obj.method() or obj:method()
			p.skipWhitespace()
			if p.match("(") {
				call := &Node{Type: NodeCallExpr, Line: p.line, Column: p.column}
				call.Children = append(call.Children, index)
				args := p.parseArgList()
				call.Children = append(call.Children, args...)
				return call, nil
			} else if p.match(":") {
				// Method call syntax sugar
				method := p.parseIdentifier()
				methodNode := &Node{Type: NodeLiteral, Value: method, Attributes: map[string]interface{}{"literal_type": "string"}}
				index.Children = append(index.Children, methodNode)

				if p.match("(") {
					call := &Node{Type: NodeCallExpr, Line: p.line, Column: p.column}
					call.Children = append(call.Children, index)
					args := p.parseArgList()
					call.Children = append(call.Children, args...)
					return call, nil
				}
			}
			return index, nil
		}

		return identNode, nil
	}

	// Tabelas
	if p.match("{") {
		return p.parseTable()
	}

	// Funções anônimas
	if p.match("function") {
		return p.parseFunction()
	}

	return nil, fmt.Errorf("expressão não reconhecida na linha %d", p.line)
}

// Helper methods (simplificados)
func (p *Parser) skipWhitespace() {
	for p.pos < len(p.source) {
		ch := p.source[p.pos]
		if ch == '-' && p.pos+1 < len(p.source) && p.source[p.pos+1] == '-' {
			// Comentário
			p.pos += 2
			for p.pos < len(p.source) && p.source[p.pos] != '\n' {
				p.pos++
			}
			p.line++
			p.column = 1
			continue
		}
		if unicode.IsSpace(rune(ch)) {
			if ch == '\n' {
				p.line++
				p.column = 1
			} else {
				p.column++
			}
			p.pos++
			continue
		}
		break
	}
}

func (p *Parser) match(keyword string) bool {
	p.skipWhitespace()
	if strings.HasPrefix(string(p.source[p.pos:]), keyword) {
		// Verificar limite de palavra
		nextPos := p.pos + len(keyword)
		if nextPos >= len(p.source) || !isIdentifierChar(p.source[nextPos]) {
			p.pos = nextPos
			p.column += len(keyword)
			return true
		}
	}
	return false
}

func (p *Parser) peekIdentifier() string {
	p.skipWhitespace()
	start := p.pos
	for p.pos < len(p.source) && isIdentifierChar(p.source[p.pos]) {
		p.pos++
	}
	if p.pos > start {
		ident := string(p.source[start:p.pos])
		p.pos = start // rewind
		if isLuaKeyword(ident) {
			return "" // keywords não são identificadores neste contexto
		}
		return ident
	}
	return ""
}

func (p *Parser) parseIdentifier() string {
	ident := p.peekIdentifier()
	if ident != "" {
		p.pos += len(ident)
		p.column += len(ident)
	}
	return ident
}

func (p *Parser) parseIdentifierWithoutKeywordCheck() string {
	p.skipWhitespace()
	start := p.pos
	for p.pos < len(p.source) && isIdentifierChar(p.source[p.pos]) {
		p.pos++
		p.column++
	}
	return string(p.source[start:p.pos])
}

func (p *Parser) peekNextNonSpace() byte {
	pos := p.pos
	for pos < len(p.source) {
		if !unicode.IsSpace(rune(p.source[pos])) {
			return p.source[pos]
		}
		pos++
	}
	return 0
}

func (p *Parser) expect(token string) bool {
	if p.match(token) {
		return true
	}
	// Simplified error handling
	return false
}

func (p *Parser) matchNumber() bool {
	p.skipWhitespace()
	if p.pos < len(p.source) && unicode.IsDigit(rune(p.source[p.pos])) {
		return true
	}
	return false
}

func (p *Parser) parseNumber() string {
	start := p.pos
	for p.pos < len(p.source) && (unicode.IsDigit(rune(p.source[p.pos])) || p.source[p.pos] == '.') {
		p.pos++
		p.column++
	}
	return string(p.source[start:p.pos])
}

func (p *Parser) matchString() bool {
	p.skipWhitespace()
	if p.pos < len(p.source) && (p.source[p.pos] == '"' || p.source[p.pos] == '\'') {
		return true
	}
	return false
}

func (p *Parser) parseString() string {
	quote := p.source[p.pos]
	p.pos++
	p.column++
	start := p.pos
	for p.pos < len(p.source) && p.source[p.pos] != quote {
		if p.source[p.pos] == '\\' {
			p.pos++
			p.column++
		}
		p.pos++
		p.column++
	}
	str := string(p.source[start:p.pos])
	if p.pos < len(p.source) {
		p.pos++
		p.column++
	}
	return str
}

func isIdentifierChar(b byte) bool {
	return (b >= 'a' && b <= 'z') || (b >= 'A' && b <= 'Z') ||
		(b >= '0' && b <= '9') || b == '_'
}

func isLuaKeyword(s string) bool {
	keywords := map[string]bool{
		"and": true, "break": true, "do": true, "else": true, "elseif": true, "end": true, "false": true,
		"for": true, "function": true, "goto": true, "if": true, "in": true, "local": true, "nil": true,
		"not": true, "or": true, "repeat": true, "return": true, "then": true, "true": true, "until": true, "while": true,
	}
	return keywords[s]
}
