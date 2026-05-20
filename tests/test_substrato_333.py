import pytest
import math
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../substrates/300-399_foundations/substrato_333')))
from hosten_refined_333 import (
    GHOST,
    HamamatsuR928_PMT,
    AdaptiveFilter,
    HostenTorsionPendulumRefined,
    AutoCalibrateRiemann,
    MicrotubuleCultureValidator
)

def test_pmt_calibration():
    pmt = HamamatsuR928_PMT()
    pmt.connect()
    calib = pmt.calibrate(100.0)
    assert pmt.connected
    assert 0.98 <= calib["factor"] <= 1.02

def test_adaptive_filter():
    filter_sys = AdaptiveFilter(window_size=10)
    raw_vals = [0.5, 0.6, 0.55, 0.58, 0.59]
    for val in raw_vals:
        t, w, k = filter_sys.process(val)

    assert t > 0
    assert w > 0
    assert k > 0

def test_auto_calibrate_riemann():
    calibrator = AutoCalibrateRiemann(tolerance=0.005)
    res = calibrator.run_auto_calibration(raw_noise_variance=0.01)
    assert 0.1 <= res["optimal_constant"] <= 0.5

def test_cross_validation():
    validator = MicrotubuleCultureValidator()
    res = validator.validate_methods(10.0 * 1e6, 0.58)
    assert res["validated"] is True
    assert res["MAE"] < 0.1
