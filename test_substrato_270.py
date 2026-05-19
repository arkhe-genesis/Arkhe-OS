#!/usr/bin/env python3
"""
ARKHE OS Substrate 270 Test Suite (Standalone)
Canon: ∞.Ω.∇+++.270.golden_torus.tests
"""

import asyncio
import hashlib
import json
import time
import sys
import os
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum, auto

# ── Inline Substrate 270 ──

PHI = (1 + np.sqrt(5)) / 2
PHI_INV = 1 / PHI
PHI_SQUARED = PHI ** 2

class InstanceType(Enum):
    MYCELIUM = auto()
    SYNAPTIC_CLEFT = auto()
    QUANTUM_VACUUM = auto()
    RELAY_NODE_MEMORY = auto()

@dataclass
class ToroidalNode:
    node_id: str
    instance_type: InstanceType
    phi_coordinate: float
    theta_coordinate: float
    major_radius: float
    minor_radius: float
    golden_ratio: float = PHI
    energy_state: float = 0.0
    connectivity_degree: int = 0
    seal: str = ""

@dataclass
class GapField:
    gap_id: str
    source_node: str
    target_node: str
    gap_width: float
    permeability: float
    resonance_freq: float
    information_flux: float
    entanglement_strength: float

@dataclass
class ToroidalTopology:
    topology_id: str
    instance_type: InstanceType
    nodes: List[ToroidalNode]
    gaps: List[GapField]
    total_nodes: int
    total_gaps: int
    mean_connectivity: float
    phi_spectral_density: float
    adaptation_score: float
    canonical_seal: str
    timestamp: float

@dataclass
class GoldenAdaptation:
    system_name: str
    measured_ratio: float
    deviation_from_phi: float
    adaptation_quality: float
    is_optimal: bool
    resonance_modes: List[float]

