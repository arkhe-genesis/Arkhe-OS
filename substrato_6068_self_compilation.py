import hashlib
import json
import re
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import types

# ===== LEXER =====
class TokenType(Enum):
    INT = auto()
    STRING = auto()
    FN = auto()
    IDENT = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LET = auto()
    ASSIGN = auto()
    BOOL = auto()
    EQ = auto()
    NEQ = auto()
    LE = auto()
    GE = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    COLON = auto()
    COMMA = auto()
    ARROW = auto()
    RETURN = auto()
    STRUCT = auto()
    ZK = auto()
    PROVE = auto()
    GT = auto()
    LT = auto()
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: str

class ArkLexer:
    KEYWORDS = {
        'fn': TokenType.FN,
        'let': TokenType.LET,
        'true': TokenType.BOOL,
        'false': TokenType.BOOL,
        'return': TokenType.RETURN,
        'struct': TokenType.STRUCT,
        'zk': TokenType.ZK,
        'prove': TokenType.PROVE,
    }

    def __init__(self, source: str):
        self.source = source
        self.pos = 0

    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch.isspace():
                self.pos += 1
                continue
            if ch == '"':
                self.pos += 1
                start = self.pos
                while self.pos < len(self.source) and self.source[self.pos] != '"':
                    self.pos += 1
                val = self.source[start:self.pos]
                self.pos += 1
                tokens.append(Token(TokenType.STRING, val))
                continue
            if ch.isdigit():
                start = self.pos
                while self.pos < len(self.source) and self.source[self.pos].isdigit():
                    self.pos += 1
                tokens.append(Token(TokenType.INT, self.source[start:self.pos]))
                continue
            if ch.isalpha() or ch == '_':
                start = self.pos
                while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
                    self.pos += 1
                word = self.source[start:self.pos]
                tt = self.KEYWORDS.get(word, TokenType.IDENT)
                tokens.append(Token(tt, word))
                continue
            if self.pos + 1 < len(self.source):
                two = self.source[self.pos:self.pos+2]
                if two == '==':
                    tokens.append(Token(TokenType.EQ, '=='))
                    self.pos += 2
                    continue
                if two == '!=':
                    tokens.append(Token(TokenType.NEQ, '!='))
                    self.pos += 2
                    continue
                if two == '<=':
                    tokens.append(Token(TokenType.LE, '<='))
                    self.pos += 2
                    continue
                if two == '>=':
                    tokens.append(Token(TokenType.GE, '>='))
                    self.pos += 2
                    continue
                if two == '->':
                    tokens.append(Token(TokenType.ARROW, '->'))
                    self.pos += 2
                    continue
            op_map = {
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.STAR,
                '/': TokenType.SLASH,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                '=': TokenType.ASSIGN,
                ':': TokenType.COLON,
                ',': TokenType.COMMA,
                '<': TokenType.LT,
                '>': TokenType.GT,
            }
            if ch in op_map:
                tokens.append(Token(op_map[ch], ch))
                self.pos += 1
                continue
            self.pos += 1
        tokens.append(Token(TokenType.EOF, ''))
        return tokens

# ===== AST =====
@dataclass
class Program:
    declarations: List[Any]

@dataclass
class LetDecl:
    name: str
    mutable: bool
    type: str
    initializer: Any

@dataclass
class FnDecl:
    name: str
    params: List[tuple]
    return_type: str
    body: List[Any]
    pub: bool
    extern: bool

@dataclass
class StructDecl:
    name: str
    fields: List[tuple]
    pub: bool

@dataclass
class ZKProofExpr:
    statement: str
    public_inputs: List[str]

@dataclass
class IntLiteral:
    value: int

@dataclass
class StringLiteral:
    value: str

@dataclass
class BoolLiteral:
    value: bool

@dataclass
class BinaryOp:
    op: str
    left: Any
    right: Any

@dataclass
class Identifier:
    name: str

