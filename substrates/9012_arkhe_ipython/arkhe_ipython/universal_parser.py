#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
universal_parser.py — Substrato 9012: Universal Parser para Arkhe-IPython
Motor de parsing universal que interpreta comandos naturais, magics, código e metadados,
convertendo-os em chamadas tipadas ao Safe Core com ancoragem temporal e correção de erros.
"""

import re
import ast
import json
import hashlib
import shlex
import difflib
import time
import asyncio
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Union, Any, Tuple, TypeVar, Generic
from enum import Enum, auto
from pathlib import Path

# ============================================================================
# TIPOS BASE DO PARSER
# ============================================================================

T = TypeVar('T')

@dataclass
class ParseContext:
    """Contexto de parsing para manter estado entre chamadas."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    notebook_path: Optional[str] = None
    phi_c_current: float = 0.997
    active_profile: str = "default"
    compliance_scope: str = "full"
    history: List[str] = field(default_factory=list)

    def add_to_history(self, command: str):
        """Adiciona comando ao histórico para sugestões contextuais."""
        self.history.append(command)
        if len(self.history) > 100:  # Limitar histórico
            self.history.pop(0)

@dataclass
class ParseNode(Generic[T]):
    """Nó da árvore de parsing com tipo, valor e metadados."""
    node_type: str
    value: T
    position: Tuple[int, int]  # (start, end) no texto original
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List['ParseNode'] = field(default_factory=list)
    temporal_anchor: Optional[str] = None

    def to_dict(self) -> Dict:
        """Serializa nó para dicionário."""
        value_serialized = self.value

        # Serialize specific objects to dictionaries so it's serializable by MCP tools
        if hasattr(self.value, 'to_call_dict'):
            value_serialized = self.value.to_call_dict()
        elif hasattr(self.value, 'to_magic_command') and callable(getattr(self.value, 'to_magic_command')):
            # It's an NLIntent
            magic_cmd = self.value.to_magic_command()
            value_serialized = magic_cmd.to_call_dict() if magic_cmd else {"intent": self.value.intent_type}
        elif self.node_type == 'code_ast' and hasattr(self.value, 'source_code'):
            value_serialized = {"source_code": self.value.source_code, "risks": self.value.risk_patterns}

        return {
            "type": self.node_type,
            "value": value_serialized,
            "position": self.position,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "children": [c.to_dict() for c in self.children],
            "temporal_anchor": self.temporal_anchor,
        }

@dataclass
class ParseTree:
    """Árvore de parsing com raiz e métodos de navegação."""
    root: ParseNode
    source_text: str
    parse_time_ms: float
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def find_nodes(self, node_type: str) -> List[ParseNode]:
        """Encontra todos os nós de um tipo específico."""
        results = []
        def _search(node: ParseNode):
            if node.node_type == node_type:
                results.append(node)
            for child in node.children:
                _search(child)
        _search(self.root)
        return results

    def get_first(self, node_type: str) -> Optional[ParseNode]:
        """Retorna o primeiro nó de um tipo."""
        nodes = self.find_nodes(node_type)
        return nodes[0] if nodes else None

    def to_dict(self) -> Dict:
        """Serializa árvore completa."""
        return {
            "root": self.root.to_dict(),
            "source_text": self.source_text,
            "parse_time_ms": self.parse_time_ms,
            "warnings": self.warnings,
            "errors": self.errors,
        }

@dataclass
class MagicCommand:
    """Comando mágico de linha %arkhe parseado."""
    command: str
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    threat_detected: bool = False
    severity: Optional[str] = None
    extracted_entities: Dict[str, Any] = field(default_factory=dict)

    def to_call_dict(self) -> Dict:
        """Converte para dicionário de chamada do Safe Core."""
        return {
            "tool": self.command,
            "arguments": {**self.kwargs, "args": self.args},
            "metadata": {
                "threat_detected": self.threat_detected,
                "severity": self.severity,
                **self.extracted_entities,
            }
        }

@dataclass
class CellMagicCommand:
    """Comando mágico de célula %%arkhe parseado."""
    command: str
    cell_content: str
    options: Dict[str, Any] = field(default_factory=dict)
    threat_detected: bool = False
    blocked: bool = False
    block_reason: Optional[str] = None
    code_ast: Optional[ast.AST] = None

    def to_call_dict(self) -> Dict:
        """Converte para dicionário de chamada do Safe Core."""
        return {
            "tool": self.command,
            "arguments": {
                "code": self.cell_content,
                **self.options,
            },
            "metadata": {
                "threat_detected": self.threat_detected,
                "blocked": self.blocked,
                "block_reason": self.block_reason,
            }
        }

@dataclass
class NLIntent:
    """Intenção extraída de linguagem natural."""
    intent_type: str  # 'remediate', 'scan', 'query', 'deploy', etc.
    entities: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    suggested_command: Optional[str] = None
    suggested_args: List[str] = field(default_factory=list)

    def to_magic_command(self) -> Optional[MagicCommand]:
        """Converte intenção NL para MagicCommand se possível."""
        if not self.suggested_command:
            return None
        return MagicCommand(
            command=self.suggested_command,
            args=self.suggested_args,
            kwargs=self.entities,
            extracted_entities=self.entities,
        )

