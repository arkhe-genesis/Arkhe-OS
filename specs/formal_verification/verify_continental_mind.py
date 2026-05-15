#!/usr/bin/env python3
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class VerificationResult:
    constraint_name: str
    status: str
    details: str
    code_location: Optional[str] = None
    spec_location: Optional[str] = None

class SysMLCodeVerifier:
    def __init__(self, spec_path: str, code_base_path: str):
        self.spec_path = Path(spec_path)
        self.code_base_path = Path(code_base_path)
        self._spec_constraints: Dict[str, Dict] = {}
        self._code_implementations: Dict[str, List[str]] = {}

    def parse_sysml_spec(self) -> bool:
        if not self.spec_path.exists():
            return False
        content = self.spec_path.read_text()
        import re
        constraints = re.findall(r'constraint\s+(\w+):\s*([^}]+)', content)
        for name, expression in constraints:
            self._spec_constraints[name] = {"expression": expression.strip(), "location": f"{self.spec_path.name}"}
        return True

    def analyze_code_base(self) -> bool:
        if not self.code_base_path.exists():
            return False
        py_files = list(self.code_base_path.rglob("*.py"))
        for py_file in py_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        for constraint_name in self._spec_constraints:
                            if constraint_name.lower() in func_name.lower():
                                location = f"{py_file.name}:{node.lineno}"
                                if constraint_name not in self._code_implementations:
                                    self._code_implementations[constraint_name] = []
                                self._code_implementations[constraint_name].append(location)
            except SyntaxError:
                continue
        return True

    def verify_constraints(self) -> List[VerificationResult]:
        results = []
        for constraint_name, spec_info in self._spec_constraints.items():
            implementations = self._code_implementations.get(constraint_name, [])
            if not implementations:
                results.append(VerificationResult(constraint_name, "FAIL", f"Constraint '{constraint_name}' especificada mas não implementada", None, spec_info["location"]))
                continue
            expression = spec_info["expression"]
            if "phi_c" in expression.lower() and ">=" in expression:
                threshold_verified = self._verify_phi_c_threshold(expression, implementations)
                status = "PASS" if threshold_verified else "WARNING"
                results.append(VerificationResult(constraint_name, status, f"Threshold Φ_C: {expression}" + (" ✓" if threshold_verified else " ⚠️ verificação parcial"), implementations[0], spec_info["location"]))
            elif "privacy" in expression.lower() or "no_raw_data" in expression.lower():
                privacy_verified = self._verify_privacy_constraint(expression, implementations)
                status = "PASS" if privacy_verified else "WARNING"
                results.append(VerificationResult(constraint_name, status, f"Privacidade: {expression}" + (" ✓" if privacy_verified else " ⚠️ verificação parcial"), implementations[0], spec_info["location"]))
            else:
                results.append(VerificationResult(constraint_name, "PASS", f"Implementação encontrada em {len(implementations)} local(is)", implementations[0], spec_info["location"]))
        return results

    def _verify_phi_c_threshold(self, expression: str, implementations: List[str]) -> bool:
        import re
        match = re.search(r'>=\s*([\d.]+)', expression)
        if not match: return False
        threshold = float(match.group(1))
        for impl_loc in implementations:
            try:
                content = Path(impl_loc.split(":")[0]).read_text()
                if f">= {threshold}" in content or f">= {threshold:.4f}" in content: return True
            except: continue
        return False

    def _verify_privacy_constraint(self, expression: str, implementations: List[str]) -> bool:
        dp_keywords = ["apply_dp", "laplace", "gaussian", "opendp", "epsilon", "delta"]
        for impl_loc in implementations:
            try:
                content = Path(impl_loc.split(":")[0]).read_text().lower()
                if any(kw in content for kw in dp_keywords): return True
            except: continue
        return False

    def generate_verification_report(self, results: List[VerificationResult]) -> Dict:
        summary = {"total_constraints": len(self._spec_constraints), "verified": sum(1 for r in results if r.status == "PASS"), "warnings": sum(1 for r in results if r.status == "WARNING"), "failures": sum(1 for r in results if r.status == "FAIL"), "timestamp": datetime.utcnow().isoformat()}
        return {"summary": summary, "details": [{"constraint": r.constraint_name, "status": r.status, "details": r.details, "spec": r.spec_location, "code": r.code_location} for r in results]}
