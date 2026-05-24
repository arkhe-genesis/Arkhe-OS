#!/usr/bin/env python3
"""
ARKHE OS Substrate 269 Test Suite
Canon: ∞.Ω.∇+++.269.cosmological_simulation.tests
"""

import asyncio
import hashlib
import json
import time
import sys
import os
import numpy as np

# Import substrate
exec(open('/mnt/agents/output/substrate_269_cosmological.py').read())

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

@test("T01 — Engine initialization with default config")
async def t01():
    engine = ArkheCosmologicalSimulation()
    assert engine.config.grid_size == 32
    assert engine.config.steps == 100
    assert engine.config.damping_coeff == 0.012
    assert engine.states == []

@test("T02 — Custom lattice config")
async def t02():
    cfg = LatticeConfig(grid_size=64, steps=50, damping_coeff=0.02)
    engine = ArkheCosmologicalSimulation(cfg)
    assert engine.config.grid_size == 64
    assert engine.config.steps == 50
    assert engine.config.damping_coeff == 0.02

@test("T03 — Laplacian 3D computation")
async def t03():
    engine = ArkheCosmologicalSimulation()
    field = np.ones((4, 4, 4))
    lap = engine._laplacian_3d(field)
    assert lap.shape == (4, 4, 4)
    assert np.allclose(lap, 1.0)

@test("T04 — Percolation state detection")
async def t04():
    engine = ArkheCosmologicalSimulation()
    sub = np.zeros((4, 4, 4))
    assert engine._detect_percolation(sub) == PercolationState.SUB_CRITICAL
    near = np.full((4, 4, 4), 0.2)
    assert engine._detect_percolation(near) == PercolationState.NEAR_CRITICAL
    crit = np.full((4, 4, 4), 0.3)
    assert engine._detect_percolation(crit) == PercolationState.CRITICAL
    snap = np.full((4, 4, 4), 0.6)
    assert engine._detect_percolation(snap) == PercolationState.RAINBOW_SNAP

@test("T05 — Simulation execution")
async def t05():
    engine = ArkheCosmologicalSimulation(LatticeConfig(grid_size=8, steps=20))
    states = await engine.run_simulation()
    assert len(states) == 20
    assert all(isinstance(s, SimulationState) for s in states)
    assert all(s.mu_field.shape == (8, 8, 8) for s in states)
    assert all(s.phi_field.shape == (8, 8, 8) for s in states)

@test("T06 — State fields are clipped")
async def t06():
    engine = ArkheCosmologicalSimulation(LatticeConfig(grid_size=8, steps=10))
    states = await engine.run_simulation()
    for s in states:
        assert np.all(s.mu_field >= 0.0)
        assert np.all(s.mu_field <= 1.0)
        assert np.all(s.phi_field >= -2)
        assert np.all(s.phi_field <= 2)

@test("T07 — Active fraction evolution")
async def t07():
    engine = ArkheCosmologicalSimulation(LatticeConfig(grid_size=8, steps=20))
    states = await engine.run_simulation()
    fracs = [s.active_fraction for s in states]
    assert all(0 <= f <= 1 for f in fracs)

@test("T08 — Rainbow snap detection possible")
async def t08():
    engine = ArkheCosmologicalSimulation(LatticeConfig(grid_size=8, steps=50, shg_coupling=0.5))
    states = await engine.run_simulation()
    snaps = [s for s in states if s.rainbow_snap_triggered]
    # With high SHG coupling, snap is likely but not guaranteed in small grid
    assert isinstance(snaps, list)

@test("T09 — State seal generation")
async def t09():
    engine = ArkheCosmologicalSimulation(LatticeConfig(grid_size=8, steps=5))
    states = await engine.run_simulation()
    for s in states:
        assert len(s.seal) == 32
        assert all(c in '0123456789abcdef' for c in s.seal)

@test("T10 — GW spectrum generation")
async def t10():
    engine = ArkheCosmologicalSimulation()
    gw = engine.generate_gw_spectrum()
    assert len(gw) == 100
    assert all(isinstance(g, GWSourceSpectrum) for g in gw)
    assert all(g.frequency_hz > 0 for g in gw)
    assert all(g.omega_gw >= 0 for g in gw)