@dataclass
class CodeAST:
    """AST de código fonte com metadados de risco."""
    ast_tree: ast.AST
    source_code: str
    risk_patterns: List[Dict] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    function_defs: List[str] = field(default_factory=list)
    class_defs: List[str] = field(default_factory=list)
    suspicious_calls: List[str] = field(default_factory=list)

    # Padrões de risco conhecidos
    RISK_PATTERNS = {
        'unsafe_deserialization': ['pickle.loads', 'yaml.load(.*, Loader=.*Unsafe.*)'],
        'code_execution': ['eval\\(', 'exec\\(', 'compile\\(', '__import__\\('],
        'file_operations': ['open\\(.*, [\'"]w[+]*[\'"]\\)', 'os.system\\(', 'subprocess\\.'],
        'network_access': ['requests\\.', 'urllib\\.', 'socket\\.'],
        'crypto_weak': ['md5\\(', 'sha1\\(', 'DES', 'ECB'],
    }

    def analyze_risks(self) -> List[Dict]:
        """Analisa código em busca de padrões de risco."""
        risks = []
        code_str = ast.unparse(self.ast_tree) if hasattr(ast, 'unparse') else self.source_code

        for risk_type, patterns in self.RISK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, code_str, re.IGNORECASE):
                    risks.append({
                        "type": risk_type,
                        "pattern": pattern,
                        "severity": self._get_severity(risk_type),
                        "line": self._find_line(code_str, pattern),
                    })
        return risks

    def _get_severity(self, risk_type: str) -> str:
        """Mapeia tipo de risco para severidade."""
        severity_map = {
            'code_execution': 'critical',
            'unsafe_deserialization': 'critical',
            'file_operations': 'high',
            'network_access': 'medium',
            'crypto_weak': 'medium',
        }
        return severity_map.get(risk_type, 'low')

    def _find_line(self, code: str, pattern: str) -> Optional[int]:
        """Encontra número da linha onde o padrão ocorre."""
        match = re.search(pattern, code, re.IGNORECASE)
        if match:
            return code[:match.start()].count('\n') + 1
        return None

@dataclass
class ParseError(Exception):
    """Erro de parsing com sugestão de correção."""
    message: str
    position: Optional[Tuple[int, int]] = None
    suggestion: Optional[str] = None
    error_type: str = "parse_error"

    def __str__(self):
        base = f"ParseError: {self.message}"
        if self.position:
            base += f" at position {self.position}"
        if self.suggestion:
            base += f"\n💡 Sugestão: {self.suggestion}"
        return base

@dataclass
class ParseWarning:
    """Aviso de parsing não crítico."""
    message: str
    position: Optional[Tuple[int, int]] = None
    warning_type: str = "parse_warning"

    def __str__(self):
        base = f"ParseWarning: {self.message}"
        if self.position:
            base += f" at position {self.position}"
        return base

# ============================================================================
# SUBPARSERS ESPECIALIZADOS
# ============================================================================