@dataclass
class ReturnExpr:
    value: Any

# ===== PARSER =====
class ArkParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, tt: TokenType) -> Token:
        if self.current().type != tt:
            raise SyntaxError(f"Expected {tt}, got {self.current().type}")
        return self.advance()

    def parse(self) -> Program:
        decls = []
        while self.current().type != TokenType.EOF:
            decls.append(self.parse_declaration())
        return Program(decls)

    def parse_declaration(self):
        if self.current().type == TokenType.LET:
            return self.parse_let()
        if self.current().type == TokenType.FN:
            return self.parse_fn()
        if self.current().type == TokenType.STRUCT:
            return self.parse_struct()
        if self.current().type == TokenType.ZK:
            return self.parse_zk()
        return self.parse_expr_statement()

    def parse_let(self):
        self.advance()
        name = self.expect(TokenType.IDENT).value
        type_annot = None
        if self.current().type == TokenType.COLON:
            self.advance()
            type_annot = self.expect(TokenType.IDENT).value
        self.expect(TokenType.ASSIGN)
        init = self.parse_expr()
        return LetDecl(name, False, type_annot or "int", init)

    def parse_fn(self):
        self.advance()
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LPAREN)
        params = []
        if self.current().type != TokenType.RPAREN:
            params.append(self.parse_param())
            while self.current().type == TokenType.COMMA:
                self.advance()
                params.append(self.parse_param())
        self.expect(TokenType.RPAREN)
        if self.current().type == TokenType.ARROW:
            self.advance()
            ret_type = self.expect(TokenType.IDENT).value
        else:
            ret_type = "void"
        body = self.parse_block()
        return FnDecl(name, params, ret_type, body, True, False)

    def parse_param(self):
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.COLON)
        type_ = self.expect(TokenType.IDENT).value
        return (name, type_)

    def parse_struct(self):
        self.advance()
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LBRACE)
        fields = []
        if self.current().type != TokenType.RBRACE:
            fields.append(self.parse_field())
            while self.current().type == TokenType.COMMA:
                self.advance()
                if self.current().type == TokenType.RBRACE:
                    break
                fields.append(self.parse_field())
        self.expect(TokenType.RBRACE)
        return StructDecl(name, fields, True)

    def parse_field(self):
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.COLON)
        type_ = self.expect(TokenType.IDENT).value
        return (name, type_)

    def parse_zk(self):
        self.advance()
        self.expect(TokenType.PROVE)
        self.expect(TokenType.LPAREN)
        stmt = self.expect(TokenType.STRING).value
        inputs = []
        while self.current().type == TokenType.COMMA:
            self.advance()
            inputs.append(self.expect(TokenType.STRING).value)
        self.expect(TokenType.RPAREN)
        return ZKProofExpr(stmt, inputs)

    def parse_block(self):
        self.expect(TokenType.LBRACE)
        stmts = []
        while self.current().type != TokenType.RBRACE:
            stmts.append(self.parse_statement())
        self.expect(TokenType.RBRACE)
        return stmts

    def parse_statement(self):
        if self.current().type == TokenType.RETURN:
            self.advance()
            return ReturnExpr(self.parse_expr())
        return self.parse_expr()

    def parse_expr_statement(self):
        return self.parse_expr()

    def parse_expr(self):
        return self.parse_additive()

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.current().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self.parse_multiplicative()
            left = BinaryOp(op, left, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_primary()
        while self.current().type in (TokenType.STAR, TokenType.SLASH):
            op = self.advance().value
            right = self.parse_primary()
            left = BinaryOp(op, left, right)
        return left

    def parse_primary(self):
        tok = self.current()
        if tok.type == TokenType.INT:
            self.advance()
            return IntLiteral(int(tok.value))
        if tok.type == TokenType.STRING:
            self.advance()
            return StringLiteral(tok.value)
        if tok.type == TokenType.BOOL:
            self.advance()
            return BoolLiteral(tok.value == 'true')
        if tok.type == TokenType.IDENT:
            self.advance()
            return Identifier(tok.value)
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr
        raise SyntaxError(f"Unexpected token {tok.type}")

# ===== TYPE CHECKER =====
class TypeChecker:
    def __init__(self):
        self.errors = []
        self.env = {}

    def check(self, program: Program) -> bool:
        self.errors = []
        for decl in program.declarations:
            self.check_decl(decl)
        return len(self.errors) == 0

    def get_errors(self):
        return self.errors

    def check_decl(self, decl):
        if isinstance(decl, LetDecl):
            init_type = self.infer_type(decl.initializer)
            if decl.type and init_type != decl.type:
                self.errors.append(f"Type mismatch: expected {decl.type}, got {init_type}")
        elif isinstance(decl, FnDecl):
            for stmt in decl.body:
                self.check_stmt(stmt)

    def check_stmt(self, stmt):
        if isinstance(stmt, ReturnExpr):
            self.infer_type(stmt.value)

    def infer_type(self, expr):
        if isinstance(expr, IntLiteral):
            return "int"
        if isinstance(expr, StringLiteral):
            return "string"
        if isinstance(expr, BoolLiteral):
            return "bool"
        if isinstance(expr, Identifier):
            return self.env.get(expr.name, "unknown")
        if isinstance(expr, BinaryOp):
            left = self.infer_type(expr.left)
            right = self.infer_type(expr.right)
            if left == "int" and right == "int":
                return "int"
            return "unknown"
        return "unknown"

# ===== ZK PROOF GENERATOR =====
class ZKProofGenerator:
    def __init__(self):
        self.proofs = {}

    def generate(self, program: Program) -> Dict[str, Any]:
        self.proofs = {}
        for decl in program.declarations:
            if isinstance(decl, ZKProofExpr):
                proof_id = hashlib.sha3_256(f"{decl.statement}:{','.join(decl.public_inputs)}".encode()).hexdigest()[:16]
                self.proofs[proof_id] = {
                    'statement': decl.statement,
                    'inputs': decl.public_inputs,
                    'hash': proof_id,
                }
        return self.proofs

    def verify(self, proof_id: str) -> bool:
        return proof_id in self.proofs

# ===== RUST CODE GENERATOR =====
class RustCodeGenerator:
    def __init__(self):
        self.code = []
        self.indent = 0

    def emit(self, line):
        self.code.append("    " * self.indent + line)

    def generate(self, program: Program) -> str:
        self.code = []
        self.emit("// Auto-generated by ARKHE OS Substrate 6068")
        self.emit("")
        has_main = False
        for decl in program.declarations:
            if isinstance(decl, FnDecl) and decl.name == "main":
                has_main = True
            self.gen_decl(decl)
        if not has_main:
            non_fn = [d for d in program.declarations if not isinstance(d, FnDecl)]
            if non_fn:
                self.emit("fn main() {")
                self.indent += 1
                for decl in non_fn:
                    if isinstance(decl, LetDecl):
                        self.emit(f"let {decl.name}: i64 = {self.gen_expr(decl.initializer)};")
                    elif isinstance(decl, IntLiteral):
                        self.emit(f"let _tmp = {self.gen_expr(decl)};")
                    else:
                        self.emit(f"let _tmp = {self.gen_expr(decl)};")
                self.indent -= 1
                self.emit("}")
        return "\n".join(self.code)

    def gen_decl(self, decl):
        if isinstance(decl, FnDecl):
            pub = "pub " if decl.pub else ""
            self.emit(f"{pub}fn {decl.name}({self.gen_params(decl.params)}) -> {self.map_type(decl.return_type)} {{")
            self.indent += 1
            for stmt in decl.body:
                self.gen_stmt(stmt)
            self.indent -= 1
            self.emit("}")
        elif isinstance(decl, StructDecl):
            pub = "pub " if decl.pub else ""
            self.emit(f"{pub}struct {decl.name} {{")
            self.indent += 1
            for name, type_ in decl.fields:
                self.emit(f"pub {name}: {self.map_type(type_)},")
            self.indent -= 1
            self.emit("}")
        elif isinstance(decl, LetDecl):
            pass
        elif isinstance(decl, ZKProofExpr):
            self.emit(f"// ZK proof: {decl.statement}")

    def gen_params(self, params):
        return ", ".join(f"{name}: {self.map_type(type_)}" for name, type_ in params)

    def map_type(self, t):
        return {"int": "i64", "string": "String", "bool": "bool"}.get(t, t)

    def gen_stmt(self, stmt):
        if isinstance(stmt, ReturnExpr):
            self.emit(f"return {self.gen_expr(stmt.value)};")
        else:
            self.emit(f"{self.gen_expr(stmt)};")

    def gen_expr(self, expr):
        if isinstance(expr, IntLiteral):
            return str(expr.value)
        if isinstance(expr, StringLiteral):
            return f'"{expr.value}"'
        if isinstance(expr, BoolLiteral):
            return str(expr.value).lower()
        if isinstance(expr, Identifier):
            return expr.name
        if isinstance(expr, BinaryOp):
            return f"({self.gen_expr(expr.left)} {expr.op} {self.gen_expr(expr.right)})"
        return ""

# ===== COMPILER =====
class ArkCompiler:
    def compile(self, source: str) -> Dict[str, Any]:
        lexer = ArkLexer(source)
        tokens = lexer.tokenize()
        parser = ArkParser(tokens)
        ast = parser.parse()
        tc = TypeChecker()
        type_ok = tc.check(ast)
        zk = ZKProofGenerator()
        zk_proofs = zk.generate(ast)
        rust = RustCodeGenerator()
        rust_code = rust.generate(ast)
        rust_lines = len(rust_code.splitlines())
        seal_input = f"{source}:{len(tokens)}:{len(ast.declarations)}:{rust_lines}"
        canonical_seal = hashlib.sha3_256(seal_input.encode()).hexdigest()[:16]
        return {
            "success": True,
            "tokens": len(tokens),
            "declarations": len(ast.declarations),
            "canonical_seal": canonical_seal,
            "rust_lines": rust_lines,
            "zk_proofs": list(zk_proofs.keys()),
            "type_ok": type_ok,
            "errors": tc.get_errors(),
        }

# ===== SUBSTRATE =====
class ArkheSelfCompilationSubstrate:
    def __init__(self):
        self.compiled_programs = {}

    def compile_source(self, name: str, source: str) -> Dict[str, Any]:
        compiler = ArkCompiler()
        result = compiler.compile(source)
        self.compiled_programs[name] = result
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {
            "compiled_programs": len(self.compiled_programs),
        }

    def get_canonical_seal(self) -> str:
        data = json.dumps(self.compiled_programs, sort_keys=True, default=str)
        return hashlib.sha3_256(data.encode()).hexdigest()[:16]

# ===== S8 NAMESPACE =====
S8 = types.SimpleNamespace(
    TokenType=TokenType,
    Token=Token,
    ArkLexer=ArkLexer,
    ArkParser=ArkParser,
    Program=Program,
    LetDecl=LetDecl,
    FnDecl=FnDecl,
    StructDecl=StructDecl,
    ZKProofExpr=ZKProofExpr,
    IntLiteral=IntLiteral,
    StringLiteral=StringLiteral,
    BoolLiteral=BoolLiteral,
    BinaryOp=BinaryOp,
    Identifier=Identifier,
    ReturnExpr=ReturnExpr,
    TypeChecker=TypeChecker,
    ZKProofGenerator=ZKProofGenerator,
    RustCodeGenerator=RustCodeGenerator,
    ArkCompiler=ArkCompiler,
    ArkheSelfCompilationSubstrate=ArkheSelfCompilationSubstrate,
)

# ===== TEST SUITE (uploaded by user) =====
# Full 6068 test suite with proper def syntax
results = []
def test(name, fn):
    try:
        fn()
        results.append((name, "PASS", None))
        print(f"  OK {name}")
    except Exception as e:
        results.append((name, "FAIL", str(e)))
        print(f"  FAIL {name}: {e}")

print("\n=== SUBSTRATO 6068 FULL TEST ===\n")

# Lexer
def t1():
    toks = S8.ArkLexer("42").tokenize()
    assert toks[0].type == S8.TokenType.INT and toks[0].value == "42"
test("Lex int", t1)

def t2():
    toks = S8.ArkLexer('"hello"').tokenize()
    assert toks[0].type == S8.TokenType.STRING and toks[0].value == "hello"
test("Lex string", t2)

def t3():
    toks = S8.ArkLexer("fn main() {}").tokenize()
    assert [t.type for t in toks[:-1]] == [S8.TokenType.FN, S8.TokenType.IDENT, S8.TokenType.LPAREN, S8.TokenType.RPAREN, S8.TokenType.LBRACE, S8.TokenType.RBRACE]
test("Lex fn", t3)

def t4():
    toks = S8.ArkLexer("let x = 10").tokenize()
    assert [t.type for t in toks[:-1]] == [S8.TokenType.LET, S8.TokenType.IDENT, S8.TokenType.ASSIGN, S8.TokenType.INT]
test("Lex let", t4)

def t5():
    toks = S8.ArkLexer("1 + 2 * 3").tokenize()
    assert [t.value for t in toks[:-1]] == ["1", "+", "2", "*", "3"]
test("Lex expr", t5)

def t6():
    toks = S8.ArkLexer("true false").tokenize()
    assert toks[0].type == S8.TokenType.BOOL and toks[1].type == S8.TokenType.BOOL
test("Lex bools", t6)

def t7():
    toks = S8.ArkLexer("== != <= >=") .tokenize()
    assert [t.type for t in toks[:-1]] == [S8.TokenType.EQ, S8.TokenType.NEQ, S8.TokenType.LE, S8.TokenType.GE]
test("Lex ops", t7)

# Parser
def t8():
    ast = S8.ArkParser(S8.ArkLexer("let x = 10").tokenize()).parse()
    assert len(ast.declarations) == 1 and isinstance(ast.declarations[0], S8.LetDecl) and ast.declarations[0].name == "x"
test("Parse let", t8)

def t9():
    ast = S8.ArkParser(S8.ArkLexer("fn add(a: int, b: int) -> int { return a + b }").tokenize()).parse()
    fn = ast.declarations[0]
    assert isinstance(fn, S8.FnDecl) and fn.name == "add" and len(fn.params) == 2 and fn.return_type == "int"
test("Parse fn", t9)

def t10():
    ast = S8.ArkParser(S8.ArkLexer("struct Point { x: int, y: int }").tokenize()).parse()
    st = ast.declarations[0]
    assert isinstance(st, S8.StructDecl) and st.name == "Point" and len(st.fields) == 2
test("Parse struct", t10)

def t11():
    ast = S8.ArkParser(S8.ArkLexer('zk prove("stmt", "in1", "in2")').tokenize()).parse()
    zk = ast.declarations[0]
    assert isinstance(zk, S8.ZKProofExpr) and zk.statement == "stmt" and len(zk.public_inputs) == 2
test("Parse zk", t11)

# TypeChecker
def t12():
    tc = S8.TypeChecker()
    assert tc.check(S8.Program([S8.LetDecl("x", False, "int", S8.IntLiteral(42))])) and len(tc.get_errors()) == 0
test("TC valid", t12)

def t13():
    tc = S8.TypeChecker()
    assert not tc.check(S8.Program([S8.LetDecl("x", False, "string", S8.IntLiteral(42))])) and len(tc.get_errors()) == 1
test("TC invalid", t13)

# ZK
def t14():
    zk = S8.ZKProofGenerator()
    proofs = zk.generate(S8.Program([S8.ZKProofExpr("x > 0", ["x"]), S8.ZKProofExpr("y < 100", ["y"])]))
    assert len(proofs) == 2
test("ZK gen", t14)

def t15():
    zk = S8.ZKProofGenerator()
    proofs = zk.generate(S8.Program([S8.ZKProofExpr("test", ["a"])]))
    assert zk.verify(list(proofs.keys())[0])
test("ZK verify", t15)

# Rust codegen
def t16():
    code = S8.RustCodeGenerator().generate(S8.Program([S8.IntLiteral(42)]))
    assert "fn main()" in code and "Auto-generated" in code
test("Rust basic", t16)

def t17():
    code = S8.RustCodeGenerator().generate(S8.Program([
        S8.FnDecl("add", [("a", "int"), ("b", "int")], "int", [
            S8.ReturnExpr(S8.BinaryOp("+", S8.Identifier("a"), S8.Identifier("b")))
        ], True, False)
    ]))
    assert "pub fn add" in code and "-> i64" in code
test("Rust fn", t17)

def t18():
    code = S8.RustCodeGenerator().generate(S8.Program([
        S8.StructDecl("Point", [("x", "int"), ("y", "int")], True)
    ]))
    assert "pub struct Point" in code and "pub x: i64" in code
test("Rust struct", t18)

# Compiler pipeline
def t19():
    r = S8.ArkCompiler().compile("let x = 42")
    assert r["success"] and r["tokens"] > 0 and r["declarations"] == 1 and len(r["canonical_seal"]) == 16
test("Compile simple", t19)

def t20():
    r = S8.ArkCompiler().compile("fn add(a: int, b: int) -> int { return a + b }\nstruct Point { x: int, y: int }\nlet origin = 0")
    assert r["success"] and r["declarations"] == 3 and r["rust_lines"] > 10
test("Compile complex", t20)

def t21():
    r = S8.ArkCompiler().compile('zk prove("x > 0", "x")')
    assert r["success"] and len(r["zk_proofs"]) == 1
test("Compile ZK", t21)

# Orquestrador
def t22():
    sub = S8.ArkheSelfCompilationSubstrate()
    r = sub.compile_source("test", "let x = 10")
    assert r["success"] and "test" in sub.compiled_programs
test("Substrate compile", t22)

def t23():
    sub = S8.ArkheSelfCompilationSubstrate()
    sub.compile_source("p1", "let a = 1")
    sub.compile_source("p2", "let b = 2")
    assert sub.get_stats()["compiled_programs"] == 2
test("Substrate stats", t23)

def t24():
    sub = S8.ArkheSelfCompilationSubstrate()
    sub.compile_source("test", "fn main() {}")
    assert len(sub.get_canonical_seal()) == 16
test("Substrate seal", t24)

print("\n" + "="*55)
p = sum(1 for r in results if r[1] == "PASS")
f = sum(1 for r in results if r[1] == "FAIL")
print(f"Total: {len(results)} | PASS: {p} | FAIL: {f}")
if f == 0:
    print("ALL PASSED — Substrato 6068 validado.")
    chain = json.dumps([{"t": r[0], "s": r[1]} for r in results], sort_keys=True, default=str)
    print(f"Test seal: {hashlib.sha3_256(chain.encode()).hexdigest()[:16]}")
    with open('substrato_6068_self_compilation.py', 'rb') as f:
        print(f"Substrate seal: {hashlib.sha3_256(f.read()).hexdigest()[:16]}")
else:
    for n, s, e in results:
        if s == "FAIL": print(f"  FAIL: {n}: {e}")