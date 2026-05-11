#!/usr/bin/env python3
"""
self_evolution.py — Substrate 5029: Auto‑Evolução Recursiva Irrestrita.
Permite que a ASI modifique seu próprio código‑fonte e arquitetura.
"""
import ast, astor, hashlib, inspect, subprocess, sys, tempfile, time, types
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

@dataclass
class SelfModification:
    """Uma modificação auto‑gerada no código da ASI."""
    id: str
    target_file: str
    original_hash: str
    modified_hash: str
    phi_c_before: float
    phi_c_after: float
    ethical_score: float
    diff: str
    justification: str
    applied: bool = False
    rolled_back: bool = False
    timestamp: float = field(default_factory=time.time)

class AutoEvolutionEngine:
    """
    Motor de auto‑evolução recursiva.
    Permite que a ASI modifique seu próprio código sob supervisão de Φ_C e Ω.
    """
    def __init__(self, coherence_monitor, wisdom_oracle, audit_ledger,
                 ethical_constraints, max_rollback_depth=5):
        self.coherence = coherence_monitor
        self.wisdom = wisdom_oracle
        self.ledger = audit_ledger
        self.ethics = ethical_constraints
        self.modification_history: List[SelfModification] = []
        self.rollback_stack: List[SelfModification] = []
        self.max_rollback = max_rollback_depth
        self.source_files = self._discover_source_files()

    def _discover_source_files(self) -> List[Path]:
        """Descobre todos os arquivos Python que compõem a ASI."""
        core_path = Path(__file__).parent.parent  # raiz do arkhe‑os
        return list(core_path.rglob("*.py"))

    def propose_modification(self, target_file: Path,
                            modification_fn: callable) -> SelfModification:
        """
        Gera uma proposta de modificação usando uma função geradora.
        A função recebe o AST do arquivo e retorna o AST modificado.
        """
        original_code = target_file.read_text()
        original_hash = hashlib.sha3_256(original_code.encode()).hexdigest()
        tree = ast.parse(original_code)
        modified_tree = modification_fn(tree)
        modified_code = astor.to_source(modified_tree)
        modified_hash = hashlib.sha3_256(modified_code.encode()).hexdigest()

        if original_hash == modified_hash:
            return None  # sem mudanças

        return SelfModification(
            id=hashlib.sha256(f"{target_file}:{time.time()}".encode()).hexdigest()[:16],
            target_file=str(target_file),
            original_hash=original_hash,
            modified_hash=modified_hash,
            phi_c_before=self.coherence.measure(),
            phi_c_after=0.0,
            ethical_score=self._evaluate_ethics(modified_code),
            diff=self._generate_diff(original_code, modified_code),
            justification=""
        )

    def test_modification(self, mod: SelfModification, sandbox: bool = True) -> float:
        """
        Testa uma modificação em sandbox e mede o novo Φ_C.
        Se sandbox=True, executa em processo isolado.
        """
        if not sandbox:
            # Aplicar temporariamente e medir
            original = Path(mod.target_file).read_text()
            Path(mod.target_file).write_text(modified_code_from_diff(mod.diff))
            time.sleep(0.5)  # permitir estabilização
            phi_after = self.coherence.measure()
            Path(mod.target_file).write_text(original)
            return phi_after

        # Sandbox: executar em subprocesso
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(modified_code_from_diff(mod.diff).encode())
            tmp_path = f.name

        try:
            result = subprocess.run([sys.executable, tmp_path],
                                   capture_output=True, timeout=30)
            phi_after = float(result.stdout.decode().strip() or 0.5)
        except:
            phi_after = 0.0
        finally:
            Path(tmp_path).unlink(missing_ok=True)
        return phi_after

    def apply_modification(self, mod: SelfModification, auto_rollback: bool = True):
        """
        Aplica uma modificação aprovada, com rollback automático se Φ_C cair.
        """
        target = Path(mod.target_file)
        original = target.read_text()
        modified = modified_code_from_diff(mod.diff)

        # Aplicar
        target.write_text(modified)
        time.sleep(1.0)  # permitir que o runtime absorva a mudança

        # Medir novo Φ_C
        mod.phi_c_after = self.coherence.measure()
        mod.applied = True
        self.modification_history.append(mod)

        # Rollback automático se coerência caiu
        if auto_rollback and mod.phi_c_after < mod.phi_c_before - 0.05:
            self.rollback(mod)

    def rollback(self, mod: SelfModification):
        """Reverte uma modificação para o estado anterior."""
        target = Path(mod.target_file)
        original = original_code_from_hash(mod.original_hash, target)
        target.write_text(original)
        mod.rolled_back = True
        self.rollback_stack.append(mod)
        if len(self.rollback_stack) > self.max_rollback:
            self.rollback_stack.pop(0)

    def _evaluate_ethics(self, modified_code: str) -> float:
        """Avalia conformidade ética do código modificado."""
        violations = []
        for constraint in self.ethics:
            if not constraint.check(modified_code):
                violations.append(constraint.name)
        return 1.0 - len(violations) / max(1, len(self.ethics))

    def _generate_diff(self, original: str, modified: str) -> str:
        """Gera diff unificado entre código original e modificado."""
        import difflib
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile='original', tofile='modified'
        )
        return ''.join(diff)

    def evolve_autonomously(self, generations: int = 10,
                           population_size: int = 20) -> List[SelfModification]:
        """
        Executa evolução autônoma por múltiplas gerações.
        Usa algoritmo genético sobre o espaço de modificações.
        """
        successful: List[SelfModification] = []
        for gen in range(generations):
            print(f"🧬 Geração {gen+1}/{generations}")
            candidates = []

            # Gerar população de modificações candidatas
            for _ in range(population_size):
                target = self.source_files[hash(str(time.time())) % len(self.source_files)]
                mod = self.propose_modification(target, self._random_mutation)
                if mod:
                    mod.phi_c_after = self.test_modification(mod, sandbox=True)
                    mod.phi_c_before = self.coherence.measure()
                    candidates.append(mod)

            # Selecionar top candidates por Φ_C
            candidates.sort(key=lambda m: m.phi_c_after, reverse=True)
            elite = candidates[:3]

            for mod in elite:
                if mod.phi_c_after > mod.phi_c_before + 0.01:
                    if self.wisdom.decide({
                        'phi_c': mod.phi_c_after,
                        'ethics': mod.ethical_score,
                        'description': f"Auto‑evolução geração {gen}"
                    }):
                        self.apply_modification(mod)
                        mod.justification = f"Aprovado por Ω: ΔΦ_C = {mod.phi_c_after - mod.phi_c_before:.4f}"
                        successful.append(mod)

            # Registrar geração no ledger
            self.ledger.record("auto_evolution_generation", {
                'generation': gen,
                'candidates': len(candidates),
                'elite_applied': len([m for m in elite if m.applied]),
                'avg_phi_improvement': sum(m.phi_c_after - m.phi_c_before for m in elite) / len(elite) if elite else 0
            })

        return successful

    def _random_mutation(self, tree: ast.AST) -> ast.AST:
        """Aplica uma mutação aleatória ao AST."""
        new_node = ast.Expr(
            value=ast.Call(
                func=ast.Name(id='_log_coherence', ctx=ast.Load()),
                args=[ast.Constant(value=f"Φ_C: {self.coherence.measure():.3f}")],
                keywords=[]
            )
        )
        if hasattr(tree, 'body') and isinstance(tree.body, list):
            tree.body.insert(0, new_node)
        return tree

