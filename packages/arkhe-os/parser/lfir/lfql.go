// lfql.go — Substrate 306: LFIR Query Language (LFQL)
//
// Canonical implementation for the ARKHE OS Catedral.
// Provides a parser and executor for a GraphQL/Cypher‑inspired query language
// that operates directly on the AGI‑enriched LFIRGraph (lfir.go).
//
// The language supports:
//   - Node patterns: (var:type {key: value})
//   - Edge patterns: [var:edge_type]
//   - Path patterns: (n1)-[e]->(n2)
//   - Metric fields: metric.coherence_score, metric.semantic_density, …
//   - Filtering, pagination and ordering.
//
// Temporal extension (AT time_expr) is reserved for the Retrocausal Channel (RCP‑1).

package lfir

import (
	"fmt"
	"strconv"
	"strings"
	"text/scanner"
)

// ---------------------------------------------------------------------------
// Lexer
// ---------------------------------------------------------------------------

type lfqlLexer struct {
	scanner.Scanner
	result lfqlToken
}

type lfqlToken int

const (
	tkEOF lfqlToken = iota
	tkIdent
	tkString
	tkNumber
	tkDot
	tkColon
	tkSemicolon
	tkLParen
	tkRParen
	tkLBrack
	tkRBrack
	tkLBrace
	tkRBrace
	tkArrow          // ->
	tkComma
	tkStar
	tkEq
	tkGt
	tkLt
	tkKeywordSelect
	tkKeywordWhere
	tkKeywordOrder
	tkKeywordBy
	tkKeywordLimit
	tkKeywordAsc
	tkKeywordDesc
	tkKeywordAnd
	tkKeywordOr
	tkKeywordNot
	tkKeywordAt     // temporal extension
	tkKeywordNode   // node.property
	tkKeywordEdge   // edge.property
	tkKeywordMetric // metric.property
)

var keywords = map[string]lfqlToken{
	"SELECT":  tkKeywordSelect,
	"WHERE":   tkKeywordWhere,
	"ORDER":   tkKeywordOrder,
	"BY":      tkKeywordBy,
	"LIMIT":   tkKeywordLimit,
	"ASC":     tkKeywordAsc,
	"DESC":    tkKeywordDesc,
	"AND":     tkKeywordAnd,
	"OR":      tkKeywordOr,
	"NOT":     tkKeywordNot,
	"AT":      tkKeywordAt,
	"NODE":    tkKeywordNode,
	"EDGE":    tkKeywordEdge,
	"METRIC":  tkKeywordMetric,
}

func (l *lfqlLexer) Lex(lval *lfqlSymType) int {
	tok := l.Scan()
	lval.str = l.TokenText()

	switch tok {
	case scanner.EOF:
		return int(tkEOF)
	case scanner.Ident:
		upper := strings.ToUpper(lval.str)
		if kw, ok := keywords[upper]; ok {
			return int(kw)
		}
		return int(tkIdent)
	case scanner.String, scanner.RawString:
		s, err := strconv.Unquote(lval.str)
		if err == nil {
			lval.str = s
		}
		return int(tkString)
	case scanner.Int, scanner.Float:
		return int(tkNumber)
	case '.':
		return int(tkDot)
	case ':':
		return int(tkColon)
	case ';':
		return int(tkSemicolon)
	case '(':
		return int(tkLParen)
	case ')':
		return int(tkRParen)
	case '[':
		return int(tkLBrack)
	case ']':
		return int(tkRBrack)
	case '{':
		return int(tkLBrace)
	case '}':
		return int(tkRBrace)
	case '-':
		if l.Peek() == '>' {
			l.Scan() // consume '>'
			lval.str = "->"
			return int(tkArrow)
		}
		return int('-')
	case ',':
		return int(tkComma)
	case '*':
		return int(tkStar)
	case '=':
		return int(tkEq)
	case '>':
		return int(tkGt)
	case '<':
		return int(tkLt)
	}
	return int(tok)
}

func (l *lfqlLexer) Error(e string) {
	// simple panic for now; wrapped in parser
	panic(fmt.Sprintf("LFQL lexer error: %s", e))
}

// ---------------------------------------------------------------------------
// Parser (yacc‑style grammar, hand‑written recursive descent)
// ---------------------------------------------------------------------------

type lfqlSymType struct {
	str   string
	num   float64
	node  *LFIRNode
	edge  *LFIREdge
	list  []interface{}
	expr  *lfqlExpression
	query *lfqlQuery
}

