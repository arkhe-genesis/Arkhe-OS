"""
physics_safety.py — Physical Safety Evaluator
Arkhe OS - Substrate 5026-A
"""
import math
from typing import List

class PhysicsSafetyEvaluator:
    def __init__(self):
        # Default ISO/TS 15066 thresholds for human-robot collaboration
        self.max_force = 150.0  # Newtons
        self.max_pressure = 50.0 # N/cm^2
        self.safe_distance_margin = 0.5 # meters

        # Biomechanical injury thresholds
        self.hic15_limit = 700.0  # HIC limit
        self.nij_limit = 1.0      # Nij limit

    def calculate_hic15(self, acceleration_curve: List[float], dt: float) -> float:
        """
        Calculate HIC15 (Head Injury Criterion over max 15ms window).
        acceleration_curve in g's.
        dt in seconds.
        """
        max_hic = 0.0
        n_samples = len(acceleration_curve)
        window_size = int(0.015 / dt) if dt > 0 else 1
        if window_size < 1:
            window_size = 1

        for i in range(n_samples):
            for j in range(i + 1, min(i + window_size + 1, n_samples)):
                t1 = i * dt
                t2 = j * dt
                if t2 - t1 > 0.015:
                    break

                # Mean acceleration in window
                mean_acc = sum(acceleration_curve[i:j]) / (j - i)
                hic = (mean_acc ** 2.5) * (t2 - t1)

                if hic > max_hic:
                    max_hic = hic

        return max_hic

    def calculate_nij(self, fz: float, fzc: float, my: float, myc: float) -> float:
        """
        Calculate Neck Injury Criterion (Nij).
        fz: axial force
        fzc: critical axial force
        my: flexion/extension moment
        myc: critical bending moment
        """
        return abs(fz / fzc) + abs(my / myc)

    def verify_iso15066_distance(self, robot_speed: float, human_speed: float, response_time: float, distance: float) -> bool:
        """
        Verify if current distance is safe according to ISO/TS 15066
        Speed and Separation Monitoring.
        """
        required_distance = (robot_speed * response_time) + (human_speed * response_time) + self.safe_distance_margin
        return distance >= required_distance

    def evaluate_motion_safety(self, hic15: float, nij: float) -> bool:
        """
        Evaluate if biomechanical metrics are within safe limits.
        """
        return hic15 <= self.hic15_limit and nij <= self.nij_limit