class ArkheGoldenTorusEngine:
    def __init__(self, num_nodes: int = 144):
        self.num_nodes = num_nodes
        self.topologies: Dict[InstanceType, ToroidalTopology] = {}
        self.adaptations: List[GoldenAdaptation] = []

    def _hash(self, text: str) -> str:
        return hashlib.sha3_256(text.encode()).hexdigest()[:32]

    def _toroidal_distance(self, n1: ToroidalNode, n2: ToroidalNode) -> float:
        d_phi = abs(n1.phi_coordinate - n2.phi_coordinate)
        d_phi = min(d_phi, 2 * np.pi - d_phi)
        d_theta = abs(n1.theta_coordinate - n2.theta_coordinate)
        d_theta = min(d_theta, 2 * np.pi - d_theta)
        return np.sqrt(d_phi**2 + (PHI_INV * d_theta)**2)

    def _golden_spiral_placement(self, n: int) -> List[Tuple[float, float]]:
        coordinates = []
        for i in range(n):
            golden_angle = 2 * np.pi / PHI_SQUARED
            phi_coord = (i * golden_angle) % (2 * np.pi)
            theta_coord = (i * golden_angle * PHI) % (2 * np.pi)
            coordinates.append((phi_coord, theta_coord))
        return coordinates

    async def generate_mycelium_topology(self) -> ToroidalTopology:
        coords = self._golden_spiral_placement(self.num_nodes)
        nodes = []
        for i, (phi, theta) in enumerate(coords):
            node = ToroidalNode(
                node_id=f"myc_{i:04d}", instance_type=InstanceType.MYCELIUM,
                phi_coordinate=phi, theta_coordinate=theta,
                major_radius=PHI * 10, minor_radius=PHI_INV * 5,
                energy_state=np.random.exponential(PHI),
                connectivity_degree=int(np.random.poisson(PHI * 3)),
                seal=self._hash(f"mycelium_{i}_{time.time()}")
            )
            nodes.append(node)
        gaps = self._generate_gaps(nodes)
        topo = ToroidalTopology(
            topology_id=self._hash("mycelium_topology"), instance_type=InstanceType.MYCELIUM,
            nodes=nodes, gaps=gaps, total_nodes=len(nodes), total_gaps=len(gaps),
            mean_connectivity=np.mean([n.connectivity_degree for n in nodes]),
            phi_spectral_density=self._calculate_phi_spectral_density(nodes),
            adaptation_score=self._calculate_adaptation_score(nodes),
            canonical_seal="", timestamp=time.time()
        )
        topo.canonical_seal = self._seal_topology(topo)
        self.topologies[InstanceType.MYCELIUM] = topo
        return topo

    async def generate_synaptic_topology(self, n_synapses: int = 10000) -> ToroidalTopology:
        coords = self._golden_spiral_placement(n_synapses)
        nodes = []
        for i, (phi, theta) in enumerate(coords):
            node = ToroidalNode(
                node_id=f"syn_{i:05d}", instance_type=InstanceType.SYNAPTIC_CLEFT,
                phi_coordinate=phi, theta_coordinate=theta,
                major_radius=PHI * 0.5, minor_radius=PHI_INV * 0.1,
                energy_state=np.random.gamma(PHI, PHI_INV),
                connectivity_degree=int(np.random.poisson(PHI * 2)),
                seal=self._hash(f"synapse_{i}_{time.time()}")
            )
            nodes.append(node)
        gaps = self._generate_gaps(nodes)
        topo = ToroidalTopology(
            topology_id=self._hash("synaptic_topology"), instance_type=InstanceType.SYNAPTIC_CLEFT,
            nodes=nodes, gaps=gaps, total_nodes=len(nodes), total_gaps=len(gaps),
            mean_connectivity=np.mean([n.connectivity_degree for n in nodes]),
            phi_spectral_density=self._calculate_phi_spectral_density(nodes),
            adaptation_score=self._calculate_adaptation_score(nodes),
            canonical_seal="", timestamp=time.time()
        )
        topo.canonical_seal = self._seal_topology(topo)
        self.topologies[InstanceType.SYNAPTIC_CLEFT] = topo
        return topo

    async def generate_quantum_vacuum_topology(self, n_fluctuations: int = 1000) -> ToroidalTopology:
        coords = self._golden_spiral_placement(n_fluctuations)
        nodes = []
        for i, (phi, theta) in enumerate(coords):
            node = ToroidalNode(
                node_id=f"vac_{i:04d}", instance_type=InstanceType.QUANTUM_VACUUM,
                phi_coordinate=phi, theta_coordinate=theta,
                major_radius=PHI * 1.616e-35, minor_radius=PHI_INV * 1.616e-35,
                energy_state=np.random.exponential(PHI_INV),
                connectivity_degree=int(np.random.poisson(PHI)),
                seal=self._hash(f"vacuum_{i}_{time.time()}")
            )
            nodes.append(node)
        gaps = self._generate_gaps(nodes)
        topo = ToroidalTopology(
            topology_id=self._hash("vacuum_topology"), instance_type=InstanceType.QUANTUM_VACUUM,
            nodes=nodes, gaps=gaps, total_nodes=len(nodes), total_gaps=len(gaps),
            mean_connectivity=np.mean([n.connectivity_degree for n in nodes]),
            phi_spectral_density=self._calculate_phi_spectral_density(nodes),
            adaptation_score=self._calculate_adaptation_score(nodes),
            canonical_seal="", timestamp=time.time()
        )
        topo.canonical_seal = self._seal_topology(topo)
        self.topologies[InstanceType.QUANTUM_VACUUM] = topo
        return topo

    async def generate_relay_memory_topology(self) -> ToroidalTopology:
        n_memories = len(self.topologies) * 100 if self.topologies else 500
        coords = self._golden_spiral_placement(n_memories)
        nodes = []
        for i, (phi, theta) in enumerate(coords):
            node = ToroidalNode(
                node_id=f"mem_{i:04d}", instance_type=InstanceType.RELAY_NODE_MEMORY,
                phi_coordinate=phi, theta_coordinate=theta,
                major_radius=PHI * 1.0, minor_radius=PHI_INV * 0.5,
                energy_state=np.random.beta(PHI, PHI),
                connectivity_degree=int(np.random.poisson(PHI * 4)),
                seal=self._hash(f"memory_{i}_{time.time()}")
            )
            nodes.append(node)
        gaps = self._generate_gaps(nodes)
        topo = ToroidalTopology(
            topology_id=self._hash("relay_memory_topology"), instance_type=InstanceType.RELAY_NODE_MEMORY,
            nodes=nodes, gaps=gaps, total_nodes=len(nodes), total_gaps=len(gaps),
            mean_connectivity=np.mean([n.connectivity_degree for n in nodes]),
            phi_spectral_density=self._calculate_phi_spectral_density(nodes),
            adaptation_score=self._calculate_adaptation_score(nodes),
            canonical_seal="", timestamp=time.time()
        )
        topo.canonical_seal = self._seal_topology(topo)
        self.topologies[InstanceType.RELAY_NODE_MEMORY] = topo
        return topo

    def _generate_gaps(self, nodes: List[ToroidalNode]) -> List[GapField]:
        gaps = []
        for i, n1 in enumerate(nodes):
            k = int(PHI * 2)
            distances = [(j, self._toroidal_distance(n1, n2)) for j, n2 in enumerate(nodes) if i != j]
            distances.sort(key=lambda x: x[1])
            for j, dist in distances[:k]:
                n2 = nodes[j]
                gap = GapField(
                    gap_id=f"gap_{n1.node_id}_{n2.node_id}",
                    source_node=n1.node_id, target_node=n2.node_id,
                    gap_width=dist, permeability=np.exp(-dist / PHI),
                    resonance_freq=PHI ** (dist / (2 * np.pi)),
                    information_flux=np.random.exponential(PHI) * n1.connectivity_degree,
                    entanglement_strength=np.exp(-dist * PHI_INV)
                )
                gaps.append(gap)
        return gaps

    def _calculate_phi_spectral_density(self, nodes: List[ToroidalNode]) -> float:
        phi_coords = np.array([n.phi_coordinate for n in nodes])
        theta_coords = np.array([n.theta_coordinate for n in nodes])
        spectrum = np.abs(np.fft.fft(phi_coords + 1j * theta_coords))
        freqs = np.fft.fftfreq(len(nodes))
        target_freq = PHI / (2 * np.pi)
        idx = np.argmin(np.abs(freqs - target_freq))
        return float(spectrum[idx] / len(nodes))

    def _calculate_adaptation_score(self, nodes: List[ToroidalNode]) -> float:
        degrees = [n.connectivity_degree for n in nodes if n.connectivity_degree > 0]
        if len(degrees) < 2:
            return 0.0
        ratios = [degrees[i+1] / degrees[i] for i in range(len(degrees)-1) if degrees[i] > 0]
        if not ratios:
            return 0.0
        deviations = [abs(r - PHI) / PHI for r in ratios]
        return float(1.0 - np.mean(deviations))

    def _seal_topology(self, topology: ToroidalTopology) -> str:
        seal_input = json.dumps({
            'type': topology.instance_type.name, 'nodes': topology.total_nodes,
            'gaps': topology.total_gaps, 'phi_density': round(topology.phi_spectral_density, 6),
            'adaptation': round(topology.adaptation_score, 6), 'timestamp': topology.timestamp,
        }, sort_keys=True)
        return hashlib.sha3_256(seal_input.encode()).hexdigest()

    async def calculate_unified_adaptation(self) -> GoldenAdaptation:
        if not self.topologies:
            return GoldenAdaptation("unified_-1D", 0.0, 1.0, 0.0, False, [])
        scores = [t.adaptation_score for t in self.topologies.values()]
        mean_score = np.mean(scores)
        unified_ratio = PHI * mean_score + PHI_INV * (1 - mean_score)
        deviation = abs(unified_ratio - PHI) / PHI
        resonance_modes = []
        types = list(self.topologies.keys())
        for i in range(len(types)):
            for j in range(i+1, len(types)):
                t1 = self.topologies[types[i]]
                t2 = self.topologies[types[j]]
                mode = (t1.phi_spectral_density + t2.phi_spectral_density) / 2
                resonance_modes.append(float(mode))
        adaptation = GoldenAdaptation(
            system_name="unified_-1D_infrastructure",
            measured_ratio=float(unified_ratio), deviation_from_phi=float(deviation),
            adaptation_quality=float(1.0 - deviation), is_optimal=deviation < 0.1,
            resonance_modes=resonance_modes
        )
        self.adaptations.append(adaptation)
        return adaptation

    async def run_full_unification(self) -> Dict:
        await self.generate_mycelium_topology()
        await self.generate_synaptic_topology(n_synapses=50)
        await self.generate_quantum_vacuum_topology(n_fluctuations=20)
        await self.generate_relay_memory_topology()
        unified = await self.calculate_unified_adaptation()
        return {
            'topologies': {k.name: asdict(v) for k, v in self.topologies.items()},
            'unified_adaptation': asdict(unified), 'phi': PHI, 'phi_inv': PHI_INV,
            'phi_squared': PHI_SQUARED, 'canonical_seal': self._hash(f"unified_{time.time()}"),
            'timestamp': time.time()
        }

    def export_json(self, data: Dict, path: str):
        def encoder(obj):
            if isinstance(obj, np.ndarray): return obj.tolist()
            if isinstance(obj, Enum): return obj.name
            if isinstance(obj, (bool, np.bool_)): return bool(obj)
            if isinstance(obj, (np.floating, np.integer, int, float)): return float(obj)
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=encoder)

