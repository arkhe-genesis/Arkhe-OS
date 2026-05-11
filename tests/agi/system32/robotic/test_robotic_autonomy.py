import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from agi.system32.robotic.physics_safety import PhysicsSafetyEvaluator
from agi.system32.robotic.skill_executor import SkillExecutor
from agi.system32.robotic.fleet_manager import FleetManager
from agi.system32.robotic.kym_robot import KYMRobotVerifier, RobotProfile

def test_physics_safety_evaluator():
    evaluator = PhysicsSafetyEvaluator()

    # Simple acceleration curve (g's)
    acc = [10.0, 20.0, 50.0, 80.0, 50.0, 20.0, 10.0]
    dt = 0.005 # 5ms

    hic15 = evaluator.calculate_hic15(acc, dt)
    assert hic15 > 0.0

    # Nij
    nij = evaluator.calculate_nij(fz=500.0, fzc=1000.0, my=50.0, myc=100.0)
    assert round(nij, 1) == 1.0

    # Motion safety evaluation
    assert evaluator.evaluate_motion_safety(hic15=500.0, nij=0.8) == True
    assert evaluator.evaluate_motion_safety(hic15=800.0, nij=0.8) == False
    assert evaluator.evaluate_motion_safety(hic15=500.0, nij=1.2) == False

    # ISO Distance
    assert evaluator.verify_iso15066_distance(robot_speed=1.0, human_speed=1.6, response_time=0.5, distance=2.0) == True
    assert evaluator.verify_iso15066_distance(robot_speed=2.0, human_speed=1.6, response_time=0.5, distance=1.0) == False

def test_skill_executor():
    executor = SkillExecutor()
    contract = '''
    (skill_id: string = "maze-bench-v1")
    (required_hardware: list = ["lidar", "rgbd_camera"])
    '''

    # Success case
    agent_profile = {"hardware": ["lidar", "rgbd_camera", "wheels"], "phi_risk": 0.2}
    result = executor.execute_skill(agent_profile, contract, {})
    assert result["status"] == "success"
    assert result["skill"] == "maze-bench-v1"

    # Missing hardware
    agent_profile_bad_hw = {"hardware": ["lidar"], "phi_risk": 0.2}
    result = executor.execute_skill(agent_profile_bad_hw, contract, {})
    assert result["status"] == "failed"
    assert result["reason"] == "Missing required hardware"

    # High Risk
    agent_profile_high_risk = {"hardware": ["lidar", "rgbd_camera"], "phi_risk": 0.7}
    result = executor.execute_skill(agent_profile_high_risk, contract, {})
    assert result["status"] == "failed"
    assert "High Φ-RISK mode triggered" in result["reason"]

def test_fleet_manager():
    manager = FleetManager()

    manager.register_robot("ASI_ROBOT_A", {"phi_risk": 0.2, "hardware": ["lidar"]})
    manager.register_robot("ASI_ROBOT_B", {"phi_risk": 0.8, "hardware": ["rgbd"]})
    manager.register_robot("ASI_ROBOT_C", {"phi_risk": 0.1, "hardware": ["lidar", "wheels"]})

    # Task allocation
    best_robot = manager.allocate_task("clean warehouse")
    assert best_robot == "ASI_ROBOT_C"

    # Shared world model
    manager.update_world_model("ASI_ROBOT_A", "Obstacle at x:10, y:5")
    assert len(manager.le_world_model) == 1

    # Conflict resolution
    winner = manager.resolve_conflict("ASI_ROBOT_B", "ASI_ROBOT_A", "corridor")
    assert winner == "ASI_ROBOT_A"

def test_kym_robot_verifier():
    verifier = KYMRobotVerifier()

    robot_good = RobotProfile(
        seal="ASI_ROBOT_1",
        phi_c=0.95,
        phi_rep=0.90,
        provenance=1.0,
        ethics_compliant=True,
        manufacturer="ArkheCorp",
        model="Humanoid-X",
        serial="SN-1234",
        firmware_hash="abcd",
        incidents=0,
        avg_hic15=200.0,
        avg_nij=0.5,
        hardware=["lidar", "arms"]
    )

    attestation = verifier.verify_robot(robot_good)
    assert attestation["status"] == "verified"
    assert attestation["safe_mode"] == False
    assert attestation["classification"] == "low"

    # High risk robot due to incidents and high physical metrics
    robot_bad = RobotProfile(
        seal="ASI_ROBOT_2",
        phi_c=0.20,
        phi_rep=0.30,
        provenance=0.5,
        ethics_compliant=True,
        manufacturer="ArkheCorp",
        model="Arm-Y",
        serial="SN-5678",
        firmware_hash="efgh",
        incidents=5,
        avg_hic15=800.0,
        avg_nij=1.2,
        hardware=["arm"]
    )

    attestation_bad = verifier.verify_robot(robot_bad)
    assert attestation_bad["classification"] == "high"
    assert attestation_bad["safe_mode"] == True
