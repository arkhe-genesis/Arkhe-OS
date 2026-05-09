#!/usr/bin/env python3
"""
contraction_5d_vs_4d.py — Benchmark de contrações tensoriais 5D vs 4D em TPU v6.
Compara throughput, latência e eficiência de memória para operações ★_5D.
"""
import torch
try:
    import torch_xla.core.xla_model as xm
    import torch_xla.debug.metrics as met
except ImportError:
    xm = None
    met = None
import time
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json

@dataclass
class BenchmarkConfig:
    """Configuração para benchmark de contrações."""
    # Dimensões do manifold
    base_dim: int = 4
    total_dim_5d: int = 5

    # Tamanhos de batch para teste
    batch_sizes: List[int] = None

    # Graus de forma a testar
    form_degrees: List[int] = None

    # Número de iterações para warmup e medida
    warmup_iterations: int = 20
    measure_iterations: int = 100

    # Dispositivos para benchmark
    devices: List[str] = None

    def __post_init__(self):
        if self.batch_sizes is None:
            self.batch_sizes = [1, 4, 16, 64, 256]
        if self.form_degrees is None:
            self.form_degrees = [0, 1, 2, 3, 4, 5]
        if self.devices is None:
            self.devices = ['cpu', 'cuda:0' if torch.cuda.is_available() else None] # removed xla for now in test
            self.devices = [d for d in self.devices if d is not None]

class ContractionBenchmark:
    """Benchmark para operações de contração tensorial em diferentes dimensões."""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.results: Dict[str, Dict] = {}

        # Pré-computar dimensões de espaços de formas
        from math import comb
        self.form_dims_4d = {k: comb(4, k) for k in range(5)}
        self.form_dims_5d = {k: comb(5, k) for k in range(6)}

    def run_benchmark(self, device: str, dim: int = 4) -> Dict:
        """Executa benchmark para dimensão especificada (4 ou 5)."""
        print(f"\n🔬 Benchmarking dim={dim}D em {device}...")

        results = {}

        for batch_size in self.config.batch_sizes:
            batch_results = {}

            for k in self.config.form_degrees:
                if dim == 4 and k > 4:
                    continue
                if dim == 5 and k > 5:
                    continue

                # Dimensão do espaço de k-formas
                form_dim = self.form_dims_5d[k] if dim == 5 else self.form_dims_4d[k]

                # Gerar dados de teste
                omega = torch.randn(batch_size, form_dim, dtype=torch.float64)

                # Mover para dispositivo
                if device.startswith('xla'):
                    import torch_xla
                    device = xm.xla_device()
                omega_dev = omega.to(device)

                # Criar operador Hodge (simplificado para benchmark)
                if dim == 5:
                    from arkhe_10q.geometry.hodge_star_5d import HodgeStar5D
                    from arkhe_10q.geometry.manifold_5d_frc2g import Manifold5DFRC2G
                    manifold = Manifold5DFRC2G(base_dim=4, learnable=False).to(device)
                    hodge = HodgeStar5D(manifold, precompute=True)
                else:
                    # Placeholder para 4D (usar implementação existente)
                    hodge = self._create_hodge_4d_stub(dim=4).to(device)

                # Warmup
                for _ in range(self.config.warmup_iterations):
                    _ = hodge.apply(omega_dev, k)
                    if device.startswith('xla'):
                        xm.mark_step()

                # Medição
                torch_xla.sync() if device.startswith('xla') else None
                start = time.perf_counter()

                for _ in range(self.config.measure_iterations):
                    result = hodge.apply(omega_dev, k)
                    if device.startswith('xla'):
                        xm.mark_step()

                torch_xla.sync() if device.startswith('xla') else None
                end = time.perf_counter()

                # Calcular métricas
                elapsed_ms = (end - start) * 1000
                throughput = (batch_size * form_dim * self.config.measure_iterations) / (elapsed_ms / 1000)

                # Métricas XLA específicas
                fallback_count = 0
                if device.startswith('xla'):
                    metrics = met.metrics_report()
                    fallback_count = metrics.get('aten::fallback', 0)
                    met.clear_metrics()

                batch_results[f'k{k}'] = {
                    'form_dim': form_dim,
                    'elapsed_ms': elapsed_ms,
                    'throughput_elements_per_sec': throughput,
                    'fallback_count': fallback_count
                }

                print(f"  • k={k}: batch={batch_size:3d}, dim={form_dim:2d}, "
                      f"throughput={throughput:.2e} elem/s, fallbacks={fallback_count}")

            results[f'batch_{batch_size}'] = batch_results

        return results

    def _create_hodge_4d_stub(self, dim: int):
        """Stub para operador Hodge 4D (benchmark simplificado)."""
        class Hodge4DStub(torch.nn.Module):
            def __init__(self, dim):
                super().__init__()
                self.dim = dim
                from math import comb
                self.form_dims = {k: comb(dim, k) for k in range(dim+1)}

            def apply(self, omega, k):
                # Transformação ortogonal simplificada com sinal correto
                sign = (-1)**(k * (self.dim - k))
                return sign * omega
        return Hodge4DStub(dim)

    def compare_dimensions(self) -> Dict:
        """Compara performance 5D vs 4D em todos os dispositivos."""
        comparison = {}

        for device in self.config.devices:
            print(f"\n📊 Comparando dimensões em {device}:")

            # Benchmark 4D
            results_4d = self.run_benchmark(device, dim=4)

            # Benchmark 5D
            results_5d = self.run_benchmark(device, dim=5)

            # Calcular overhead 5D vs 4D
            overhead_analysis = {}
            for batch_key in results_4d.keys():
                if batch_key not in results_5d:
                    continue

                batch_overhead = {}
                for k_key in results_4d[batch_key].keys():
                    if k_key not in results_5d[batch_key]:
                        continue

                    t4 = results_4d[batch_key][k_key]['elapsed_ms']
                    t5 = results_5d[batch_key][k_key]['elapsed_ms']

                    if t4 > 0:
                        overhead = (t5 - t4) / t4 * 100
                        batch_overhead[k_key] = {
                            'overhead_percent': overhead,
                            'throughput_4d': results_4d[batch_key][k_key]['throughput_elements_per_sec'],
                            'throughput_5d': results_5d[batch_key][k_key]['throughput_elements_per_sec']
                        }

                overhead_analysis[batch_key] = batch_overhead

            comparison[device] = {
                'results_4d': results_4d,
                'results_5d': results_5d,
                'overhead_analysis': overhead_analysis
            }

        return comparison

    def export_results(self, path: str):
        """Exporta resultados para JSON."""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        export_data = {
            'config': asdict(self.config),
            'results': self.results,
            'comparison': self.compare_dimensions() if self.results else None,
            'timestamp': time.time()
        }

        with open(path, 'w') as f:
            json.dump(export_data, f, indent=2, default=lambda x: x.item() if isinstance(x, (np.floating, np.integer)) else str(x))

        print(f"\n💾 Resultados exportados para {path}")