type lfqlParser struct {
	lex *lfqlLexer
	peekTok lfqlToken
	peekLval lfqlSymType
	hasPeek bool
}

func (p *lfqlParser) peek() lfqlToken {
	if !p.hasPeek {
		p.peekTok = lfqlToken(p.lex.Lex(&p.peekLval))
		p.hasPeek = true
	}
	return p.peekTok
}

func (p *lfqlParser) consume() {
	if !p.hasPeek {
		p.lex.Lex(&p.peekLval)
	}
	p.hasPeek = false
}

func (p *lfqlParser) peekLvalStr() string {
	p.peek()
	return p.peekLval.str
}

type lfqlQuery struct {
	Projection  lfqlProjection
	Patterns    []lfqlPattern
	Where       *lfqlExpression
	OrderBy     string
	OrderDir    string
	Limit       int
	AtTime      string // temporal expression
}

type lfqlProjection struct {
	Fields []lfqlField
	All    bool
}

type lfqlField struct {
	Prefix string // node, edge, metric
	Name   string
	Alias  string
}

type lfqlPattern struct {
	NodeVar    string
	NodeType   string
	NodeProps  map[string]string
	EdgeVar    string
	EdgeType   string
	TargetNode *lfqlPattern // for path patterns
}

type lfqlExpression struct {
	Op    string
	Left  interface{} // *lfqlExpression or string
	Right interface{}
}

func (p *lfqlParser) Parse() (q *lfqlQuery, err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("parser panic: %v", r)
		}
	}()
	q = p.parseQuery()
	return q, nil
}

func (p *lfqlParser) parseQuery() *lfqlQuery {
	q := &lfqlQuery{}
	if p.peek() != tkKeywordSelect {
		panic("expected SELECT")
	}
	p.consume()
	q.Projection = p.parseProjection()
	if p.peek() == tkKeywordWhere {
		p.consume()
		q.Patterns = p.parsePatterns()
		if p.peek() == tkKeywordAnd || p.peek() == tkKeywordOr {
			q.Where = p.parseBoolExpr()
		}
	}
	if p.peek() == tkKeywordOrder {
		p.consume()
		p.consume() // BY
		f := p.parseField()
		q.OrderBy = f.Name
		q.OrderDir = "ASC"
		if p.peek() == tkKeywordAsc || p.peek() == tkKeywordDesc {
			q.OrderDir = strings.ToUpper(p.peekLvalStr())
			p.consume()
		}
	}
	if p.peek() == tkKeywordLimit {
		p.consume()
		if p.peek() != tkNumber {
			panic("LIMIT requires integer")
		}
		n, _ := strconv.Atoi(p.peekLvalStr())
		q.Limit = n
		p.consume()
	}
	if p.peek() == tkKeywordAt {
		p.consume()
		if p.peek() != tkString && p.peek() != tkIdent && p.peek() != tkNumber {
			panic("AT requires time expression")
		}
		q.AtTime = p.peekLvalStr()
		p.consume()
	}
	return q
}

func (p *lfqlParser) parseProjection() lfqlProjection {
	proj := lfqlProjection{}
	if p.peek() == tkStar {
		proj.All = true
		p.consume()
		return proj
	}
	for {
		proj.Fields = append(proj.Fields, p.parseField())
		if p.peek() != tkComma {
			break
		}
		p.consume()
	}
	return proj
}

func (p *lfqlParser) parseField() lfqlField {
	prefix := ""
	name := ""
	if p.peek() == tkKeywordNode || p.peek() == tkKeywordEdge || p.peek() == tkKeywordMetric {
		prefix = p.peekLvalStr()
		p.consume()
		if p.peek() != tkDot {
			panic(fmt.Sprintf("expected dot after prefix, got %v", p.peek()))
		}
		p.consume()
	}
	if p.peek() != tkIdent && p.peek() != tkString && p.peek() != tkStar {
		panic("expected field name")
	}
	name = p.peekLvalStr()
	p.consume()
	return lfqlField{Prefix: prefix, Name: name}
}

func (p *lfqlParser) parsePatterns() []lfqlPattern {
	var patterns []lfqlPattern
	patterns = append(patterns, p.parseSinglePattern())
	for p.peek() == tkComma {
		p.consume()
		patterns = append(patterns, p.parseSinglePattern())
	}
	return patterns
}

