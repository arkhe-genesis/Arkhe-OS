import pytest
import sys
import os

# Ensure the root is in the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from substrato_9027_edge_runtime import (
    HAS_CPP_MODULE,
    arkhe_edge_runtime_module
)

def test_config_initialization():
    config = arkhe_edge_runtime_module.InferenceConfig()
    config.model_path = "test_model.tflite"
    config.preferred_backend = arkhe_edge_runtime_module.HwBackend.AUTO
    config.num_threads = 2

    assert config.model_path == "test_model.tflite"
    assert config.preferred_backend == arkhe_edge_runtime_module.HwBackend.AUTO
    assert config.num_threads == 2
    assert config.enable_temporal_anchor is True # Default
    assert config.enable_phi_c_validation is True # Default

def test_runtime_execution():
    config = arkhe_edge_runtime_module.InferenceConfig()
    config.model_path = "test_model.tflite"
    config.preferred_backend = arkhe_edge_runtime_module.HwBackend.FALLBACK_CPU

    runtime = arkhe_edge_runtime_module.ArkheEdgeRuntime(config)

    input_data = [0.5] * 1024
    result = runtime.run(input_data)

    assert result.success is True
    assert result.latency_ms >= 0.0
    assert result.phi_c_before > 0.0
    assert result.phi_c_after > 0.0
    assert isinstance(result.temporal_seal, str)
    assert len(result.temporal_seal) > 0
    assert len(result.output_data) == 1024
