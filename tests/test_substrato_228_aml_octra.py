import pytest
import importlib.util
import sys

spec = importlib.util.spec_from_file_location(
    "substrato_228_aml_octra",
    "substrates/200-299_expansion/substrato_228/substrato_228_aml_octra.py"
)
substrato_228_aml_octra = importlib.util.module_from_spec(spec)
sys.modules["substrato_228_aml_octra"] = substrato_228_aml_octra
spec.loader.exec_module(substrato_228_aml_octra)

def test_substrato_228_results():
    results = substrato_228_aml_octra.run_test_suite()
    assert results["total_tests"] == 6
    assert results["passed_tests"] == 6
    assert results["phi_c"] > 0.5
