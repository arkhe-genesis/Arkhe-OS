# arkhe_os/testing/coherence_aggregator.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import time
import numpy as np
from collections import defaultdict

@dataclass
class TestFrameworkReport:
    framework: str          # "pytest", "jest", "cargo-test", "go-test"
    language: str           # "python", "typescript", "rust", "go"
    node_id: str
    project: str
    commit_hash: str
    metrics: Dict
    timestamp: float

class CrossLanguageCoherenceAggregator:
    """Agrega métricas de teste de múltiplos frameworks em Φ_C unificado."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.framework_reports: Dict[str, List[TestFrameworkReport]] = defaultdict(list)
        self.global_phi_c: float = 0.85  # baseline
        self.weights = {
            "python": 0.35,
            "typescript": 0.35,
            "rust": 0.20,
            "go": 0.10,
        }

    def ingest_report(self, report: TestFrameworkReport) -> Dict:
        """Ingere relatório de qualquer framework e recalcula coerência."""
        self.framework_reports[report.framework].append(report)

        # Calcular Φ_C por framework
        framework_phi = {}
        for fw, reports in self.framework_reports.items():
            if reports:
                avg_pass_rate = np.mean([r.metrics.get("pass_rate", 0.0) for r in reports])
                avg_coverage = np.mean([r.metrics.get("coverage_percent", 0.0) for r in reports])
                framework_phi[fw] = (avg_pass_rate * 0.6 + (avg_coverage / 100.0) * 0.4)

        # Calcular Φ_C global ponderado por linguagem
        total_weight = 0.0
        weighted_phi = 0.0
        for fw, phi in framework_phi.items():
            lang = self._framework_to_language(fw)
            weight = self.weights.get(lang, 0.1)
            weighted_phi += phi * weight
            total_weight += weight

        self.global_phi_c = weighted_phi / total_weight if total_weight > 0 else 0.85

        return {
            "project_id": self.project_id,
            "global_phi_c": round(self.global_phi_c, 4),
            "by_framework": {fw: round(phi, 4) for fw, phi in framework_phi.items()},
            "framework_count": len(framework_phi),
            "timestamp": int(time.time()),
        }

    def _framework_to_language(self, framework: str) -> str:
        mapping = {
            "pytest": "python", "jest": "typescript",
            "cargo-test": "rust", "go-test": "go"
        }
        return mapping.get(framework, "unknown")
