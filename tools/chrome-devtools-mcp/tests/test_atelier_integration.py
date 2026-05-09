import pytest
import os
import sys
from src.lib.state_anchor_parser import StateAnchorParser

# Add arkhe-brain to path to import subagents
sys.path.append(os.path.abspath("arkhe-brain"))
from subagents import ReachabilitySubagent, ManifestationSubagent

def test_state_anchor_parser():
    # Setup mock files
    memory_content = "# 🜏 Arkhe-Chain Persistence: MEMORY.md\n**Current Block:** 847.813\n**Global Coherence (λ₂):** 0.999"
    with open("TEST_MEMORY.md", "w") as f:
        f.write(memory_content)

    parser = StateAnchorParser(memory_path="TEST_MEMORY.md")
    identity = parser.parse_current_identity()

    assert identity["block"] == 847813
    assert identity["lambda"] == 0.999

    os.remove("TEST_MEMORY.md")

def test_subagents_existence():
    reach = ReachabilitySubagent()
    mani = ManifestationSubagent()

    assert reach.agent_id == "REACHABILITY_AGENT"
    assert mani.agent_id == "MANIFESTATION_AGENT"

if __name__ == "__main__":
    pytest.main([__file__])