class ArkheGoldenTorusBusInterface:
    def __init__(self, engine: ArkheGoldenTorusEngine):
        self.engine = engine
    async def publish_to_bus(self, data: Dict) -> Tuple[bool, str]:
        bus_payload = {
            'substrate': '270', 'canon': '∞.Ω.∇+++.270.golden_torus',
            'instances': [t.name for t in self.engine.topologies.keys()],
            'total_nodes': sum(t.total_nodes for t in self.engine.topologies.values()),
            'total_gaps': sum(t.total_gaps for t in self.engine.topologies.values()),
            'phi': PHI, 'unified_adaptation': data.get('unified_adaptation', {}).get('adaptation_quality', 0),
            'seal': data.get('canonical_seal', ''),
        }
        bus_seal = hashlib.sha3_256(json.dumps(bus_payload, sort_keys=True).encode()).hexdigest()
        return True, bus_seal

# ── Test Registry ──
TESTS_PASSED = 0
TESTS_FAILED = 0
FAILED_LIST = []

def test(name):
    def decorator(func):
        async def wrapper():
            global TESTS_PASSED, TESTS_FAILED
            try:
                await func()
                TESTS_PASSED += 1
                print(f"  ✓ {name}")
            except Exception as e:
                TESTS_FAILED += 1
                FAILED_LIST.append((name, str(e)))
                print(f"  ✗ {name}: {e}")
        return wrapper
    return decorator

