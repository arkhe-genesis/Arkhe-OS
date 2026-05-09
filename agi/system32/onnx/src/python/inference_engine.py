#!/usr/bin/env python3
"""Hardware-aware ONNX inference engine with TEE support."""
import numpy as np
from typing import Dict, Optional
import onnxruntime as ort
from .registry import ONNXModelRegistry

class ONNXInferenceEngine:
    def __init__(self, registry: ONNXModelRegistry):
        self.registry = registry
        self._sessions: Dict[str, ort.InferenceSession] = {}

    def select_providers(self) -> list[str]:
        available = ort.get_available_providers()
        priority = ["TensorRTExecutionProvider", "CUDAExecutionProvider",
                    "OpenVINOExecutionProvider", "CoreMLExecutionProvider",
                    "CPUExecutionProvider"]
        return [p for p in priority if p in available]

    def run_inference(self, model_hash: str, inputs: Dict[str, np.ndarray],
                      use_tee: bool = False) -> Dict[str, np.ndarray]:
        session = self._sessions.get(model_hash)
        if not session:
            session = self.registry.load_session(model_hash, self.select_providers())
            self._sessions[model_hash] = session

        input_names = [inp.name for inp in session.get_inputs()]
        output_names = [out.name for out in session.get_outputs()]

        feed = {name: inputs[name] for name in input_names if name in inputs}

        if use_tee:
            # Em produção: rotear via API do enclave TEE
            pass

        outputs = session.run(output_names, feed)
        return dict(zip(output_names, outputs))
