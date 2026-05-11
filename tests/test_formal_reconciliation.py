import pytest
import os
from src.cuda.continuous_reconciler import ContinuousReconciler
from src.lib.state_anchor_parser import StateAnchorParser

class MockGPUReconciler:
    def __init__(self):
        self.avg_lambda = 0.99
    def tick(self):
        return self

@pytest.fixture
def parser():
    return StateAnchorParser(dreams_path="TEST_DREAMS.md", memory_path="TEST_MEMORY.md")

@pytest.fixture
def reconciler(parser):
    gpu_rec = MockGPUReconciler()
    return ContinuousReconciler(gpu_reconciler=gpu_rec, parser=parser)

def test_dream_inconsistent_trigger(reconciler):
    """Verify that an invalid dream proof triggers DREAM_INCONSISTENT."""
    # Setup TEST_DREAMS.md with an invalid proof (not starting with 0x)
    with open("TEST_DREAMS.md", "w") as f:
        f.write("| ID | Target Block | Target λ₂ | Status | Proof |\n")
        f.write("| `FAIL_DREAM` | 900000 | 0.999 | `PROVEN` | `INVALID_PROOF` |\n")

    with open("TEST_MEMORY.md", "w") as f:
        f.write("Block: 847,826\nλ₂: 0.999\nHash: 0x...")

    result = reconciler.tick()
    assert result == "DREAM_INCONSISTENT"

def test_dream_consistent_flow(reconciler):
    """Verify that a valid dream proof allows reconciliation to continue."""
    # Setup TEST_DREAMS.md with a valid proof
    with open("TEST_DREAMS.md", "w") as f:
        f.write("| ID | Target Block | Target λ₂ | Status | Proof |\n")
        f.write("| `GOOD_DREAM` | 900000 | 0.999 | `PROVEN` | `0xVALID` |\n")

    with open("TEST_MEMORY.md", "w") as f:
        f.write("Block: 847,826\nλ₂: 0.999\nHash: 0x...")

    stats = reconciler.tick()
    assert stats.avg_lambda == 0.99
    assert reconciler.active_dream["id"] == "GOOD_DREAM"

def test_maley_precursor_detection(reconciler):
    """Verify Maley precursor detection logic."""
    psd_data = {"precursor": 0.08}
    detected = reconciler.detect_maley_precursor(psd_data)
    assert detected is True

    psd_data_low = {"precursor": 0.01}
    detected_low = reconciler.detect_maley_precursor(psd_data_low)
    assert detected_low is False

def teardown_module(module):
    """Cleanup test files."""
    for f in ["TEST_DREAMS.md", "TEST_MEMORY.md"]:
        if os.path.exists(f):
            os.remove(f)
