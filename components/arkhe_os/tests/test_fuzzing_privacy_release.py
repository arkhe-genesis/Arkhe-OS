import pytest
from arkhe_os.fuzzing.fuzzer import CoherentFuzzer
from arkhe_os.federated.cross_repo_propagator import CrossRepoPropagator
from arkhe_os.federated.verification import OctraRegistry, FederatedVerifier
from arkhe_os.privacy.dp_reports import DifferentialPrivacy, AuditTrail, ComplianceReportManager
from arkhe_os.release.packager_259 import ReleaseOrchestrator

def test_fuzzer():
    fuzzer = CoherentFuzzer()
    mutated = fuzzer.ast_mutate({"type": "LFIRModule", "id": "test_1"})
    assert mutated is not None
    assert isinstance(fuzzer.utility_function(0.5, 0.1), float)

def test_cross_repo_propagator():
    propagator = CrossRepoPropagator()
    propagator.add_dependency("repoA", "repoB", "security")
    assert propagator.validate_graph() == True

def test_federated_verification():
    registry = OctraRegistry()
    registry.register_key("domain_test", "PUB_KEY_123")
    verifier = FederatedVerifier(registry)

    proof = {"domain": "domain_test", "is_valid": True, "hash": "abc"}
    assert verifier.verify_individual(proof) == True

def test_privacy_dp():
    dp = DifferentialPrivacy(epsilon=1.0)
    values = [0.1, 0.2, 0.3, 0.4, 0.5]

    noisy_mean = dp.aggregate_with_dp(values)
    assert isinstance(noisy_mean, float)

    noisy_val = dp.add_laplace_noise(0.5)
    assert isinstance(noisy_val, float)

def test_release_packager():
    orchestrator = ReleaseOrchestrator()
    meta, pkg_hash = orchestrator.package_substrates()
    assert meta["name"] == "arkhe-os"
    assert "substrates-0-259" in meta["version"]