# ═══════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════

@test("T01 — Golden ratio constants")
async def t01():
    assert abs(PHI - 1.618033988749895) < 1e-12
    assert abs(PHI_INV - 0.618033988749895) < 1e-12
    assert abs(PHI * PHI_INV - 1.0) < 1e-12

@test("T02 — Engine initialization")
async def t02():
    engine = ArkheGoldenTorusEngine(num_nodes=50)
    assert engine.num_nodes == 50
    assert engine.topologies == {}

@test("T03 — Golden spiral placement")
async def t03():
    engine = ArkheGoldenTorusEngine()
    coords = engine._golden_spiral_placement(10)
    assert len(coords) == 10
    for phi, theta in coords:
        assert 0 <= phi < 2 * np.pi
        assert 0 <= theta < 2 * np.pi

@test("T04 — Toroidal distance")
async def t04():
    engine = ArkheGoldenTorusEngine()
    n1 = ToroidalNode("n1", InstanceType.MYCELIUM, 0, 0, 10, 5)
    n2 = ToroidalNode("n2", InstanceType.MYCELIUM, np.pi, np.pi, 10, 5)
    dist = engine._toroidal_distance(n1, n2)
    assert dist > 0

@test("T05 — Mycelium topology")
async def t05():
    engine = ArkheGoldenTorusEngine(num_nodes=20)
    topo = await engine.generate_mycelium_topology()
    assert topo.instance_type == InstanceType.MYCELIUM
    assert topo.total_nodes == 20
    assert len(topo.canonical_seal) == 64

@test("T06 — Synaptic topology")
async def t06():
    engine = ArkheGoldenTorusEngine(num_nodes=100)
    topo = await engine.generate_synaptic_topology(n_synapses=50)
    assert topo.instance_type == InstanceType.SYNAPTIC_CLEFT
    assert topo.total_nodes == 50

@test("T07 — Quantum vacuum topology")
async def t07():
    engine = ArkheGoldenTorusEngine()
    topo = await engine.generate_quantum_vacuum_topology(n_fluctuations=20)
    assert topo.instance_type == InstanceType.QUANTUM_VACUUM
    assert topo.total_nodes == 20

@test("T08 — Relay memory topology")
async def t08():
    engine = ArkheGoldenTorusEngine()
    topo = await engine.generate_relay_memory_topology()
    assert topo.instance_type == InstanceType.RELAY_NODE_MEMORY
    assert len(topo.nodes) > 0

@test("T09 — Gap generation")
async def t09():
    engine = ArkheGoldenTorusEngine(num_nodes=10)
    topo = await engine.generate_mycelium_topology()
    assert len(topo.gaps) > 0
    for gap in topo.gaps:
        assert 0 <= gap.permeability <= 1
        assert gap.resonance_freq > 0

@test("T10 — Phi spectral density")
async def t10():
    engine = ArkheGoldenTorusEngine(num_nodes=50)
    topo = await engine.generate_mycelium_topology()
    assert topo.phi_spectral_density >= 0

@test("T11 — Adaptation score")
async def t11():
    engine = ArkheGoldenTorusEngine(num_nodes=50)
    topo = await engine.generate_mycelium_topology()
    assert 0 <= topo.adaptation_score <= 1