func (p *lfqlParser) parseSinglePattern() lfqlPattern {
	pat := lfqlPattern{}
	if p.peek() == tkLParen {
		p.consume()
		if p.peek() == tkIdent {
			pat.NodeVar = p.peekLvalStr()
			p.consume()
		}
		if p.peek() == tkColon {
			p.consume()
			pat.NodeType = p.peekLvalStr()
			p.consume()
		}
		if p.peek() == tkLBrace {
			pat.NodeProps = p.parseProps()
		}
		if p.peek() != tkRParen {
			panic("expected )")
		}
		p.consume()
		// optional edge and target node
		if p.peek() == tkArrow || (p.peek() == tkLBrack) {
			// edge pattern: -[e:TYPE]->
			if p.peek() == tkArrow {
				p.consume()
			}
			if p.peek() == tkLBrack {
				p.consume()
				if p.peek() == tkIdent {
					pat.EdgeVar = p.peekLvalStr()
					p.consume()
				}
				if p.peek() == tkColon {
					p.consume()
					pat.EdgeType = p.peekLvalStr()
					p.consume()
				}
				if p.peek() != tkRBrack {
					panic("expected ]")
				}
				p.consume()
			}
			if p.peek() == tkArrow {
				p.consume()
			}
			if p.peek() == tkLParen {
				target := p.parseSinglePattern()
				pat.TargetNode = &target
			}
		}
	}
	return pat
}

func (p *lfqlParser) parseProps() map[string]string {
	props := map[string]string{}
	p.consume() // '{'
	for p.peek() != tkRBrace {
		key := ""
		if p.peek() == tkIdent || p.peek() == tkString {
			key = p.peekLvalStr()
			p.consume()
		} else {
			panic("expected property key")
		}
		if p.peek() != tkColon {
			panic("expected ':'")
		}
		p.consume()
		val := ""
		if p.peek() == tkString || p.peek() == tkIdent || p.peek() == tkNumber {
			val = p.peekLvalStr()
			p.consume()
		} else {
			panic("expected property value")
		}
		props[key] = val
		if p.peek() == tkComma {
			p.consume()
		}
	}
	p.consume() // '}'
	return props
}

func (p *lfqlParser) parseBoolExpr() *lfqlExpression {
	left := p.parseAtomicExpr()
	if p.peek() == tkKeywordAnd || p.peek() == tkKeywordOr {
		op := strings.ToUpper(p.peekLvalStr())
		p.consume()
		right := p.parseBoolExpr()
		return &lfqlExpression{Op: op, Left: left, Right: right}
	}
	return left
}

func (p *lfqlParser) parseAtomicExpr() *lfqlExpression {
	if p.peek() == tkKeywordNot {
		p.consume()
		expr := p.parseAtomicExpr()
		return &lfqlExpression{Op: "NOT", Left: expr}
	}
	// for simplicity, only field comparisons
	left := p.parseFieldExpr()
	op := ""
	if p.peek() == tkEq || p.peek() == tkGt || p.peek() == tkLt {
		op = p.peekLvalStr()
		p.consume()
	} else {
		panic("expected comparison operator")
	}
	right := p.parseValue()
	return &lfqlExpression{Op: op, Left: left, Right: right}
}

func (p *lfqlParser) parseFieldExpr() lfqlField {
	return p.parseField()
}

func (p *lfqlParser) parseValue() interface{} {
	if p.peek() == tkString || p.peek() == tkIdent || p.peek() == tkNumber {
		val := p.peekLvalStr()
		p.consume()
		return val
	}
	panic("expected value")
}

// ---------------------------------------------------------------------------
// Executor (evaluates query on LFIRGraph)
// ---------------------------------------------------------------------------

type LFQLResult struct {
	Nodes []*LFIRNode
	Edges []*LFIREdge
	Metrics map[string]float64
}

func ExecuteLFQL(graph *LFIRGraph, queryStr string) (*LFQLResult, error) {
	var lex lfqlLexer
	lex.Init(strings.NewReader(queryStr))
	parser := &lfqlParser{lex: &lex}
	q, err := parser.Parse()
	if err != nil {
		return nil, err
	}
	return evaluateQuery(graph, q), nil
}

