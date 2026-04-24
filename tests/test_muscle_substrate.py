import pytest
import numpy as np
from catedrald_muscle import LightMuscleSubstrate, inject_muscle_into_core

class MockCore:
    def __init__(self):
        self.coherence = 1.0
        self.evo = type('obj', (object,), {'population': []})
    def inject_coherence(self, delta):
        self.coherence = min(1.0, self.coherence + delta)
    def get_coherence(self):
        return self.coherence

def test_muscle_initialization():
    core = MockCore()
    muscle = inject_muscle_into_core(core)
    assert muscle.name == "LightMuscle_Alpha"
    assert muscle.calibration_status == "uncalibrated"

def test_muscle_calibration():
    core = MockCore()
    muscle = inject_muscle_into_core(core)
    result = muscle.calibrate_muscle()
    assert result["status"] == "success"
    assert muscle.calibration_status == "calibrated"

def test_muscle_apply_force():
    core = MockCore()
    muscle = inject_muscle_into_core(core)
    muscle.calibrate_muscle()

    force_vector = np.array([0.0, 0.0, 10.0])
    success = muscle.apply_force(force_vector)

    assert success is True
    # In the current simulation, force is dominated by Z axis due to simplified physics
    assert muscle.measured_force[2] > 0

def test_muscle_get_status():
    core = MockCore()
    muscle = inject_muscle_into_core(core)
    status = muscle.get_status()
    assert status["substrate_id"] == 51
    assert "measured_force_n" in status
