import io
import json
import math
from typing import Dict, Any, Optional, List
from pathlib import Path

from arkhe_os.starter.shared.lfir_parser import LFIRGraph, LFIRNode, Language

class MLFrameworkParser:
    def __init__(self):
        # Hyperparameters for Phi_C
        self.alpha = 1.0
        self.beta = 0.05
        self.gamma = 0.5
        self.delta = 0.1
        self.lambda_val = 0.01

    def get_language(self) -> str:
        return "ml-framework"

    def get_extensions(self) -> list:
        return [".pt", ".pth", ".h5", ".pb", ".pkl", ".joblib", ".json", ".bst", ".txt"]

    def parse(self, source: bytes, filename: str, metadata: Optional[Dict] = None) -> LFIRGraph:
        ext = Path(filename).suffix.lower()

        framework = metadata.get("framework", "") if metadata else ""

        if framework == "kronos" or ext in (".kronos",) or "kronos" in filename.lower():
            return self._parse_kronos(source, metadata, filename)
        elif ext in (".pt", ".pth"):
            return self._parse_pytorch(source, metadata, filename)
        elif ext in (".h5", ".pb"):
            return self._parse_tensorflow(source, metadata, filename)
        elif ext in (".pkl", ".joblib"):
            return self._parse_scikit(source, metadata, filename)
        elif ext in (".json", ".bst", ".txt"):
            return self._parse_xgboost(source, metadata, filename)
        else:
            raise ValueError(f"Unsupported ML framework extension: {ext}")

    def _compute_phi_c(self, auc: float, complexity: float, bias: float, latency: float) -> float:
        perf = self.alpha * auc
        comp_term = self.beta * math.log10(max(complexity, 1))
        equity = self.gamma * (1.0 - bias)
        eff = self.delta * math.exp(-self.lambda_val * latency)

        phi = perf - comp_term + equity + eff
        return max(0.0, min(1.0, phi))

    def _parse_pytorch(self, source: bytes, metadata: Dict, filename: str) -> LFIRGraph:
        graph = LFIRGraph(project_id="ml_models", language=Language.UNKNOWN)
        root = LFIRNode("pytorch_model", "pytorch_model", "pytorch", Language.UNKNOWN, filename, 0, 0)
        graph.add_node(root)

        try:
            import torch
            model = torch.load(io.BytesIO(source), map_location="cpu")
            if hasattr(model, "state_dict"):
                state = model.state_dict()
            else:
                state = model

            total_params = sum(p.numel() for p in state.values() if hasattr(p, 'numel'))
        except Exception:
            total_params = 25600000 # Default fallback for missing torch

        root.metadata["total_params"] = total_params
        root.metadata["architecture"] = "ResNet-50" # default mock

        # Calculate Phi_C
        auc = metadata.get("auc", 0.942) if metadata else 0.942
        bias = metadata.get("bias", 0.03) if metadata else 0.03
        latency = metadata.get("latency", 2.3) if metadata else 2.3

        coherence = self._compute_phi_c(auc, total_params, bias, latency)
        root.metadata["coherence"] = coherence

        return graph

    def _parse_kronos(self, source: bytes, metadata: Dict, filename: str) -> LFIRGraph:
        graph = LFIRGraph(project_id="ml_models", language=Language.UNKNOWN)
        root = LFIRNode("kronos_model", "kronos_model", "kronos", Language.UNKNOWN, filename, 0, 0)
        graph.add_node(root)

        try:
            import torch
            model = torch.load(io.BytesIO(source), map_location="cpu")
            if hasattr(model, "state_dict"):
                state = model.state_dict()
            else:
                state = model
            total_params = sum(p.numel() for p in state.values() if hasattr(p, 'numel'))
        except Exception:
            total_params = 24700000 # Default fallback to Kronos-small size 24.7M

        root.metadata["total_params"] = total_params
        root.metadata["architecture"] = "Kronos Foundation Model"

        root.metadata["lookback"] = metadata.get("lookback", 400) if metadata else 400
        root.metadata["pred_len"] = metadata.get("pred_len", 120) if metadata else 120

        auc = metadata.get("auc", 0.942) if metadata else 0.942
        bias = metadata.get("bias", 0.03) if metadata else 0.03
        latency = metadata.get("latency", 2.3) if metadata else 2.3

        coherence = self._compute_phi_c(auc, total_params, bias, latency)
        root.metadata["coherence"] = coherence

        return graph

    def _parse_tensorflow(self, source: bytes, metadata: Dict, filename: str) -> LFIRGraph:
        graph = LFIRGraph(project_id="ml_models", language=Language.UNKNOWN)
        root = LFIRNode("tensorflow_model", "tensorflow_model", "tensorflow", Language.UNKNOWN, filename, 0, 0)
        graph.add_node(root)

        total_params = 1000000
        root.metadata["total_params"] = total_params

        auc = metadata.get("auc", 0.41) if metadata else 0.41
        bias = metadata.get("bias", 0.1) if metadata else 0.1
        latency = metadata.get("latency", 5.0) if metadata else 5.0

        coherence = self._compute_phi_c(auc, total_params, bias, latency)
        root.metadata["coherence"] = coherence

        return graph

    def _parse_scikit(self, source: bytes, metadata: Dict, filename: str) -> LFIRGraph:
        graph = LFIRGraph(project_id="ml_models", language=Language.UNKNOWN)
        root = LFIRNode("sklearn_model", "sklearn_model", "sklearn", Language.UNKNOWN, filename, 0, 0)
        graph.add_node(root)

        total_params = 1000
        root.metadata["total_params"] = total_params

        auc = metadata.get("auc", 0.68) if metadata else 0.68
        bias = metadata.get("bias", 0.4) if metadata else 0.4 # high bias
        latency = metadata.get("latency", 1.0) if metadata else 1.0

        coherence = self._compute_phi_c(auc, total_params, bias, latency)
        root.metadata["coherence"] = coherence

        return graph

    def _parse_xgboost(self, source: bytes, metadata: Dict, filename: str) -> LFIRGraph:
        graph = LFIRGraph(project_id="ml_models", language=Language.UNKNOWN)
        root = LFIRNode("xgboost_model", "xgboost_model", "xgboost", Language.UNKNOWN, filename, 0, 0)
        graph.add_node(root)

        try:
            config = json.loads(source.decode('utf-8'))
            n_trees = int(config.get("learner", {}).get("gradient_booster", {}).get("gbtree_train_param", {}).get("num_parallel_tree", 100))
            max_depth = int(config.get("learner", {}).get("gradient_booster", {}).get("gbtree_train_param", {}).get("max_depth", 6))
        except Exception:
            n_trees = 100
            max_depth = 6

        root.metadata["n_estimators"] = n_trees
        root.metadata["max_depth"] = max_depth

        complexity = n_trees * math.log2(max(max_depth, 2))
        # For ensemble models, the complexity replaces params directly in the formula since
        # beta * log10(complexity) vs beta * log10(params)

        auc = metadata.get("auc", 0.941) if metadata else 0.941
        bias = metadata.get("bias", 0.05) if metadata else 0.05
        latency = metadata.get("latency", 1.5) if metadata else 1.5

        coherence = self._compute_phi_c(auc, complexity, bias, latency)
        root.metadata["coherence"] = coherence

        return graph
