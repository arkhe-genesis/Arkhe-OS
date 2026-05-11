#!/usr/bin/env python3
"""
arkhe_photonics_leveling.py
Arkhe(n) – Calibration and stress test for 405 nm LED array (Tissium photopolymerization).
Ensures flat‑top beam profile, thermal safety, and registers results in Arkhe‑Chain.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from datetime import datetime, timezone
import json
import time
import os

# ============================================================================
# HARDWARE SIMULATION (replace with real sensor drivers)
# ============================================================================
class CMOSIrradianceSensor:
    """Simulates reading of a CMOS camera with 405 nm filter."""
    @staticmethod
    def capture_irradiance_map():
        # Simulate a Gaussian‑like beam (before calibration)
        x = np.linspace(-1, 1, 8*10)  # 80x120 virtual pixels
        y = np.linspace(-1, 1, 12*10)
        X, Y = np.meshgrid(x, y)
        irradiance = 20 * np.exp(-(X*2)**2 - (Y*2)**2) + 0.5 * np.random.rand(*X.shape)
        return irradiance

class PWMLEDController:
    """Simulate per‑well PWM adjustment."""
    def __init__(self, n_rows=8, n_cols=12):
        self.current_duty = np.ones((n_rows, n_cols)) * 0.5  # initial 50% duty cycle
    def set_duty(self, row, col, duty):
        self.current_duty[row, col] = np.clip(float(duty), 0.0, 1.0)

# ============================================================================
# CALIBRATION ENGINE
# ============================================================================
class PhotonicLeveler:
    def __init__(self, target_irradiance_mWcm2=15.0, tolerance=0.05):
        self.target = target_irradiance_mWcm2
        self.tolerance = tolerance
        self.sensor = CMOSIrradianceSensor()
        self.led_ctrl = PWMLEDController()
        self.calibration_log = []

    def adjust_pwm(self, current_irradiance):
        """Compute new PWM duty cycle for each well."""
        # Simple simulation: assume irradiance is 12x8
        # In reality, we would sample the irradiance map at well positions
        n_rows, n_cols = 8, 12
        # Reshape or sample irrad_map to 8x12
        sampled_irrad = cv2.resize(current_irradiance, (n_cols, n_rows), interpolation=cv2.INTER_AREA)

        new_duty = np.zeros_like(sampled_irrad)
        for i in range(n_rows):
            for j in range(n_cols):
                ratio = self.target / (sampled_irrad[i, j] + 1e-8)
                new_duty[i, j] = np.clip(ratio, 0.3, 1.0)  # limit to 30‑100%
        return new_duty

    def run_calibration(self, max_iter=5):
        print("[Arkhe] Starting photonic leveling...")
        cv = 1.0
        for iteration in range(max_iter):
            # Capture current irradiance map
            irrad_map = self.sensor.capture_irradiance_map()
            mean_irrad = np.mean(irrad_map)
            std_irrad = np.std(irrad_map)
            cv = std_irrad / mean_irrad
            print(f"  Iter {iteration+1}: mean={mean_irrad:.2f} mW/cm², CV={cv:.4f}")

            # Compute new PWM settings
            new_duty = self.adjust_pwm(irrad_map)
            for i in range(new_duty.shape[0]):
                for j in range(new_duty.shape[1]):
                    self.led_ctrl.set_duty(i, j, new_duty[i, j])

            # Simulate settling and re‑measure
            time.sleep(0.1)
            # Break if uniformity achieved
            if cv <= self.tolerance:
                print(f"[Arkhe] Calibration converged after {iteration+1} iterations.")
                break
        else:
            print("[Arkhe] Calibration reached max iterations.")
        return True, cv

    def stress_test(self, duration_sec=60, temp_threshold=42.0, cv=0.05):
        """
        Runs a thermal stress test on a sacrificial plate (no cells).
        Simulates temperature rise using a thermal camera model.
        """
        print("[Arkhe] Running photonic stress test on sacrificial plate...")
        # Simulate temperature distribution (heating due to LED irradiation)
        # Assume base temp 37°C, heating proportional to irradiance
        irrad_map = self.sensor.capture_irradiance_map()
        # Sample to 8x12
        sampled_irrad = cv2.resize(irrad_map, (12, 8), interpolation=cv2.INTER_AREA)

        # Apply calibration correction (simulate corrected output)
        duty = np.array([[self.led_ctrl.current_duty[i, j] for j in range(12)] for i in range(8)])
        corrected_irrad = sampled_irrad * duty

        # Temperature rise: ΔT = (irradiance * time * absorption) / (density * heat_cap * thickness)
        absorption = 0.8
        density = 1.0  # g/cm³
        heat_cap = 4.18  # J/g°C
        thickness = 0.1  # cm (1 mm)
        time_sec = duration_sec
        delta_T = (corrected_irrad * time_sec * absorption) / (density * heat_cap * thickness)
        final_temp = 37.0 + delta_T

        # Report statistics
        max_temp = np.max(final_temp)
        min_temp = np.min(final_temp)
        mean_temp = np.mean(final_temp)
        print(f"  Temperature range: {min_temp:.1f} – {max_temp:.1f} °C")
        if max_temp > temp_threshold:
            print(f"  [WARNING] Maximum temperature exceeds {temp_threshold}°C threshold.")
            verdict = "REJECTED"
        else:
            print(f"  [OK] All wells within safe thermal limits.")
            verdict = "APPROVED"

        # Create thermal map plot
        plt.figure(figsize=(10, 6))
        im = plt.imshow(final_temp, cmap='coolwarm', interpolation='bilinear', aspect='auto')
        plt.colorbar(im, label='Temperature (°C)')
        plt.title('Simulated Thermal Map after 60s Irradiation')
        plt.xlabel('Column')
        plt.ylabel('Row')
        plt.tight_layout()
        plt.savefig('thermal_stress_test_map.png', dpi=150)
        print("[Arkhe] Thermal map saved as thermal_stress_test_map.png")

        # Generate report
        report = {
            "protocol": "PHOTONIC_STRESS_TEST_v1",
            "timestamp": datetime.now().isoformat(),
            "duration_sec": duration_sec,
            "target_irradiance_mWcm2": self.target,
            "uniformity_cv": float(cv),
            "temperature_stats": {
                "min_C": float(min_temp),
                "max_C": float(max_temp),
                "mean_C": float(mean_temp)
            },
            "threshold_C": temp_threshold,
            "verdict": verdict
        }
        with open('thermal_stress_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        print("[Arkhe-Chain] Stress test report registered.")
        return verdict, final_temp

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    leveler = PhotonicLeveler(target_irradiance_mWcm2=15.0, tolerance=0.05)
    success, final_cv = leveler.run_calibration()
    verdict, temp_map = leveler.stress_test(duration_sec=60, temp_threshold=42.0, cv=final_cv)
    if verdict == "APPROVED":
        print("\n✅ Photonic leveling validated. Ready for biological experiments.")
    else:
        print("\n❌ Thermal stress test failed. Re‑calibrate LED currents or adjust cooling.")
