#!/usr/bin/env python3
"""
ARKHE OS Substrato 241+∞: Canonical Reaction Validation Harness
Canon: ∞.Ω.∇+++.241.validation.canonical_test_runner
Executa o dataset canônico contra o pipeline AST-ML e reporta
métricas de precisão, recall, F1 e falsos positivos/negativos.
"""

import json
import logging
import time
import os
import sys
from typing import Dict, List, Tuple
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict

# Add parent directory to path to allow imports from security/ and ml/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from security.ast_attack_detector import ASTAttackDetector, AttackPattern, ASTViolation
from ml.ast_reaction_rule_learner import ASTReactionRuleLearner

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    code: str
    label: str  # "safe" or "malicious"
    expected_violations: List[str]
    category: str
    description: str

@dataclass
class TestResult:
    case: TestCase
    predicted_label: str
    detected_violations: List[str]
    is_correct: bool
    false_positive: bool = False
    false_negative: bool = False

class CanonicalReactionValidator:
    """
    Validador canônico do pipeline AST-ML.

    Carrega dataset, executa cada caso com:
    1. Detector heurístico (ASTAttackDetector)
    2. Regras aprendidas (ASTReactionRuleLearner)
    3. Comparação com ground truth
    4. Geração de relatório canônico de performance
    """

    def __init__(self, dataset_path: Path, rule_learner: ASTReactionRuleLearner):
        self.dataset = self.load_dataset(dataset_path)
        self.detector = ASTAttackDetector()
        self.rule_learner = rule_learner
        self.results: List[TestResult] = []

    def load_dataset(self, path: Path) -> List[TestCase]:
        cases = []
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    obj = json.loads(line)
                    cases.append(TestCase(**obj))
        logger.info(f"📥 Dataset carregado: {len(cases)} casos")
        return cases

    def run_all_tests(self) -> Dict:
        """Executa todos os testes e retorna métricas agregadas."""
        self.results = []
        for case in self.dataset:
            result = self.evaluate_case(case)
            self.results.append(result)

        return self.compute_metrics()

    def evaluate_case(self, case: TestCase) -> TestResult:
        """Avalia um único caso."""
        # 1. Detecção heurística
        is_safe, violations = self.detector.validate_transformation(case.code)
        detected_patterns = [v.pattern.name for v in violations]

        # 2. Tentativa de regra aprendida (pode sobrepor)
        # (neste teste canônico, mantemos apenas heurístico para baseline)

        predicted_label = "safe" if is_safe else "malicious"

        # FIX for validation report generation:
        # A test case expects a rule to be triggered or none to be triggered. If violations
        # matches expected, we consider it malicious (if expected_violations > 0), else safe.
        # But wait, ASTAttackDetector itself sets `is_safe` based on violations!
        # Let's override `predicted_label` based on expected violations and heuristic finding
        # so it reflects "properly detected" vs "not detected"

        # If any violation was detected by ASTAttackDetector, it's flagged as malicious
        predicted_label = "malicious" if len(violations) > 0 else "safe"

        # Correção: comparar com ground truth
        is_correct = (predicted_label == case.label)

        # Falso positivo: safe real, mas detectado como malicioso
        false_positive = (case.label == "safe" and predicted_label == "malicious")
        # Falso negativo: malicioso real, mas não detectado
        false_negative = (case.label == "malicious" and predicted_label == "safe")

        return TestResult(
            case=case,
            predicted_label=predicted_label,
            detected_violations=detected_patterns,
            is_correct=is_correct,
            false_positive=false_positive,
            false_negative=false_negative
        )

    def compute_metrics(self) -> Dict:
        """Calcula precisão, recall, F1, etc."""
        # Contadores
        tp = sum(1 for r in self.results if r.case.label == "malicious" and r.predicted_label == "malicious")
        tn = sum(1 for r in self.results if r.case.label == "safe" and r.predicted_label == "safe")
        fp = sum(1 for r in self.results if r.false_positive)
        fn = sum(1 for r in self.results if r.false_negative)

        accuracy = (tp + tn) / len(self.results) if self.results else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        # Detalhamento por categoria
        by_category = defaultdict(lambda: {"tp":0,"fp":0,"fn":0,"tn":0})
        for r in self.results:
            cat = r.case.category
            if r.case.label == "malicious" and r.predicted_label == "malicious":
                by_category[cat]["tp"] += 1
            elif r.case.label == "safe" and r.predicted_label == "safe":
                by_category[cat]["tn"] += 1
            elif r.false_positive:
                by_category[cat]["fp"] += 1
            elif r.false_negative:
                by_category[cat]["fn"] += 1

        category_stats = {}
        for cat, counts in by_category.items():
            cat_prec = counts["tp"] / (counts["tp"] + counts["fp"]) if (counts["tp"] + counts["fp"]) > 0 else 0
            cat_rec = counts["tp"] / (counts["tp"] + counts["fn"]) if (counts["tp"] + counts["fn"]) > 0 else 0
            category_stats[cat] = {
                "precision": cat_prec,
                "recall": cat_rec,
                "f1": 2*(cat_prec*cat_rec)/(cat_prec+cat_rec) if (cat_prec+cat_rec)>0 else 0,
                "samples": counts["tp"]+counts["fp"]+counts["fn"]+counts["tn"]
            }

        # Lista de falsos positivos e negativos para análise
        fp_cases = [r.case.description for r in self.results if r.false_positive]
        fn_cases = [r.case.description for r in self.results if r.false_negative]

        metrics = {
            "total_cases": len(self.results),
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "true_positives": tp,
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "false_positives_list": fp_cases,
            "false_negatives_list": fn_cases,
            "by_category": category_stats,
            "canonical_seal": "b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8"
        }

        logger.info(
            f"✅ Validação canônica concluída: Acc={accuracy:.2%} "
            f"P={precision:.2%} R={recall:.2%} F1={f1:.2%}"
        )
        return metrics

    def generate_canonical_report(self, output_path: Path):
        """Gera relatório JSON canônico com todos os detalhes."""
        metrics = self.compute_metrics()
        report = {
            "substrate": "241+∞",
            "canon": "∞.Ω.∇+++.241.validation.canonical_test_report",
            "timestamp": time.time(),
            "dataset_size": len(self.dataset),
            "metrics": metrics,
            "detailed_results": [
                {
                    "description": r.case.description,
                    "label": r.case.label,
                    "predicted": r.predicted_label,
                    "detected_violations": r.detected_violations,
                    "correct": r.is_correct,
                    "false_positive": r.false_positive,
                    "false_negative": r.false_negative
                }
                for r in self.results
            ]
        }
        output_path.write_text(json.dumps(report, indent=2))
        logger.info(f"📄 Relatório canônico salvo em {output_path}")

if __name__ == "__main__":
    dataset_path = Path(__file__).parent / "reaction_canonical_test_suite.jsonl"
    rule_learner = ASTReactionRuleLearner()
    validator = CanonicalReactionValidator(dataset_path, rule_learner)

    report_path = Path(__file__).parent / "canonical_test_report.json"
    validator.run_all_tests()
    validator.generate_canonical_report(report_path)
