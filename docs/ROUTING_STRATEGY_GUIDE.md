# Routing Strategy Guide for Arkhe Substrates

## Use Case Recommendations

| Substrate | Typical Application | Recommended Routing | Justification |
|-----------|---------------------|----------------------|---------------|
| **93** (cbytes Compiler) | Circuit serialization | **Coherence-based** | Preserves topological invariants during transmission |
| **97** (Sophon) | Calabi-Yau computation | **Coherence-based** | High coherence essential for quantum operations |
| **98** (Crystal Clock) | Time synchronization | **Hybrid** | Uses coherence for sync, traditional for data |
| **89** (Irrotational Antenna) | Scalar RF transmission | **Traditional** | Coherence less critical; latency is priority |
| **104** (Fourier Lens) | Unified optical/RF sensor | **Coherence-based** | Wave propagation benefits from coherence routing |
| **85/86** (Materials) | Distributed sensing | **Adaptive** | Switches based on dynamic coherence threshold |

## Quantitative Decision Rule

```python
def recommend_routing_strategy(use_case: dict, coherence_requirement: float) -> str:
    """
    Recommend routing strategy based on coherence requirement and performance constraints.

    Args:
        use_case: Dict with keys: latency_critical, coherence_critical, compute_budget
        coherence_requirement: Minimum coherence threshold [0, 1]

    Returns:
        'coherence_based', 'traditional', or 'adaptive'
    """
    if coherence_requirement >= 0.85:
        return 'coherence_based'  # Sophon protocol essential
    elif coherence_requirement <= 0.65:
        return 'traditional'  # Overhead not justified
    else:
        # Adaptive: use coherence-based for control packets, traditional for data
        if use_case.get('latency_critical', False):
            return 'adaptive'
        elif use_case.get('compute_budget', float('inf')) < 1.0:  # ms/packet
            return 'traditional'
        else:
            return 'coherence_based'
```
