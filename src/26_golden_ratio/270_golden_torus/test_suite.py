import pytest
import math
import os
import sys

# Because the directories start with numbers which are invalid Python module names without importlib hacking,
# we add the exact dir to sys path for the test.
sys.path.insert(0, os.path.dirname(__file__))

from torus_engine import GoldenTorusEngine, PHI, PHI_INV, PHI_SQ

@pytest.fixture
def engine():
    return GoldenTorusEngine()

def test_t01_golden_constants():
    """T01 — Golden ratio constants"""
    assert math.isclose(PHI, 1.618033988749895)
    assert math.isclose(PHI_INV, 0.6180339887498949)
    assert math.isclose(PHI_SQ, 2.618033988749895)

def test_t02_engine_initialization(engine):
    """T02 — Engine initialization"""
    assert engine.topologies == {}
    assert engine.unified_adaptation_score == 0.0

def test_t03_golden_spiral_placement(engine):
    """T03 — Golden spiral placement"""
    nodes = engine._generate_golden_spiral_nodes(10, "test")
    assert len(nodes) == 10
    assert all(math.isclose(math.sqrt(n.x**2 + n.y**2 + n.z**2), 1.0, rel_tol=1e-5) for n in nodes)

def test_t04_toroidal_distance(engine):
    """T04 — Toroidal distance"""
    nodes = engine._generate_golden_spiral_nodes(2, "test")
    dist = engine.compute_toroidal_distance(nodes[0], nodes[1])
    assert dist > 0

def test_t05_mycelium_topology(engine):
    """T05 — Mycelium topology"""
    topo = engine.generate_mycelium(144)
    assert len(topo["nodes"]) == 144
    assert len(topo["gaps"]) > 0

def test_t06_synaptic_topology(engine):
    """T06 — Synaptic topology"""
    topo = engine.generate_synaptic(89)
    assert len(topo["nodes"]) == 89
    assert len(topo["gaps"]) > 0

def test_t07_quantum_vacuum_topology(engine):
    """T07 — Quantum vacuum topology"""
    topo = engine.generate_quantum_vacuum(233)
    assert len(topo["nodes"]) == 233
    assert len(topo["gaps"]) > 0

def test_t08_relay_memory_topology(engine):
    """T08 — Relay memory topology"""
    topo = engine.generate_relay_memory(55)
    assert len(topo["nodes"]) == 55
    assert len(topo["gaps"]) > 0

def test_t09_gap_generation(engine):
    """T09 — Gap generation"""
    topo = engine.generate_synaptic(10)
    gap = topo["gaps"][0]
    assert gap.permeability == 0.9
    assert gap.resonance > 0
    assert gap.information_flow > 0

def test_t10_phi_spectral_density(engine):
    """T10 — Phi spectral density"""
    topo = engine.generate_mycelium(10)
    assert engine.calculate_phi_spectral_density(topo) == PHI


def test_t11_adaptation_score(engine):
    """T11 — Adaptation score"""
    topo = engine.generate_synaptic(10)
    score = engine.compute_adaptation_score(topo)
    assert score == 1.0

def test_t12_all_four_topologies(engine):
    """T12 — All four topologies"""
    engine.unify_all_topologies()
    assert "mycelium" in engine.topologies
    assert "synaptic" in engine.topologies
    assert "quantum_vacuum" in engine.topologies
    assert "relay_memory" in engine.topologies

def test_t13_unified_adaptation(engine):
    """T13 — Unified adaptation"""
    engine.unify_all_topologies()
    assert engine.unified_adaptation_score == 1.0

def test_t14_full_unification_pipeline(engine):
    """T14 — Full unification pipeline"""
    topo = engine.unify_all_topologies()
    assert len(topo) == 4

def test_t15_json_export(engine, tmp_path):
    """T15 — JSON export"""
    engine.unify_all_topologies()
    filepath = tmp_path / "test_unified.json"
    engine.export_to_json(str(filepath))
    assert filepath.exists()
    import json
    with open(filepath) as f:
        data = json.load(f)
    assert "topologies" in data
    assert "metrics" in data

def test_t16_bus_interface(engine):
    """T16 — Bus interface"""
    # Simply test access as a mock for bus interfacing
    topo = engine.generate_relay_memory(10)
    assert isinstance(topo, dict)

def test_t17_node_seals(engine):
    """T17 — Node seals"""
    nodes = engine._generate_golden_spiral_nodes(5, "test")
    seals = engine.generate_node_seals(nodes)
    assert len(seals) == 5
    assert all(isinstance(s, str) and len(s) == 64 for s in seals)

def test_t18_timestamp(engine):
    """T18 — Timestamp"""
    ts = engine.get_timestamp()
    assert isinstance(ts, float)
    assert ts > 0

def test_t19_gap_permeability(engine):
    """T19 — Gap permeability"""
    topo = engine.generate_mycelium(10)
    # the maximum generated distances in mycelium topology result in varied resonances
    for gap in topo["gaps"]:
        assert gap.permeability == 0.8
        assert gap.information_flow > 0

def test_t20_resonance_modes(engine):
    """T20 — Resonance modes"""
    topo = engine.generate_synaptic(10)
    modes = engine.get_resonance_modes(topo)
    assert len(modes) == 4
    assert PHI_INV in modes
    assert 1.0 in modes
    assert PHI in modes
    assert PHI_SQ in modes
