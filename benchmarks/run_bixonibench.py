#!/usr/bin/env python3
"""
run_bixonibench.py — Executa benchmark BixoniBench no Protocolo Arkhe
"""

import json
import time
import argparse
import sys
import os

# Ensure conrag is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conrag.orchestrator import ProtocoloArkhe, Veredito

def run_benchmark(dataset_path: str, output_path: str):
    """Executa benchmark completo."""
    # Carregar dataset
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)

    protocolo = ProtocoloArkhe()
    resultados = []

    print(f"🧪 Iniciando BixoniBench v{dataset['metadata']['version']}")
    print(f"   Total de casos: {dataset['metadata']['total_cases']}")
    print(f"   Domínios: {', '.join(dataset['metadata']['domains'])}")
    print()

    start = time.time()

    for i, case in enumerate(dataset['test_cases'], 1):
        resultado = protocolo.verificar(
            query=case['query'],
            metadados={'dominio': case['domain'], 'benchmark': 'bixonibench', 'case_id': case['id']}
        )

        # Verificar acurácia
        expected = case['expected_verdict']
        actual = resultado.veredito.value
        correto = (expected == actual)

        resultados.append({
            'case_id': case['id'],
            'expected': expected,
            'actual': actual,
            'correto': correto,
            'confianca': resultado.confianca,
            'tempo_ms': None  # Preenchido no agregado
        })

        if i % 100 == 0:
            print(f"   Progresso: {i}/{len(dataset['test_cases'])} casos")

    elapsed = time.time() - start

    # Calcular métricas
    total = len(resultados)
    accuracy = sum(1 for r in resultados if r['correto']) / total
    rejection_rate = sum(1 for r in resultados if r['actual'] == 'refutado') / total
    avg_confidence = sum(r['confianca'] for r in resultados) / total

    # Métricas por domínio
    by_domain = {}
    for case, res in zip(dataset['test_cases'], resultados):
        domain = case['domain']
        if domain not in by_domain:
            by_domain[domain] = {'total': 0, 'corretos': 0}
        by_domain[domain]['total'] += 1
        if res['correto']:
            by_domain[domain]['corretos'] += 1

    for domain in by_domain:
        d = by_domain[domain]
        d['accuracy'] = d['corretos'] / d['total']

    # Relatório final
    report = {
        'benchmark': dataset['metadata'],
        'execution': {
            'start_time': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start)),
            'elapsed_seconds': elapsed,
            'cases_per_second': total / elapsed
        },
        'metrics': {
            'accuracy': accuracy,
            'expected_rejection_rate': dataset['metadata']['expected_rejection_rate'],
            'actual_rejection_rate': rejection_rate,
            'avg_confidence': avg_confidence,
            'ece_estimate': abs(avg_confidence - accuracy)  # Estimativa simples de ECE
        },
        'by_domain': by_domain,
        'sample_results': resultados[:20],  # Primeiros 20 para inspeção
        'protocol_version': 'Arkhe v4.0',
        'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Salvar relatório
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Imprimir resumo
    print(f"\n✅ BixoniBench concluído")
    print(f"   Acurácia: {accuracy:.2%} (esperado: 100%)")
    print(f"   Taxa de rejeição: {rejection_rate:.2%} (esperado: 100%)")
    print(f"   Confiança média: {avg_confidence:.3f}")
    print(f"   ECE estimado: {abs(avg_confidence - accuracy):.3f} (limiar: 0.05)")
    print(f"   Tempo: {elapsed:.1f}s ({total/elapsed:.1f} casos/s)")
    print(f"   Relatório salvo em: {output_path}")

    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executar BixoniBench")
    parser.add_argument("--dataset", default="benchmarks/bixonibench_v1.json")
    parser.add_argument("--output", default="reports/bixonibench_result.json")
    args = parser.parse_args()

    run_benchmark(args.dataset, args.output)
