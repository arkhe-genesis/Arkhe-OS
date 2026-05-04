#!/usr/bin/env python3
from individual_omega_calibration import IndividualOmegaCalibrator, CalibrationMethod
import numpy as np

def test_calibration():
    calibrator = IndividualOmegaCalibrator(None)

    # Test Medical Screening
    eligible, exclusions = calibrator.verify_eligibility({"photosensitive_epilepsy": True})
    print(f"Eligible: {eligible}, Exclusions: {exclusions}")

    # Test Bayesian Calibration
    measurements = [0.94, 0.95, 0.93, 0.96, 0.94]
    profile = calibrator.calibrate("user_123", measurements, CalibrationMethod.ADAPTIVE_BAYESIAN)
    print(f"Profile: baseline={profile.baseline_omega:.4f}, CI={profile.confidence_interval}")

    # Test Resting State Calibration
    profile_rs = calibrator.calibrate("user_456", measurements, CalibrationMethod.RESTING_STATE_AVERAGE)
    print(f"Profile RS: baseline={profile_rs.baseline_omega:.4f}, std={profile_rs.baseline_std:.4f}")

if __name__ == "__main__":
    test_calibration()
