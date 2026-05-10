"""
kym_robot.py — Know Your Machine for Robots
Arkhe OS - Substrate 5026
"""
from dataclasses import dataclass
from typing import Dict, Any, Tuple
import time
import sys
import os

# Ensure we can import the base KYMVerifier
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from agi.system32.kym.kym_verifier import KYMVerifier, EntityInfo

@dataclass
class RobotProfile(EntityInfo):
    manufacturer: str
    model: str
    serial: str
    firmware_hash: str
    incidents: int
    avg_hic15: float
    avg_nij: float
    hardware: list

class KYMRobotVerifier(KYMVerifier):
    def __init__(self):
        super().__init__()
        # Additional weights for robot-specific risk factors
        self.robot_weights = {
            "incidents": 0.1,
            "hic15": 0.1,
            "nij": 0.1
        }

    def calculate_phi_risk_robot(self, robot: RobotProfile) -> Tuple[float, str]:
        """
        Calculate dynamic risk including physical factors.
        """
        # Base KYM risk
        base_phi_risk, _ = self.calculate_phi_risk(robot)

        # Penalties
        incident_penalty = min(robot.incidents * 0.05, 0.2)

        # Normalize HIC15 (limit 700)
        hic15_penalty = min(robot.avg_hic15 / 700.0, 1.0) * 0.1

        # Normalize Nij (limit 1.0)
        nij_penalty = min(robot.avg_nij / 1.0, 1.0) * 0.1

        total_risk = base_phi_risk + incident_penalty + hic15_penalty + nij_penalty
        total_risk = min(total_risk, 1.0)

        if total_risk < 0.3:
            classification = "low"
        elif total_risk < 0.6:
            classification = "medium"
        else:
            classification = "high"

        return total_risk, classification

    def verify_robot(self, robot: RobotProfile) -> Dict[str, Any]:
        """Main KYM verification flow for robots."""
        if not self.resolve_identity(robot):
            return {"status": "rejected", "reason": "Invalid identity"}

        total_risk, classification = self.calculate_phi_risk_robot(robot)

        safe_mode = classification == "high"

        attestation = self.register_kym(robot, total_risk, classification)
        attestation["safe_mode"] = safe_mode
        attestation["robot_model"] = robot.model
        attestation["hardware"] = robot.hardware

        return attestation
