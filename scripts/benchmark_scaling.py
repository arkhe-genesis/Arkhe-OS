# benchmark_scaling.py
import time
import numpy as np
from scalable_simulation import ScalableWakefieldCluster

def benchmark(num_nodes_list: list, steps: int = 100):
    """Benchmark de performance para diferentes tamanhos de cluster."""
    results = []

    for num_nodes in num_nodes_list:
        print(f"🔧 Testando {num_nodes} nós...")
        cluster = ScalableWakefieldCluster(num_nodes, avg_degree=6)

        # Simular elétrons (10% dos nós)
        num_electrons = max(1, num_nodes // 10)
        electron_assignments = np.random.randint(0, num_nodes, size=num_electrons)

        start = time.time()
        for step in range(steps):
            metrics = cluster.step(electron_assignments)
        elapsed = time.time() - start

        results.append({
            'num_nodes': num_nodes,
            'steps': steps,
            'elapsed_s': elapsed,
            'steps_per_second': steps / elapsed,
            'memory_estimate_MB': num_nodes * 100 / 1024 / 1024  # ~100 bytes/nó
        })
        print(f"  ✓ {num_nodes} nós: {steps/elapsed:.1f} passos/s")

    # Plot resultados
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    nodes = [r['num_nodes'] for r in results]
    speed = [r['steps_per_second'] for r in results]
    ax.plot(nodes, speed, marker='o')
    ax.set_xlabel('Número de Nós'); ax.set_ylabel('Passos por Segundo')
    ax.set_title('Benchmark de Escala — ARKHE OS v158')
    ax.grid(True); plt.tight_layout()
    plt.savefig('benchmark_scaling.png')

    return results

if __name__ == "__main__":
    results = benchmark([10, 50, 100, 200, 500], steps=50)
    for r in results:
        print(f"{r['num_nodes']:4d} nós: {r['steps_per_second']:6.1f} passos/s, "
              f"~{r['memory_estimate_MB']:.1f} MB RAM estimado")
