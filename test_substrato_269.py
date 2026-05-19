#!/usr/bin/env python3
"""
Tests for ARKHE OS Substrate 269: Cosmological Simulation Engine
"""

import pytest
import numpy as np
import time
from substrato_269 import (
    ArkheCosmologicalSimulation,
    LatticeConfig,
    PercolationState,
    ArkheCosmologicalBusInterface,
    LatticeDimension,
)

@pytest.mark.asyncio
async def test_run_simulation():
    config = LatticeConfig(grid_size=8, steps=5)
    engine = ArkheCosmologicalSimulation(config)
    states = await engine.run_simulation()

    assert len(states) == 5
    assert states[0].mu_field.shape == (8, 8, 8)
    assert states[-1].phi_field.shape == (8, 8, 8)

@pytest.mark.asyncio
async def test_canonize():
    config = LatticeConfig(grid_size=8, steps=5)
    engine = ArkheCosmologicalSimulation(config)
    report = await engine.canonize()

    assert report.total_timesteps == 5
    assert report.gw_sources == 100
    assert report.cmb_constraints == 5
    assert len(report.canonical_seal) == 64

@pytest.mark.asyncio
async def test_publish_to_bus():
    config = LatticeConfig(grid_size=8, steps=5)
    engine = ArkheCosmologicalSimulation(config)
    report = await engine.canonize()

    bus = ArkheCosmologicalBusInterface(engine)
    success, seal = await bus.publish_to_bus(report)

    assert success is True
    assert len(seal) == 64

def test_detect_percolation():
    engine = ArkheCosmologicalSimulation()

    active = np.zeros((8, 8, 8))
    assert engine._detect_percolation(active) == PercolationState.SUB_CRITICAL

    active.fill(1.0)
    assert engine._detect_percolation(active) == PercolationState.RAINBOW_SNAP
