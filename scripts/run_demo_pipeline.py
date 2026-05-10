#!/usr/bin/env python3
"""
run_demo_pipeline.py
Executa pipeline completo com dados sintéticos + benchmark de performance.
"""
import time
import json
import os
import subprocess
from pathlib import Path

def main():
    print("🔐 ARKHE OS v∞.320.2 — Demo Pipeline Execution + Benchmark")
    print("=" * 70)

    # Check if the backend library exists, otherwise compile it
    ext_suffix = subprocess.check_output(['python3-config', '--extension-suffix']).decode().strip()
    backend_lib = f'zee200_backend{ext_suffix}'
    if not os.path.exists(backend_lib):
        subprocess.run([
            'c++', '-O3', '-Wall', '-shared', '-std=c++17', '-fPIC',
            *subprocess.check_output(['python3', '-m', 'pybind11', '--includes']).decode().strip().split(),
            'backend_zee200.cpp', '-o', backend_lib
        ], check=True)

    from track1_gtzk_wrapper import track1_gtzk_instruction
    from track2_gtzk_wrapper import track2_gtzk_instruction
    from track3_gtzk_wrapper import track3_gtzk_instruction
    from recursive_aggregation import aggregate_track_proofs
    from verify_aggregated_proof import verify_aggregated_proof

    def benchmark(func, *args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        if isinstance(result, tuple) and len(result) == 3:
            return result[0], result[1], result[2], elapsed
        elif isinstance(result, tuple) and len(result) == 2:
            return result[0], result[1], elapsed
        elif isinstance(result, tuple):
            return (*result, elapsed)
        else:
            return result, elapsed

    # 1. Carregar dados de exemplo
    print("\n[1/5] Loading demo data...")
    with open('results/track1_raw.json') as f:
        track1_data = json.load(f)
    with open('results/track2_raw.json') as f:
        track2_data = json.load(f)
    with open('results/track3_raw.json') as f:
        track3_data = json.load(f)

    # 2. Gerar instruções GTZK com benchmark
    print("\n[2/5] Generating GTZK instructions...")
    track_results = {}

    # Track 1
    t1_inst, t1_out, t1_time = benchmark(
        track1_gtzk_instruction,
        track1_data['grid_sizes'],
        track1_data['measurements']
    )
    track_results['track1'] = {'instruction': t1_inst, 'public_outputs': t1_out}
    print(f"   Track 1: {t1_time*1000:.1f} ms | BF={t1_out['bayes_factor']:.1f}")

    # Track 2
    t2_inst, t2_out, t2_time = benchmark(
        track2_gtzk_instruction,
        track2_data['intention_signals'],
        track2_data['sensor_readings'],
        track2_data['sensor_params']
    )
    track_results['track2'] = {'instruction': t2_inst, 'public_outputs': t2_out}
    print(f"   Track 2: {t2_time*1000:.1f} ms | MI={t2_out['mi_nats']:.4f} nats")

    # Track 3
    t3_inst, t3_out, t3_time = benchmark(
        track3_gtzk_instruction,
        track3_data['velocity_fields'],
        track3_data['pressure_field'],
        track3_data['grid_size']
    )
    track_results['track3'] = {'instruction': t3_inst, 'public_outputs': t3_out}
    print(f"   Track 3: {t3_time*1000:.1f} ms | ||[A,B,C]||={t3_out['associator_norm']:.6f}")

    # 3. Agregar provas
    print("\n[3/5] Aggregating proofs via Merkle tree...")
    root_hash, agg_proof, vkey, agg_time = benchmark(aggregate_track_proofs, track_results)
    print(f"   Root hash: {root_hash[:16]}... | {agg_time*1000:.1f} ms")

    # 4. Verificar prova agregada
    print("\n[4/5] Verifying aggregated proof...")
    verify_result, verify_time = benchmark(
        verify_aggregated_proof, agg_proof, vkey, track_results
    )
    status = "✓" if verify_result['overall_valid'] else "✗"
    print(f"   {status} {verify_result['message']} | {verify_time*1000:.2f} ms")

    # 5. Relatório de performance
    print("\n[5/5] Performance Summary")
    total_time = t1_time + t2_time + t3_time + agg_time + verify_time
    total_instructions = 3  # 1 por track
    khz_equiv = total_instructions / total_time / 1000

    print(f"""
   ┌─────────────────────────────────┐
   │ Pipeline Performance            │
   ├─────────────────────────────────┤
   │ Track 1 (Mass Scaling):  {t1_time*1000:6.1f} ms │
   │ Track 2 (Intention):     {t2_time*1000:6.1f} ms │
   │ Track 3 (Associator):    {t3_time*1000:6.1f} ms │
   │ Aggregation:             {agg_time*1000:6.1f} ms │
   │ Verification:            {verify_time*1000:6.2f} ms │
   ├─────────────────────────────────┤
   │ Total Time:              {total_time*1000:6.1f} ms │
   │ Instructions:            {total_instructions:6d}   │
   │ Effective Speed:         {khz_equiv:6.1f} KHz │
   └─────────────────────────────────┘

   🎯 Target: 200 KHz | Current: {khz_equiv:.1f} KHz
   📈 Gap: {200/khz_equiv:.1f}× speedup needed
    """)

    # Salvar resultados
    output = {
        'execution_valid': verify_result['overall_valid'],
        'performance': {
            'track1_ms': t1_time*1000,
            'track2_ms': t2_time*1000,
            'track3_ms': t3_time*1000,
            'aggregation_ms': agg_time*1000,
            'verification_ms': verify_time*1000,
            'total_ms': total_time*1000,
            'effective_khz': khz_equiv
        },
        'results': {
            'track1': t1_out,
            'track2': t2_out,
            'track3': t3_out
        },
        'root_hash': root_hash
    }

    Path('results').mkdir(exist_ok=True)
    with open('results/demo_execution_v320_2.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"💾 Resultados salvos: results/demo_execution_v320_2.json")
    return output

if __name__ == '__main__':
    main()
