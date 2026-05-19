import pytest
import asyncio
from substrato_263 import ArkhePerformanceEngine, CanonicalBenchmark

@pytest.mark.asyncio
async def test_canonize_timestamp():
    engine = ArkhePerformanceEngine()
    benchmark = await engine.canonize()

    assert isinstance(benchmark, CanonicalBenchmark)

    # Check that seal matches timestamp
    import json, hashlib

    # Re-calculate seal with the same timestamp
    improvements = [r.improvement_pct for r in engine.results if r.improvement_pct is not None]
    phi_c = (sum(improvements) / len(improvements) / 100 + 1) / 2 if improvements else 0.5
    phi_c = max(0.0, min(1.0, phi_c))

    seal_input = json.dumps({
        'benchmarks': len(engine.results),
        'optimizations': len(engine.strategies),
        'regressions': len(engine.alerts),
        'phi_c': round(phi_c, 6),
        'timestamp': benchmark.timestamp,
    }, sort_keys=True)

    expected_seal = hashlib.sha3_256(seal_input.encode()).hexdigest()
    assert benchmark.seal == expected_seal
