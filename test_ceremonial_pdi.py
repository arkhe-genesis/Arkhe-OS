import pytest
from core.pdi.pdi_calibration_interface import PDICalibrationInterface
from core.visualization.ceremonial.ceremonial_feedback_ui import CeremonialFeedbackUI
from core.integration.tdcs.tdcs_neurofeedback_bridge import TDCSNeurofeedbackBridge

def test_pdi_calibration_step():
    interface = PDICalibrationInterface()
    result = interface.step(theta_human_phase=0.8, gamma_phase_var=0.08, dmn_alpha_power=0.5)
    assert "PDI" in result
    assert result["epsilon"] == 0.08
    assert result["state"] == "CALIBRATING"

def test_tdcs_bridge():
    bridge = TDCSNeurofeedbackBridge()
    bridge.connect()

    # Test forming
    res = bridge.apply_stimulation("FORMING", 0.075, 0.5, 0.08)
    assert res["action"] == "BASELINE_STIM"

    # Test calibration
    res = bridge.apply_stimulation("CALIBRATING", 0.08, 0.8, 0.12)
    assert res["action"] == "DRIFT_CORRECTION"
