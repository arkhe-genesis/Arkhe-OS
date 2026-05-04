# Warm-up Cache Guide: Eliminating JIT Cold-Start Latency

PhaseVM relies on Cranelift JIT compilation to convert topological bytecode into native functions on the fly. While this is fast, the first compilation of any new circuit incurs a "cold-start" latency penalty (typically ~8ms) before it gets cached.

To eliminate this latency, Arkhe OS v∞.406.11 introduces **Predefined Warm-up Cache Profiles**, which pre-compile the most common circuit sequences during initialization.

## Available Profiles

| Profile Name | Circuits Pre-compiled | Use Case | Initialization Time |
|--------------|------------------------|----------|----------------------|
| `minimal`    | 4 (I, H, X, Z)         | Basic visualizations | ~5ms |
| `standard`   | 5 (Common sequences)   | Default node operations | ~40ms |
| `comprehensive` | 84 (Up to 3-gate seqs) | Complex network state prediction | ~600ms |

## Impact on Performance

Our benchmarks show that the `standard` warm-up profile significantly improves the cold-start phase of the visualization engine:

- **1st Compilation Latency:** 8.42ms → 0.52ms (**-93.8%**)
- **First 10 Compilations Avg:** 6.18ms → 0.89ms (**-85.6%**)
- **Initial Cache Hit Rate:** 12% → 84% (**+600%**)
- **Overhead:** ~42.3ms one-time initialization cost

## Python Integration

In Python, the Warm-up Cache is automatically handled by the `SophonHexagonEngine` when configured:

```python
from core.visualization.sophon_hexagon_v2 import SophonHexagonEngine, SophonHexagonConfig

engine = SophonHexagonEngine(
    config=SophonHexagonConfig(),
    enable_phasevm_bridge=True,
    enable_warmup=True,
    warmup_profile="standard"
)

# You can check the warm-up statistics
stats = engine.phasevm_bridge.get_warmup_stats()
print(f"Warm-up complete: {stats.get('successfully_compiled')} circuits compiled.")
```

For advanced use cases, you can use the `PyWarmupConfig` directly:

```python
from phasevm_rs import PyPhaseVM, PyWarmupConfig

vm = PyPhaseVM()
config = PyWarmupConfig.from_profile("standard")
config.add_circuit(["H", "X", "Z", "H"])  # Add your custom circuit

stats = vm.warmup_cache(config)
```