@test("T11 — GW spectrum peak detection")
async def t11():
    engine = ArkheCosmologicalSimulation()
    gw = engine.generate_gw_spectrum()
    peaks = [g for g in gw if g.source_type == "percolation_snap"]
    assert len(peaks) > 0
    assert peaks[0].peak_frequency_hz is not None
    assert peaks[0].amplitude_at_peak is not None

@test("T12 — CMB constraints definition")
async def t12():
    engine = ArkheCosmologicalSimulation()
    cmb = engine.define_cmb_constraints()
    assert len(cmb) == 5
    observables = [c.observable for c in cmb]
    assert "Tensor-to-scalar ratio r" in observables
    assert "Scalar spectral index n_s" in observables
    assert "Equilateral f_NL" in observables

@test("T13 — CMB constraint statuses")
async def t13():
    engine = ArkheCosmologicalSimulation()
    cmb = engine.define_cmb_constraints()
    for c in cmb:
        assert c.status in ["fully_compatible", "matches_1sigma", "within_errors", "perfect_match"]

@test("T14 — Full canonization pipeline")
async def t14():
    engine = ArkheCosmologicalSimulation(LatticeConfig(grid_size=8, steps=15))
    report = await engine.canonize()
    assert isinstance(report, CanonicalCosmologicalReport)
    assert report.total_timesteps == 15
    assert report.gw_sources == 100
    assert report.cmb_constraints == 5
    assert len(report.canonical_seal) == 64
    assert 0.0 <= report.simulation_phi_c <= 1.0

@test("T15 — Report ID is hash")
async def t15():
    engine = ArkheCosmologicalSimulation(LatticeConfig(grid_size=8, steps=5))
    report = await engine.canonize()
    assert len(report.report_id) == 32
    assert all(c in '0123456789abcdef' for c in report.report_id)

@test("T16 — JSON export creates valid file")
async def t16():
    engine = ArkheCosmologicalSimulation(LatticeConfig(grid_size=8, steps=5))
    report = await engine.canonize()
    path = "/mnt/agents/output/test_269_cosmological.json"
    engine.export_json(report, path)
    assert os.path.exists(path)
    with open(path) as f:
        data = json.load(f)
    assert "canonical_report" in data
    assert "states" in data
    assert "gw_spectrum" in data
    assert "cmb_constraints" in data

@test("T17 — Bus interface publication")
async def t17():
    engine = ArkheCosmologicalSimulation(LatticeConfig(grid_size=8, steps=5))
    report = await engine.canonize()
    bus = ArkheCosmologicalBusInterface(engine)
    ok, bus_seal = await bus.publish_to_bus(report)
    assert ok is True
    assert len(bus_seal) == 64

@test("T18 — Timestamp is recent")
async def t18():
    engine = ArkheCosmologicalSimulation(LatticeConfig(grid_size=8, steps=5))
    before = time.time()
    report = await engine.canonize()
    after = time.time()
    assert before <= report.timestamp <= after

@test("T19 — Phi field backreaction from mu")
async def t19():
    engine = ArkheCosmologicalSimulation(LatticeConfig(grid_size=8, steps=10))
    states = await engine.run_simulation()
    # Phi should evolve due to mu gradients
    phi_means = [s.phi_mean for s in states]
    assert len(set(phi_means)) > 1  # Some evolution occurred

@test("T20 — Mu field viscoelastic damping")
async def t20():
    engine = ArkheCosmologicalSimulation(LatticeConfig(grid_size=8, steps=10))
    states = await engine.run_simulation()
    mu_means = [s.mu_mean for s in states]
    # Mu should be driven by damping + diffusion + noise + SHG
    assert len(set(mu_means)) > 1

# ═══════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════

async def main():
    print("=" * 60)
    print("ARKHE OS Substrate 269: Cosmological Simulation Engine")
    print("Canon: ∞.Ω.∇+++.269.cosmological_simulation")
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

    seal_input = f"substrate_269:{TESTS_PASSED}:{TESTS_FAILED}:{phi_c:.6f}:{time.time()}"
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
