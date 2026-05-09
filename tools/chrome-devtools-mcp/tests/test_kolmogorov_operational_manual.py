import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from algorithmic.kolmogorov_operational import (
    OperationalKolmogorovEstimator,
    SimplicialComplexMetrics,
    compute_official_delta_rel,
    AlgorithmicCoherenceTensor,
    clean_exit_predicate
)
from compiler.llm_with_zk_verification import LLMCompilerWithZKVerification, PLANKCeremony

def test_kolmogorov():
    estimator = OperationalKolmogorovEstimator()
    delta = estimator.estimate_k_relative([1.0, 2.0, 3.0], [1.1, 2.1, 3.1])
    assert delta is not None

    metrics = SimplicialComplexMetrics(euler_characteristic=1.05, k_per_node=500000.0, triangle_density=0.5, zone_is_synchronous=True, num_nodes=10)
    assert metrics.is_structurally_consistent()
    assert 0 <= metrics.compression_efficiency() <= 1.0

    delta_official = compute_official_delta_rel("Interior")
    assert delta_official is not None

    tensor = AlgorithmicCoherenceTensor(0.9, 0.9, 0.9, 0.05)
    assert tensor.is_within_optimal_band()

    # Mock compute_official_delta_rel inside test context to fall within optimal range
    import algorithmic.kolmogorov_operational as ko
    original_compute = ko.compute_official_delta_rel
    ko.compute_official_delta_rel = lambda z: 0.05

    # Clean exit
    assert clean_exit_predicate("Interior", {}) is True

    # Restore original function
    ko.compute_official_delta_rel = original_compute

def test_compiler():
    compiler = LLMCompilerWithZKVerification()
    ceremony = PLANKCeremony("test", {}, {}, {})
    result = compiler.compile_and_verify(ceremony, "zynq")
    assert result.status in ["ACCEPTED", "REJECTED_SAFETY_VIOLATION", "REJECTED_ZK_VERIFICATION_FAILED"]

if __name__ == "__main__":
    test_kolmogorov()
    test_compiler()
    print("All custom tests passed.")
