# tests/unit/test_reciprocal_space_parser.py
"""
Unit tests for ReciprocalSpaceParser with cross-platform validation.
"""
import pytest
import numpy as np
from pathlib import Path

from arkhe_os.parser.reciprocal_space_parser import ReciprocalSpaceParser
from arkhe_os.parser.atomic_structure import AtomicStructure
from arkhe_os.parser.rsp_model import ReciprocalSpaceNN
from conftest import requires_gpu

def test_parser_initialization_cross_platform(platform_info):
    """Test parser initialization on all platforms."""
    # CPU should always work
    parser_cpu = ReciprocalSpaceParser(device='cpu')
    assert parser_cpu.device == 'cpu'
    assert parser_cpu.torch_device.type == 'cpu'

    # GPU backends: test if available
    if platform_info['is_linux'] or platform_info['is_macos']:
        # Try CUDA on Linux, MPS on macOS
        preferred_gpu = 'cuda' if platform_info['is_linux'] else 'mps'
        parser_gpu = ReciprocalSpaceParser(device=preferred_gpu)
        # Should fallback to CPU if GPU not available
        assert parser_gpu.device in ['cpu', preferred_gpu]

def test_parse_small_structure(sample_structure_file, sample_model_config):
    """Test parsing a small structure (platform-independent)."""
    parser = ReciprocalSpaceParser(device='cpu', cache_fourier=False)

    graph = parser.parse(
        structure=sample_structure_file,
        model=sample_model_config
    )

    # Validate graph structure
    assert len(graph.nodes) > 0
    assert any('atom' in n.id for n in graph.nodes)
    assert any('kpoint' in n.id for n in graph.nodes)
    assert 0.0 <= graph.coherence_score <= 1.0

@pytest.mark.parametrize("device", ['cpu'])  # Add 'cuda', 'mps' if available
def test_parse_device_compatibility(sample_structure_file, sample_model_config, device):
    """Test parsing with different device backends."""
    parser = ReciprocalSpaceParser(device=device, cache_fourier=False)
    graph = parser.parse(sample_structure_file, sample_model_config)
    assert graph.coherence_score >= 0.0

@requires_gpu
def test_gpu_acceleration(sample_structure_file, sample_model_config):
    """Test GPU acceleration if available."""
    import torch

    # Parse with CPU
    parser_cpu = ReciprocalSpaceParser(device='cpu', cache_fourier=False)
    graph_cpu = parser_cpu.parse(sample_structure_file, sample_model_config)

    # Parse with GPU (if available)
    device = 'cuda' if torch.cuda.is_available() else 'mps'
    parser_gpu = ReciprocalSpaceParser(device=device, cache_fourier=False)
    graph_gpu = parser_gpu.parse(sample_structure_file, sample_model_config)

    # Results should be numerically equivalent (within floating-point tolerance)
    assert abs(graph_cpu.coherence_score - graph_gpu.coherence_score) < 1e-5