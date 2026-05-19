#!/usr/bin/env python3
"""
ARKHE OS Substrate 254: Constitutional Linter Engine
Canon: ∞.Ω.∇+++.254.constitutional_linter

Automatic verification of P1-P7 constitutional compliance in source code.
Supports Python, Rust, Solidity, Lean, and other canonical languages.
"""

import ast
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import libcst  # For Python AST with comments preservation

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# TIPOS CANÔNICOS DO LINTER
# =============================================================================

class ConstitutionalPrinciple(Enum):
    """Princípios constitucionais P1-P7."""
    P1_VERIFICACAO_FORMAL = "P1"
    P2_REDUNDANCIA_INTENCOES = "P2"
    P3_GAP_SOBERANO = "P3"
    P4_FEDERACAO_CROSS_PLATFORM = "P4"
    P5_APRENDIZADO_CANONICO = "P5"
    P6_TRANSPARENCIA_AUDITAVEL = "P6"
    P7_ENERGIA_RECURSO = "P7"

class ViolationSeverity(Enum):
    """Severidade de violação constitucional."""
    ERROR = "error"      # Blocks commit/deploy
    WARNING = "warning"  # Requires review
    INFO = "info"        # Suggestion for improvement

@dataclass
class ConstitutionalViolation:
    """Representação de uma violação constitucional detectada."""
    principle: ConstitutionalPrinciple
    severity: ViolationSeverity
    file_path: str
    line: int
    column: int
    message: str
    code_snippet: str
    suggested_fix: Optional[str]
    phi_c_impact: float  # Estimated Φ_C degradation (0.0-0.1)

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "principle": self.principle.value,
            "severity": self.severity.value
        }

@dataclass
class LinterReport:
    """Relatório consolidado de análise constitucional."""
    file_path: str
    language: str
    total_checks: int
    violations: List[ConstitutionalViolation]
    passed_checks: int
    constitutional_compliance: bool
    estimated_phi_c_impact: float
    temporal_chain_seal: Optional[str]
    analysis_timestamp: float

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "violations": [v.to_dict() for v in self.violations]
        }

# =============================================================================
# REGRAS CONSTITUCIONAIS POR PRINCÍPIO
# =============================================================================

class P1FormalVerificationRule:
    """P1: Verificação Formal — Every critical function must have formal spec."""

    CRITICAL_DECORATORS = ["@critical", "@verified", "@formal_spec"]
    SPEC_KEYWORDS = ["spec:", "lemma", "theorem", "proof", "ensures", "requires"]

    @staticmethod
    def check_python(node: libcst.CSTNode, file_content: str) -> List[ConstitutionalViolation]:
        """Check Python code for P1 compliance."""
        violations = []

        # Find function definitions
        class FunctionVisitor(libcst.CSTVisitor):
            def __init__(self, content: str):
                self.content = content
                self.violations = []

            def visit_FunctionDef(self, node: libcst.FunctionDef) -> None:
                # Check if function is marked critical
                is_critical = any(
                    hasattr(dec.decorator, 'value') and
                    dec.decorator.value in P1FormalVerificationRule.CRITICAL_DECORATORS
                    for dec in node.decorators
                )

                if is_critical:
                    # Check for formal spec in docstring or comments
                    has_spec = False
                    if node.docs and any(kw in node.docs.value for kw in P1FormalVerificationRule.SPEC_KEYWORDS):
                        has_spec = True

                    # Check for linked Lean/Coq proof file
                    proof_file = f"{node.name.value}.lean"
                    if Path(proof_file).exists() or Path(f"proofs/{proof_file}").exists():
                        has_spec = True

                    if not has_spec:
                        violations.append(ConstitutionalViolation(
                            principle=ConstitutionalPrinciple.P1_VERIFICACAO_FORMAL,
                            severity=ViolationSeverity.ERROR,
                            file_path="<current>",
                            line=node.lines[0].start_line if getattr(node, 'lines', None) else 0,
                            column=node.lines[0].start_column if getattr(node, 'lines', None) else 0,
                            message=f"Critical function '{node.name.value}' lacks formal specification",
                            code_snippet=libcst.Module([]).code_for_node(node)[:100],
                            suggested_fix=f"Add formal spec docstring or link proof file: {proof_file}",
                            phi_c_impact=0.08
                        ))

        visitor = FunctionVisitor(file_content)
        node.visit(visitor)
        return visitor.violations

