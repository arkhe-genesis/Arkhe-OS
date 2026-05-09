"""
pip_sovereign — Substrate 5018: Sovereign Python Package Management
Secure, verified, and coherent dependency installation for ARKHE OS.
"""
__version__ = "1.0.0"
__substrate_id__ = 5018
__canonical_seal__ = "0x5018_SOVEREIGN_PIP_9f2a8b1c7d4e6f3a"

from .cli import main as pip_sovereign_main
from .installer import install_package, install_requirements
from .verifier import verify_package_integrity
from .registry import SovereignRegistryClient
from .coherence_monitor import DependencyCoherenceMonitor

__all__ = [
    "pip_sovereign_main",
    "install_package",
    "install_requirements",
    "verify_package_integrity",
    "SovereignRegistryClient",
    "DependencyCoherenceMonitor",
]