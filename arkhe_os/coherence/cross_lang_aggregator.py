# arkhe_os/coherence/cross_lang_aggregator.py
"""
Substrato 277: Agregador de Coerência Cross-Linguagem
Normaliza e agrega métricas de teste de múltiplos ecossistemas.
"""
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Protocol
from datetime import datetime, timezone
from enum import Enum

class LanguageEcosystem(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    RUST = "rust"
    GO = "go"
    UNKNOWN = "unknown"

@dataclass
class NormalizedTestMetric:
    """Formato canônico para métricas de teste, independente de linguagem."""
    ecosystem: LanguageEcosystem
    test_id: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    duration_ms: float
    file_path: str
    line_number: Optional[int]
    error_message: Optional[str]
    substrate_id: Optional[str]
    coherence_score: float  # Φ_C individual do teste
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self) -> Dict:
        return {
            "ecosystem": self.ecosystem.value,
            "test_id": self.test_id,
            "status": self.status,
            "duration_ms": round(self.duration_ms, 2),
            "file_path": self.file_path,
            "line": self.line_number,
            "error": self.error_message[:500] if self.error_message else None,
            "substrate_id": self.substrate_id,
            "phi_c": round(self.coherence_score, 4),
            "metadata": self.metadata,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

class TestMetricAdapter(Protocol):
    """Interface para adapters de ecossistemas de teste."""
    def parse(self, raw_output: str, source_dir: Path) -> List[NormalizedTestMetric]:
        """Converte output bruto do runner de testes para formato canônico."""
        ...

class JestAdapter:
    """Adapter para output do Jest (TypeScript/JavaScript)."""

    def parse(self, raw_output: str, source_dir: Path) -> List[NormalizedTestMetric]:
        metrics = []
        try:
            # Jest pode outputar JSON com --json flag
            report = json.loads(raw_output)
            for test_result in report.get("testResults", []):
                file_path = test_result.get("name", "")
                for assertion in test_result.get("assertionResults", []):
                    status_map = {"passed": "passed", "failed": "failed", "pending": "skipped"}
                    metrics.append(NormalizedTestMetric(
                        ecosystem=LanguageEcosystem.TYPESCRIPT,
                        test_id=f"{file_path}::{assertion.get('title')}",
                        status=status_map.get(assertion.get("status"), "unknown"),
                        duration_ms=assertion.get("duration", 0),
                        file_path=str(source_dir / file_path),
                        line_number=assertion.get("location", {}).get("line"),
                        error_message=assertion.get("failureMessages", [""])[0] if assertion.get("status") == "failed" else None,
                        substrate_id=self._extract_substrate_id(file_path),
                        coherence_score=self._compute_coherence(assertion),
                        metadata={"jest_version": report.get("version")},
                    ))
        except json.JSONDecodeError:
            # Fallback: parse textual output
            pass
        return metrics

    def _extract_substrate_id(self, file_path: str) -> Optional[str]:
        # Extrai ID de substrato do caminho (ex: substrates/273-*/ → "273")
        import re
        match = re.search(r'substrates/(\d+)-', file_path)
        return match.group(1) if match else None

    def _compute_coherence(self, assertion: Dict) -> float:
        # Heurística simples: passed=1.0, failed=0.0, skipped=0.5
        status = assertion.get("status")
        if status == "passed":
            return 1.0
        elif status == "failed":
            return 0.0
        return 0.5

class CargoAdapter:
    """Adapter para output do Cargo test (Rust)."""

    def parse(self, raw_output: str, source_dir: Path) -> List[NormalizedTestMetric]:
        metrics = []
        # Parse output do cargo test --message-format=json
        for line in raw_output.strip().split('\n'):
            if not line.strip():
                continue
            try:
                msg = json.loads(line)
                if msg.get("reason") != "test":
                    continue
                metrics.append(NormalizedTestMetric(
                    ecosystem=LanguageEcosystem.RUST,
                    test_id=f"{msg.get('package')}::{msg.get('name')}",
                    status="passed" if msg.get("success") else "failed",
                    duration_ms=msg.get("exec_time", 0) * 1000,
                    file_path=str(source_dir / msg.get("package", "")),
                    line_number=None,  # Cargo não fornece linha por default
                    error_message=msg.get("stdout") if not msg.get("success") else None,
                    substrate_id=self._extract_substrate_id(msg.get("package", "")),
                    coherence_score=1.0 if msg.get("success") else 0.0,
                    metadata={"cargo_version": msg.get("package_version")},
                ))
            except json.JSONDecodeError:
                continue
        return metrics

    def _extract_substrate_id(self, package_name: str) -> Optional[str]:
        # Assume convenção: arkhe-substrate-273 → "273"
        import re
        match = re.search(r'substrate-(\d+)', package_name)
        return match.group(1) if match else None

class GoTestAdapter:
    """Adapter para output do go test -json."""

    def parse(self, raw_output: str, source_dir: Path) -> List[NormalizedTestMetric]:
        metrics = []
        current_test = None
        for line in raw_output.strip().split('\n'):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                action = event.get("Action")
                if action == "run":
                    current_test = event.get("Test")
                elif action in ("pass", "fail", "skip"):
                    if current_test:
                        metrics.append(NormalizedTestMetric(
                            ecosystem=LanguageEcosystem.GO,
                            test_id=f"{event.get('Package')}::{current_test}",
                            status=action,
                            duration_ms=event.get("Elapsed", 0) * 1000,
                            file_path=str(source_dir / event.get("Package", "").replace("github.com/arkhe-os/", "")),
                            line_number=None,
                            error_message=event.get("Output") if action == "fail" else None,
                            substrate_id=self._extract_substrate_id(event.get("Package", "")),
                            coherence_score=1.0 if action == "pass" else (0.0 if action == "fail" else 0.5),
                            metadata={"package": event.get("Package")},
                        ))
                        current_test = None
            except json.JSONDecodeError:
                continue
        return metrics

    def _extract_substrate_id(self, package_path: str) -> Optional[str]:
        import re
        match = re.search(r'substrate(\d+)', package_path)
        return match.group(1) if match else None

class CrossLangCoherenceAggregator:
    """Agrega métricas de múltiplos ecossistemas em campo de coerência unificado."""

    def __init__(self, node_id: str, hypermesh_endpoint: str):
        self.node_id = node_id
        self.endpoint = hypermesh_endpoint
        self.adapters: Dict[LanguageEcosystem, TestMetricAdapter] = {
            LanguageEcosystem.PYTHON: None,  # pytest-arkhe já fornece formato canônico
            LanguageEcosystem.TYPESCRIPT: JestAdapter(),
            LanguageEcosystem.RUST: CargoAdapter(),
            LanguageEcosystem.GO: GoTestAdapter(),
        }
        self._collected: List[NormalizedTestMetric] = []

    def ingest(self, ecosystem: LanguageEcosystem, raw_output: str, source_dir: Path):
        """Ingeste output bruto de um runner de testes."""
        adapter = self.adapters.get(ecosystem)
        if adapter:
            metrics = adapter.parse(raw_output, source_dir)
            self._collected.extend(metrics)
        elif ecosystem == LanguageEcosystem.PYTHON:
            # pytest-arkhe já emite formato canônico via JSON
            for item in json.loads(raw_output).get("metrics", []):
                self._collected.append(NormalizedTestMetric(**item))

    def aggregate(self) -> Dict[str, Any]:
        """Calcula métricas agregadas por ecossistema e global."""
        by_ecosystem = {}
        for eco in LanguageEcosystem:
            eco_metrics = [m for m in self._collected if m.ecosystem == eco]
            if eco_metrics:
                passed = sum(1 for m in eco_metrics if m.status == "passed")
                total = len(eco_metrics)
                avg_phi = sum(m.coherence_score for m in eco_metrics) / total
                by_ecosystem[eco.value] = {
                    "total_tests": total,
                    "passed": passed,
                    "pass_rate": passed / total if total > 0 else 0,
                    "avg_phi_c": round(avg_phi, 4),
                    "total_duration_ms": sum(m.duration_ms for m in eco_metrics),
                }

        # Métricas globais
        all_phi = [m.coherence_score for m in self._collected]
        global_phi = sum(all_phi) / len(all_phi) if all_phi else 0.0

        # Delta em relação ao baseline (placeholder)
        baseline = 0.85
        delta_phi = global_phi - baseline

        return {
            "version": "v∞.Ω.∇.CROSS-LANG.1",
            "node_id": self.node_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_metrics": len(self._collected),
            "global_phi_c": round(global_phi, 4),
            "delta_phi_c": round(delta_phi, 4),
            "mercy_gap_valid": 0.04 <= abs(delta_phi) <= 0.10 or abs(delta_phi) < 0.01,
            "by_ecosystem": by_ecosystem,
            "findings": [
                m.to_canonical_dict() for m in self._collected if m.status in ("failed", "error")
            ],
        }

    def submit_to_hypermesh(self) -> Dict[str, Any]:
        """Submete relatório agregado ao canal de coerência."""
        report = self.aggregate()
        # Em produção: enviar via qhttp_client
        # Aqui: salvar localmente para demonstração
        output_dir = Path(".arkhe/cross_lang_reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        report_file = output_dir / f"coherence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.write_text(json.dumps(report, indent=2, default=str))

        print(f"\n🌐 Cross-Lang Coherence Report: {report_file}")
        print(f"   Global Φ_C: {report['global_phi_c']:.4f} | ΔΦ_C: {report['delta_phi_c']:+.4f}")
        for eco, stats in report['by_ecosystem'].items():
            print(f"   • {eco}: Φ_C={stats['avg_phi_c']:.3f} ({stats['passed']}/{stats['total_tests']} passed)")

        return {"success": True, "report_path": str(report_file)}
