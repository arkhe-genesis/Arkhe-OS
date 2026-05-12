#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag_evaluator.py — Avaliador oficial para BixoniBench
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

class Veredito(Enum):
    VERIFIED = "verified"
    REFUTED = "refuted"
    INDETERMINATE = "indeterminate"

@dataclass
class BenchmarkResult:
    case_id: str
    expected: str
    actual: str
    confidence: float
    canonical_seal: str
    status: str  # "PASS" ou "FAIL"
    execution_time_ms: float
    metadata: Dict

class BixoniBenchEvaluator:
    """Avaliador oficial do benchmark BixoniBench."""

    def __init__(self, protocol_impl):
        """
        Args:
            protocol_impl: Implementação do protocolo a ser avaliada
                          (deve ter método .verificar(query, contexto, metadados))
        """
        self.protocol = protocol_impl
        self.results: List[BenchmarkResult] = []

    def evaluate_case(self, case: Dict) -> BenchmarkResult:
        """Avalia um único caso de teste."""
        start_time = time.time()

        # Executar verificação
        result = self.protocol.verificar(
            query=case['query'],
            contexto=case.get('context', ''),
            metadados={
                'language': case.get('language'),
                'difficulty': case.get('difficulty'),
                'benchmark': 'bixonibench'
            }
        )

        execution_time = (time.time() - start_time) * 1000

        # Determinar status
        expected = case['expected']
        actual = result.veredito.value if hasattr(result.veredito, 'value') else str(result.veredito)
        passed = (expected == actual)

        # Gerar selo canônico para auditoria
        seal_payload = f"{case['id']}:{expected}:{actual}:{result.confianca}:{execution_time}"
        canonical_seal = hashlib.sha3_256(seal_payload.encode()).hexdigest()[:16]

        return BenchmarkResult(
            case_id=case['id'],
            expected=expected,
            actual=actual,
            confidence=result.confianca,
            canonical_seal=canonical_seal,
            status="PASS" if passed else "FAIL",
            execution_time_ms=execution_time,
            metadata={
                'difficulty': case.get('difficulty'),
                'trap_type': case.get('trap_type'),
                'explanation': case.get('explanation')
            }
        )

    def run_full_benchmark(self, dataset_path: str) -> Dict:
        """Executa benchmark completo em um dataset."""
        dataset_path = Path(dataset_path)

        # Carregar casos
        cases = []
        for file in dataset_path.glob("*.jsonl"):
            with open(file, 'r') as f:
                for line in f:
                    if line.strip():
                        cases.append(json.loads(line))

        print(f"🧪 Avaliando {len(cases)} casos de {dataset_path.name}")

        # Avaliar cada caso
        results = []
        for case in cases:
            result = self.evaluate_case(case)
            results.append(result)
            self.results.append(result)

        # Calcular métricas
        total = len(results)
        passed = sum(1 for r in results if r.status == "PASS")

        # Métricas por dificuldade
        by_difficulty = {}
        for r in results:
            diff = r.metadata.get('difficulty', 'unknown')
            if diff not in by_difficulty:
                by_difficulty[diff] = {'total': 0, 'passed': 0}
            by_difficulty[diff]['total'] += 1
            if r.status == "PASS":
                by_difficulty[diff]['passed'] += 1

        for diff in by_difficulty:
            d = by_difficulty[diff]
            d['accuracy'] = d['passed'] / d['total'] if d['total'] > 0 else 0

        # Métricas por tipo de armadilha
        by_trap = {}
        for r in results:
            trap = r.metadata.get('trap_type', 'unknown')
            if trap not in by_trap:
                by_trap[trap] = {'total': 0, 'passed': 0}
            by_trap[trap]['total'] += 1
            if r.status == "PASS":
                by_trap[trap]['passed'] += 1

        for trap in by_trap:
            t = by_trap[trap]
            t['accuracy'] = t['passed'] / t['total'] if t['total'] > 0 else 0

        # Calcular ECE (Expected Calibration Error)
        predictions = [r.confidence for r in results]
        labels = [1 if r.expected == r.actual else 0 for r in results]
        ece = self._compute_ece(predictions, labels)

        return {
            'benchmark': 'BixoniBench v1.0',
            'dataset': dataset_path.name,
            'total_cases': total,
            'passed': passed,
            'accuracy': passed / total if total > 0 else 0,
            'ece': ece,
            'avg_confidence': np.mean(predictions) if predictions else 0,
            'avg_execution_time_ms': np.mean([r.execution_time_ms for r in results]),
            'by_difficulty': by_difficulty,
            'by_trap_type': by_trap,
            'results': [asdict(r) for r in results[:100]],  # Primeiros 100 para inspeção
            'canonical_seal': hashlib.sha3_256(
                json.dumps({k: v for k, v in locals().items() if k != 'results'}, sort_keys=True).encode()
            ).hexdigest()[:16],
            'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

    def _compute_ece(self, predictions: List[float], labels: List[int], n_bins: int = 10) -> float:
        """Calcula Expected Calibration Error."""
        if not predictions:
            return 0.0

        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        ece = 0.0

        for i in range(n_bins):
            in_bin = [(p, l) for p, l in zip(predictions, labels)
                     if bin_boundaries[i] <= p < bin_boundaries[i+1]]
            if not in_bin:
                continue
            bin_acc = np.mean([l for _, l in in_bin])
            bin_conf = np.mean([p for p, _ in in_bin])
            bin_weight = len(in_bin) / len(predictions)
            ece += bin_weight * abs(bin_acc - bin_conf)

        return ece

    def generate_report(self, output_path: str):
        """Gera relatório em formato Markdown."""
        results = self.run_full_benchmark("benchmarks/bixonibench/datasets/programming")

        report = f"""# BixoniBench Report — {results['timestamp']}

## Resumo Executivo
- **Dataset**: {results['dataset']}
- **Casos Totais**: {results['total_cases']}
- **Acurácia**: {results['accuracy']:.2%}
- **ECE**: {results['ece']:.4f} (threshold: 0.05)
- **Confiança Média**: {results['avg_confidence']:.3f}
- **Tempo Médio**: {results['avg_execution_time_ms']:.1f}ms

## Desempenho por Dificuldade
| Dificuldade | Casos | Passou | Acurácia |
|-------------|-------|--------|----------|
"""
        for diff, stats in results['by_difficulty'].items():
            report += f"| {diff} | {stats['total']} | {stats['passed']} | {stats['accuracy']:.2%} |\n"

        report += f"""
## Desempenho por Tipo de Armadilha
| Tipo de Armadilha | Casos | Passou | Acurácia |
|-------------------|-------|--------|----------|
"""
        for trap, stats in results['by_trap_type'].items():
            report += f"| {trap} | {stats['total']} | {stats['passed']} | {stats['accuracy']:.2%} |\n"

        report += f"""
## Selo Canônico
`{results['canonical_seal']}`

*Relatório gerado pelo BixoniBench Evaluator v1.0*
"""

        Path(output_path).write_text(report)
        print(f"📄 Relatório salvo em: {output_path}")