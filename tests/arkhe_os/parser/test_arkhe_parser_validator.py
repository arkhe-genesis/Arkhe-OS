import pytest
import numpy as np
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from arkhe_os.parser.arkhe_parser_validator import (
    MercyGap, RiemannianState, Stage, CompetencyNode, ArkheParserValidator,
    EmbeddingVector, ImprovedEmbeddingEngine, VectorStore, ImprovedRAGPipeline,
    FineTuningEngine, SubstrateBridge
)

def test_mercy_gap():
    assert MercyGap.validate(0.05) == True
    assert MercyGap.validate(0.01) == False
    assert MercyGap.validate(0.2) == False
    assert MercyGap.clamp(0.01) == 0.04
    assert MercyGap.clamp(0.2) == 0.10
    assert MercyGap.clamp(0.05) == 0.05

def test_riemannian_state():
    coords = np.array([1.0, 0.0])
    metric = np.eye(2)
    state1 = RiemannianState(coordinates=coords, metric_tensor=metric)
    state2 = RiemannianState(coordinates=np.array([0.0, 1.0]), metric_tensor=metric)
    assert state1.geodesic_distance(state2) == pytest.approx(np.sqrt(2))
    coh = state1.compute_coherence(state2)
    assert coh == pytest.approx(np.exp(-2.0 / 2.0))

def test_validator_initialization():
    validator = ArkheParserValidator("test_user")
    assert validator.learner_id == "test_user"
    assert len(validator.states) > 0
    assert "PY-01" in validator.states
    assert "PY-01_optimal" in validator.states

def test_validator_submit_exercise():
    validator = ArkheParserValidator("test_user")
    result = validator.submit_exercise("PY-01", 1.0, 10.0)
    assert "mastery" in result
    assert "coherence" in result
    assert result["mastery"] > 0

def test_embedding_vector():
    vec = EmbeddingVector(text="test", vector=np.array([1.0, 1.0]))
    assert np.linalg.norm(vec.vector) == pytest.approx(1.0)

def test_embedding_engine():
    engine = ImprovedEmbeddingEngine(dim=16)
    emb = engine.embed("quantum computing")
    assert isinstance(emb, EmbeddingVector)
    assert len(emb.vector) == 16

def test_vector_store():
    store = VectorStore(dim=16)
    engine = ImprovedEmbeddingEngine(dim=16)
    store.add_texts(["text1", "text2"], engine=engine)
    assert len(store.vectors) == 2

def test_rag_pipeline():
    engine = ImprovedEmbeddingEngine(dim=16)
    store = VectorStore(dim=16)
    store.add_texts(["This is about quantum mechanics", "AI is cool"], engine=engine)
    rag = ImprovedRAGPipeline(engine, store, top_k=1)
    res = rag.query("quantum mechanics")
    assert "response" in res

def test_finetuning_engine():
    ft = FineTuningEngine(base_dim=16, rank=4)
    x = np.random.randn(5, 16)
    y = np.random.randn(5, 16)
    res = ft.train_step(x, y)
    assert "loss" in res
    assert "grad_norm" in res

def test_substrate_bridge():
    validator = ArkheParserValidator("test_user")
    bridge = SubstrateBridge()
    # Should not unlock since incomplete
    res = bridge.unlock_stage(Stage.PYTHON, validator)
    assert res["unlocked"] == False
