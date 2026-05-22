import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_substrato_483_ensemble_aggregator_canonize():
    file_path = "substrates/400-499_advanced/substrato_483_ensemble_aggregator/substrato_483_ensemble_aggregator.py"
    module = load_module_from_path("substrato_483_ensemble_aggregator", file_path)

    substrate = module.Substrato483EnsembleAggregator()
    report_path = substrate.canonize()

    assert os.path.exists(report_path)

    with open(report_path, "r") as f:
        data = json.load(f)

    assert "SEAL_483_ENSEMBLE_AGGREGATOR" in data
    assert "Hash" in data["SEAL_483_ENSEMBLE_AGGREGATOR"]
    assert "Phi_C" in data["SEAL_483_ENSEMBLE_AGGREGATOR"]
    assert data["SEAL_483_ENSEMBLE_AGGREGATOR"]["Aggregated"] == True

    os.remove(report_path)
