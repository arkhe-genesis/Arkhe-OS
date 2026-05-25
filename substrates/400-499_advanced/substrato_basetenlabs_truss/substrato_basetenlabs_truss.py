import json
import tempfile
import os

class SubstratoBasetenlabsTruss:
    def canonize(self):
        report = {
            "Title": "Truss - The simplest way to serve AI/ML models in production",
            "Description": "Truss is the CLI for deploying and serving ML models on Baseten. It lets you package your model's serving logic in Python, launch training jobs, and deploy to production, handling containerization, dependency management, and GPU configuration. It supports models created and served with any open-source framework.",
            "Features": [
                "Write once, run anywhere: Package model code, weights, and dependencies with a model server that behaves the same in development and production.",
                "Fast developer loop: Iterate with live reload, skip Docker and Kubernetes configuration, and use a batteries-included serving environment.",
                "Support for all Python frameworks: Supports transformers, diffusers, PyTorch, TensorFlow, vLLM, SGLang, and TensorRT-LLM.",
                "Production-ready: Built-in support for GPUs, secrets, caching, and autoscaling when deployed to Baseten or your own infrastructure."
            ],
            "Architecture": [
                "CLI for model deployment via `uvx truss push` and `uvx truss watch`",
                "YAML-based configuration (`config.yaml`) for specifying model, hardware, and engine",
                "Optional `model/` directory for custom Python code (preprocessing, postprocessing)",
                "Integrates with Baseten Inference Stack for optimized serving (e.g. TensorRT-LLM)"
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_truss_", text=True)
        with os.fdopen(fd, 'w', encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

        print("Canonized Truss. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoBasetenlabsTruss()
    substrate.canonize()
