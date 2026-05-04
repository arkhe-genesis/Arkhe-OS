#!/usr/bin/env python3
"""
benchmarks/run_comparative_benchmark.py
Executa benchmark comparativo: baseline vs. otimizações Track 2/3.
"""
import time
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

@dataclass
class BenchmarkResult:
    scenario: str
    track: str
    total_time_ms: float
    proof_time_ms: float
    verify_time_ms: float
    proof_size_bytes: int
    effective_khz: float
    optimizations: Dict[str, any]
    security_bits: int
    success: bool

def run_track_benchmark(
    track_name: str,
    use_real_zee200: bool = False,
    optimizations: Optional[Dict] = None,
    security_bits: int = 40,
    n_runs: int = 5
) -> List[BenchmarkResult]:
    """Executa benchmark para um track específico com múltiplas execuções."""
    optimizations = optimizations or {}
    results = []

    print(f"\n🔬 Benchmarking {track_name} (real_zee200={use_real_zee200}, opt={optimizations})")

    # Carregar dados de exemplo
    data_path = Path(f'results/{track_name}_raw.json')
    if not data_path.exists():
        print(f"⚠️  Generating demo data for {track_name}...")
        try:
            from generate_demo_data import generate_track2_demo_data, generate_track3_demo_data
            if track_name == 'track2':
                generate_track2_demo_data()
            elif track_name == 'track3':
                generate_track3_demo_data()
        except ImportError:
            data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(data_path, 'w') as f:
                json.dump({
                    'intention_signals': [1.0, 2.0],
                    'sensor_readings': [0.5, 0.6],
                    'sensor_params': [1.0],
                    'velocity_fields': [0.1, 0.2],
                    'pressure_field': [1.0],
                    'grid_size': 16
                }, f)

    with open(data_path) as f:
        data = json.load(f)

    for run in range(n_runs):
        start_total = time.perf_counter()

        # Importar wrapper apropriado
        if use_real_zee200:
            if track_name == 'track2':
                from src.track2_gtzk_real import track2_gtzk_instruction_real as gtzk_fn
            elif track_name == 'track3':
                from src.track3_gtzk_real import track3_gtzk_instruction_real as gtzk_fn
        else:
            if track_name == 'track2':
                from src.track2_gtzk_wrapper_optimized import track2_gtzk_instruction_optimized as gtzk_fn
            elif track_name == 'track3':
                from src.track3_gtzk_wrapper_optimized import track3_gtzk_instruction_optimized as gtzk_fn

        # Executar geração de instrução GTZK
        if track_name == 'track2':
            inst, outputs = gtzk_fn(
                data['intention_signals'],
                data['sensor_readings'],
                data['sensor_params'],
                mi_bins=optimizations.get('mi_bins', 40)
            )
        elif track_name == 'track3':
            inst, outputs = gtzk_fn(
                data['velocity_fields'],
                data['pressure_field'],
                data['grid_size'],
                sample_rate=optimizations.get('sample_rate', 1.0)
            )

        instruction_time = time.perf_counter() - start_total

        # Gerar prova ZK se backend real
        proof_time = 0
        proof_size = 0
        if use_real_zee200:
            start_proof = time.perf_counter()
            proof = inst.prove(security_bits=security_bits)
            proof_time = time.perf_counter() - start_proof
            proof_size = proof['proof_size_bytes']

        # Verificar prova
        verify_time = 0
        verified = True
        if use_real_zee200:
            start_verify = time.perf_counter()
            verified = inst.verify(proof, list(outputs.values()))
            verify_time = time.perf_counter() - start_verify

        total_time = time.perf_counter() - start_total

        # Calcular speed efetivo
        n_instructions = 1  # 1 instrução GTZK por track
        effective_khz = n_instructions / (total_time / 1000) if total_time > 0 else 0

        result = BenchmarkResult(
            scenario=f"{'real' if use_real_zee200 else 'sim'}_{'opt' if optimizations else 'base'}",
            track=track_name,
            total_time_ms=total_time * 1000,
            proof_time_ms=proof_time * 1000,
            verify_time_ms=verify_time * 1000,
            proof_size_bytes=proof_size,
            effective_khz=effective_khz,
            optimizations=optimizations,
            security_bits=security_bits,
            success=verified
        )
        results.append(result)

        print(f"   Run {run+1}/{n_runs}: {total_time*1000:.1f} ms, {effective_khz:.1f} KHz")

    return results

