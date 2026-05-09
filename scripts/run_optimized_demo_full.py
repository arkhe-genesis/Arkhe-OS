#!/usr/bin/env python3
import time
import json
import subprocess
import os
import sys
from pathlib import Path

def main():
    print("🚀 ARKHE OS v∞.320.2 — Full Optimized Demo Pipeline with ZEE200 C++ Backend")
    print("=" * 70)

    # 1. Compile backend dynamically if not exists
    ext_suffix = subprocess.check_output(['python3-config', '--extension-suffix']).decode().strip()
    backend_lib = f'zee200_backend{ext_suffix}'
    if not os.path.exists(backend_lib):
        subprocess.run([
            'c++', '-O3', '-Wall', '-shared', '-std=c++17', '-fPIC',
            *subprocess.check_output(['python3', '-m', 'pybind11', '--includes']).decode().strip().split(),
            'backend_zee200.cpp', '-o', backend_lib
        ], check=True)

    from track1_gtzk_wrapper_optimized import track1_gtzk_instruction_optimized
    from track2_gtzk_wrapper_optimized import track2_gtzk_instruction_optimized
    from track3_gtzk_wrapper_optimized import track3_gtzk_instruction_optimized
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

    with open('results/track1_raw.json') as f:
        track1_data = json.load(f)
    with open('results/track2_raw.json') as f:
        track2_data = json.load(f)
    with open('results/track3_raw.json') as f:
        track3_data = json.load(f)

    track_results = {}

    t1_inst, t1_out, t1_time = benchmark(
        track1_gtzk_instruction_optimized,
        track1_data['grid_sizes'],
        track1_data['measurements']
    )
    track_results['track1'] = {'instruction': t1_inst, 'public_outputs': t1_out}
    print(f"   Track 1 Opt: {t1_time*1000:.1f} ms | BF={t1_out['bayes_factor']:.1f}")

    t2_inst, t2_out, t2_time = benchmark(
        track2_gtzk_instruction_optimized,
        track2_data['intention_signals'],
        track2_data['sensor_readings'],
        track2_data['sensor_params']
    )
    track_results['track2'] = {'instruction': t2_inst, 'public_outputs': t2_out}
    print(f"   Track 2 Opt: {t2_time*1000:.1f} ms | MI={t2_out['mi_nats']:.4f} nats")

    t3_inst, t3_out, t3_time = benchmark(
        track3_gtzk_instruction_optimized,
        track3_data['velocity_fields'],
        track3_data['pressure_field'],
        track3_data['grid_size']
    )
    track_results['track3'] = {'instruction': t3_inst, 'public_outputs': t3_out}
    print(f"   Track 3 Opt: {t3_time*1000:.1f} ms | ||[A,B,C]||={t3_out['associator_norm']:.6f}")

    root_hash, agg_proof, vkey, agg_time = benchmark(aggregate_track_proofs, track_results)
    verify_result, verify_time = benchmark(verify_aggregated_proof, agg_proof, vkey, track_results)

    total_time = t1_time + t2_time + t3_time + agg_time + verify_time
    total_instructions = 3
    khz_equiv = total_instructions / total_time / 1000

    print(f"   Total Time: {total_time*1000:.1f} ms")
    print(f"   Effective Speed: {khz_equiv:.1f} KHz")

if __name__ == '__main__':
    main()