class MagicLineParser:
    """Parser para comandos de linha %arkhe."""

    VALID_COMMANDS = [
        'status', 'scan', 'sbom', 'audit', 'profile',
        'compliance', 'model-attack', 'phi-c', 'deploy', 'grc-sync'
    ]

    COMMAND_ARGS = {
        'scan': {'required': ['code'], 'optional': ['language', 'artifact_hash']},
        'sbom': {'required': [], 'optional': ['release_id', 'format', 'include_dev_deps']},
        'audit': {'required': ['seal'], 'optional': []},
        'profile': {'required': [], 'optional': ['domain']},
        'compliance': {'required': [], 'optional': ['scope', 'release_id']},
        'model-attack': {'required': ['service_map'], 'optional': ['threat_context']},
        'phi-c': {'required': [], 'optional': ['time_range', 'node_id']},
        'deploy': {'required': ['vulnerability_id', 'patched_release'], 'optional': ['strategy', 'environments']},
        'grc-sync': {'required': ['cve_id'], 'optional': ['platforms']},
        'status': {'required': [], 'optional': []},
    }

    def parse(self, line: str) -> MagicCommand:
        """Parseia comando de linha %arkhe."""
        # Remover prefixo %arkhe se presente
        line = line.strip()
        if line.startswith('%arkhe'):
            line = line[6:].strip()

        # Dividir em partes
        try:
            parts = shlex.split(line)
        except ValueError as e:
            raise ParseError(f"Erro ao parsear argumentos: {e}", suggestion="Verifique aspas e escapes")

        if not parts:
            raise ParseError("Comando vazio", suggestion="Use %arkhe --help para ver comandos disponíveis")

        command = parts[0].lower()

        # Validar comando
        if command not in self.VALID_COMMANDS:
            suggestion = self._suggest_correction(command, self.VALID_COMMANDS)
            raise ParseError(
                f"Comando desconhecido: '{command}'",
                suggestion=suggestion
            )

        # Parsear argumentos
        args, kwargs = self._parse_command_args(command, parts[1:])

        # Extrair entidades adicionais
        entities = self._extract_entities(command, args, kwargs)

        # Verificar ameaças em argumentos de código
        threat_detected, severity = self._check_code_threats(command, args, kwargs)

        return MagicCommand(
            command=command,
            args=args,
            kwargs=kwargs,
            threat_detected=threat_detected,
            severity=severity,
            extracted_entities=entities,
        )

    def _parse_command_args(self, command: str, parts: List[str]) -> Tuple[List[str], Dict[str, Any]]:
        """Parseia argumentos posicionais e nomeados."""
        args = []
        kwargs = {}

        expected = self.COMMAND_ARGS.get(command, {'required': [], 'optional': []})

        i = 0
        while i < len(parts):
            part = parts[i]

            # Verificar se é argumento nomeado (--key=value ou --key value)
            if part.startswith('--'):
                key = part[2:]  # Remover --
                if '=' in key:
                    # Formato --key=value
                    k, v = key.split('=', 1)
                    kwargs[k] = self._parse_value(v)
                elif i + 1 < len(parts) and not parts[i + 1].startswith('--'):
                    # Formato --key value
                    kwargs[key] = self._parse_value(parts[i + 1])
                    i += 1
                else:
                    kwargs[key] = True  # Flag booleana
            else:
                # Argumento posicional
                args.append(part)

            i += 1

        return args, kwargs

    def _parse_value(self, value: str) -> Any:
        """Parseia valor de argumento para tipo apropriado."""
        # Tentar JSON primeiro (para dicts, lists)
        if value.startswith(('{', '[')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # Tentar boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # Tentar número
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Retornar como string
        return value

    def _extract_entities(self, command: str, args: List[str], kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai entidades relevantes dos argumentos."""
        entities = {}

        # Extrair CVEs
        cve_extractor = CVEExtractor()
        all_text = ' '.join(args) + ' ' + ' '.join(str(v) for v in kwargs.values())
        cves = cve_extractor.extract(all_text)
        if cves:
            entities['cves'] = cves

        # Extrair selos temporais
        seal_extractor = SealExtractor()
        seals = seal_extractor.extract(all_text)
        if seals:
            entities['seals'] = seals

        # Extrair domínios
        domain_parser = DomainParser()
        domains = domain_parser.extract(all_text)
        if domains:
            entities['domains'] = domains

        return entities

    def _check_code_threats(self, command: str, args: List[str], kwargs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Verifica se argumentos contêm código com ameaças."""
        if command != 'scan':
            return False, None

        # Obter código para análise
        code = None
        if args:
            code = args[0]
        elif 'code' in kwargs:
            code = kwargs['code']

        if not code:
            return False, None

        # Analisar com CodeParser
        code_parser = CodeParser()
        try:
            code_ast = code_parser.parse(code)
            risks = code_ast.analyze_risks()
            if risks:
                # Retornar severidade mais alta
                severities = [r['severity'] for r in risks]
                severity_order = ['critical', 'high', 'medium', 'low', 'info']
                for sev in severity_order:
                    if sev in severities:
                        return True, sev
        except Exception:
            pass

        return False, None

    def _suggest_correction(self, invalid: str, valid_options: List[str]) -> str:
        """Sugere correção para comando inválido."""
        matches = difflib.get_close_matches(invalid, valid_options, n=1, cutoff=0.6)
        if matches:
            return f"Did you mean '%arkhe {matches[0]}'?"
        return f"Comandos válidos: {', '.join(valid_options)}"


class MagicCellParser:
    """Parser para comandos de célula %%arkhe."""

    VALID_CELL_COMMANDS = ['secure', 'regenerate']

    def parse(self, line: str, cell: str) -> CellMagicCommand:
        """Parseia comando de célula %%arkhe."""
        # Remover prefixo %%arkhe se presente
        line = line.strip()
        if line.startswith('%%arkhe'):
            line = line[7:].strip()

        # Dividir comando e opções
        parts = line.split(None, 1)
        command = parts[0].lower() if parts else ''
        options_str = parts[1] if len(parts) > 1 else ''

        # Validar comando
        if command not in self.VALID_CELL_COMMANDS:
            suggestion = self._suggest_correction(command, self.VALID_CELL_COMMANDS)
            raise ParseError(
                f"Comando de célula desconhecido: '{command}'",
                suggestion=suggestion
            )

        # Parsear opções
        options = self._parse_options(options_str)

        # Analisar código da célula
        code_parser = CodeParser()
        try:
            code_ast = code_parser.parse(cell)
            risks = code_ast.analyze_risks()
        except Exception as e:
            code_ast = None
            risks = [{"type": "parse_error", "message": str(e), "severity": "high"}]

        # Determinar se deve bloquear
        blocked = False
        block_reason = None
        if command == 'secure' and risks:
            critical_risks = [r for r in risks if r.get('severity') == 'critical']
            if critical_risks:
                blocked = True
                block_reason = f"Riscos críticos detectados: {', '.join(r['type'] for r in critical_risks)}"

        return CellMagicCommand(
            command=command,
            cell_content=cell,
            options=options,
            threat_detected=bool(risks),
            blocked=blocked,
            block_reason=block_reason,
            code_ast=code_ast,
        )

    def _parse_options(self, options_str: str) -> Dict[str, Any]:
        """Parseia opções da linha de comando de célula."""
        options = {}
        if not options_str:
            return options

        # Suporte para --flag e --key=value
        parts = shlex.split(options_str)
        i = 0
        while i < len(parts):
            part = parts[i]
            if part.startswith('--'):
                key = part[2:]
                if '=' in key:
                    k, v = key.split('=', 1)
                    options[k] = self._parse_value(v)
                elif i + 1 < len(parts) and not parts[i + 1].startswith('--'):
                    options[key] = self._parse_value(parts[i + 1])
                    i += 1
                else:
                    options[key] = True
            i += 1

        return options

    def _parse_value(self, value: str) -> Any:
        """Parseia valor para tipo apropriado."""
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    def _suggest_correction(self, invalid: str, valid: List[str]) -> str:
        """Sugere correção para comando inválido."""
        matches = difflib.get_close_matches(invalid, valid, n=1, cutoff=0.6)
        if matches:
            return f"Did you mean '%%arkhe {matches[0]}'?"
        return f"Comandos válidos: {', '.join(valid)}"


class NaturalLanguageParser:
    """Parser de linguagem natural para comandos do Safe Core."""

    # Padrões de intenção
    INTENT_PATTERNS = {
        'remediate': [
            r'(?i)(fix|corrigir|patch|remediate|resolve).*(cve-\d{4}-\d{4,})',
            r'(?i)(cve-\d{4}-\d{4,}).*(fix|corrigir|patch|remediate)',
        ],
        'scan': [
            r'(?i)(scan|analyze|verificar|escanear).*(code|código|vulnerability)',
            r'(?i)(check|checar|verify).*(security|segurança)',
        ],
        'query': [
            r'(?i)(show|mostrar|query|consultar).*(audit|log|seal|registro)',
            r'(?i)(what|qual|status).*(compliance|conformidade)',
        ],
        'deploy': [
            r'(?i)(deploy|deployar|install|instalar).*(patch|fix|update)',
            r'(?i)(apply|aplicar).*(cve-\d{4}-\d{4,}).*(prod|production)',
        ],
        'profile': [
            r'(?i)(change|mudar|set|definir).*(profile|perfil|mode|modo)',
            r'(?i)(switch|alternar).*(creative|technical|educational)',
        ],
    }

    # Entidades extraíveis
    ENTITY_PATTERNS = {
        'cve': r'CVE-\d{4}-\d{4,}',
        'seal': r'[a-f0-9]{16,64}',
        'environment': r'\b(prod|production|staging|dev|development|test)\b',
        'domain': r'\b(creative|technical|educational|scientific|conversational|default)\b',
        'scope': r'\b(full|cvs|apm|inv|aro)\b',
        'severity': r'\b(critical|high|medium|low|info)\b',
    }

    # Mapeamento de intenção para comando mágico
    INTENT_TO_COMMAND = {
        'remediate': 'deploy',
        'scan': 'scan',
        'query': 'audit',
        'deploy': 'deploy',
        'profile': 'profile',
    }

    def parse(self, text: str) -> NLIntent:
        """Parseia texto em linguagem natural para intenção."""
        text = text.strip()

        # Detectar intenção
        intent_type, intent_confidence = self._detect_intent(text)

        if not intent_type:
            return NLIntent(
                intent_type='unknown',
                entities={},
                confidence=0.0,
                suggested_command=None,
            )

        # Extrair entidades
        entities = self._extract_entities(text)

        # Sugerir comando mágico equivalente
        suggested_command = self.INTENT_TO_COMMAND.get(intent_type)
        suggested_args = self._build_suggested_args(intent_type, entities)

        return NLIntent(
            intent_type=intent_type,
            entities=entities,
            confidence=intent_confidence,
            suggested_command=suggested_command,
            suggested_args=suggested_args,
        )

    def _detect_intent(self, text: str) -> Tuple[Optional[str], float]:
        """Detecta intenção principal do texto."""
        best_intent = None
        best_score = 0.0

        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    # Score baseado no comprimento do match e posição
                    score = len(match.group()) / len(text) * 0.5 + 0.5
                    if score > best_score:
                        best_score = score
                        best_intent = intent

        return best_intent, best_score

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extrai entidades nomeadas do texto."""
        entities = {}

        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if entity_type in ['cve', 'seal']:
                    # Valores únicos para identificadores
                    entities[entity_type] = matches[0].upper() if entity_type == 'cve' else matches[0]
                else:
                    # Lista para categorias
                    entities[f'{entity_type}s'] = list(set(m.lower() for m in matches))

        return entities

    def _build_suggested_args(self, intent_type: str, entities: Dict[str, Any]) -> List[str]:
        """Constrói argumentos sugeridos para o comando mágico."""
        args = []

        if intent_type == 'remediate' and 'cve' in entities:
            args.append(entities['cve'])
            if 'environment' in entities:
                args.append(f"--env={entities['environment']}")
        elif intent_type == 'scan' and 'code' in entities:
            args.append(entities['code'])
        elif intent_type == 'query' and 'seal' in entities:
            args.append(entities['seal'])

        return args


class CodeParser:
    """Parser de código fonte Python com análise de risco."""

    def parse(self, code: str) -> CodeAST:
        """Parseia código Python para AST com metadados."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ParseError(
                f"Erro de sintaxe Python: {e}",
                position=(e.lineno, e.offset) if hasattr(e, 'lineno') else None,
                suggestion="Verifique a sintaxe do código Python"
            )

        code_ast = CodeAST(
            ast_tree=tree,
            source_code=code,
        )

        # Extrair metadados
        code_ast.imports = self._extract_imports(tree)
        code_ast.function_defs = self._extract_function_defs(tree)
        code_ast.class_defs = self._extract_class_defs(tree)
        code_ast.suspicious_calls = self._extract_suspicious_calls(tree)
        code_ast.risk_patterns = code_ast.analyze_risks()

        return code_ast

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extrai imports do AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        return imports

    def _extract_function_defs(self, tree: ast.AST) -> List[str]:
        """Extrai definições de funções."""
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

    def _extract_class_defs(self, tree: ast.AST) -> List[str]:
        """Extrai definições de classes."""
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    def _extract_suspicious_calls(self, tree: ast.AST) -> List[str]:
        """Extrai chamadas potencialmente suspeitas."""
        suspicious = []
        suspicious_funcs = ['eval', 'exec', 'compile', '__import__', 'pickle.loads', 'yaml.load']

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                func_name = None
                if isinstance(func, ast.Name):
                    func_name = func.id
                elif isinstance(func, ast.Attribute):
                    func_name = func.attr

                if func_name in suspicious_funcs:
                    suspicious.append(func_name)

        return suspicious


# ============================================================================
# EXTRACTORS ESPECIALIZADOS
# ============================================================================

class CVEExtractor:
    """Extrator de identificadores CVE de texto livre."""

    CVE_PATTERN = re.compile(r'CVE-\d{4}-\d{4,}', re.IGNORECASE)

    def extract(self, text: str) -> List[str]:
        """Extrai todos os CVEs válidos do texto."""
        matches = self.CVE_PATTERN.findall(text)
        # Validar formato básico
        return [m.upper() for m in matches if self._validate_cve(m)]

    def _validate_cve(self, cve: str) -> bool:
        """Valida formato básico de CVE."""
        parts = cve.upper().split('-')
        if len(parts) != 3 or parts[0] != 'CVE':
            return False
        try:
            year = int(parts[1])
            num = int(parts[2])
            return 2000 <= year <= 2100 and num >= 1
        except ValueError:
            return False


class SealExtractor:
    """Extrator de selos temporais SHA3-256 de texto livre."""

    # SHA3-256 produz 64 caracteres hex, mas podemos aceitar prefixos
    SEAL_PATTERN = re.compile(r'\b[a-f0-9]{16,64}\b', re.IGNORECASE)

    def extract(self, text: str) -> List[str]:
        """Extrai possíveis selos temporais do texto."""
        matches = self.SEAL_PATTERN.findall(text)
        # Filtrar por comprimento típico de hash
        return [m.lower() for m in matches if 16 <= len(m) <= 64]


class ServiceMapParser:
    """Parser de mapas de serviço em JSON/YAML/dict."""

    def parse(self, input_str: str) -> Dict[str, Any]:
        """Parseia string para mapa de serviço."""
        input_str = input_str.strip()

        # Tentar JSON primeiro
        if input_str.startswith('{'):
            try:
                return json.loads(input_str)
            except json.JSONDecodeError as e:
                raise ParseError(f"JSON inválido: {e}", suggestion="Verifique a sintaxe JSON")

        # Tentar YAML se disponível
        if input_str.startswith('-') or ':' in input_str:
            try:
                import yaml
                return yaml.safe_load(input_str)
            except ImportError:
                pass
            except Exception as e:
                raise ParseError(f"YAML inválido: {e}")

        # Fallback: tentar avaliar como dict Python (com segurança limitada)
        try:
            # Apenas para demonstração - em produção usar ast.literal_eval
            result = ast.literal_eval(input_str)
            if isinstance(result, dict):
                return result
        except:
            pass

        raise ParseError(
            "Formato de service_map não reconhecido",
            suggestion="Use JSON: {\"api\": {\"exposure\": 0.9}}"
        )


class DomainParser:
    """Parser de perfis de domínio do campo atrator."""

    VALID_DOMAINS = ['creative', 'technical', 'educational', 'scientific', 'conversational', 'default']

    def extract(self, text: str) -> List[str]:
        """Extrai domínios válidos do texto."""
        found = []
        text_lower = text.lower()
        for domain in self.VALID_DOMAINS:
            if re.search(rf'\b{domain}\b', text_lower):
                found.append(domain)
        return found

    def validate(self, domain: str) -> bool:
        """Valida se domínio é válido."""
        return domain.lower() in self.VALID_DOMAINS

    def suggest(self, invalid: str) -> Optional[str]:
        """Sugere correção para domínio inválido."""
        matches = difflib.get_close_matches(invalid.lower(), self.VALID_DOMAINS, n=1, cutoff=0.6)
        return matches[0] if matches else None


class ComplianceScopeParser:
    """Parser de escopos de conformidade MA-S2."""

    VALID_SCOPES = ['full', 'cvs', 'apm', 'inv', 'aro']

    def extract(self, text: str) -> List[str]:
        """Extrai escopos válidos do texto."""
        found = []
        text_lower = text.lower()
        for scope in self.VALID_SCOPES:
            if re.search(rf'\b{scope}\b', text_lower):
                found.append(scope)
        return found

    def validate(self, scope: str) -> bool:
        """Valida se escopo é válido."""
        return scope.lower() in self.VALID_SCOPES


class ThreatSeverityParser:
    """Parser de níveis de severidade de ameaças."""

    VALID_SEVERITIES = ['critical', 'high', 'medium', 'low', 'info']
    SEVERITY_ORDER = {'critical': 5, 'high': 4, 'medium': 3, 'low': 2, 'info': 1}

    def extract(self, text: str) -> List[str]:
        """Extrai severidades válidas do texto."""
        found = []
        text_lower = text.lower()
        for sev in self.VALID_SEVERITIES:
            if re.search(rf'\b{sev}\b', text_lower):
                found.append(sev)
        return found

    def get_highest(self, severities: List[str]) -> Optional[str]:
        """Retorna severidade mais alta de uma lista."""
        if not severities:
            return None
        return max(severities, key=lambda s: self.SEVERITY_ORDER.get(s.lower(), 0))


class ErrorCorrector:
    """Corretor de erros de digitação usando difflib."""

    def __init__(self, vocabulary: List[str]):
        self.vocabulary = vocabulary

    def suggest(self, invalid: str, cutoff: float = 0.6) -> Optional[str]:
        """Sugere correção para palavra inválida."""
        matches = difflib.get_close_matches(invalid.lower(), self.vocabulary, n=1, cutoff=cutoff)
        return matches[0] if matches else None

    def correct_command(self, invalid: str) -> Tuple[str, bool]:
        """Corrige comando e retorna (corrigido, foi_corrigido)."""
        corrected = self.suggest(invalid)
        if corrected and corrected != invalid.lower():
            return corrected, True
        return invalid.lower(), False


# ============================================================================
# PARSER UNIVERSAL PRINCIPAL
# ============================================================================

class UniversalParser:
    """
    Parser universal que orquestra todos os subparsers e retorna ParseTree tipada.

    Funcionalidades:
    • Parse de comandos %arkhe e %%arkhe
    • Parse de linguagem natural para intenções do Safe Core
    • Parse de código Python com análise de risco via AST
    • Extração de CVEs, selos, domínios, escopos de texto livre
    • Correção de erros de digitação com sugestões contextuais
    • Ancoragem temporal de cada parsing bem-sucedido
    • Integração com GuardianAttractor para validação pré-execução
    """

    def __init__(
        self,
        temporal_chain=None,
        guardian=None,
        audit_api=None,
    ):
        self.temporal_chain = temporal_chain
        self.guardian = guardian
        self.audit_api = audit_api

        # Inicializar subparsers
        self.magic_line_parser = MagicLineParser()
        self.magic_cell_parser = MagicCellParser()
        self.nl_parser = NaturalLanguageParser()
        self.code_parser = CodeParser()
        self.cve_extractor = CVEExtractor()
        self.seal_extractor = SealExtractor()
        self.service_map_parser = ServiceMapParser()
        self.domain_parser = DomainParser()
        self.scope_parser = ComplianceScopeParser()
        self.severity_parser = ThreatSeverityParser()
        self.error_corrector = ErrorCorrector(
            vocabulary=MagicLineParser.VALID_COMMANDS + MagicCellParser.VALID_CELL_COMMANDS
        )

    def parse(self, text: str, context: Optional[ParseContext] = None) -> ParseTree:
        """
        Parseia texto genérico e retorna ParseTree tipada.

        Detecta automaticamente o tipo de entrada:
        • Começa com %arkhe → MagicLineParser
        • Começa com %%arkhe → MagicCellParser (requer cell content)
        • Parece código Python → CodeParser
        • Texto livre → NaturalLanguageParser
        """
        start_time = time.time()
        context = context or ParseContext()
        warnings = []
        errors = []

        text_stripped = text.strip()

        # Roteamento baseado no padrão do texto
        if text_stripped.startswith('%arkhe ') or text_stripped.startswith('%arkhe\n') or text_stripped == '%arkhe':
            # Magic line command
            try:
                magic_cmd = self.magic_line_parser.parse(text_stripped)
                root = ParseNode(
                    node_type='magic_command',
                    value=magic_cmd,
                    position=(0, len(text)),
                    confidence=1.0,
                    metadata={'command_type': 'line'},
                )
            except ParseError as e:
                errors.append(str(e))
                root = ParseNode(
                    node_type='error',
                    value=str(e),
                    position=(0, len(text)),
                    confidence=0.0,
                    metadata={'error_type': e.error_type},
                )

        elif text_stripped.startswith('%%arkhe'):
            # Magic cell command - requires cell content
            # For line-only parse, return partial
            root = ParseNode(
                node_type='cell_magic_stub',
                value={'line': text_stripped, 'note': 'Cell content required for full parse'},
                position=(0, len(text)),
                confidence=0.5,
            )
            warnings.append("%%arkhe requires cell content - use parse_cell_magic() for full parse")

        elif self._looks_like_python_code(text_stripped):
            # Python code
            try:
                code_ast = self.code_parser.parse(text_stripped)
                root = ParseNode(
                    node_type='code_ast',
                    value=code_ast,
                    position=(0, len(text)),
                    confidence=1.0,
                    metadata={
                        'imports': code_ast.imports,
                        'functions': code_ast.function_defs,
                        'risks': [r['type'] for r in code_ast.risk_patterns],
                    },
                )
                if code_ast.risk_patterns:
                    warnings.append(f"⚠️ {len(code_ast.risk_patterns)} risk patterns detected in code")
            except ParseError as e:
                errors.append(str(e))
                root = ParseNode(
                    node_type='error',
                    value=str(e),
                    position=(0, len(text)),
                    confidence=0.0,
                )

        else:
            # Natural language or structured data
            # Try NL parser first
            nl_intent = self.nl_parser.parse(text_stripped)

            if nl_intent.intent_type != 'unknown' and nl_intent.confidence > 0.5:
                root = ParseNode(
                    node_type='nl_intent',
                    value=nl_intent,
                    position=(0, len(text)),
                    confidence=nl_intent.confidence,
                    metadata={'intent': nl_intent.intent_type},
                )
                if nl_intent.suggested_command:
                    warnings.append(f"💡 Suggested command: %arkhe {nl_intent.suggested_command}")
            else:
                # Try structured data parse
                try:
                    parsed = self.service_map_parser.parse(text_stripped)
                    root = ParseNode(
                        node_type='structured_data',
                        value=parsed,
                        position=(0, len(text)),
                        confidence=0.9,
                        metadata={'format': 'json_like'},
                    )
                except ParseError:
                    # Fallback: return raw text with extracted entities
                    entities = {
                        'cves': self.cve_extractor.extract(text_stripped),
                        'seals': self.seal_extractor.extract(text_stripped),
                        'domains': self.domain_parser.extract(text_stripped),
                        'scopes': self.scope_parser.extract(text_stripped),
                    }
                    root = ParseNode(
                        node_type='free_text',
                        value=text_stripped,
                        position=(0, len(text)),
                        confidence=0.3,
                        metadata={'extracted_entities': entities},
                    )
                    if any(entities.values()):
                        warnings.append(f"🔍 Extracted entities: {entities}")

        # Build ParseTree
        parse_time = (time.time() - start_time) * 1000
        tree = ParseTree(
            root=root,
            source_text=text,
            parse_time_ms=parse_time,
            warnings=warnings,
            errors=errors,
        )

        # Anchor successful parse in TemporalChain
        if not errors and self.temporal_chain:
            anchor_data = {
                "parse_type": root.node_type,
                "confidence": root.confidence,
                "warnings": warnings,
                "timestamp": time.time(),
            }

            def run_asyncio(coro):
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    return loop.create_task(coro)
                else:
                    return asyncio.run(coro)

            try:
                run_asyncio(self.temporal_chain.anchor_event("parse_success", anchor_data))
            except Exception:
                pass

        # Log ambiguous/corrected parses to AuditAPI
        if warnings and self.audit_api:

            def run_asyncio(coro):
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    return loop.create_task(coro)
                else:
                    return asyncio.run(coro)

            try:
                run_asyncio(self.audit_api.log_event("parse_corrected", {
                    "text_preview": text[:100],
                    "warnings": warnings,
                    "timestamp": time.time(),
                }))
            except Exception:
                pass

        return tree

    def parse_magic(self, line: str) -> MagicCommand:
        """Parseia comando de linha %arkhe."""
        return self.magic_line_parser.parse(line)

    def parse_cell_magic(self, line: str, cell: str) -> CellMagicCommand:
        """Parseia comando de célula %%arkhe."""
        return self.magic_cell_parser.parse(line, cell)

    def parse_natural_language(self, text: str) -> NLIntent:
        """Parseia texto em linguagem natural."""
        return self.nl_parser.parse(text)

    def parse_code(self, code: str) -> CodeAST:
        """Parseia código Python para AST."""
        return self.code_parser.parse(code)

    def parse_config(self, config_str: str) -> Dict:
        """Parseia string de configuração para dict."""
        return self.service_map_parser.parse(config_str)

    # ========================================================================
    # MÉTODOS DE EXTRAÇÃO
    # ========================================================================

    def extract_cves(self, text: str) -> List[str]:
        """Extrai identificadores CVE de texto livre."""
        return self.cve_extractor.extract(text)

    def extract_seals(self, text: str) -> List[str]:
        """Extrai selos temporais de texto livre."""
        return self.seal_extractor.extract(text)

    def extract_domains(self, text: str) -> List[str]:
        """Extrai perfis de domínio de texto livre."""
        return self.domain_parser.extract(text)

    def extract_scopes(self, text: str) -> List[str]:
        """Extrai escopos de conformidade de texto livre."""
        return self.scope_parser.extract(text)

    def extract_severities(self, text: str) -> List[str]:
        """Extrai níveis de severidade de texto livre."""
        return self.severity_parser.extract(text)

    # ========================================================================
    # MÉTODOS DE CORREÇÃO E SUGESTÃO
    # ========================================================================

    def suggest_correction(self, invalid_input: str, context: Optional[ParseContext] = None) -> str:
        """Sugere correção para entrada inválida."""
        context = context or ParseContext()

        # Tentar corrigir como comando mágico
        parts = invalid_input.strip().split(None, 1)
        if parts:
            first_word = parts[0]

            # Remover prefixos de magic se presente
            if first_word.startswith('%'):
                first_word = first_word.lstrip('%').lstrip('arkhe').strip()

            corrected, was_corrected = self.error_corrector.correct_command(first_word)
            if was_corrected:
                # Reconstruir comando com correção
                rest = f" {parts[1]}" if len(parts) > 1 else ""
                prefix = "%%" if invalid_input.startswith('%%') else "%"
                return f"{prefix}arkhe {corrected}{rest}"

        # Fallback: sugerir baseado no histórico
        if context.history:
            # Encontrar comando mais similar no histórico
            all_commands = [h.split()[0] if h.split() else '' for h in context.history if h.startswith('%arkhe')]
            if all_commands:
                suggestion = self.error_corrector.suggest(invalid_input.split()[0] if invalid_input.split() else '', all_commands)
                if suggestion:
                    return f"%arkhe {suggestion}"

        return "Não foi possível sugerir uma correção. Use %arkhe --help para ver comandos disponíveis."

    # ========================================================================
    # UTILITÁRIOS
    # ========================================================================

    def _looks_like_python_code(self, text: str) -> bool:
        """Heurística para detectar se texto parece código Python."""
        # Indicadores de código Python
        python_indicators = [
            r'^import\s+\w+',
            r'^from\s+\w+\s+import',
            r'^def\s+\w+\s*\(',
            r'^class\s+\w+',
            r'^\s*if\s+.*:',
            r'^\s*for\s+.*:',
            r'^\s*while\s+.*:',
            r'^\s*try\s*:',
            r'^\s*with\s+.*:',
            r'=\s*[\[\{\'\"]',  # Atribuição com estrutura
        ]

        for pattern in python_indicators:
            if re.search(pattern, text, re.MULTILINE):
                return True

        # Se tem múltiplas linhas e parece estruturado, provavelmente é código
        if '\n' in text and ('def ' in text or 'class ' in text or 'import ' in text):
            return True

        return False


# ============================================================================
# INTEGRAÇÃO COM SAFE CORE MCP
# ============================================================================

def register_mcp_tool(server):
    """Registra ferramenta de parsing no servidor MCP."""

    @server.call_tool()
    async def parse_command(name: str, arguments: Dict) -> Dict:
        """Ferramenta MCP para parsing universal de comandos."""
        if name != "parse_command":
            raise ValueError(f"Unknown tool: {name}")

        text = arguments.get("text", "")
        context_data = arguments.get("context", {})

        # Construir contexto
        context = ParseContext(
            user_id=context_data.get("user_id"),
            session_id=context_data.get("session_id"),
            phi_c_current=context_data.get("phi_c_current", 0.997),
        )

        # Executar parsing
        parser = UniversalParser()
        tree = parser.parse(text, context)

        # Retornar resultado serializável
        return {
            "success": not tree.errors,
            "parse_tree": tree.to_dict(),
            "warnings": tree.warnings,
            "errors": tree.errors,
            "parse_time_ms": tree.parse_time_ms,
        }

    return parse_command


# ============================================================================
# PONTO DE ENTRADA PARA TESTES
# ============================================================================

if __name__ == "__main__":
    print("🔍 ARKHE Universal Parser v1.0.0 — Teste Interativo")
    print("=" * 60)

    parser = UniversalParser()

    # Exemplos de teste
    test_cases = [
        ("%arkhe scan import os; os.system('ls')", "Magic line with code"),
        ("%arkhe deploy CVE-2026-12345", "Magic line with CVE"),
        ("Corrija a vulnerabilidade CVE-2026-99999 em produção", "Natural language remediate"),
        ("import pickle\ndata = pickle.loads(open('evil.pkl','rb').read())", "Python code with risk"),
        ("%arkhe profil technical", "Typo correction test"),
        ('{"api": {"exposure": 0.9}, "db": {"exposure": 0.2}}', "Structured service map"),
    ]

    for text, description in test_cases:
        print(f"\n📝 {description}")
        print(f"Input: {text[:80]}{'...' if len(text) > 80 else ''}")

        try:
            tree = parser.parse(text)
            print(f"✅ Parse success ({tree.parse_time_ms:.2f}ms)")
            print(f"   Type: {tree.root.node_type}")
            print(f"   Confidence: {tree.root.confidence:.2f}")
            if tree.warnings:
                print(f"   ⚠️ Warnings: {tree.warnings}")
            if tree.root.metadata:
                print(f"   Metadata: {tree.root.metadata}")
        except Exception as e:
            print(f"❌ Parse error: {e}")

    print(f"\n✨ Universal Parser test complete!")