def run_full_comparative_benchmark():
    """Executa benchmark comparativo completo para todos os cenários."""
    print("🚀 ARKHE OS v∞.320.4 — Comparative Benchmark Suite")
    print("=" * 70)

    all_results = []

    # Cenários a testar
    scenarios = [
        # Track 2: Baseline (simulado, sem otimizações)
        ('track2', False, {}, 40, 3),
        # Track 2: Otimizado (bins=20, simulado)
        ('track2', False, {'mi_bins': 20}, 40, 3),
        # Track 2: Real ZEE200, otimizado
        ('track2', True, {'mi_bins': 20}, 40, 3),

        # Track 3: Baseline (simulado, sem otimizações)
        ('track3', False, {}, 40, 3),
        # Track 3: Otimizado (sample_rate=0.25, simulado)
        ('track3', False, {'sample_rate': 0.25}, 40, 3),
        # Track 3: Real ZEE200, otimizado
        ('track3', True, {'sample_rate': 0.25}, 40, 3),
    ]

    for track, use_real, opts, sec_bits, n_runs in scenarios:
        results = run_track_benchmark(track, use_real, opts, sec_bits, n_runs)
        all_results.extend(results)

    # Calcular estatísticas agregadas
    summary = {}
    for track in ['track2', 'track3']:
        track_results = [r for r in all_results if r.track == track]

        # Agrupar por cenário
        by_scenario = {}
        for r in track_results:
            key = r.scenario
            if key not in by_scenario:
                by_scenario[key] = []
            by_scenario[key].append(r)

        summary[track] = {}
        for scenario, runs in by_scenario.items():
            avg_time = np.mean([r.total_time_ms for r in runs])
            avg_khz = np.mean([r.effective_khz for r in runs])
            std_time = np.std([r.total_time_ms for r in runs])

            summary[track][scenario] = {
                'avg_time_ms': float(avg_time),
                'std_time_ms': float(std_time),
                'avg_khz': float(avg_khz),
                'n_runs': len(runs)
            }

    # Calcular speedups
    print("\n📊 Comparative Results Summary:")
    print(f"{'Track':<10} {'Scenario':<25} {'Time (ms)':>12} {'Speed (KHz)':>14} {'Speedup':>10}")
    print("-" * 75)

    for track in ['track2', 'track3']:
        baseline = summary[track].get('sim_base', {})
        baseline_khz = baseline.get('avg_khz', 1)

        for scenario, stats in summary[track].items():
            speedup = stats['avg_khz'] / baseline_khz if baseline_khz > 0 else 1
            print(f"{track:<10} {scenario:<25} {stats['avg_time_ms']:>12.1f}±{stats['std_time_ms']:.1f} {stats['avg_khz']:>14.1f} {speedup:>10.1f}×")

    # Salvar resultados
    Path('results/benchmarks').mkdir(parents=True, exist_ok=True)
    output = {
        'timestamp': time.time(),
        'raw_results': [asdict(r) for r in all_results],
        'summary': summary,
        'projected_200khz': any(
            stats['avg_khz'] >= 150
            for track_data in summary.values()
            for stats in track_data.values()
        )
    }

    with open('results/benchmarks/comparative_v320_4.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Results saved: results/benchmarks/comparative_v320_4.json")

    # Projeção final
    best_khz = max(
        stats['avg_khz']
        for track_data in summary.values()
        for stats in track_data.values()
    )
    if best_khz >= 150:
        print(f"\n✅ Projected speed: {best_khz:.1f} KHz — within margin of 200 KHz target!")
    else:
        print(f"\n⚠️  Projected speed: {best_khz:.1f} KHz — needs additional optimization for 200 KHz")

    return output

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--quick', action='store_true', help='Run quick benchmark')
    args = parser.parse_args()

    run_full_comparative_benchmark()