class P2RedundancyRule:
    """P2: Redundância de Intenções — Critical logic in ≥3 languages."""

    CRITICAL_PATTERNS = [
        r"def\s+(process_payment|verify_signature|anchor_seal)",  # Python
        r"fn\s+(process_payment|verify_signature|anchor_seal)",   # Rust
        r"function\s+(processPayment|verifySignature|anchorSeal)", # Solidity
    ]

    @staticmethod
    def check_repository(repo_path: str) -> List[ConstitutionalViolation]:
        """Check entire repository for P2 compliance."""
        violations = []

        # Find critical functions across languages
        critical_functions: Dict[str, Set[str]] = {}  # function_name -> set of languages

        for pattern in P2RedundancyRule.CRITICAL_PATTERNS:
            for file_path in Path(repo_path).rglob("*"):
                if file_path.suffix in [".py", ".rs", ".sol"]:
                    try:
                        content = file_path.read_text()
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            func_name = match.group(1)
                            lang = file_path.suffix[1:]
                            if func_name not in critical_functions:
                                critical_functions[func_name] = set()
                            critical_functions[func_name].add(lang)
                    except Exception:
                        continue

        # Check each critical function has ≥3 language implementations
        for func_name, langs in critical_functions.items():
            if len(langs) < 3:
                violations.append(ConstitutionalViolation(
                    principle=ConstitutionalPrinciple.P2_REDUNDANCIA_INTENCOES,
                    severity=ViolationSeverity.WARNING,
                    file_path="repository",
                    line=0,
                    column=0,
                    message=f"Critical function '{func_name}' implemented in {len(langs)}/3 languages: {langs}",
                    code_snippet=f"function: {func_name}",
                    suggested_fix=f"Implement '{func_name}' in missing languages to reach 3-language redundancy",
                    phi_c_impact=0.05
                ))

        return violations

class P3SovereignGapRule:
    """P3: Gap Soberano — Φ_C < 1.0 enforcement."""

    @staticmethod
    def check_phi_c_enforcement(code: str, language: str) -> List[ConstitutionalViolation]:
        """Check code enforces Φ_C < 1.0."""
        violations = []

        # Patterns that should enforce Φ_C cap
        phi_c_patterns = [
            r"phi_c\s*[<>=]\s*1\.0",  # Direct comparison
            r"PHI_C_CAP\s*=\s*1\.0",  # Constant definition
            r"sovereign_gap",          # Gap-related code
        ]

        has_enforcement = any(re.search(p, code, re.IGNORECASE) for p in phi_c_patterns)

        # Check for novelty injection (required for gap preservation)
        novelty_patterns = [r"novelty", r"residual_flux", r"randomness", r"entropy"]
        has_novelty = any(re.search(p, code, re.IGNORECASE) for p in novelty_patterns)

        if not has_enforcement or not has_novelty:
            violations.append(ConstitutionalViolation(
                principle=ConstitutionalPrinciple.P3_GAP_SOBERANO,
                severity=ViolationSeverity.ERROR if not has_enforcement else ViolationSeverity.WARNING,
                file_path="<current>",
                line=0,
                column=0,
                message="Code must enforce Φ_C < 1.0 and include novelty injection",
                code_snippet=code[:100],
                suggested_fix="Add phi_c < 1.0 check and residual_flux novelty generator",
                phi_c_impact=0.10 if not has_enforcement else 0.03
            ))

        return violations

# =============================================================================
# LINTER ENGINE PRINCIPAL
# =============================================================================

