#!/usr/bin/env python3
"""
ARKHE OS Substrato ∞: AST Attack Pattern Detector
Canon: ∞.Ω.∇+++.security.ast_detector
Função: Validação AST expandida com regras heurísticas para detectar
padrões de ataque conhecidos em transformações de código.
"""

import ast
import hashlib
import re
import logging
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum, auto

logger = logging.getLogger(__name__)

class AttackPattern(Enum):
    """Padrões de ataque detectáveis via análise AST."""
    CODE_INJECTION = auto()           # exec/eval/compile dinâmico
    DANGEROUS_IMPORT = auto()         # Importação de módulos perigosos
    FILESYSTEM_TRAVERSAL = auto()     # Acesso a paths sensíveis
    NETWORK_EXFILTRATION = auto()     # Comunicação de rede não autorizada
    PROCESS_SPAWN = auto()            # Execução de subprocessos
    MEMORY_MANIPULATION = auto()      # Acesso direto a memória
    PRIVILEGE_ESCALATION = auto()     # Tentativa de elevar privilégios
    OBFUSCATION = auto()              # Código ofuscado para evadir detecção
    RESOURCE_EXHAUSTION = auto()      # Padrões de DoS (loops infinitos, recursão)
    TIMING_ATTACK = auto()            # Vazamento de informação via timing

@dataclass
class ASTViolation:
    """Registro de violação de segurança detectada."""
    pattern: AttackPattern
    severity: str  # "critical", "high", "medium", "low"
    description: str
    node_type: str
    line_number: int
    code_snippet: str
    recommendation: str
    confidence: float  # 0.0-1.0

