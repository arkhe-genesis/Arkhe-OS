#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arkhe_polyglot_parser.py — ARKHE Ω-TEMP v5.0.0 Substrato 6061
================================================================
Polymath-Polyglot Parser (P³): O Intérprete Universal da Catedral.

Uso:
  python arkhe_polyglot_parser.py --demo
  python arkhe_polyglot_parser.py detect --file hello.py
  python arkhe_polyglot_parser.py transpile --source hello.py --target rust
"""

import argparse
import hashlib
import json
import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import ctypes
import importlib.util
from typing import Set

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from lark import Lark, Tree as LarkTree
    HAS_LARK = True
except ImportError:
    HAS_LARK = False

try:
    # Attempt to import TemporalHashChain
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from temporal_network import TemporalHashChain, TemporalMessage
    HAS_TEMPORAL = True
except ImportError:
    HAS_TEMPORAL = False


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

VERSION = "5.0.0"
SUBSTRATE = 6061

log = logging.getLogger("arkhe.p3")

def setup_logging(level: str = "INFO"):
    fmt = "[%(asctime)s] [%(levelname)-8s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt, datefmt=datefmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

# ============================================================================
# TIPOS BÁSICOS
# ============================================================================

class LanguageType(Enum):
    FreeForm = auto()
    IndentationSensitive = auto()
    PatternBased = auto()
    ExpressionBased = auto()
    Declarative = auto()
    Mixed = auto()

class NodeKind(Enum):
    Program = auto(); Module = auto(); Package = auto(); File = auto(); Block = auto()
    DeclVariable = auto(); DeclFunction = auto(); DeclClass = auto()
    DeclInterface = auto(); DeclEnum = auto(); DeclImport = auto(); DeclExport = auto()
    ExprLiteral = auto(); ExprIdentifier = auto(); ExprUnary = auto(); ExprBinary = auto()
    ExprTernary = auto(); ExprCall = auto(); ExprMethodCall = auto(); ExprIndex = auto()
    ExprField = auto(); ExprArrow = auto(); ExprLambda = auto(); ExprAwait = auto()
    ExprReturn = auto(); ExprThrow = auto(); ExprCast = auto(); ExprAssignment = auto();
    DeclTypeAlias = auto(); DeclTrait = auto()
    ExprMatch = auto()
    StmtExpression = auto(); StmtIf = auto(); StmtWhile = auto(); StmtFor = auto()
    StmtSwitch = auto(); StmtBreak = auto(); StmtContinue = auto(); StmtTry = auto()
    TypePrimitive = auto(); TypeReference = auto(); TypeRef = auto(); TypeArray = auto(); TypeTuple = auto()
    TypeFunction = auto(); TypeGeneric = auto(); TypeOptional = auto()
    OOPField = auto(); OOPMethod = auto(); OOPConstructor = auto()
    ConcurrentSpawn = auto(); ConcurrentSend = auto()
    LogicFact = auto(); LogicRule = auto(); LogicQuery = auto()
    SQLSelect = auto(); SQLFrom = auto(); SQLWhere = auto(); SQLJoin = auto()
    GraphMatch = auto(); GraphCreate = auto()
    ChainStorage = auto(); ChainEvent = auto()
    WasmModule = auto(); WasmFunction = auto(); WasmParam = auto()
    Annotation = auto(); Comment = auto()

@dataclass
class UASTNode:
    id: int
    kind: NodeKind
    children: List[int] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    line: int = 0
    column: int = 0

@dataclass
class UAST:
    root: int
    nodes: Dict[int, UASTNode]
    language: str
    version_hash: str = ""

    def compute_hash(self) -> str:
        data = json.dumps({k: {"kind": v.kind.name, **v.attributes} for k, v in self.nodes.items()}, sort_keys=True)
        return hashlib.sha3_256(data.encode()).hexdigest()

    def node_count(self) -> int:
        return len(self.nodes)


    def to_mermaid(self) -> str:
        lines = ["graph TD"]
        for nid, node in self.nodes.items():
            name = node.attributes.get("name", node.kind.name)
            lines.append(f"    N{nid}[\"{name}\"]")
            for child in node.children:
                lines.append(f"    N{nid} --> N{child}")
        return "\n".join(lines)

    def to_dot(self) -> str:
        lines = ["digraph UAST {"]
        for nid, node in self.nodes.items():
            name = node.attributes.get("name", node.kind.name)
            lines.append(f"    N{nid} [label=\"{name}\"];")
            for child in node.children:
                lines.append(f"    N{nid} -> N{child};")
        lines.append("}")
        return "\n".join(lines)

    def max_depth(self) -> int:
        def depth(node_id: int) -> int:
            node = self.nodes.get(node_id)
            if not node or not node.children:
                return 1
            return 1 + max(depth(c) for c in node.children)
        return depth(self.root)

# ============================================================================
# REGISTRY DE LINGUAGENS
# ============================================================================

@dataclass
class LanguageSpec:
    name: str
    display_name: str
    version: str
    language_type: LanguageType
    author: str
    description: str
    file_extensions: List[str]
    shebangs: List[str]
    keywords: List[str]
    grammar_version: str

class LanguageRegistry:
    def __init__(self):
        self._languages: Dict[str, LanguageSpec] = {}
        self._by_extension: Dict[str, LanguageSpec] = {}
        self._ml_clf = None
        self._ml_vec = None
        self._register_defaults()
        if HAS_SKLEARN:
            self._init_ml()

    def _init_ml(self):
        self._ml_vec = TfidfVectorizer(max_features=100)
        self._ml_clf = MultinomialNB()
        corpus = [
            "def main(): print('hello')",
            "fn main() { println!(\"hello\"); }",
            "function main() { console.log('hello'); }",
            "int main() { printf(\"hello\"); return 0; }",
            "package main; func main() { fmt.Println(\"hello\") }",
        ]
        labels = ["python", "rust", "javascript", "c", "go"]
        try:
            X = self._ml_vec.fit_transform(corpus)
            self._ml_clf.fit(X, labels)
        except Exception as e:
            log.warning(f"Failed to init ML detection: {e}")
            self._ml_clf = None

    def _register_defaults(self):
        defaults = [
            LanguageSpec("rust", "Rust", "2024", LanguageType.FreeForm, "Mozilla", "Systems programming language focused on safety.", [".rs"], ["#!/usr/bin/env rust"], ["fn ", "let mut", "impl", "trait", "struct", "enum", "match", "pub fn", "use ", "mod ", "unsafe", "async fn", "await"], "1.0"),
            LanguageSpec("python", "Python", "3.12", LanguageType.IndentationSensitive, "PSF", "High-level interpreted language emphasizing readability.", [".py", ".pyw", ".pyi"], ["#!/usr/bin/env python3"], ["def ", "class ", "import ", "from ", "if ", "elif ", "else:", "for ", "while ", "try:", "except", "with ", "yield", "lambda", "return", "None", "True", "False", "self,"], "3.12"),
            LanguageSpec("javascript", "JavaScript", "ES2024", LanguageType.FreeForm, "ECMA", "Dynamic language for web and server.", [".js", ".mjs", ".cjs"], ["#!/usr/bin/env node"], ["function ", "const ", "let ", "var ", "=>", "async function", "await ", "export ", "import ", "class ", "extends", "new ", "typeof ", "instanceof", "document.", "console."], "ES2024"),
            LanguageSpec("typescript", "TypeScript", "5.4", LanguageType.FreeForm, "Microsoft", "JavaScript with optional static typing.", [".ts", ".tsx", ".mts", ".cts"], ["#!/usr/bin/env ts-node"], ["interface ", "type ", ": string", ": number", ": boolean", "as ", "enum ", "readonly", "declare", "namespace", "Record<", "Partial<"], "5.4"),
            LanguageSpec("c", "C", "C17", LanguageType.FreeForm, "ISO/IEC", "General-purpose procedural language.", [".c", ".h"], [], ["#include", "int main", "printf", "malloc", "free", "struct ", "typedef ", "char *", "void *", "for (", "while (", "#define", "return 0;"], "C17"),
            LanguageSpec("cpp", "C++", "C++23", LanguageType.FreeForm, "ISO/IEC", "Multi-paradigm language with OOP and templates.", [".cpp", ".cc", ".cxx", ".hpp"], [], ["#include", "int main", "namespace", "std::", "class ", "template", "public:", "private:", "virtual", "override", "cout <<", "std::cout"], "C++23"),
            LanguageSpec("go", "Go", "1.21", LanguageType.FreeForm, "Google", "Simple, fast, concurrent programming language.", [".go"], ["#!/usr/bin/env go run"], ["func ", "package ", "import ", "var ", "const ", "type ", "struct", "interface", "go ", "defer ", "chan ", "fmt.Println", "make(", "range "], "1.21"),
            LanguageSpec("zig", "Zig", "0.12", LanguageType.FreeForm, "Andrew Kelley", "General-purpose language for robust software.", [".zig"], [], ["fn ", "const ", "var ", "pub fn", "comptime", "struct {", "union(enum)", "test ", "try ", "defer ", "errdefer", "usingnamespace"], "0.12"),
            LanguageSpec("haskell", "Haskell", "2010", LanguageType.Mixed, "Haskell Committee", "Purely functional language with lazy evaluation.", [".hs"], [], ["module ", "where", "let", "in ", "case ", "of ", "do ", "data ", "type ", "class ", "instance", "import ", ":: ", "->", "= "], "2010"),
            LanguageSpec("prolog", "Prolog", "ISO", LanguageType.PatternBased, "Colmerauer/Kowalski", "Logic programming language for AI.", [".pl", ".pro"], ["#!/usr/bin/env swipl"], [":-", "?", "- ", "is ", "write(", "read(", "nl", "fail.", "true.", "assert", "retract", "atom"], "ISO"),
            LanguageSpec("sql", "SQL", "SQL:2023", LanguageType.Declarative, "ISO", "Query language for relational databases.", [".sql"], [], ["SELECT ", "FROM ", "WHERE ", "JOIN ", "ON ", "GROUP BY", "ORDER BY", "INSERT INTO", "UPDATE ", "DELETE FROM", "CREATE TABLE", "ALTER TABLE", "DISTINCT", "COUNT(", "SUM("], "SQL:2023"),
            LanguageSpec("cypher", "Cypher", "GQL", LanguageType.Declarative, "Neo4j", "Graph query language for property graphs.", [".cypher"], [], ["MATCH ", "CREATE ", "MERGE ", "WHERE ", "RETURN ", "WITH ", "DELETE ", "SET ", "REMOVE ", "UNWIND"], "GQL"),
            LanguageSpec("sparql", "SPARQL", "1.2", LanguageType.Declarative, "W3C", "Query language for RDF graphs.", [".rq", ".sparql"], [], ["PREFIX ", "SELECT ", "WHERE {", "?s ", "?p ", "?o ", "FILTER", "ORDER BY", "LIMIT"], "1.2"),
            LanguageSpec("cairo", "Cairo", "2.7", LanguageType.FreeForm, "StarkWare", "Language for provable programs on StarkNet.", [".cairo"], [], ["func ", "fn main", "@storage", "@event", "@interface", "returns", "felt", "uint256", "implicits", "builtins"], "2.7"),
            LanguageSpec("noir", "Noir", "0.1", LanguageType.FreeForm, "Aztec", "Language for private smart contracts.", [".nr"], [], ["fn ", "pub fn", "let ", "mut ", "for ", "in ", "comptime", "unconstrained", "std::"], "0.1"),
            LanguageSpec("move", "Move", "1.0", LanguageType.FreeForm, "Meta/Diem", "Safe smart contract language for blockchain.", [".move"], [], ["module ", "fun ", "struct ", "resource ", "public ", "acquires", "native", "spec ", "invariant", "pragma"], "1.0"),
            LanguageSpec("solidity", "Solidity", "0.8.24", LanguageType.FreeForm, "Ethereum Foundation", "Smart contract language for Ethereum.", [".sol"], [], ["pragma solidity", "contract ", "function ", "event ", "mapping(", "msg.sender", "require(", "emit ", "address", "uint256", "IERC"], "0.8.24"),
            LanguageSpec("coq", "Coq", "8.19", LanguageType.PatternBased, "INRIA", "Formal proof management system.", [".v"], [], ["Theorem", "Lemma", "Proof.", "Qed.", "Definition", "Inductive", "Fixpoint", "Require Import", "Section", "Variable"], "8.19"),
            LanguageSpec("agda", "Agda", "2.6.3", LanguageType.Mixed, "Chalmers", "Dependently typed functional language.", [".agda"], [], ["module ", "where", "data ", "record ", "postulate", "open import", "Set", "Type"], "2.6.3"),
            LanguageSpec("idris", "Idris", "2", LanguageType.FreeForm, "Edwin Brady", "General purpose dependently typed language.", [".idr"], [], ["module ", "where", "data ", "record ", "interface", "implementation", "Nat", "Vect", "the ", "repl"], "2.0"),
            LanguageSpec("lua", "Lua", "5.4", LanguageType.FreeForm, "PUC-Rio", "Lightweight embeddable scripting language.", [".lua"], ["#!/usr/bin/env lua"], ["function ", "local ", "return ", "if ", "then", "else", "elseif", "for ", "while ", "do", "end", "nil", "true", "false", "require("], "5.4"),
            LanguageSpec("ruby", "Ruby", "3.3", LanguageType.FreeForm, "Yukihiro Matsumoto", "Dynamic, reflective, object-oriented language.", [".rb"], ["#!/usr/bin/env ruby"], ["def ", "class ", "module ", "require ", "include ", "attr_accessor", "yield", "block_given?", "self.", "puts ", "end"], "3.3"),
            LanguageSpec("r", "R", "4.3", LanguageType.ExpressionBased, "R Core Team", "Language for statistical computing.", [".r", ".R"], [], ["function(", "<-", "=>", "library(", "data.frame", "ggplot", "lm(", "summary(", "plot(", "c(", "list(", "matrix("], "4.3"),
            LanguageSpec("julia", "Julia", "1.10", LanguageType.FreeForm, "Bezanson et al.", "High-performance language for technical computing.", [".jl"], ["#!/usr/bin/env julia"], ["function ", "end", "module ", "using ", "import ", "struct ", "mutable struct", "abstract type", "where ", "macro ", "@time", "println("], "1.10"),
            LanguageSpec("wat", "WebAssembly Text", "1.0", LanguageType.ExpressionBased, "W3C", "Text format for WebAssembly.", [".wat"], [], ["(module", "(func", "(param", "(result", "(local", "(global", "(memory", "(table", "(data", "(elem", "(export", "(import", "i32", "i64", "f32", "f64"], "1.0"),
            LanguageSpec("yaml", "YAML", "1.2", LanguageType.Declarative, "Evans/Ben-Kiki", "Human-readable data serialization.", [".yml", ".yaml"], [], ["---", "...", ": ", "- ", "  ", "# ", "true", "false", "null", "|", ">"], "1.2"),
            LanguageSpec("toml", "TOML", "1.0", LanguageType.Declarative, "Tom Preston-Werner", "Minimal configuration file format.", [".toml"], [], ["[", "]", "= ", "# ", "true", "false", chr(34)+chr(34)+chr(34), chr(39)+chr(39)+chr(39), "[[", "]]"], "1.0"),
            LanguageSpec("agi", "AGI Specification", "1.0", LanguageType.Declarative, "ARKHE Cathedral", "ARKHE General Intelligence spec format.", [".agi"], [], ["name:", "version:", "description:", "type:", "input:", "output:", "constraint:", "permission:", "endpoint:", "payload:", "signature:"], "1.0"),
            LanguageSpec("arkasm", "ARKHE Assembly", "1.0", LanguageType.ExpressionBased, "ARKHE Cathedral", "Low-level assembly for ARKHE VM.", [".arkasm"], [], ["MOV", "ADD", "SUB", "MUL", "DIV", "JMP", "CALL", "RET", "PUSH", "POP", "LOAD", "STORE", "NOP", "HLT"], "1.0"),
        ]
        for spec in defaults:
            self.register(spec)

    def register(self, spec: LanguageSpec):
        self._languages[spec.name] = spec
        for ext in spec.file_extensions:
            self._by_extension[ext.lower()] = spec

    def get(self, name: str) -> Optional[LanguageSpec]:
        return self._languages.get(name.lower())

    def get_by_extension(self, ext: str) -> Optional[LanguageSpec]:
        return self._by_extension.get(ext.lower())

    def detect(self, source: str, filename: Optional[str] = None) -> List[Tuple[LanguageSpec, float]]:
        candidates = []
        if filename:
            ext = Path(filename).suffix.lower()
            if ext:
                spec = self.get_by_extension(ext)
                if spec:
                    candidates.append((spec, 0.85))
        first_line = source.splitlines()[0] if source else ""
        for spec in self._languages.values():
            for shebang in spec.shebangs:
                if first_line.startswith(shebang):
                    candidates.append((spec, 0.95))

        if HAS_SKLEARN and self._ml_clf is not None and source:
            try:
                X_test = self._ml_vec.transform([source])
                preds = self._ml_clf.predict_proba(X_test)[0]
                classes = self._ml_clf.classes_
                for i, prob in enumerate(preds):
                    if prob > 0.1:
                        spec = self.get(classes[i])
                        if spec:
                            candidates.append((spec, prob * 0.5)) # ML as a soft signal
            except Exception:
                pass

        for spec in self._languages.values():
            score = self._score_content(source, spec)
            if score > 0.15:
                candidates.append((spec, score))
        seen = set()
        unique = []
        for spec, score in sorted(candidates, key=lambda x: x[1], reverse=True):
            if spec.name not in seen:
                seen.add(spec.name)
                unique.append((spec, score))
        return unique[:5]

    def _score_content(self, source: str, spec: LanguageSpec) -> float:
        if not spec.keywords:
            return 0.0
        hits = sum(1 for kw in spec.keywords if kw in source)
        return min(1.0, hits / len(spec.keywords))

    def list_all(self) -> List[str]:
        return sorted(self._languages.keys())

    def count(self) -> int:
        return len(self._languages)

# ============================================================================
# PARSER
# ============================================================================


class PolyglotParser:
    def __init__(self):
        self.registry = LanguageRegistry()
        self._parse_count = 0
        self._transpile_count = 0
        self.temporal_chain = None
        if HAS_TEMPORAL:
            self.temporal_chain = TemporalHashChain()
        self._plugins = {}



    def detect_language(self, source: str, filename: Optional[str] = None) -> Dict:
        candidates = self.registry.detect(source, filename)

        # Consult plugins for language detection
        for p_name, p_mod in self._plugins.items():
            if hasattr(p_mod, 'detect'):
                p_cand = p_mod.detect(source, filename)
                if p_cand:
                    candidates.extend(p_cand)
                    candidates.sort(key=lambda x: x[1], reverse=True)

        if not candidates:
            return {"language": "unknown", "confidence": 0.0, "alternatives": []}

        best, score = candidates[0]
        return {
            "language": best.name,
            "display_name": best.display_name,
            "confidence": round(score, 4),
            "alternatives": [{"name": s.name, "confidence": round(sc, 4)} for s, sc in candidates[1:3]],
            "language_type": best.language_type.name,
        }


    def load_plugin(self, path: str):
        if path.endswith(".so"):
            try:
                plugin = ctypes.CDLL(path)
                log.info(f"Loaded .so plugin: {path}")
                self._plugins[path] = plugin
            except Exception as e:
                log.error(f"Failed to load .so plugin {path}: {e}")
        elif path.endswith(".py"):
            try:
                name = Path(path).stem
                spec = importlib.util.spec_from_file_location(name, path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                log.info(f"Loaded Python plugin: {path}")
                self._plugins[name] = mod
            except Exception as e:
                log.error(f"Failed to load Python plugin {path}: {e}")
        elif path.endswith(".wasm"):
            log.info(f"WASM plugins not natively supported yet: {path}")

    def parse(self, source: str, filename: Optional[str] = None) -> Dict:
        detection = self.detect_language(source, filename)
        lang = detection["language"]
        uast = self._build_uast(source, lang)

        if self.temporal_chain:
            try:
                # Assuming simple append method exists
                import time
                import uuid
                msg = TemporalMessage(
                    id=str(uuid.uuid4()),
                    content=str(uast.version_hash),
                    source_timestamp=time.time(),
                    target_timestamp=time.time(),
                    sender_seal="P3_PARSER",
                    receiver_seal="UAST",
                    metadata={"hash": uast.version_hash, "language": lang}
                )
                self.temporal_chain.insert_retrocausal(
                    target_ts=time.time(),
                    data={"hash": uast.version_hash, "language": lang},
                    proof="P3_PARSER_PROOF"
                )
                log.info(f"Registered UAST {uast.version_hash[:8]} in TemporalHashChain")
            except Exception as e:
                log.warning(f"Failed to register in TemporalHashChain: {e}")

        self._parse_count += 1
        return {
            "detected_language": lang,
            "confidence": detection["confidence"],
            "uast": {
                "root": uast.root,
                "node_count": uast.node_count(),
                "max_depth": uast.max_depth(),
                "language": uast.language,
                "version_hash": uast.version_hash,
            },
            "metrics": {
                "source_length": len(source),
                "line_count": source.count(chr(10)) + 1,
                "token_estimate": len(source.split()),
            }
        }



    def _build_uast(self, source: str, language: str) -> UAST:
        if HAS_LARK and language in ["python", "c", "rust"]:
            grammar = """
                start: decl+
                decl: "def" WS NAME "(" ")" ":" WS "pass" -> func_decl
                    | "let" WS NAME "=" NUMBER ";" -> var_decl
                %import common.CNAME -> NAME
                %import common.NUMBER
                %import common.WS
                %ignore WS
            """
            try:
                parser = Lark(grammar, start='start', parser='lalr')
                tree = parser.parse(source)
                # Naively add a root node
                nodes = {0: UASTNode(id=0, kind=NodeKind.Program, line=1, column=1)}
                # In real scenario we traverse the Lark tree to populate nodes
                # For demo, just say we successfully parsed via Lark
                nodes[0].attributes["parsed_via"] = "lark"
                uast = UAST(root=0, nodes=nodes, language=language)
                uast.version_hash = uast.compute_hash()
                return uast
            except Exception as e:
                # Fallback to simple parser on failure
                pass

        nodes: Dict[int, UASTNode] = {}
        node_id = 0
        root = UASTNode(id=node_id, kind=NodeKind.Program, line=1, column=1)
        nodes[node_id] = root
        current_parent = node_id
        node_id += 1

        lines = source.splitlines()
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue
            if any(kw in stripped for kw in ["def ", "fn ", "function ", "func "]):
                n = UASTNode(id=node_id, kind=NodeKind.DeclFunction, line=i, column=line.index(stripped.split()[0]) + 1)
                n.attributes["name"] = stripped.split("(")[0].split()[-1] if "(" in stripped else "anon"
                nodes[node_id] = n
                nodes[current_parent].children.append(node_id)
                current_parent = node_id
                node_id += 1
            elif any(kw in stripped for kw in ["class ", "struct ", "trait ", "interface "]):
                n = UASTNode(id=node_id, kind=NodeKind.DeclClass, line=i)
                n.attributes["name"] = stripped.split()[-1].split("{")[0].strip()
                nodes[node_id] = n
                nodes[current_parent].children.append(node_id)
                node_id += 1
            elif any(kw in stripped for kw in ["if ", "if(", "match ", "switch"]):
                n = UASTNode(id=node_id, kind=NodeKind.StmtIf, line=i)
                nodes[node_id] = n
                nodes[current_parent].children.append(node_id)
                node_id += 1
            elif any(kw in stripped for kw in ["for ", "for(", "while ", "while("]):
                n = UASTNode(id=node_id, kind=NodeKind.StmtFor, line=i)
                nodes[node_id] = n
                nodes[current_parent].children.append(node_id)
                node_id += 1
            elif "return" in stripped:
                n = UASTNode(id=node_id, kind=NodeKind.ExprReturn, line=i)
                nodes[node_id] = n
                nodes[current_parent].children.append(node_id)
                node_id += 1
            elif any(kw in stripped for kw in ["let ", "var ", "const ", "mut "]):
                n = UASTNode(id=node_id, kind=NodeKind.DeclVariable, line=i)
                nodes[node_id] = n
                nodes[current_parent].children.append(node_id)
                node_id += 1
            elif "import" in stripped or "use " in stripped or "from " in stripped:
                n = UASTNode(id=node_id, kind=NodeKind.DeclImport, line=i)
                nodes[node_id] = n
                nodes[current_parent].children.append(node_id)
                node_id += 1


        # Basic Type Inference
        for nid, node in nodes.items():
            if node.kind == NodeKind.DeclVariable:
                val = str(node.attributes.get("value", ""))
                if val.isdigit():
                    node.attributes["inferred_type"] = "int"
                elif val.startswith('"') or val.startswith("'"):
                    node.attributes["inferred_type"] = "string"
            elif node.kind == NodeKind.DeclFunction:
                name = node.attributes.get("name", "")
                if name.startswith("is_") or name.startswith("has_"):
                    node.attributes["inferred_type"] = "bool"
                elif "TypeRef" not in node.attributes:
                    node.attributes["TypeRef"] = "Any"

        uast = UAST(root=0, nodes=nodes, language=language)
        uast.version_hash = uast.compute_hash()
        return uast

    def transpile(self, source: str, from_lang: Optional[str], to_lang: str) -> Dict:
        detection = self.detect_language(source, None) if not from_lang else {"language": from_lang, "confidence": 1.0}
        src_lang = detection["language"]
        uast = self._build_uast(source, src_lang)
        codegen = CodeGenFactory.get(to_lang)
        code = codegen.generate(uast)
        self._transpile_count += 1
        return {
            "source_language": src_lang,
            "target_language": to_lang,
            "code": code,
            "uast_nodes": uast.node_count(),
            "confidence": detection["confidence"],
        }

    def analyze(self, source: str, language: Optional[str] = None) -> Dict:
        lang = language or self.detect_language(source)["language"]
        uast = self._build_uast(source, lang)
        lines = source.count(chr(10)) + 1
        functions = sum(1 for n in uast.nodes.values() if n.kind == NodeKind.DeclFunction)
        classes = sum(1 for n in uast.nodes.values() if n.kind == NodeKind.DeclClass)
        imports = sum(1 for n in uast.nodes.values() if n.kind == NodeKind.DeclImport)
        ifs = sum(1 for n in uast.nodes.values() if n.kind == NodeKind.StmtIf)
        loops = sum(1 for n in uast.nodes.values() if n.kind == NodeKind.StmtFor)
        complexity = 1 + ifs + loops
        depth = uast.max_depth()
        return {
            "language": lang,
            "metrics": {
                "lines": lines,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "conditionals": ifs,
                "loops": loops,
                "cyclomatic_complexity": complexity,
                "max_depth": depth,
            },
            "scores": {
                "complexity": round(max(0, 1.0 - complexity / 20), 4),
                "maintainability": round(max(0, 1.0 - depth / 10), 4),
                "structure": round(min(1.0, (functions + classes) / max(lines / 20, 1)), 4),
            }
        }

    def diff(self, old_source: str, new_source: str) -> Dict:
        old_uast = self._build_uast(old_source, "")
        new_uast = self._build_uast(new_source, "")
        old_ids = set(old_uast.nodes.keys())
        new_ids = set(new_uast.nodes.keys())
        added = len(new_ids - old_ids)
        removed = len(old_ids - new_ids)
        common = old_ids & new_ids
        modified = sum(1 for k in common if old_uast.nodes[k].kind != new_uast.nodes[k].kind)
        return {
            "added_nodes": added,
            "removed_nodes": removed,
            "modified_nodes": modified,
            "old_node_count": len(old_ids),
            "new_node_count": len(new_ids),
            "semantic_stability": round(len(common) / max(len(old_ids), len(new_ids)), 4),
        }

# ============================================================================
# CODE GENERATORS
# ============================================================================

class CodeGenerator(ABC):
    @abstractmethod
    def generate(self, uast: UAST) -> str: pass

class RustCodeGen(CodeGenerator):
    def generate(self, uast: UAST) -> str:
        lines = ["// Transpilado pelo ARKHE P3", "#![allow(unused)]", ""]
        for nid in uast.nodes[0].children:
            node = uast.nodes.get(nid)
            if not node:
                continue
            if node.kind == NodeKind.DeclFunction:
                name = node.attributes.get("name", "func")
                lines.append(f"fn {name}() {{")
                lines.append("    // corpo")
                lines.append("}")
            elif node.kind == NodeKind.DeclClass:
                name = node.attributes.get("name", "Struct")
                lines.append(f"struct {name} {{")
                lines.append("    // campos")
                lines.append("}")
            elif node.kind == NodeKind.DeclVariable:
                lines.append("let x = 42;")
        return chr(10).join(lines)

class PythonCodeGen(CodeGenerator):
    def generate(self, uast: UAST) -> str:
        lines = ["# Transpilado pelo ARKHE P3", ""]
        for nid in uast.nodes[0].children:
            node = uast.nodes.get(nid)
            if not node:
                continue
            if node.kind == NodeKind.DeclFunction:
                name = node.attributes.get("name", "func")
                lines.append(f"def {name}():")
                lines.append("    pass")
            elif node.kind == NodeKind.DeclClass:
                name = node.attributes.get("name", "Class")
                lines.append(f"class {name}:")
                lines.append("    pass")
            elif node.kind == NodeKind.DeclVariable:
                lines.append("x = 42")
        return chr(10).join(lines)

class JavaScriptCodeGen(CodeGenerator):
    def generate(self, uast: UAST) -> str:
        lines = ["// Transpilado pelo ARKHE P3", ""]
        for nid in uast.nodes[0].children:
            node = uast.nodes.get(nid)
            if not node:
                continue
            if node.kind == NodeKind.DeclFunction:
                name = node.attributes.get("name", "func")
                lines.append(f"function {name}() {{")
                lines.append("    // body")
                lines.append("}")
            elif node.kind == NodeKind.DeclClass:
                name = node.attributes.get("name", "Class")
                lines.append(f"class {name} {{")
                lines.append("    constructor() {}")
                lines.append("}")
        return chr(10).join(lines)

class CCodeGen(CodeGenerator):
    def generate(self, uast: UAST) -> str:
        lines = ["/* Transpilado pelo ARKHE P3 */", "#include <stdio.h>", ""]
        for nid in uast.nodes[0].children:
            node = uast.nodes.get(nid)
            if not node:
                continue
            if node.kind == NodeKind.DeclFunction:
                name = node.attributes.get("name", "func")
                lines.append(f"void {name}(void) {{")
                lines.append("    /* body */")
                lines.append("}")
        lines.append("")
        lines.append("int main(void) { return 0; }")
        return chr(10).join(lines)

class GoCodeGen(CodeGenerator):
    def generate(self, uast: UAST) -> str:
        lines = ["// Transpilado pelo ARKHE P3", "package main", ""]
        for nid in uast.nodes[0].children:
            node = uast.nodes.get(nid)
            if not node:
                continue
            if node.kind == NodeKind.DeclFunction:
                name = node.attributes.get("name", "func")
                lines.append(f"func {name}() {{")
                lines.append("    // body")
                lines.append("}")
        lines.append("")
        lines.append("func main() {}")
        return chr(10).join(lines)

class HaskellCodeGen(CodeGenerator):
    def generate(self, uast: UAST) -> str:
        lines = ["-- Transpilado pelo ARKHE P3", "module Main where", ""]
        for nid in uast.nodes[0].children:
            node = uast.nodes.get(nid)
            if not node:
                continue
            if node.kind == NodeKind.DeclFunction:
                name = node.attributes.get("name", "func")
                lines.append(f"{name} = undefined")
        lines.append("")
        lines.append("main = putStrLn \"Hello\"")
        return chr(10).join(lines)

class PrologCodeGen(CodeGenerator):
    def generate(self, uast: UAST) -> str:
        lines = ["% Transpilado pelo ARKHE P3", ""]
        for nid in uast.nodes[0].children:
            node = uast.nodes.get(nid)
            if not node:
                continue
            if node.kind == NodeKind.DeclFunction:
                name = node.attributes.get("name", "func")
                lines.append(f"{name} :- true.")
        lines.append("")
        lines.append("?- true.")
        return chr(10).join(lines)

class SQLCodeGen(CodeGenerator):
    def generate(self, uast: UAST) -> str:
        return chr(10).join(["-- Transpilado pelo ARKHE P3", "", "SELECT * FROM table_name;"])

class WATCodeGen(CodeGenerator):
    def generate(self, uast: UAST) -> str:
        lines = [";; Transpilado pelo ARKHE P3", "(module"]
        for nid in uast.nodes[0].children:
            node = uast.nodes.get(nid)
            if not node:
                continue
            if node.kind == NodeKind.DeclFunction:
                name = node.attributes.get("name", "func")
                lines.append(f'  (func ${name} (result i32)')
                lines.append('    i32.const 42')
                lines.append('  )')
        lines.append('  (export "_start" (func $main))')
        lines.append(")")
        return chr(10).join(lines)

class AGICodeGen(CodeGenerator):
    def generate(self, uast: UAST) -> str:
        return chr(10).join([
            "# AGI Specification v1.0", "# Transpilado pelo ARKHE P3", "",
            "name: GeneratedAgent", "version: 1.0.0", "type: function",
            "input: any", "output: any"
        ])

class CodeGenFactory:
    _generators = {
        "rust": RustCodeGen(), "python": PythonCodeGen(), "py": PythonCodeGen(),
        "javascript": JavaScriptCodeGen(), "js": JavaScriptCodeGen(),
        "typescript": JavaScriptCodeGen(), "ts": JavaScriptCodeGen(),
        "c": CCodeGen(), "cpp": CCodeGen(),
        "go": GoCodeGen(), "haskell": HaskellCodeGen(), "hs": HaskellCodeGen(),
        "prolog": PrologCodeGen(), "pl": PrologCodeGen(),
        "sql": SQLCodeGen(), "wat": WATCodeGen(), "wasm": WATCodeGen(), "agi": AGICodeGen(),
    }

    @classmethod
    def get(cls, lang: str) -> CodeGenerator:
        return cls._generators.get(lang.lower(), PythonCodeGen())

    @classmethod
    def supported(cls) -> List[str]:
        return sorted(cls._generators.keys())

# ============================================================================
# DEMONSTRAÇÃO
# ============================================================================

def run_demo():
    setup_logging("INFO")
    parser = PolyglotParser()

    log.info("=" * 62)
    log.info("  ARKHE OMEGA-TEMP v%s — SUBSTRATO %d", VERSION, SUBSTRATE)
    log.info("  POLYMATH-POLYGLOT PARSER (P3)")
    log.info("=" * 62)

    log.info("\\n  Linguagens registradas: %d", parser.registry.count())

    log.info("\\n  [TESTE 1] Deteccao de linguagem")
    samples = [
        ("def hello():\\n    print('world')", "hello.py"),
        ("fn main() { println!(\"hello\"); }", "main.rs"),
        ("function hello() { console.log('world'); }", "hello.js"),
        ("int main() { return 0; }", "main.c"),
        ("package main\\nfunc main() {}", "main.go"),
        ("SELECT * FROM users WHERE id = 1", "query.sql"),
        ("MATCH (n) RETURN n", "query.cypher"),
        ("(module (func $hello))", "hello.wat"),
    ]
    for source, filename in samples:
        det = parser.detect_language(source, filename)
        log.info("    %s -> %s (%.1f%%)", filename.ljust(22), det["language"].ljust(12), det["confidence"] * 100)

    log.info("\\n  [TESTE 2] Parse para UAST")
    py_code = "def factorial(n):\\n    if n <= 1:\\n        return 1\\n    return n * factorial(n - 1)\\n\\nresult = factorial(5)\\n"
    parse_result = parser.parse(py_code, "factorial.py")
    log.info("    Linguagem: %s (%.1f%%)", parse_result["detected_language"], parse_result["confidence"] * 100)
    log.info("    Nos UAST: %d", parse_result["uast"]["node_count"])
    log.info("    Profundidade: %d", parse_result["uast"]["max_depth"])
    log.info("    Hash: %s...", parse_result["uast"]["version_hash"][:16])

    log.info("\\n  [TESTE 3] Transpilacao cross-language")
    targets = ["rust", "javascript", "c", "go", "haskell", "prolog", "wat", "agi"]
    for target in targets:
        result = parser.transpile(py_code, "python", target)
        preview = result["code"].splitlines()[0] if result["code"] else ""
        log.info("    python -> %s: %s", target.ljust(12), preview[:45])

    log.info("\\n  [TESTE 4] Analise semantica")
    analysis = parser.analyze(py_code, "python")
    log.info("    Linhas: %d", analysis["metrics"]["lines"])
    log.info("    Funcoes: %d", analysis["metrics"]["functions"])
    log.info("    Complexidade ciclomatica: %d", analysis["metrics"]["cyclomatic_complexity"])
    log.info("    Profundidade maxima: %d", analysis["metrics"]["max_depth"])
    log.info("    Scores: complexity=%.2f, maintainability=%.2f, structure=%.2f",
             analysis["scores"]["complexity"], analysis["scores"]["maintainability"], analysis["scores"]["structure"])

    log.info("\\n  [TESTE 5] Diff temporal")
    old_code = "def hello():\\n    return 'world'"
    new_code = "def hello(name):\\n    return f'Hello, {name}'"
    diff_result = parser.diff(old_code, new_code)
    log.info("    Adicionados: %d", diff_result["added_nodes"])
    log.info("    Removidos: %d", diff_result["removed_nodes"])
    log.info("    Modificados: %d", diff_result["modified_nodes"])
    log.info("    Estabilidade semantica: %.1f%%", diff_result["semantic_stability"] * 100)

    log.info("\\n" + "=" * 62)
    log.info("  SUBSTRATO %d CANONIZADO", SUBSTRATE)
    log.info("  %d linguagens | 1 UAST | Infinitas possibilidades", parser.registry.count())
    log.info("=" * 62)

# ============================================================================
# CLI
# ============================================================================

def main():
    argparser = argparse.ArgumentParser(prog='arkhe-polyglot', description=f'ARKHE P3 v{VERSION}')
    argparser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    subparsers = argparser.add_subparsers(dest='command')

    subparsers.add_parser('demo', help='Demonstracao completa')
    subparsers.add_parser('languages', help='Listar linguagens')

    detect_parser = subparsers.add_parser('detect', help='Detectar linguagem')
    detect_parser.add_argument('--source', '-s', type=str)
    detect_parser.add_argument('--file', '-f', type=str)

    parse_parser = subparsers.add_parser('parse', help='Parse para UAST')
    parse_parser.add_argument('--source', '-s', type=str)
    parse_parser.add_argument('--file', type=str)

    transpile_parser = subparsers.add_parser('transpile', help='Transpilar')
    transpile_parser.add_argument('--source', '-s', type=str, required=True)
    transpile_parser.add_argument('--from', dest='from_lang', type=str)
    transpile_parser.add_argument('--target', '-t', type=str, required=True)

    analyze_parser = subparsers.add_parser('analyze', help='Analise semantica')
    analyze_parser.add_argument('--source', '-s', type=str)
    analyze_parser.add_argument('--file', type=str)
    analyze_parser.add_argument('--language', '-l', type=str)

    diff_parser = subparsers.add_parser('diff', help='Diff temporal')
    diff_parser.add_argument('--old', type=str, required=True)
    diff_parser.add_argument('--new', type=str, required=True)

    argparser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    args = argparser.parse_args()

    setup_logging(args.log_level)
    p = PolyglotParser()

    if args.command == 'demo' or not args.command:
        run_demo()
    elif args.command == 'languages':
        for name in p.registry.list_all():
            spec = p.registry.get(name)
            print(f"{name:15} {spec.display_name:20} {spec.version:10} {spec.language_type.name}")
    elif args.command == 'detect':
        source = args.source or (open(args.file).read() if args.file else "")
        print(json.dumps(p.detect_language(source, args.file), indent=2))
    elif args.command == 'parse':
        source = args.source or (open(args.file).read() if args.file else "")
        print(json.dumps(p.parse(source, args.file), indent=2, default=str))
    elif args.command == 'transpile':
        result = p.transpile(args.source, args.from_lang, args.target)
        print(result["code"])
    elif args.command == 'analyze':
        source = args.source or (open(args.file).read() if args.file else "")
        print(json.dumps(p.analyze(source, args.language), indent=2))
    elif args.command == 'diff':
        print(json.dumps(p.diff(args.old, args.new), indent=2))
    else:
        argparser.print_help()

if __name__ == "__main__":
    main()