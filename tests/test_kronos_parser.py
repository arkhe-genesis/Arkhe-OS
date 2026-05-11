import pytest
from arkhe_os.parser.frontends.ml_framework_parser import MLFrameworkParser

def test_kronos_parser():
    parser = MLFrameworkParser()

    source = b'dummy kronos source'
    metadata = {
        "framework": "kronos",
        "lookback": 512,
        "pred_len": 60,
        "auc": 0.95,
        "bias": 0.02,
        "latency": 1.5
    }

    graph = parser.parse(source, "model.pt", metadata)

    assert len(graph.nodes) == 1
    root = list(graph.nodes.values())[0]

    assert root.name == "kronos_model"
    assert root.node_type == "kronos"
    assert root.metadata["lookback"] == 512
    assert root.metadata["pred_len"] == 60
    assert root.metadata["architecture"] == "Kronos Foundation Model"
    assert root.metadata["total_params"] == 24700000  # Default fallback since dummy source won't load in torch

    # Coherence should be > 0
    assert root.metadata["coherence"] > 0.0

def test_kronos_parser_extension():
    parser = MLFrameworkParser()
    source = b'dummy kronos source'

    graph = parser.parse(source, "model.kronos")

    assert len(graph.nodes) == 1
    root = list(graph.nodes.values())[0]

    assert root.name == "kronos_model"
    assert root.metadata["lookback"] == 400  # Default fallback
    assert root.metadata["pred_len"] == 120  # Default fallback
