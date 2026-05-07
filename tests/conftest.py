# tests/conftest.py
"""
Cross-platform pytest fixtures for ARKHE RSP Parser tests.
"""
import pytest
import sys
import os
import platform
import json
from pathlib import Path

@pytest.fixture(scope="session")
def platform_info():
    """Provide platform information to tests."""
    return {
        'system': platform.system(),
        'machine': platform.machine(),
        'is_windows': sys.platform == 'win32',
        'is_macos': sys.platform == 'darwin',
        'is_linux': sys.platform == 'linux',
        'is_ci': 'CI' in os.environ
    }

@pytest.fixture
def sample_structure_file(tmp_path, platform_info):
    """Create a sample POSCAR file for testing."""
    content = """NaCl
1.0
5.64 0.0 0.0
0.0 5.64 0.0
0.0 0.0 5.64
Na Cl
4 4
Direct
0.0 0.0 0.0
0.0 0.5 0.5
0.5 0.0 0.5
0.5 0.5 0.0
0.5 0.5 0.5
0.5 0.0 0.0
0.0 0.5 0.0
0.0 0.0 0.5
"""
    structure_file = tmp_path / "test.poscar"
    structure_file.write_text(content)
    return structure_file

@pytest.fixture
def sample_model_config(tmp_path):
    """Create a sample RSP model config JSON."""
    config = {
        "model_type": "RSP",
        "n_kpoints": 512,
        "k_mesh_shape": [8, 8, 8],
        "angular_channels": 16,
        "cutoff_radius": 5.0,
        "invariance": "euclidean"
    }
    config_file = tmp_path / "model.json"
    config_file.write_text(json.dumps(config))
    return config_file

def _has_gpu_acceleration():
    """Check if GPU acceleration is available."""
    try:
        import torch
        return torch.cuda.is_available() or (
            hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
        )
    except:
        return False

# Platform-specific skip decorators
requires_windows = pytest.mark.skipif(
    sys.platform != 'win32', reason="Requires Windows"
)

requires_macos = pytest.mark.skipif(
    sys.platform != 'darwin', reason="Requires macOS"
)

requires_linux = pytest.mark.skipif(
    sys.platform != 'linux', reason="Requires Linux"
)

requires_gpu = pytest.mark.skipif(
    not _has_gpu_acceleration(), reason="Requires GPU (CUDA/MPS)"
)
