"""
Tests for Substrato 9029 - Superlinked SIE Integration
"""

import sys
import importlib.util
import pytest

module_name = 'sie_integration'
module_path = 'substrates/9029_superlinked_sie/sie_integration.py'
spec = importlib.util.spec_from_file_location(module_name, module_path)
sie_module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = sie_module
spec.loader.exec_module(sie_module)

SIEIntegration = sie_module.SIEIntegration

class MockTC:
    def __init__(self):
        self.events = []

    def anchor_event(self, event_type, payload):
        self.events.append({"event_type": event_type, "payload": payload})
        return "mock_anchor"

class MockGuardian:
    pass

def test_sie_integration_init():
    sie = SIEIntegration()
    assert "bge-small-en-v1.5" in sie.sie.models
    assert sie.sie.models["bge-small-en-v1.5"] == "encode"

def test_sie_encode():
    sie = SIEIntegration()
    texts = ["test1", "test2"]
    embeddings = sie.encode_text(texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 768

def test_sie_score():
    sie = SIEIntegration()
    texts = ["doc1", "doc2"]
    scores = sie.score_documents("query", texts)
    assert len(scores) == 2
    assert isinstance(scores[0], float)

def test_sie_extract():
    sie = SIEIntegration()
    texts = ["doc1", "doc2"]
    entities = sie.extract_entities(texts, {"type": "person"})
    assert len(entities) == 2
    assert "entities" in entities[0]

def test_sie_anchoring():
    tc = MockTC()
    sie = SIEIntegration(temporal_chain=tc)

    sie.encode_text(["test"])
    sie.score_documents("query", ["doc1"])
    sie.extract_entities(["doc1"], {"type": "person"})

    assert len(tc.events) == 3
    assert tc.events[0]["payload"]["task"] == "encode"
    assert tc.events[1]["payload"]["task"] == "score"
    assert tc.events[2]["payload"]["task"] == "extract"

if __name__ == "__main__":
    pytest.main(["-v", "test_substrato_9029.py"])
