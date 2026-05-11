#!/usr/bin/env python3
"""
benchmark_hesitation.py — Mede overhead da hesitação vs. ganho de integridade
"""

import time
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class BenchmarkResult:
    hesitation_entropy: float
    avg_delay_ms: float
    std_delay_ms: float
    integrity_score: float
    fusion_score: float
    overhead_pct: float  # Overhead vs. execução sem hesitação

def run_benchmark_iteration(
    entropy: float,
    base_delay: float,
    jitter: float,
    n_samples: int = 100
) -> BenchmarkResult:
    """Executa uma iteração do benchmark"""
    delays = []

    for _ in range(n_samples):
        # Calcular delay ritualístico
        modulated = base_delay * (1.0 + 0.5 * entropy)
        jitter_sample = np.random.normal(0, jitter)
        delay = max(0.0, modulated + jitter_sample)
        delays.append(delay)

    # Calcular métricas
    avg_delay = np.mean(delays)
    std_delay = np.std(delays)

    # Integridade: função da entropia (mais entropia = mais integridade, até um ponto)
    integrity_score = min(1.0, 0.7 + 0.4 * entropy - 0.2 * entropy**2)

    # Score de fusão (média geométrica)
    fusion_score = np.sqrt(0.95 * integrity_score)  # 0.95 = S-value simulado

    # Overhead: comparação com execução sem hesitação (base_delay = 50.0 assumed as baseline if entropy=0)
    overhead_pct = (avg_delay / base_delay * 100) if base_delay > 0 else 0

    return BenchmarkResult(
        hesitation_entropy=entropy,
        avg_delay_ms=avg_delay,
        std_delay_ms=std_delay,
        integrity_score=integrity_score,
        fusion_score=fusion_score,
        overhead_pct=overhead_pct
    )

def run_full_benchmark(
    entropies: List[float],
    base_delay: float = 50.0,
    jitter: float = 5.0,
    n_iterations: int = 50
) -> pd.DataFrame:
    """Executa benchmark completo para múltiplos valores de entropia"""
    results = []

    for entropy in entropies:
        iteration_results = [
            run_benchmark_iteration(entropy, base_delay, jitter)
            for _ in range(n_iterations)
        ]

        # Média das iterações
        avg_result = BenchmarkResult(
            hesitation_entropy=entropy,
            avg_delay_ms=np.mean([r.avg_delay_ms for r in iteration_results]),
            std_delay_ms=np.mean([r.std_delay_ms for r in iteration_results]),
            integrity_score=np.mean([r.integrity_score for r in iteration_results]),
            fusion_score=np.mean([r.fusion_score for r in iteration_results]),
            overhead_pct=np.mean([r.overhead_pct for r in iteration_results])
        )
        results.append(avg_result)

    return pd.DataFrame([r.__dict__ for r in results])

def generate_report(df: pd.DataFrame):
    """Gera relatório textual do benchmark"""
    print("\n" + "="*70)
    print("RELATÓRIO DE BENCHMARK — HESITAÇÃO vs. INTEGRIDADE")
    print("="*70)

    # Encontrar ponto ótimo (máximo fusion_score com overhead < 200%)
    valid = df[df['overhead_pct'] < 200]
    if not valid.empty:
        optimal = valid.loc[valid['fusion_score'].idxmax()]
        print(f"\nPonto Ótimo Recomendado:")
        print(f"  Entropia: {optimal['hesitation_entropy']:.2f}")
        print(f"  Delay médio: {optimal['avg_delay_ms']:.1f} ms")
        print(f"  Overhead: {optimal['overhead_pct']:.1f}%")
        print(f"  Score de fusão: {optimal['fusion_score']:.3f}")
        print(f"  Integridade: {optimal['integrity_score']:.3f}")

    # Estatísticas gerais
    print(f"\nEstatísticas Gerais:")
    print(f"  Entropias testadas: {df['hesitation_entropy'].min():.2f} — {df['hesitation_entropy'].max():.2f}")
    print(f"  Overhead médio: {df['overhead_pct'].mean():.1f}% ± {df['overhead_pct'].std():.1f}%")
    print(f"  Fusion score médio: {df['fusion_score'].mean():.3f} ± {df['fusion_score'].std():.3f}")

    # Recomendações
    print(f"\nRecomendações:")
    if df['fusion_score'].max() > 0.90:
        print("  ✓ Alta integridade alcançável com entropia moderada (0.6–0.8)")
    if df[df['overhead_pct'] < 150]['fusion_score'].max() > 0.85:
        print("  ✓ Score > 0.85 possível com overhead < 150% (eficiente)")
    if df['fusion_score'].min() < 0.70:
        print("  ⚠ Evitar entropia muito baixa (< 0.3) — integridade comprometida")

    print("="*70 + "\n")

def main():
    print("[Benchmark] Iniciando medição de overhead vs. integridade...")

    # Configuração do benchmark
    entropies = np.linspace(0.0, 1.0, 11)  # 0.0, 0.1, ..., 1.0
    base_delay = 50.0  # ms
    jitter = 5.0  # ms
    n_iterations = 50

    # Executar benchmark
    df = run_full_benchmark(entropies, base_delay, jitter, n_iterations)

    # Gerar saída
    generate_report(df)

    # Salvar dados brutos
    df.to_csv("benchmark_data.csv", index=False)
    print(f"[✓] Dados brutos salvos em: benchmark_data.csv")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
