# arkhe_os/refactoring/auto_refactor_engine.py
"""
Substrato 276: Auto-Refatoração Guiada por Coerência
Analisa falhas e sugere correções com impacto previsto em Φ_C.
"""
import ast
import difflib
import textwrap
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
import hashlib

@dataclass
class RefactoringSuggestion:
    """Sugestão de refatoração com impacto estimado em coerência."""
    suggestion_id: str
    file_path: str
    line_start: int
    line_end: int
    category: str  # "extract_method", "add_docstring", "reduce_complexity", etc.
    title: str
    description: str
    original_code: str
    suggested_code: str
    estimated_phi_delta: float  # ΔΦ_C estimado após aplicar
    confidence: float  # [0, 1] confiança na estimativa
    test_failures: List[str] = field(default_factory=list)  # IDs de testes relacionados
    metadata: Dict[str, any] = field(default_factory=dict)

    def to_diff(self) -> str:
        """Gera diff unificado para aplicação."""
        return "\n".join(difflib.unified_diff(
            self.original_code.splitlines(keepends=True),
            self.suggested_code.splitlines(keepends=True),
            fromfile=f"a/{self.file_path}",
            tofile=f"b/{self.file_path}",
            lineterm=""
        ))

class CoherenceAwareRefactorEngine:
    """Motor de refatoração que usa métricas de coerência para priorizar sugestões."""

    def __init__(self, lfir_mapper, test_results: Optional[Dict] = None):
        self.lfir_mapper = lfir_mapper
        self.test_results = test_results or {}
        self._suggestion_counter = 0

    def analyze_project(self, source_dir: Path, min_phi_threshold: float = 0.7) -> List[RefactoringSuggestion]:
        """Analisa projeto e retorna sugestões ordenadas por impacto."""
        suggestions = []

        # 1. Analisar arquivos Python com baixa coerência
        for py_file in source_dir.rglob("*.py"):
            if "test_" in py_file.name or py_file.name.startswith("test_"):
                continue  # Pular arquivos de teste

            try:
                lfir = self.lfir_mapper.parse_file(str(py_file))
                for node in getattr(lfir, "nodes", []):
                    if getattr(node, "coherence", 1.0) < min_phi_threshold:
                        suggestions.extend(self._suggest_for_low_coherence(node, py_file))
            except Exception:
                continue  # Ignorar arquivos com parsing problemático

        # 2. Analisar falhas de teste recentes
        for failure in self.test_results.get("failures", []):
            suggestions.extend(self._suggest_for_test_failure(failure))

        # 3. Detectar padrões de código problemáticos
        for py_file in source_dir.rglob("*.py"):
            suggestions.extend(self._detect_code_smells(py_file))

        # Ordenar por impacto estimado e confiança
        return sorted(
            suggestions,
            key=lambda s: (s.estimated_phi_delta * s.confidence),
            reverse=True
        )

    def _suggest_for_low_coherence(self, node, file_path: Path) -> List[RefactoringSuggestion]:
        """Gera sugestões para nós com baixa coerência."""
        suggestions = []

        # Alta complexidade ciclomática → extrair método
        if hasattr(node, 'complexity') and node.complexity > 10:
            suggestions.append(self._create_extract_method_suggestion(node, file_path))

        # Falta de documentação → adicionar docstring
        if not getattr(node, 'docstring', None):
            suggestions.append(self._create_docstring_suggestion(node, file_path))

        # Muitos parâmetros → usar dataclass/config object
        if hasattr(node, 'num_params') and node.num_params > 5:
            suggestions.append(self._create_parameter_object_suggestion(node, file_path))

        return suggestions

    def _create_extract_method_suggestion(self, node, file_path: Path) -> RefactoringSuggestion:
        """Sugere extrair trecho complexo para novo método."""
        self._suggestion_counter += 1
        with open(file_path, 'r') as f:
            source_lines = f.readlines()

        original = "".join(source_lines[node.line_start-1:node.line_end])
        suggested = self._generate_extracted_method(node, source_lines)

        return RefactoringSuggestion(
            suggestion_id=f"extract-{self._suggestion_counter}",
            file_path=str(file_path),
            line_start=node.line_start,
            line_end=node.line_end,
            category="extract_method",
            title=f"Extract complex block from {node.name}",
            description=f"Reduce complexity from {node.complexity} to <10 by extracting to helper method",
            original_code=original,
            suggested_code=suggested,
            estimated_phi_delta=0.15 * (node.complexity / 20),  # Heurística
            confidence=0.75,
            test_failures=self._find_related_test_failures(node),
            metadata={"original_complexity": node.complexity, "target_complexity": 10},
        )

    def _create_docstring_suggestion(self, node, file_path: Path) -> RefactoringSuggestion:
        """Sugere adicionar docstring."""
        self._suggestion_counter += 1
        docstring_template = self._generate_docstring_template(node)

        return RefactoringSuggestion(
            suggestion_id=f"docstring-{self._suggestion_counter}",
            file_path=str(file_path),
            line_start=node.line_start,
            line_end=node.line_start,
            category="add_docstring",
            title=f"Add docstring to {node.name}",
            description="Improve code documentation and coherence",
            original_code=f"def {node.name}(...):\n    ...",
            suggested_code=docstring_template,
            estimated_phi_delta=0.08,
            confidence=0.92,
            metadata={"function_name": node.name},
        )

    def _create_parameter_object_suggestion(self, node, file_path: Path) -> RefactoringSuggestion:
        """Sugere usar object config parameter object."""
        self._suggestion_counter += 1

        return RefactoringSuggestion(
            suggestion_id=f"param-obj-{self._suggestion_counter}",
            file_path=str(file_path),
            line_start=node.line_start,
            line_end=node.line_start,
            category="parameter_object",
            title=f"Extract parameter object for {node.name}",
            description="Improve method signature coherence by using a config object",
            original_code=f"def {node.name}(...):\n    ...",
            suggested_code=f"def {node.name}(config: Config):\n    ...",
            estimated_phi_delta=0.05,
            confidence=0.85,
            metadata={"function_name": node.name},
        )

    def _suggest_for_test_failure(self, failure: Dict) -> List[RefactoringSuggestion]:
        """Gera sugestões baseadas em falhas específicas de teste."""
        suggestions = []
        error_type = failure.get("error_type", "")
        file_path = Path(failure.get("file", ""))

        if not file_path.exists():
            return suggestions

        if "TypeError" in error_type:
            suggestions.append(self._create_type_hint_suggestion(failure, file_path))
        elif "AttributeError" in error_type:
            suggestions.append(self._create_null_check_suggestion(failure, file_path))
        elif "IndexError" in error_type or "KeyError" in error_type:
            suggestions.append(self._create_bounds_check_suggestion(failure, file_path))

        return suggestions

    def _create_type_hint_suggestion(self, failure: Dict, file_path: Path) -> RefactoringSuggestion:
        """Sugere adicionar type hints para corrigir TypeError."""
        self._suggestion_counter += 1
        line = failure.get("line", 1)

        with open(file_path, 'r') as f:
            lines = f.readlines()
            original = lines[line-1].strip() if line <= len(lines) else ""

        return RefactoringSuggestion(
            suggestion_id=f"type-hint-{self._suggestion_counter}",
            file_path=str(file_path),
            line_start=line,
            line_end=line,
            category="add_type_hints",
            title=f"Add type hints to fix TypeError",
            description=f"TypeError at line {line}: {failure.get('message', '')[:100]}",
            original_code=original,
            suggested_code=f"# Add type hints: def func(arg: Type) -> ReturnType:\n{original}",
            estimated_phi_delta=0.12,
            confidence=0.85,
            test_failures=[failure.get("test_id")],
            metadata={"error_type": "TypeError", "line": line},
        )

    def _create_null_check_suggestion(self, failure: Dict, file_path: Path) -> RefactoringSuggestion:
        """Sugere adicionar null check para corrigir AttributeError."""
        self._suggestion_counter += 1
        line = failure.get("line", 1)

        with open(file_path, 'r') as f:
            lines = f.readlines()
            original = lines[line-1].strip() if line <= len(lines) else ""

        return RefactoringSuggestion(
            suggestion_id=f"null-check-{self._suggestion_counter}",
            file_path=str(file_path),
            line_start=line,
            line_end=line,
            category="add_null_check",
            title=f"Add null check to fix AttributeError",
            description=f"AttributeError at line {line}: {failure.get('message', '')[:100]}",
            original_code=original,
            suggested_code=f"if obj is not None:\n    {original}",
            estimated_phi_delta=0.08,
            confidence=0.90,
            test_failures=[failure.get("test_id")],
            metadata={"error_type": "AttributeError", "line": line},
        )

    def _create_bounds_check_suggestion(self, failure: Dict, file_path: Path) -> RefactoringSuggestion:
        """Sugere adicionar bounds check."""
        self._suggestion_counter += 1
        line = failure.get("line", 1)

        with open(file_path, 'r') as f:
            lines = f.readlines()
            original = lines[line-1].strip() if line <= len(lines) else ""

        return RefactoringSuggestion(
            suggestion_id=f"bounds-check-{self._suggestion_counter}",
            file_path=str(file_path),
            line_start=line,
            line_end=line,
            category="add_bounds_check",
            title=f"Add bounds check to fix IndexError/KeyError",
            description=f"IndexError/KeyError at line {line}: {failure.get('message', '')[:100]}",
            original_code=original,
            suggested_code=f"if index_or_key in container:\n    {original}",
            estimated_phi_delta=0.08,
            confidence=0.90,
            test_failures=[failure.get("test_id")],
            metadata={"error_type": "IndexError", "line": line},
        )

    def _detect_code_smells(self, file_path: Path) -> List[RefactoringSuggestion]:
        """Detecta code smells e sugere refatorações."""
        suggestions = []
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
        except SyntaxError:
            return suggestions

        for node in ast.walk(tree):
            # Funções muito longas
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.end_lineno - node.lineno > 50:
                    suggestions.append(self._create_split_function_suggestion(node, file_path))

            # Classes muito grandes
            elif isinstance(node, ast.ClassDef):
                if len(node.body) > 20:
                    suggestions.append(self._create_extract_class_suggestion(node, file_path))

        return suggestions

    def _create_split_function_suggestion(self, node, file_path: Path) -> RefactoringSuggestion:
        self._suggestion_counter += 1
        return RefactoringSuggestion(
            suggestion_id=f"split-func-{self._suggestion_counter}",
            file_path=str(file_path),
            line_start=node.lineno,
            line_end=node.end_lineno,
            category="split_function",
            title=f"Split long function {node.name}",
            description=f"Function {node.name} is too long (>50 lines). Split into smaller functions.",
            original_code=f"def {node.name}(...):\n    ...",
            suggested_code=f"def {node.name}(...):\n    _part1()\n    _part2()",
            estimated_phi_delta=0.10,
            confidence=0.80,
            metadata={"function_name": node.name},
        )

    def _create_extract_class_suggestion(self, node, file_path: Path) -> RefactoringSuggestion:
        self._suggestion_counter += 1
        return RefactoringSuggestion(
            suggestion_id=f"extract-class-{self._suggestion_counter}",
            file_path=str(file_path),
            line_start=node.lineno,
            line_end=node.end_lineno,
            category="extract_class",
            title=f"Extract class from {node.name}",
            description=f"Class {node.name} has too many methods (>20). Extract functionality into new classes.",
            original_code=f"class {node.name}:\n    ...",
            suggested_code=f"class {node.name}:\n    def __init__(self):\n        self.helper = HelperClass()",
            estimated_phi_delta=0.15,
            confidence=0.75,
            metadata={"class_name": node.name},
        )

    def _generate_docstring_template(self, node) -> str:
        """Gera template de docstring baseado na assinatura da função."""
        args = [arg.arg for arg in node.args.args if arg.arg != "self"]
        returns = "None" if isinstance(node.returns, ast.Constant) and node.returns.value is None else "Any"

        doc = f'    """\n'
        doc += f'    {node.name.replace("_", " ").title()}.\n\n'
        for arg in args:
            doc += f'    Args:\n        {arg}: Description of {arg}.\n'
        doc += f'\n    Returns:\n        {returns}: Description of return value.\n'
        doc += f'    """\n'
        return doc

    def _generate_extracted_method(self, node, source_lines: List[str]) -> str:
        """Gera código sugerido para extração de método."""
        # Placeholder: em produção, usar análise de AST para extração real
        return f"def _helper_{node.name}(...):\n    # Extracted from lines {node.line_start}-{node.line_end}\n    pass\n\n"

    def _find_related_test_failures(self, node) -> List[str]:
        """Encontra testes que falharam relacionados ao nó."""
        # Placeholder: em produção, mapear cobertura de teste para nós LFIR
        return []

    def apply_suggestion(self, suggestion: RefactoringSuggestion, dry_run: bool = True) -> Dict:
        """Aplica sugestão ao arquivo fonte."""
        if dry_run:
            return {
                "status": "preview",
                "diff": suggestion.to_diff(),
                "estimated_phi_impact": suggestion.estimated_phi_delta,
            }

        # Aplicar modificação real
        with open(suggestion.file_path, 'r') as f:
            content = f.read()

        new_content = content.replace(suggestion.original_code, suggestion.suggested_code, 1)
        with open(suggestion.file_path, 'w') as f:
            f.write(new_content)

        return {
            "status": "applied",
            "file": suggestion.file_path,
            "suggestion_id": suggestion.suggestion_id,
        }