class ConstitutionalLinter:
    """Engine principal do linter constitucional."""

    SUPPORTED_LANGUAGES = {
        ".py": "python",
        ".rs": "rust",
        ".sol": "solidity",
        ".lean": "lean",
        ".coq": "coq",
    }

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.rules = {
            ConstitutionalPrinciple.P1_VERIFICACAO_FORMAL: P1FormalVerificationRule(),
            ConstitutionalPrinciple.P2_REDUNDANCIA_INTENCOES: P2RedundancyRule(),
            ConstitutionalPrinciple.P3_GAP_SOBERANO: P3SovereignGapRule(),
            # P4-P7 rules would be implemented similarly
        }

    def lint_file(self, file_path: str) -> LinterReport:
        """Executa análise constitucional em um arquivo."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        language = self.SUPPORTED_LANGUAGES.get(path.suffix, "unknown")
        content = path.read_text()

        violations = []
        checks_performed = 0

        # Execute applicable rules
        if language == "python" and ConstitutionalPrinciple.P1_VERIFICACAO_FORMAL in self.rules:
            try:
                cst_tree = libcst.parse_module(content)
                violations.extend(self.rules[ConstitutionalPrinciple.P1_VERIFICACAO_FORMAL].check_python(cst_tree, content))
                checks_performed += 1
            except Exception as e:
                logger.warning(f"⚠️ P1 check failed for {file_path}: {e}")

        # P3 check for all languages
        if ConstitutionalPrinciple.P3_GAP_SOBERANO in self.rules:
            violations.extend(self.rules[ConstitutionalPrinciple.P3_GAP_SOBERANO].check_phi_c_enforcement(content, language))
            checks_performed += 1

        # P2 check at repository level (skip for single file)
        # Would be called separately via lint_repository()

        # Calculate metrics
        passed_checks = checks_performed - len(set(v.principle for v in violations))
        estimated_phi_c_impact = sum(v.phi_c_impact for v in violations)
        constitutional_compliance = all(v.severity != ViolationSeverity.ERROR for v in violations)

        # Generate temporal seal
        report_payload = {
            "file": str(path),
            "language": language,
            "violations_count": len(violations),
            "compliance": constitutional_compliance,
            "timestamp": time.time()
        }
        temporal_seal = hashlib.sha3_256(
            json.dumps(report_payload, sort_keys=True).encode()
        ).hexdigest()

        return LinterReport(
            file_path=str(path),
            language=language,
            total_checks=checks_performed,
            violations=violations,
            passed_checks=passed_checks,
            constitutional_compliance=constitutional_compliance,
            estimated_phi_c_impact=estimated_phi_c_impact,
            temporal_chain_seal=temporal_seal,
            analysis_timestamp=time.time()
        )

    def lint_repository(self) -> List[LinterReport]:
        """Executa análise constitucional em todo o repositório."""
        reports = []

        # P2 repository-level check
        p2_violations = P2RedundancyRule().check_repository(str(self.repo_path))
        if p2_violations:
            reports.append(LinterReport(
                file_path="repository",
                language="multi",
                total_checks=1,
                violations=p2_violations,
                passed_checks=0 if p2_violations else 1,
                constitutional_compliance=len([v for v in p2_violations if v.severity == ViolationSeverity.ERROR]) == 0,
                estimated_phi_c_impact=sum(v.phi_c_impact for v in p2_violations),
                temporal_chain_seal=hashlib.sha3_256(json.dumps({"repo": str(self.repo_path)}, sort_keys=True).encode()).hexdigest(),
                analysis_timestamp=time.time()
            ))

        # File-level checks for supported languages
        for ext in self.SUPPORTED_LANGUAGES:
            for file_path in self.repo_path.rglob(f"*{ext}"):
                # Skip vendor/node_modules/etc.
                if any(skip in str(file_path) for skip in ["node_modules", "vendor", ".git", "build"]):
                    continue
                try:
                    report = self.lint_file(str(file_path))
                    if report.violations or not report.constitutional_compliance:
                        reports.append(report)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to lint {file_path}: {e}")

        return reports

    def generate_fix_patch(self, violation: ConstitutionalViolation) -> Optional[str]:
        """Gera patch automático para corrigir violação (quando possível)."""
        if not violation.suggested_fix:
            return None

        # Auto-fix patterns (simplified examples)
        if violation.principle == ConstitutionalPrinciple.P3_GAP_SOBERANO:
            if "phi_c < 1.0" in violation.suggested_fix:
                return """
# Constitutional fix: Enforce Φ_C < 1.0
def enforce_sovereign_gap(phi_c: float) -> float:
    return min(phi_c, 0.9999)  # Hard cap preserving Gap Soberano
"""

        # For other violations, return manual guidance
        return f"# Manual fix required: {violation.suggested_fix}"

# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ARKHE Constitutional Linter")
    parser.add_argument("path", help="File or repository path to lint")
    parser.add_argument("--fix", action="store_true", help="Generate auto-fix patches")
    parser.add_argument("--output", help="Output report file (JSON)")
    parser.add_argument("--temporal-anchor", action="store_true", help="Anchor report to TemporalChain")

    args = parser.parse_args()

    linter = ConstitutionalLinter(args.path)

    if Path(args.path).is_file():
        report = linter.lint_file(args.path)
        reports = [report]
    else:
        reports = linter.lint_repository()

    # Output results
    for report in reports:
        print(f"\n📋 Constitutional Lint Report: {report.file_path}")
        print(f"   Language: {report.language}")
        print(f"   Compliance: {'✅ PASS' if report.constitutional_compliance else '❌ FAIL'}")
        print(f"   Φ_C Impact: {report.estimated_phi_c_impact:.3f}")
        print(f"   Temporal Seal: {report.temporal_chain_seal[:16]}...")

        if report.violations:
            print(f"\n   ⚠️  Violations ({len(report.violations)}):")
            for v in report.violations:
                icon = "🔴" if v.severity == ViolationSeverity.ERROR else "🟡"
                print(f"   {icon} {v.principle.value}: {v.message}")
                print(f"      {v.file_path}:{v.line}:{v.column}")
                if args.fix and v.suggested_fix:
                    patch = linter.generate_fix_patch(v)
                    if patch:
                        print(f"      💡 Auto-fix available:\n{patch}")

    # Save report
    if args.output:
        with open(args.output, 'w') as f:
            json.dump([r.to_dict() for r in reports], f, indent=2)
        print(f"\n💾 Report saved to {args.output}")

    # Anchor to TemporalChain
    if args.temporal_anchor and reports:
        for report in reports:
            if report.temporal_chain_seal:
                print(f"🔗 Anchoring to TemporalChain: {report.temporal_chain_seal[:16]}...")
                # In production: POST to TemporalChain endpoint

if __name__ == "__main__":
    main()