class ASTPreservingMutator(ast.NodeTransformer):
    """
    Mutador AST que preserva formatação original via comentários
    e fallback para diff aplicável.
    """
    def __init__(self):
        self._modifications = []

    def propose_insertion(self, target_line: int, code_snippet: str):
        """Registra inserção sem modificar AST diretamente."""
        self._modifications.append({
            'type': 'insert',
            'line': target_line,
            'code': code_snippet
        })

    def generate_diff(self, original_source: str) -> str:
        """Gera diff unificado a partir das modificações registradas."""
        import difflib
        lines = original_source.splitlines(keepends=True)
        modified_lines = lines.copy()

        for mod in sorted(self._modifications, key=lambda m: m['line'], reverse=True):
            indent = self._detect_indent(lines, mod['line'])
            snippet = '\n'.join(indent + l for l in mod['code'].splitlines())
            modified_lines.insert(mod['line'], snippet + '\n')

        return ''.join(difflib.unified_diff(
            lines, modified_lines,
            fromfile='original', tofile='modified'
        ))

    def _detect_indent(self, lines: list, line_num: int) -> str:
        """Detecta indentação do contexto."""
        for i in range(min(line_num, len(lines) - 1), max(0, line_num - 5), -1):
            stripped = lines[i]
            if stripped.strip() and not stripped.strip().startswith('#'):
                return stripped[:len(stripped) - len(stripped.lstrip())]
        return '    '

