#!/usr/bin/env python3
"""
benchmarks/test_profile_tuning.py
Testa impacto do profile (1,2,1,2) vs. baseline (1,1,1,1).
"""
import subprocess
import json
import time
import os

def benchmark_with_profile(profile_name: str, profile_values: tuple):
    """Executa benchmark com profile específico."""
    uin, uset, ukvs, ux = profile_values

    print(f"\n🔬 Testing profile {profile_name} = {profile_values}...")

    # Rebuild com profile
    env = {
        **os.environ,
        'CXXFLAGS': f'-DARKHE_UNIVERSAL_PROFILE_UIN={uin} '
                   f'-DARKHE_UNIVERSAL_PROFILE_USET={uset} '
                   f'-DARKHE_UNIVERSAL_PROFILE_UKVS={ukvs} '
                   f'-DARKHE_UNIVERSAL_PROFILE_UX={ux} '
                   f'-O3 -march=native'
    }

    # Rebuild (simplificado; em produção usar sistema de build mais robusto)
    subprocess.run(['scripts/rebuild_with_profile.sh'], env=env, check=True)

    # Executar benchmark rápido
    result = subprocess.run(
        ['python', 'benchmarks/run_comparative_benchmark.py', '--quick'],
        capture_output=True,
        text=True,
        cwd='zee200_integration'
    )

    # Parse output para extrair speed
    for line in result.stdout.split('\n'):
        if 'Projected speed:' in line:
            speed = float(line.split(':')[1].strip().split()[0])
            print(f"   ✓ Speed with {profile_name}: {speed:.1f} KHz")
            return speed

    return None

if __name__ == '__main__':
    print("⚙️  Profile Tuning Benchmark")
    print("=" * 50)

    # Testar profiles
    profiles = [
        ('baseline (1,1,1,1)', (1, 1, 1, 1)),
        ('arkhe-optimized (1,2,1,2)', (1, 2, 1, 2)),
        ('kvs-heavy (1,1,2,2)', (1, 1, 2, 2)),
    ]

    results = {}
    for name, values in profiles:
        speed = benchmark_with_profile(name, values)
        if speed:
            results[name] = speed

    # Comparar
    baseline = results.get('baseline (1,1,1,1)', 1)
    print(f"\n📊 Profile Comparison (relative to baseline):")
    for name, speed in results.items():
        speedup = speed / baseline if baseline > 0 else 1
        marker = "✓" if speed >= 150 else "⚠️" if speed >= 100 else ""
        print(f"   {marker} {name:<25} {speed:>6.1f} KHz ({speedup:.2f}×)")

    # Recomendar
    if results:
        best = max(results.items(), key=lambda x: x[1])
        print(f"\n✅ Recommended: {best[0]} → {best[1]:.1f} KHz")