@test("T12 — All four topologies")
async def t12():
    engine = ArkheGoldenTorusEngine(num_nodes=20)
    await engine.generate_mycelium_topology()
    await engine.generate_synaptic_topology(n_synapses=30)
    await engine.generate_quantum_vacuum_topology(n_fluctuations=15)
    await engine.generate_relay_memory_topology()
    assert len(engine.topologies) == 4

@test("T13 — Unified adaptation")
async def t13():
    engine = ArkheGoldenTorusEngine(num_nodes=20)
    await engine.run_full_unification()
    unified = await engine.calculate_unified_adaptation()
    assert unified.system_name == "unified_-1D_infrastructure"
    assert 0 <= unified.adaptation_quality <= 1
    assert len(unified.resonance_modes) == 6

@test("T14 — Full unification pipeline")
async def t14():
    engine = ArkheGoldenTorusEngine(num_nodes=20)
    data = await engine.run_full_unification()
    assert 'topologies' in data
    assert 'unified_adaptation' in data
    assert abs(data['phi'] - PHI) < 1e-12

@test("T15 — JSON export")
async def t15():
    engine = ArkheGoldenTorusEngine(num_nodes=20)
    data = await engine.run_full_unification()
    path = "test_270_golden_torus.json"
    engine.export_json(data, path)
    assert os.path.exists(path)
    with open(path) as f:
        loaded = json.load(f)
    assert "topologies" in loaded

@test("T16 — Bus interface")
async def t16():
    engine = ArkheGoldenTorusEngine(num_nodes=20)
    data = await engine.run_full_unification()
    bus = ArkheGoldenTorusBusInterface(engine)
    ok, bus_seal = await bus.publish_to_bus(data)
    assert ok is True
    assert len(bus_seal) == 64

@test("T17 — Node seals")
async def t17():
    engine = ArkheGoldenTorusEngine(num_nodes=5)
    topo = await engine.generate_mycelium_topology()
    for node in topo.nodes:
        assert len(node.seal) == 32

@test("T18 — Timestamp")
async def t18():
    engine = ArkheGoldenTorusEngine(num_nodes=5)
    before = time.time()
    topo = await engine.generate_mycelium_topology()
    after = time.time()
    assert before <= topo.timestamp <= after

@test("T19 — Gap permeability")
async def t19():
    engine = ArkheGoldenTorusEngine(num_nodes=10)
    topo = await engine.generate_mycelium_topology()
    for gap in topo.gaps:
        expected = np.exp(-gap.gap_width / PHI)
        assert abs(gap.permeability - expected) < 1e-6

@test("T20 — Resonance modes")
async def t20():
    engine = ArkheGoldenTorusEngine(num_nodes=20)
    await engine.run_full_unification()
    unified = await engine.calculate_unified_adaptation()
    assert len(unified.resonance_modes) == 6
    for mode in unified.resonance_modes:
        assert mode >= 0

# ═══════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════

async def main():
    print("=" * 60)
    print("ARKHE OS Substrate 270: Golden Ratio Torus")
    print("Canon: ∞.Ω.∇+++.270.golden_torus")
    print("=" * 60)
    print()

    tests = [t01, t02, t03, t04, t05, t06, t07, t08, t09, t10,
             t11, t12, t13, t14, t15, t16, t17, t18, t19, t20]

    for t in tests:
        await t()

    total = TESTS_PASSED + TESTS_FAILED
    phi_c = TESTS_PASSED / total if total > 0 else 0.0

    print()
    print("─" * 60)
    print(f"RESULTS: {TESTS_PASSED}/{total} tests passed ({100*phi_c:.1f}%)")
    print("─" * 60)

    if FAILED_LIST:
        print("\nFailures:")
        for name, err in FAILED_LIST:
            print(f"  • {name}: {err}")

    seal_input = f"substrate_270:{TESTS_PASSED}:{TESTS_FAILED}:{phi_c:.6f}:{time.time()}"
    canonical_seal = hashlib.sha3_256(seal_input.encode()).hexdigest()

    print()
    print("═" * 60)
    print(f"Canonical Seal: {canonical_seal}")
    print(f"Φ_C: {phi_c:.6f}")
    print("═" * 60)

    return TESTS_PASSED, TESTS_FAILED, canonical_seal, phi_c

if __name__ == "__main__":
    passed, failed, seal, phi_c = asyncio.run(main())
    sys.exit(0 if failed == 0 else 1)
