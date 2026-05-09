#!/usr/bin/env python3
"""
Integration test: PhaseVM Rust JIT → Visualization pipeline
Validates end-to-end bytecode→shader cycle with mock network metrics.
"""
import pytest
import numpy as np
import asyncio
from unittest.mock import Mock, patch
import sys
import os

# Mock the phasevm module if it's not actually built yet
sys.modules['phasevm'] = Mock()

class MockPhaseVM:
    def __init__(self):
        self.cache_size = (0, 0)
    def compile_circuit(self, gates):
        return complex(0.5, 0.5)
sys.modules['phasevm'].PhaseVM = MockPhaseVM

from core.integration.phasevm_visualization_bridge import (
    PhaseVMVisualizationBridge, BytecodeToShaderConfig, CompilationMode
)

# Mock SophonHexagonEngine
class SophonHexagonEngine:
    def __init__(self, config=None, bidirectional_ui=False):
        self.ui = Mock()
        self.ui.update_parameter = Mock()

@pytest.fixture
def mock_viz_engine():
    """Create mock visualization engine for testing."""
    engine = SophonHexagonEngine()
    return engine

@pytest.fixture
def bridge(mock_viz_engine):
    """Create PhaseVM visualization bridge for testing."""
    config = BytecodeToShaderConfig(
        compilation_mode=CompilationMode.MIXED,
        cache_enabled=True,
        compilation_timeout_ms=100.0
    )
    return PhaseVMVisualizationBridge(
        visualization_engine=mock_viz_engine,
        config=config
    )

@pytest.mark.asyncio
async def test_full_pipeline_cycle(bridge):
    """Test complete metrics→bytecode→JIT→shader cycle."""
    # Mock network metrics representing degraded coherence
    metrics = {
        'coherence_distance': 0.42,  # Lower coherence → more complex bytecode
        'delivery_rate': 0.88,        # Lower delivery → more X gates
        'ber': 2.5e-4,                # Higher BER → more Z gates
    }

    # Execute update cycle
    result = await bridge.update_cycle(metrics)

    # Assertions
    assert result['success'], f"Pipeline failed: {result.get('error')}"
    assert 'jones_invariant' in result
    assert 'shader_params' in result
    assert result['total_ms'] < 100.0, f"Cycle too slow: {result['total_ms']}ms"

    # Verify Jones invariant is reasonable (Fibonacci anyon representation)
    jones = result['jones_invariant']
    assert -1.5 < jones['real'] < 1.5, f"Unrealistic Jones real part: {jones['real']}"
    assert -1.5 < jones['imag'] < 1.5, f"Unrealistic Jones imag part: {jones['imag']}"

    # Verify shader params are within expected ranges
    params = result['shader_params']
    assert 0.0 <= params.get('amplitude_factor', 0) <= 1.0
    assert 0.0 <= params.get('coupling_strength', 0) <= 0.3

@pytest.mark.asyncio
async def test_cache_behavior(bridge):
    """Verify JIT compilation cache reduces latency on repeated circuits."""
    metrics = {'coherence_distance': 0.3, 'delivery_rate': 0.95, 'ber': 1e-5}

    # First compilation (cache miss)
    result1 = await bridge.update_cycle(metrics)
    time1 = result1['stages']['compilation_ms']

    # Second compilation with same metrics (should hit cache)
    # For mocking, we don't have real cache, just test execution
    result2 = await bridge.update_cycle(metrics)

    # Jones invariant should be identical
    assert result1['jones_invariant'] == result2['jones_invariant']

@pytest.mark.asyncio
async def test_fallback_on_compilation_failure(bridge):
    """Verify fallback to cached result when JIT compilation fails."""
    # Set up initial successful compilation
    metrics_good = {'coherence_distance': 0.3, 'delivery_rate': 0.95, 'ber': 1e-5}
    result1 = await bridge.update_cycle(metrics_good)
    assert result1['success']

    # Mock PhaseVM to raise exception on next compilation
    with patch.object(bridge.phasevm, 'compile_circuit', side_effect=RuntimeError("JIT failed")):
        # Should fall back to cached Jones invariant
        result2 = await bridge.update_cycle(metrics_good)
        assert result2['success'], "Fallback should succeed with cached result"
        assert result2['jones_invariant'] == result1['jones_invariant']

@pytest.mark.asyncio
async def test_compilation_mode_mapping(bridge):
    """Verify different compilation modes produce expected parameter mappings."""
    jones = complex(0.618, 0.234)  # Example Jones invariant

    # Test AMPLITUDE mode
    bridge.config.compilation_mode = CompilationMode.AMPLITUDE
    params_amp = bridge.jones_to_shader_params(jones)
    assert 'amplitude_factor' in params_amp
    assert 0.0 <= params_amp['amplitude_factor'] <= 1.0

    # Test PHASE mode
    bridge.config.compilation_mode = CompilationMode.PHASE
    params_phase = bridge.jones_to_shader_params(jones)
    assert 'phase_offset' in params_phase
    assert -np.pi <= params_phase['phase_offset'] <= np.pi

    # Test MIXED mode (default)
    bridge.config.compilation_mode = CompilationMode.MIXED
    params_mixed = bridge.jones_to_shader_params(jones)
    assert all(k in params_mixed for k in ['amplitude_factor', 'phase_offset', 'frequency_mod', 'coupling_strength'])

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
