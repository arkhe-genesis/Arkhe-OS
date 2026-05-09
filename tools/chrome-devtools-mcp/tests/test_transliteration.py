import pytest
import numpy as np
from arkhe_core.transliteration.algebra import Clifford4D
from arkhe_core.transliteration.synthesis import SyntheticCore, SynthesisViolation
from arkhe_core.transliteration.coherence import CoherenceEnforcer, CoherenceViolation
from arkhe_core.transliteration.cohesion import CohesionGuardian, CohesionViolation
from arkhe_core.transliteration.dependencies import K6O_Cathedral, QNode
from arkhe_core.transliteration.transliterator import ArkheTransliterator

@pytest.fixture
def algebra():
    return Clifford4D()

@pytest.fixture
def synthesis(algebra):
    return SyntheticCore(algebra)

@pytest.fixture
def k6o():
    return K6O_Cathedral(n_nodes=10, K=1.0)

@pytest.fixture
def qnode():
    qn = QNode(node_id="test-node")
    qn.entangled_pairs["remote"] = (0, 0)
    return qn

@pytest.fixture
def coherence(k6o):
    return CoherenceEnforcer(k6o)

@pytest.fixture
def cohesion(qnode):
    return CohesionGuardian(qnode)

def test_synthesis_truncation(synthesis, algebra):
    # Cria um multivector com dados em todas as grades (0-4)
    data = np.ones(algebra.total_size)

    # Vamos usar b diferente de zero para testar fusão
    b = np.zeros(algebra.total_size)
    b[0] = 1.0 # scalar = 1

    fused = synthesis.fuse(data, b)

    assert np.all(fused[11:] == 0)
    # Grade 0: a[0]*b[0] + dot = 1*1 + 0 = 1
    assert fused[0] != 0

def test_synthesis_entropy_check(synthesis, algebra):
    s1 = np.zeros(algebra.total_size)
    s1[0] = 1.0

    s2 = np.zeros(algebra.total_size)
    s2[1] = 1.0

    fused = synthesis.fuse(s1, s2)
    # Entropia sintética não deve aumentar
    assert synthesis.synthetic_entropy(fused) <= max(synthesis.synthetic_entropy(s1), synthesis.synthetic_entropy(s2)) + 1e-6

def test_coherence_enforcement(coherence):
    state = np.random.rand(16)
    source_phase = 0.0
    target = "SUBSTRATE_B"

    coherence.k6o.phases = np.zeros(coherence.k6o.n_nodes) # r=1
    _, target_phase = coherence.transliterate(state, source_phase, target)
    assert isinstance(target_phase, (float, np.float64))

def test_coherence_violation(k6o):
    # Força decoerência total
    k6o.K = 0.5
    # Espalha fases para r -> 0
    k6o.phases = np.linspace(0, 2*np.pi, k6o.n_nodes, endpoint=False)

    enforcer = CoherenceEnforcer(k6o)
    state = np.random.rand(16)

    with pytest.raises(CoherenceViolation):
        enforcer.transliterate(state, 0.0, "SUBSTRATE_X")

def test_cohesion_causal_check(cohesion):
    features = ["A", "B"]
    state_src = np.array([0.5, 0.5])
    state_tgt = np.array([0.5, 0.5])
    mapping = {"A": "A'", "B": "B'"}
    target_features = ["A'", "B'"]

    G_src = cohesion.extract_causal_graph(state_src, features)
    G_tgt = cohesion.extract_causal_graph(state_tgt, target_features)

    assert cohesion.verify_cohesion(G_src, G_tgt, mapping)

def test_cohesion_violation(cohesion):
    features = ["A", "B"]
    state_src = np.array([1.0, 1.0])
    state_tgt = np.array([0.0, 0.0])
    mapping = {"A": "A'", "B": "B'"}
    target_features = ["A'", "B'"]

    G_src = cohesion.extract_causal_graph(state_src, features)
    G_tgt = cohesion.extract_causal_graph(state_tgt, target_features)

    with pytest.raises(CohesionViolation):
        cohesion.verify_cohesion(G_src, G_tgt, mapping)

def test_full_transliteration(k6o, qnode):
    k6o.phases = np.zeros(k6o.n_nodes) # r=1
    transliterator = ArkheTransliterator(k6o, qnode)

    payload = np.random.rand(16)
    src_feat = ["sensor_x", "sensor_y"]
    tgt_feat = ["node_a", "node_b"]
    mapping = {"sensor_x": "node_a", "sensor_y": "node_b"}

    result, phase = transliterator.transmute(
        payload, "SENSOR", "CORE", 0.5, src_feat, tgt_feat, mapping
    )

    assert result.shape == (16,)
    assert 0 <= phase <= 2 * np.pi
    assert len(transliterator.history) == 1
