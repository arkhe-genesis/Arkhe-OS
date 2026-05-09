import sys
import os
import numpy as np
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from physics.neural_phase_coach import black_mirror_phase_coach

def test_coach_mastery_detection():
    print("Testing Mastery Detection...")
    res = 50
    field = np.random.uniform(-0.1, 0.1, (res, res)) # Low noise
    field[10:20, 10:20] = 1.0 # Strong mastery alignment

    report = black_mirror_phase_coach(field)

    mastery_found = any(data['type'] == 'mastery' for data in report['attractors'].values())
    assert mastery_found, "Should have detected a mastery attractor"
    print("✓ Mastery Detection Passed")

def test_coach_trauma_detection():
    print("Testing Trauma Detection...")
    res = 50
    field = np.random.uniform(-0.1, 0.1, (res, res)) # Low noise
    field[30:40, 30:40] = -1.0 # Strong trauma alignment

    report = black_mirror_phase_coach(field)

    trauma_found = any(data['type'] == 'trauma' for data in report['attractors'].values())
    assert trauma_found, "Should have detected a trauma attractor"
    assert report['summary']['has_trauma_loops'] == True, "Summary should indicate trauma loops"
    print("✓ Trauma Detection Passed")

if __name__ == "__main__":
    try:
        test_coach_mastery_detection()
        test_coach_trauma_detection()
        print("\nAll Neural Coach tests passed!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