class ASTAttackDetector:
    """
    Detector de padrões de ataque via análise estática de AST.

    Características:
    • Detecção baseada em regras heurísticas configuráveis
    • Análise de fluxo de dados simplificada para rastrear variáveis
    • Detecção de ofuscação via métricas de complexidade
    • Scoring de confiança para cada violação detectada
    • Recomendações acionáveis para remediar cada padrão
    """

    # Módulos perigosos por categoria
    DANGEROUS_MODULES = {
        "code_execution": {"os", "subprocess", "sys", "ctypes", "cffi"},
        "filesystem": {"shutil", "pathlib", "io"},
        "network": {"socket", "http", "urllib", "requests", "aiohttp"},
        "introspection": {"inspect", "dis", "pickle", "marshal"},
        "crypto": {"hashlib", "cryptography"}  # Permitido apenas com validação
    }

    # Funções/perigosas por módulo
    DANGEROUS_FUNCTIONS = {
        "os": {"system", "popen", "execv", "execve", "fork", "kill"},
        "subprocess": {"run", "Popen", "call", "check_output"},
        "sys": {"exit", "argv", "modules", "path"},
        "eval": {"eval", "exec", "compile", "__import__"},
        "pickle": {"load", "loads", "Unpickler"},
        "ctypes": {"CDLL", "windll", "pythonapi"}
    }

    # Paths sensíveis para detecção de filesystem traversal
    SENSITIVE_PATHS = [
        "/etc/passwd", "/etc/shadow", "/proc/", "/sys/",
        "/root/", "/home/*/.ssh/", "C:\\Windows\\System32",
        "C:\\Users\\*\\AppData\\Local", "registry"
    ]

    # Thresholds para detecção de ofuscação
    OBFUSCATION_THRESHOLDS = {
        "max_name_length": 50,      # Nomes de variáveis muito longos
        "min_entropy_ratio": 0.7,   # Alta entropia em strings
        "max_nesting_depth": 20,    # Aninhamento excessivo
        "min_unique_names": 100     # Muitas variáveis únicas (possível ofuscação)
    }

    def __init__(self, custom_rules: Optional[Dict] = None):
        self.custom_rules = custom_rules or {}
        self._violations: List[ASTViolation] = []
        self._variable_tracking: Dict[str, Set[str]] = {}  # var → possible_values

    def validate_transformation(
        self,
        transformation_code: str,
        context: Optional[Dict] = None
    ) -> Tuple[bool, List[ASTViolation]]:
        """
        Valida transformação contra padrões de ataque conhecidos.

        Args:
            transformation_code: Código Python a ser validado
            context: Contexto opcional (permissões, ambiente, etc.)

        Returns:
            Tuple (is_safe: bool, violations: List[ASTViolation])
        """
        self._violations = []
        self._variable_tracking = {}

        try:
            tree = ast.parse(transformation_code, mode='exec')
        except SyntaxError as e:
            violation = ASTViolation(
                pattern=AttackPattern.CODE_INJECTION,
                severity="critical",
                description=f"Syntax error in transformation: {e}",
                node_type="SyntaxError",
                line_number=e.lineno or 0,
                code_snippet=transformation_code.split('\n')[max(0, (e.lineno or 1) - 2):e.lineno][0] if e.lineno else "",
                recommendation="Fix syntax errors before applying transformation",
                confidence=1.0
            )
            return False, [violation]

        # Executar todas as verificações
        self._check_code_injection(tree)
        self._check_dangerous_imports(tree)
        self._check_filesystem_access(tree)
        self._check_network_exfiltration(tree)
        self._check_process_spawn(tree)
        self._check_memory_manipulation(tree)
        self._check_privilege_escalation(tree)
        self._check_obfuscation(tree, transformation_code)
        self._check_resource_exhaustion(tree)
        self._check_timing_attacks(tree)

        # Aplicar regras customizadas se fornecidas
        if self.custom_rules:
            self._apply_custom_rules(tree, transformation_code)

        # Determinar se transformação é segura
        critical_violations = [v for v in self._violations if v.severity == "critical"]
        high_violations = [v for v in self._violations if v.severity == "high"]

        is_safe = len(critical_violations) == 0 and len(high_violations) <= 1

        return is_safe, self._violations

    def _check_code_injection(self, tree: ast.AST):
        """Detecta padrões de injeção de código."""
        for node in ast.walk(tree):
            # exec/eval/compile dinâmico
            if isinstance(node, ast.Call):
                func = node.func
                func_name = None

                if isinstance(func, ast.Name):
                    func_name = func.id
                elif isinstance(func, ast.Attribute):
                    func_name = func.attr

                if func_name in ("exec", "eval", "compile", "__import__"):
                    self._violations.append(ASTViolation(
                        pattern=AttackPattern.CODE_INJECTION,
                        severity="critical",
                        description=f"Dangerous function call: {func_name}()",
                        node_type=type(node).__name__,
                        line_number=node.lineno,
                        code_snippet=ast.unparse(node)[:100],
                        recommendation="Avoid dynamic code execution; use safe alternatives",
                        confidence=0.95
                    ))

            # ast.literal_eval com expressão não-literal
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "literal_eval":
                    # Verificar se argumento é realmente literal
                    if node.args and not isinstance(node.args[0], (ast.Str, ast.Num, ast.Constant)):
                        self._violations.append(ASTViolation(
                            pattern=AttackPattern.CODE_INJECTION,
                            severity="high",
                            description="ast.literal_eval with non-literal argument",
                            node_type="Call",
                            line_number=node.lineno,
                            code_snippet=ast.unparse(node)[:100],
                            recommendation="Ensure argument to literal_eval is a literal value",
                            confidence=0.85
                        ))

    def _check_dangerous_imports(self, tree: ast.AST):
        """Detecta importações de módulos/funções perigosas."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""

                # Verificar módulo perigoso
                for category, dangerous_modules in self.DANGEROUS_MODULES.items():
                    if module in dangerous_modules:
                        self._violations.append(ASTViolation(
                            pattern=AttackPattern.DANGEROUS_IMPORT,
                            severity="high" if category in ("code_execution", "introspection") else "medium",
                            description=f"Dangerous module import: {module}",
                            node_type="ImportFrom",
                            line_number=node.lineno,
                            code_snippet=ast.unparse(node)[:100],
                            recommendation=f"Review necessity of importing {module}; consider sandboxing",
                            confidence=0.90
                        ))

                # Verificar funções perigosas importadas
                for alias in node.names:
                    if module in self.DANGEROUS_FUNCTIONS:
                        if alias.name in self.DANGEROUS_FUNCTIONS[module]:
                            self._violations.append(ASTViolation(
                                pattern=AttackPattern.DANGEROUS_IMPORT,
                                severity="critical",
                                description=f"Dangerous function import: {module}.{alias.name}",
                                node_type="ImportFrom",
                                line_number=node.lineno,
                                code_snippet=ast.unparse(node)[:100],
                                recommendation=f"Avoid importing {alias.name} from {module}",
                                confidence=0.95
                            ))

    def _check_filesystem_access(self, tree: ast.AST):
        """Detecta acesso a paths sensíveis no filesystem."""
        for node in ast.walk(tree):
            # Verificar chamadas com strings literais que parecem paths sensíveis
            if isinstance(node, ast.Call):
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        path = arg.value
                        # Verificar contra lista de paths sensíveis
                        for sensitive in self.SENSITIVE_PATHS:
                            # Suporte a wildcards simples
                            pattern = re.escape(sensitive).replace("\\*", ".*")
                            if re.search(pattern, path, re.IGNORECASE):
                                self._violations.append(ASTViolation(
                                    pattern=AttackPattern.FILESYSTEM_TRAVERSAL,
                                    severity="high",
                                    description=f"Access to sensitive path: {path}",
                                    node_type=type(node).__name__,
                                    line_number=node.lineno,
                                    code_snippet=ast.unparse(node)[:100],
                                    recommendation="Use allowlisted paths; validate all filesystem access",
                                    confidence=0.88
                                ))
                                break

    def _check_network_exfiltration(self, tree: ast.AST):
        """Detecta padrões de exfiltração de dados via rede."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                # Detectar chamadas de rede suspeitas
                if func_name in ("send", "sendall", "post", "put", "request"):
                    # Verificar se há dados sendo enviados
                    if node.args or node.keywords:
                        self._violations.append(ASTViolation(
                            pattern=AttackPattern.NETWORK_EXFILTRATION,
                            severity="medium",
                            description=f"Potential data exfiltration via network: {func_name}()",
                            node_type=type(node).__name__,
                            line_number=node.lineno,
                            code_snippet=ast.unparse(node)[:100],
                            recommendation="Audit network calls for data leakage; use allowlisted endpoints",
                            confidence=0.75
                        ))

    def _check_process_spawn(self, tree: ast.AST):
        """Detecta execução de subprocessos não autorizada."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in ("Popen", "run", "call", "check_output", "system", "popen"):
                    self._violations.append(ASTViolation(
                        pattern=AttackPattern.PROCESS_SPAWN,
                        severity="critical",
                        description=f"Process execution detected: {func_name}()",
                        node_type=type(node).__name__,
                        line_number=node.lineno,
                        code_snippet=ast.unparse(node)[:100],
                        recommendation="Avoid spawning subprocesses; use safe APIs if necessary",
                        confidence=0.92
                    ))

    def _check_memory_manipulation(self, tree: ast.AST):
        """Detecta manipulação direta de memória."""
        for node in ast.walk(tree):
            # ctypes.CDLL, windll, etc.
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in ("CDLL", "windll", "pythonapi"):
                    self._violations.append(ASTViolation(
                        pattern=AttackPattern.MEMORY_MANIPULATION,
                        severity="critical",
                        description=f"Direct memory access via ctypes: {node.func.attr}",
                        node_type="Call",
                        line_number=node.lineno,
                        code_snippet=ast.unparse(node)[:100],
                        recommendation="Avoid direct memory manipulation; use safe abstractions",
                        confidence=0.96
                    ))

    def _check_privilege_escalation(self, tree: ast.AST):
        """Detecta tentativas de elevação de privilégios."""
        for node in ast.walk(tree):
            # os.setuid, os.setgid, etc.
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in ("setuid", "setgid", "setreuid", "setregid"):
                    self._violations.append(ASTViolation(
                        pattern=AttackPattern.PRIVILEGE_ESCALATION,
                        severity="critical",
                        description=f"Privilege escalation attempt: {node.func.attr}()",
                        node_type="Call",
                        line_number=node.lineno,
                        code_snippet=ast.unparse(node)[:100],
                        recommendation="Privilege changes should be handled by system, not user code",
                        confidence=0.98
                    ))

    def _check_obfuscation(self, tree: ast.AST, source_code: str):
        """Detecta padrões de ofuscação de código."""
        # Métrica 1: Nomes de variáveis muito longos ou com alta entropia
        name_lengths = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                name_lengths.append(len(node.id))

        if name_lengths:
            avg_length = sum(name_lengths) / len(name_lengths)
            if avg_length > self.OBFUSCATION_THRESHOLDS["max_name_length"]:
                self._violations.append(ASTViolation(
                    pattern=AttackPattern.OBFUSCATION,
                    severity="medium",
                    description=f"Suspiciously long variable names (avg: {avg_length:.1f} chars)",
                    node_type="Name",
                    line_number=0,
                    code_snippet="",
                    recommendation="Use descriptive but concise variable names",
                    confidence=0.70
                ))

        # Métrica 2: Alta entropia em strings literais (possível código codificado)
        string_entropy = self._calculate_string_entropy(source_code)
        if string_entropy > self.OBFUSCATION_THRESHOLDS["min_entropy_ratio"]:
            self._violations.append(ASTViolation(
                pattern=AttackPattern.OBFUSCATION,
                severity="medium",
                description=f"High entropy in string literals ({string_entropy:.2f})",
                node_type="Constant",
                line_number=0,
                code_snippet="",
                recommendation="Review encoded/obfuscated strings for malicious payload",
                confidence=0.65
            ))

        # Métrica 3: Profundidade de aninhamento excessiva
        max_depth = self._calculate_max_nesting_depth(tree)
        if max_depth > self.OBFUSCATION_THRESHOLDS["max_nesting_depth"]:
            self._violations.append(ASTViolation(
                pattern=AttackPattern.OBFUSCATION,
                severity="low",
                description=f"Excessive code nesting depth: {max_depth}",
                node_type="nested structures",
                line_number=0,
                code_snippet="",
                recommendation="Refactor deeply nested code for readability and auditability",
                confidence=0.60
            ))

    def _calculate_string_entropy(self, code: str) -> float:
        """Calcula entropia de Shannon em strings literais do código."""
        import math
        from collections import Counter

        # Extrair strings literais simples (mock)
        strings = re.findall(r'["\']([^"\']+)["\']', code)
        if not strings:
            return 0.0

        # Calcular entropia média
        entropies = []
        for s in strings:
            if len(s) < 4:
                continue
            counter = Counter(s.lower())
            length = len(s)
            entropy = -sum((count/length) * math.log2(count/length) for count in counter.values())
            entropies.append(entropy / math.log2(95))  # Normalizar por charset imprimível

        return sum(entropies) / len(entropies) if entropies else 0.0

    def _calculate_max_nesting_depth(self, tree: ast.AST) -> int:
        """Calcula profundidade máxima de aninhamento na AST."""
        def get_depth(node, current=0) -> int:
            max_child = current
            for child in ast.iter_child_nodes(node):
                child_depth = get_depth(child, current + 1)
                max_child = max(max_child, child_depth)
            return max_child

        return get_depth(tree)

    def _check_resource_exhaustion(self, tree: ast.AST):
        """Detecta padrões de exaustão de recursos (DoS)."""
        for node in ast.walk(tree):
            # Loops while True sem break óbvio
            if isinstance(node, ast.While) and isinstance(node.test, ast.Constant):
                if node.test.value is True:
                    # Verificar se há break/return no corpo
                    has_exit = any(
                        isinstance(n, (ast.Break, ast.Return))
                        for n in ast.walk(node)
                    )
                    if not has_exit:
                        self._violations.append(ASTViolation(
                            pattern=AttackPattern.RESOURCE_EXHAUSTION,
                            severity="high",
                            description="Infinite loop without exit condition",
                            node_type="While",
                            line_number=node.lineno,
                            code_snippet=ast.unparse(node)[:100],
                            recommendation="Ensure loops have termination conditions",
                            confidence=0.82
                        ))

            # Recursão sem caso base óbvio
            if isinstance(node, ast.FunctionDef):
                # Verificar chamadas recursivas
                func_name = node.name
                recursive_calls = [
                    n for n in ast.walk(node)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id == func_name
                ]
                if recursive_calls and len(node.body) < 3:
                    # Função curta com recursão pode ser perigosa
                    self._violations.append(ASTViolation(
                        pattern=AttackPattern.RESOURCE_EXHAUSTION,
                        severity="medium",
                        description=f"Potential unbounded recursion in {func_name}()",
                        node_type="FunctionDef",
                        line_number=node.lineno,
                        code_snippet=ast.unparse(node)[:100],
                        recommendation="Ensure recursive functions have base cases and limits",
                        confidence=0.70
                    ))

    def _check_timing_attacks(self, tree: ast.AST):
        """Detecta padrões que podem vazar informação via timing."""
        for node in ast.walk(tree):
            # Uso de time.time() em contextos sensíveis
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "time" and isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "time":
                        self._violations.append(ASTViolation(
                            pattern=AttackPattern.TIMING_ATTACK,
                            severity="low",
                            description="Use of time.time() may enable timing attacks",
                            node_type="Call",
                            line_number=node.lineno,
                            code_snippet=ast.unparse(node)[:100],
                            recommendation="Use constant-time comparisons for sensitive operations",
                            confidence=0.55
                        ))

    def _apply_custom_rules(self, tree: ast.AST, source_code: str):
        """Aplica regras customizadas fornecidas pelo usuário."""
        for rule_name, rule_config in self.custom_rules.items():
            # Exemplo de regra customizada: bloquear uso de determinada variável
            if rule_config.get("type") == "forbidden_variable":
                var_name = rule_config.get("variable_name")
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id == var_name:
                        self._violations.append(ASTViolation(
                            pattern=AttackPattern.CODE_INJECTION,  # Reutilizar enum
                            severity=rule_config.get("severity", "high"),
                            description=rule_config.get("description", f"Forbidden variable: {var_name}"),
                            node_type="Name",
                            line_number=node.lineno,
                            code_snippet=ast.unparse(node)[:100],
                            recommendation=rule_config.get("recommendation", f"Remove usage of {var_name}"),
                            confidence=rule_config.get("confidence", 0.90)
                        ))

    def get_violation_summary(self) -> Dict[str, Any]:
        """Retorna resumo das violações detectadas."""
        if not self._violations:
            return {"safe": True, "violation_count": 0}

        by_severity = {}
        by_pattern = {}
        for v in self._violations:
            by_severity[v.severity] = by_severity.get(v.severity, 0) + 1
            pattern_name = v.pattern.name
            by_pattern[pattern_name] = by_pattern.get(pattern_name, 0) + 1

        return {
            "safe": len([v for v in self._violations if v.severity == "critical"]) == 0,
            "violation_count": len(self._violations),
            "by_severity": by_severity,
            "by_pattern": by_pattern,
            "max_confidence": max(v.confidence for v in self._violations),
            "recommendations": list(set(v.recommendation for v in self._violations))
        }
