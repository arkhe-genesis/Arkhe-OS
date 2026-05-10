import pytest
import os
from unittest.mock import MagicMock

# Fix python path for testing
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

from agi.system32.asi.asi_onnx_runtime import ASIONNXRuntime

def test_asi_onnx_runtime():
    registry_mock = MagicMock()
    coherence_mock = MagicMock()

    class FakeSession:
        def run(self, out, feed):
            import numpy as np
            return [np.array([1, 2, 3], dtype=np.float32)]

    registry_mock.load_session.return_value = FakeSession()

    runtime = ASIONNXRuntime(registry_mock, coherence_mock)

    # Load model
    assert runtime.load_model("test_func", "dummy_hash") is True
    assert "test_func" in runtime.active_models

    # Run inference
    import numpy as np
    input_data = np.zeros((1, 3, 224, 224), dtype=np.float32).tobytes()
    res = runtime.run("test_func", input_data)

    assert res == np.array([1, 2, 3], dtype=np.float32).tobytes()

    # Hot swap
    assert runtime.hot_swap_model("test_func", "new_hash") is True
    assert runtime.active_models["test_func"].model_hash == "new_hash"

    # Check status
    status = runtime.get_model_status()
    assert "test_func" in status
    assert status["test_func"]["calls"] == 1