def main():
    """Executa benchmark completo."""
    print("=" * 90)
    print("ARKHE OS 10Q — BENCHMARK: CONTRAÇÕES 5D vs 4D")
    print("=" * 90)

    config = BenchmarkConfig()
    benchmark = ContractionBenchmark(config)

    # Executar benchmarks
    for device in config.devices:
        try:
            results_4d = benchmark.run_benchmark(device, dim=4)
            results_5d = benchmark.run_benchmark(device, dim=5)
            benchmark.results[device] = {'4d': results_4d, '5d': results_5d}
        except Exception as e:
            print(f"  ✗ Erro em {device}: {e}")
            benchmark.results[device] = {'error': str(e)}

    # Exportar resultados
    benchmark.export_results('arkhe_10q/benchmarks/results/contraction_benchmark.json')

    # Relatório resumido
    print("\n" + "=" * 90)
    print("📈 RESUMO DO BENCHMARK")
    print("=" * 90)

    for device, data in benchmark.results.items():
        if 'error' in data:
            print(f"  {device}: ❌ {data['error']}")
            continue

        print(f"\n  {device}:")
        for dim_label, results in [('4D', data['4d']), ('5D', data['5d'])]:
            print(f"    {dim_label}:")
            for batch_key, batch_results in list(results.items())[:2]:  # Mostrar primeiros 2 batch sizes
                avg_throughput = np.mean([r['throughput_elements_per_sec'] for r in batch_results.values()])
                print(f"      {batch_key}: {avg_throughput:.2e} elem/s (média)")

if __name__ == "__main__":
    main()
