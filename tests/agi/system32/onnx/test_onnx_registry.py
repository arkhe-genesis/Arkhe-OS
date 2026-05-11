import pytest
import os
import tempfile
import json
import hashlib
from unittest.mock import MagicMock
from pathlib import Path

# Fix python path for testing
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

from agi.system32.onnx.src.python.registry import ONNXModelRegistry, ONNXModelEntry
from agi.system32.onnx.src.python import crypto

def test_registry():
    with tempfile.TemporaryDirectory() as d:
        # Mocking ort.InferenceSession
        import onnxruntime as ort
        ort.InferenceSession = MagicMock()

        reg = ONNXModelRegistry(storage_dir=d)

        # Create a fake ONNX file
        onnx_file = Path(d) / "test.onnx"
        onnx_file.write_bytes(b"fake_onnx_model_content")

        hash_val = hashlib.sha3_256(b"fake_onnx_model_content").hexdigest()

        h = reg.register_model(
            onnx_path=str(onnx_file),
            publisher_seal="test_seal",
            phi_c_training=0.95,
            datasets=["test_ds"],
            license_type="MIT",
            signature="test_sig"
        )

        assert h == hash_val

        # Test loading
        sess = reg.load_session(h)
        assert sess is not None

def test_inference_engine():
    with tempfile.TemporaryDirectory() as d:
        # Mocking ort.InferenceSession
        import onnxruntime as ort
        ort.get_available_providers = MagicMock(return_value=["CPUExecutionProvider"])

        class FakeSession:
            def get_inputs(self):
                class FakeInput:
                    name = "input"
                return [FakeInput()]
            def get_outputs(self):
                class FakeOutput:
                    name = "output"
                return [FakeOutput()]
            def run(self, out, feed):
                return [feed["input"] * 2]

        ort.InferenceSession = MagicMock(return_value=FakeSession())

        reg = ONNXModelRegistry(storage_dir=d)

        onnx_file = Path(d) / "test.onnx"
        onnx_file.write_bytes(b"fake_onnx_model_content")

        h = reg.register_model(
            onnx_path=str(onnx_file),
            publisher_seal="test_seal",
            phi_c_training=0.95,
            datasets=["test_ds"],
            license_type="MIT",
            signature="test_sig"
        )

        from agi.system32.onnx.src.python.inference_engine import ONNXInferenceEngine
        engine = ONNXInferenceEngine(registry=reg)

        import numpy as np
        res = engine.run_inference(h, {"input": np.array([1, 2, 3])})
        assert "output" in res
        assert (res["output"] == np.array([2, 4, 6])).all()