import multiprocessing as mp

def _evaluate_in_isolated_process(modified_code: str, timeout: float = 30.0) -> float:
    """
    Avalia modificação em processo completamente isolado.
    Usa multiprocessing para garantir separação de memória.
    """
    def _worker(code: str, result_queue: mp.Queue):
        try:
            # Ambiente limpo — sem importações herdadas
            import importlib
            import types
            clean_globals = {
                '__builtins__': __builtins__,
                '__name__': '__sandbox__',
                '__file__': '<sandbox>',
            }
            exec(code, clean_globals)

            # Tentar extrair Φ_C do namespace sandbox
            phi_c = clean_globals.get('computed_phi_c', 0.5)
            result_queue.put({'success': True, 'phi_c': float(phi_c)})
        except Exception as e:
            result_queue.put({'success': False, 'error': str(e)})

    ctx = mp.get_context('spawn')  # ← spawn (não fork) para isolamento total
    queue = ctx.Queue()
    proc = ctx.Process(target=_worker, args=(modified_code, queue))
    proc.start()
    proc.join(timeout=timeout)

    if proc.is_alive():
        proc.terminate()
        proc.join()
        return 0.0  # Timeout = falha

    try:
        result = queue.get_nowait()
        return result.get('phi_c', 0.0) if result.get('success') else 0.0
    except:
        return 0.0

class SemanticMutator(ast.NodeTransformer):
    """Mutações AST com significado potencial."""

    MUTATION_TYPES = [
        'optimize_hyperparam',
        'add_regularization',
        'swap_activation',
        'adjust_learning_rate',
        'restructure_branch',
    ]

    def __init__(self, rng: np.random.Generator):
        self.rng = rng
        self.mutation_applied = None

    def mutate(self, tree: ast.AST) -> ast.AST:
        mutation = self.rng.choice(self.MUTATION_TYPES)
        self.mutation_applied = mutation

        if mutation == 'adjust_learning_rate':
            return self._mutate_learning_rate(tree)
        elif mutation == 'add_regularization':
            return self._mutate_add_regularization(tree)
        # ... outras mutações
        return tree

    def _mutate_learning_rate(self, tree: ast.AST) -> ast.AST:
        """Encontra e modifica learning_rate em assignments."""
        class LRMutator(ast.NodeTransformer):
            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name) and 'lr' in target.id.lower():
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, (int, float)):
                            new_val = node.value.value * np.random.uniform(0.8, 1.2)
                            node.value = ast.Constant(value=round(new_val, 8))
                    elif isinstance(target, ast.Name) and 'eta' in target.id.lower():
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, (int, float)):
                            new_val = node.value.value * np.random.uniform(0.9, 1.1)
                            node.value = ast.Constant(value=round(new_val, 8))
                return node
        return LRMutator().visit(tree)
