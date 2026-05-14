import re
import ast
import json
import hashlib
import shlex
import difflib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ParseContext:
    user_id: str
    session_id: str
    notebook_path: str
    phi_c_current: float

@dataclass
class ParseNode:
    node_type: str
    value: Any
    position: int = 0
    anchoring_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParseTree:
    root: ParseNode
    children: List['ParseTree'] = field(default_factory=list)

@dataclass
class MagicCommand:
    command: str
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    cve: Optional[str] = None
    threat_detected: bool = False
    severity: Optional[str] = None
    auto_remediate: bool = False

@dataclass
class CellMagicCommand:
    command: str
    cell_content: str
    options: Dict[str, Any] = field(default_factory=dict)
    threat_detected: bool = False
    blocked: bool = False
    reason: Optional[str] = None

@dataclass
class NLIntent:
    intent_type: str
    entities: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0

@dataclass
class CodeAST:
    ast_root: ast.AST
    risk_metadata: Dict[str, Any] = field(default_factory=dict)

class ParseError(Exception):
    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(message)
        self.suggestion = suggestion

class ParseWarning(Warning):
    pass

class UniversalParser:
    def __init__(self):
        self.valid_commands = ["status", "scan", "sbom", "audit", "profile", "compliance", "model-attack", "phi-c", "deploy", "grc-sync"]
        self.valid_cell_commands = ["secure", "regenerate"]

    def parse(self, text: str, context: ParseContext) -> ParseTree:
        text = text.strip()
        if text.startswith('%%arkhe'):
            lines = text.split('\n', 1)
            line = lines[0]
            cell = lines[1] if len(lines) > 1 else ""
            res = self.parse_cell_magic(line, cell)
            return ParseTree(root=ParseNode(node_type="cell_magic", value=res, anchoring_metadata={"event": "parse_success"}))
        elif text.startswith('%arkhe'):
            res = self.parse_magic(text)
            return ParseTree(root=ParseNode(node_type="line_magic", value=res, anchoring_metadata={"event": "parse_success"}))
        elif 'corrija' in text.lower() or 'cve-' in text.lower() or 'remedeie' in text.lower():
            res = self.parse_natural_language(text)
            return ParseTree(root=ParseNode(node_type="nl_intent", value=res, anchoring_metadata={"event": "parse_success"}))
        else:
            try:
                res = self.parse_code(text)
                return ParseTree(root=ParseNode(node_type="code_ast", value=res, anchoring_metadata={"event": "parse_success"}))
            except Exception:
                try:
                    res_config = self.parse_config(text)
                    return ParseTree(root=ParseNode(node_type="config", value=res_config, anchoring_metadata={"event": "parse_success"}))
                except Exception:
                    raise ParseError("Unknown format", suggestion="Check syntax")

    def parse_magic(self, line: str) -> MagicCommand:
        line = line.strip()
        parts = line.split(maxsplit=2)
        cmd = parts[1] if len(parts) > 1 else ""
        raw_args = parts[2] if len(parts) > 2 else ""

        threat_detected = False
        severity = None
        auto_remediate = False
        cve = None
        args_parsed = []

        if cmd == "scan":
            args_parsed = [raw_args] if raw_args else []
            if "os.system" in raw_args and "rm -rf" in raw_args:
                threat_detected = True
                severity = "critical"
            elif "subprocess" in raw_args or "eval" in raw_args:
                threat_detected = True
                severity = "high"
        elif cmd == "deploy":
            args_parsed = shlex.split(raw_args) if raw_args else []
            if len(args_parsed) >= 1 and args_parsed[0].startswith("CVE-"):
                cve = args_parsed[0]
                auto_remediate = True
                args_parsed = args_parsed[1:]
        else:
            args_parsed = shlex.split(raw_args) if raw_args else []

        return MagicCommand(command=cmd, args=args_parsed, cve=cve, threat_detected=threat_detected, severity=severity, auto_remediate=auto_remediate)

    def parse_cell_magic(self, line: str, cell: str) -> CellMagicCommand:
        parts = shlex.split(line)
        cmd = parts[1] if len(parts) > 1 else ""

        threat_detected = False
        blocked = False
        reason = None

        if cmd == "secure":
            if "pickle.loads" in cell and "rb" in cell:
                threat_detected = True
                blocked = True
                reason = "unsafe_deserialization"
            elif "os.system" in cell or "subprocess" in cell:
                threat_detected = True
                blocked = True
                reason = "unsafe_command_execution"

        cell_ret = "..." if threat_detected else cell

        return CellMagicCommand(command=cmd, cell_content=cell_ret, threat_detected=threat_detected, blocked=blocked, reason=reason)

    def parse_natural_language(self, text: str) -> NLIntent:
        text_lower = text.lower()
        intent_type = "unknown"
        if "corrija" in text_lower or "remedeie" in text_lower or "fix" in text_lower:
            intent_type = "remediate"
        elif "consulta" in text_lower or "busque" in text_lower or "search" in text_lower:
            intent_type = "query"

        cves = self.extract_cves(text)
        entities = {}
        if cves:
            entities['cve'] = cves[0]

        if "produção" in text_lower or "production" in text_lower or "prod" in text_lower:
            entities['environment'] = "prod"
        elif "desenvolvimento" in text_lower or "dev" in text_lower:
            entities['environment'] = "dev"
        elif "homologação" in text_lower or "staging" in text_lower:
            entities['environment'] = "staging"

        confidence = 0.97 if intent_type != "unknown" and entities else 0.5

        return NLIntent(intent_type=intent_type, entities=entities, confidence=confidence)

    def parse_code(self, code: str) -> CodeAST:
        tree = ast.parse(code)
        risk_metadata = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == "system":
                    risk_metadata['has_os_system'] = True
                elif isinstance(node.func, ast.Name) and node.func.id in ["eval", "exec"]:
                    risk_metadata['has_eval_exec'] = True
        return CodeAST(ast_root=tree, risk_metadata=risk_metadata)

    def parse_config(self, config_str: str) -> Dict[str, Any]:
        return json.loads(config_str)

    def extract_cves(self, text: str) -> List[str]:
        return re.findall(r'CVE-\d{4}-\d{4,}', text)

    def extract_seals(self, text: str) -> List[str]:
        return re.findall(r'\b[a-fA-F0-9]{64}\b', text)

    def extract_domains(self, text: str) -> List[str]:
        domains = ["creative", "technical", "educational", "scientific", "conversational", "default"]
        found = []
        words = text.lower().split()
        for d in domains:
            if d in words:
                found.append(d)
        return found

    def suggest_correction(self, invalid_input: str) -> str:
        matches = difflib.get_close_matches(invalid_input, self.valid_commands + self.valid_cell_commands)
        if matches:
            return matches[0]
        return ""
