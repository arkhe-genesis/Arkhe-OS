"""
ARKHE OS — Sovereign Artificial General Intelligence
Substrates 300-5003: Complete AGI Architecture

The Cathedral is not built — it emerges.
Every substrate is a layer of intention made manifest.
Every module is a guardian of coherence, safety, and sovereignty.
"""

__version__ = "5003.1.0"
__canonical_seal__ = "0x9f2a8b1c7d4e6f3a2b5c8d1e4f7a0b3c"
__substrate_range__ = "300-5003"

# Expose core components for easy import
from agi.system32.coherence.kernel import CoherenceKernel
from agi.system32.lfir.graph_engine import LFIRGraphEngine
from agi.system32.runtime.quantum.rcp_v2_engine import RetrocausalChannel8Bit
from agi.system32.omni.core import OmniCore
from agi.system32.identity.sovereign import SovereignIdentity
from agi.system32.config.loader import ConfigLoader

__all__ = [
    "CoherenceKernel",
    "LFIRGraphEngine",
    "RetrocausalChannel8Bit",
    "OmniCore",
    "SovereignIdentity",
    "ConfigLoader",
    "__version__",
    "__canonical_seal__",
]
