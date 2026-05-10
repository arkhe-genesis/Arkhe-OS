#!/usr/bin/env python3
"""
benchmark_xla_5d.py — Benchmark de operações Manifold5D em TPU v6 via XLA.

ARKHE 10Q Phase 0 — Milestone 1 Validation
"""

import torch
try:
    import torch_xla.core.xla_model as xm
    import torch_xla.debug.metrics as met
    XLA_AVAILABLE = True
except ImportError:
    XLA_AVAILABLE = False
import time
import numpy as np
from typing import Dict, List
from dataclasses import dataclass, asdict
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@dataclass
class XLABenchmarkConfig:
    batch_sizes: List[int] = None
    form_degrees: List[int] = None
    warmup: int = 20
    iterations: int = 100
    devices: List[str] = None

    def __post_init__(self):
        if self.batch_sizes is None:
            self.batch_sizes = [1, 4, 16, 64]
        if self.form_degrees is None:
            self.form_degrees = [0, 1, 2, 3, 4, 5]
        if self.devices is None:
            self.devices = ['cpu', 'xla:0'] if XLA_AVAILABLE else ['cpu']

class XLABenchmark5D:
    """Benchmark para operações Manifold5D em diferentes backends."""

    def __init__(self, config: XLABenchmarkConfig):
        self.config = config
        self.results: Dict[str, Dict] = {}

    def run_benchmark(self, device: str) -> Dict:
        """Executa benchmark em dispositivo específico."""
        print(f"🔬 Benchmarking em {device}...")

        from arkhe_10q.geometry.manifold_5d_xla import Manifold5DXLA, HodgeStar5DXLA
        from math import comb

        results = {}

        for batch_size in self.config.batch_sizes:
            batch_results = {}

            for k in self.config.form_degrees:
                dim_k = comb(5, k)
                omega = torch.randn(batch_size, dim_k, dtype=torch.float32)

                # Instanciar operador
                manifold = Manifold5DXLA(base_dim=4, learnable=False)
                hodge = HodgeStar5DXLA(manifold, precompute=True)

                # Mover para dispositivo
                if device.startswith('xla') and XLA_AVAILABLE:
                    device_xla = xm.xla_device()
                    manifold = manifold.to(device_xla)
                    omega = omega.to(device_xla)

                # Warmup
                for _ in range(self.config.warmup):
                    _ = hodge.apply(omega, k)
                    if device.startswith('xla') and XLA_AVAILABLE:
                        xm.mark_step()

                # Medição
                if device.startswith('xla') and XLA_AVAILABLE:
                    xm.mark_step()
                start = time.perf_counter()

                for _ in range(self.config.iterations):
                    result = hodge.apply(omega, k)
                    if device.startswith('xla') and XLA_AVAILABLE:
                        xm.mark_step()

                if device.startswith('xla') and XLA_AVAILABLE:
                    xm.mark_step()
                end = time.perf_counter()

                # Métricas
                elapsed_ms = (end - start) * 1000
                throughput = (batch_size * dim_k * self.config.iterations) / (elapsed_ms / 1000)

                # Fallbacks (apenas XLA)
                fallback_count = 0
                if device.startswith('xla') and XLA_AVAILABLE:
                    metrics = met.metrics_report()
                    fallback_count = metrics.get('aten::fallback', 0)
                    met.clear_metrics()

                batch_results[f'k{k}'] = {
                    'dim': dim_k,
                    'elapsed_ms': elapsed_ms,
                    'throughput_elem_per_sec': throughput,
                    'fallback_count': fallback_count
                }

                print(f"  • k={k}: batch={batch_size:2d}, dim={dim_k:2d}, "
                      f"throughput={throughput:.2e} elem/s, fallbacks={fallback_count}")

            results[f'batch_{batch_size}'] = batch_results

        return results

    def compare_devices(self) -> Dict:
        """Compara performance CPU vs TPU."""
        comparison = {}

        for device in self.config.devices:
            results = self.run_benchmark(device)
            comparison[device] = results

            # Calcular speedup vs CPU
            if device != 'cpu' and 'cpu' in self.results:
                cpu_results = self.results['cpu']
                for batch_key in results:
                    if batch_key in cpu_results:
                        for k_key in results[batch_key]:
                            if k_key in cpu_results[batch_key]:
                                cpu_t = cpu_results[batch_key][k_key]['elapsed_ms']
                                dev_t = results[batch_key][k_key]['elapsed_ms']
                                if cpu_t > 0:
                                    speedup = cpu_t / dev_t
                                    results[batch_key][k_key]['speedup_vs_cpu'] = speedup
                                    print(f"  📈 {device} vs CPU: {speedup:.2f}× speedup")

        self.results = comparison
        return comparison

    def export_results(self, path: str):
        """Exporta resultados para JSON."""
        export_data = {
            'config': asdict(self.config),
            'results': self.results,
            'timestamp': time.time()
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(export_data, f, indent=2,
                     default=lambda x: x.item() if isinstance(x, (np.floating, np.integer)) else str(x))
        print(f"💾 Resultados exportados para {path}")

if __name__ == '__main__':
    print("=" * 80)
    print("ARKHE 10Q — BENCHMARK XLA/TPU v6: MANIFOLD5D OPERATIONS")
    print("=" * 80)

    config = XLABenchmarkConfig(iterations=50)
    benchmark = XLABenchmark5D(config)

    # Executar benchmarks
    for device in config.devices:
        try:
            results = benchmark.run_benchmark(device)
            benchmark.results[device] = results
        except Exception as e:
            print(f"  ✗ Erro em {device}: {e}")
            benchmark.results[device] = {'error': str(e)}

    # Comparar e exportar
    benchmark.compare_devices()
    benchmark.export_results(os.path.join(os.path.dirname(__file__), 'results/xla_5d_benchmark.json'))

    print("\n" + "=" * 80)
    print("✅ BENCHMARK CONCLUÍDO")
    print("=" * 80)