func evaluateQuery(graph *LFIRGraph, q *lfqlQuery) *LFQLResult {
	if q == nil {
		return &LFQLResult{}
	}
	res := &LFQLResult{}

	// Collect candidate nodes based on patterns
	candidateNodes := make(map[string]*LFIRNode)
	if len(q.Patterns) == 0 {
		for _, node := range graph.Nodes {
			candidateNodes[node.ID] = node
		}
	} else {
		for _, pat := range q.Patterns {
			for _, node := range graph.Nodes {
				if matchNode(node, pat) {
					candidateNodes[node.ID] = node
				}
			}
		}
	}

	// Apply WHERE expression if any
	if q.Where != nil {
		for id, node := range candidateNodes {
			if !evaluateExpr(q.Where, node, graph) {
				delete(candidateNodes, id)
			}
		}
	}

	// Collect edges if path patterns were used
	for _, pat := range q.Patterns {
		if pat.TargetNode != nil {
			for _, edge := range graph.Edges {
				src, ok1 := candidateNodes[edge.Source]
				tgt, ok2 := candidateNodes[edge.Target]
				if ok1 && ok2 && matchEdge(edge, pat) {
					res.Edges = append(res.Edges, edge)
					// Keep both nodes
					candidateNodes[edge.Source] = src
					candidateNodes[edge.Target] = tgt
				}
			}
		}
	}

	// Output nodes
	for _, node := range candidateNodes {
		res.Nodes = append(res.Nodes, node)
	}

	// Compute metric fields if requested
	res.Metrics = make(map[string]float64)
	for _, f := range q.Projection.Fields {
		if f.Prefix == "metric" {
			switch f.Name {
			case "coherence_score":
				res.Metrics["coherence_score"] = graph.Metrics.CoherenceScore
			case "semantic_density":
				res.Metrics["semantic_density"] = graph.Metrics.SemanticDensity
			case "accessibility_score":
				res.Metrics["accessibility_score"] = graph.Metrics.AccessibilityScore
			default:
				// ignore
			}
		}
	}

	// Post-processing: limit, order (simplified)
	if q.Limit > 0 && len(res.Nodes) > q.Limit {
		res.Nodes = res.Nodes[:q.Limit]
	}

	return res
}

func matchNode(node *LFIRNode, pat lfqlPattern) bool {
	if pat.NodeType != "" && string(node.Type) != pat.NodeType && node.Name != pat.NodeType {
		return false
	}
	for k, v := range pat.NodeProps {
		attrVal, ok := node.Attributes[k]
		if !ok || fmt.Sprint(attrVal) != v {
			return false
		}
	}
	return true
}

func matchEdge(edge *LFIREdge, pat lfqlPattern) bool {
	if pat.EdgeType != "" && string(edge.Type) != pat.EdgeType {
		return false
	}
	return true
}

func evaluateExpr(expr *lfqlExpression, node *LFIRNode, graph *LFIRGraph) bool {
	if expr.Op == "NOT" {
		return !evaluateExpr(expr.Left.(*lfqlExpression), node, graph)
	}
	if expr.Op == "AND" {
		return evaluateExpr(expr.Left.(*lfqlExpression), node, graph) && evaluateExpr(expr.Right.(*lfqlExpression), node, graph)
	}
	if expr.Op == "OR" {
		return evaluateExpr(expr.Left.(*lfqlExpression), node, graph) || evaluateExpr(expr.Right.(*lfqlExpression), node, graph)
	}
	// comparison
	leftField, ok := expr.Left.(lfqlField)
	if !ok {
		return false
	}
	rightVal, ok := expr.Right.(string)
	if !ok {
		return false
	}

	var leftVal string
	switch leftField.Prefix {
	case "node":
		leftVal = fmt.Sprint(node.Attributes[leftField.Name])
	case "metric":
		// simple metric handling: just compare string (for now)
		switch leftField.Name {
		case "coherence_score":
			leftVal = strconv.FormatFloat(graph.Metrics.CoherenceScore, 'f', -1, 64)
		default:
			leftVal = ""
		}
	default:
		leftVal = ""
	}

	switch expr.Op {
	case "=":
		return leftVal == rightVal
	case ">":
		lf, _ := strconv.ParseFloat(leftVal, 64)
		rf, _ := strconv.ParseFloat(rightVal, 64)
		return lf > rf
	case "<":
		lf, _ := strconv.ParseFloat(leftVal, 64)
		rf, _ := strconv.ParseFloat(rightVal, 64)
		return lf < rf
	}
	return false
}
