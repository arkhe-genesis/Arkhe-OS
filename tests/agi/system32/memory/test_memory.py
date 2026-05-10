import pytest
import numpy as np
import networkx as nx
import os
import sys

# Ensure agi can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

from agi.system32.memory.graph_store import LFIRGraphStore
from agi.system32.memory.vector_index import SemanticVectorIndex
from agi.system32.memory.rcp_align import RetrocausalAligner
from agi.system32.memory.retrieval_engine import CoherenceGuidedRetrieval

class MockRCPEngine:
    def simulate_trajectory(self, start_state, steps, policy):
        return [{"coherence": 0.8}, {"coherence": 0.9}]

class MockPolicyEngine:
    def get_current_policy(self):
        return "mock_policy"

def test_graph_store(tmp_path):
    db_path = tmp_path / "test_graph.gml"
    store = LFIRGraphStore(db_path=str(db_path))

    mock_graph = nx.Graph()
    mock_graph.add_node("concept1")

    store.store_state("state1", mock_graph, coherence=0.8, metadata={"type": "test"})
    store.store_state("state2", mock_graph, coherence=0.4, metadata={"type": "test"})

    high_coh = store.retrieve_by_coherence(0.7)
    assert len(high_coh) == 1
    assert "state1" in high_coh

    pruned = store.prune_low_coherence(0.5)
    assert pruned == 1
    assert "state2" not in store.graph.nodes()

def test_vector_index():
    index = SemanticVectorIndex(dim=4)

    # Mock embeddings
    emb1 = np.array([1.0, 0.0, 0.0, 0.0])
    emb2 = np.array([0.0, 1.0, 0.0, 0.0])

    index.add("state1", emb1, coherence=0.9)
    index.add("state2", emb2, coherence=0.5)

    results = index.search(emb1, k=1, min_coherence=0.6)
    assert len(results) == 1
    assert results[0]["state_id"] == "state1"

def test_rcp_aligner():
    rcp = MockRCPEngine()
    policy = MockPolicyEngine()
    aligner = RetrocausalAligner(rcp_engine=rcp, policy_engine=policy)

    mem_states = [
        {"state_id": "state1", "similarity": 0.8},
        {"state_id": "state2", "similarity": 0.6}
    ]

    aligned = aligner.align_query({"query": "test"}, mem_states)
    assert len(aligned) == 2
    assert aligned[0]["state_id"] == "state1" # similarity should preserve order

def test_retrieval_engine(tmp_path):
    db_path = tmp_path / "test_graph.gml"
    graph_store = LFIRGraphStore(db_path=str(db_path))
    vector_index = SemanticVectorIndex(dim=768)

    rcp = MockRCPEngine()
    policy = MockPolicyEngine()
    rcp_aligner = RetrocausalAligner(rcp_engine=rcp, policy_engine=policy)

    # Add a mock embedding to the vector index so it can find something
    np.random.seed(42)
    mock_emb = np.random.randn(768)
    vector_index.add("state1", mock_emb, coherence=0.9)

    engine = CoherenceGuidedRetrieval(graph_store, vector_index, rcp_aligner)

    results = engine.retrieve({"query": "test_query"}, k=1)

    assert len(results) == 1
    assert results[0]["state_id"] == "state1"
