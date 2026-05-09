from agi.system32.robotics.safety.physical_evaluator import PhysicalSafetyEvaluator
from agi.system32.robotics.orchestration.fleet_manager import FleetManager

class MockRobot:
    def __init__(self, rid, risk):
        self.id = rid
        self.phi_risk = risk

def test_physical_safety():
    evaluator = PhysicalSafetyEvaluator()
    safe_metrics = {'hic_15': 500, 'nij': 0.8, 'speed': 0.2, 'force': 100}
    assert evaluator.get_safety_seal(safe_metrics) is True

    unsafe_metrics = {'hic_15': 800, 'nij': 1.2, 'speed': 0.5, 'force': 200}
    assert evaluator.get_safety_seal(unsafe_metrics) is False

def test_fleet_manager():
    manager = FleetManager()
    r1 = MockRobot("r1", 0.2)
    r2 = MockRobot("r2", 0.7)

    # R1 deve ser escolhido por ter menor phi_risk
    assert manager.allocate_task("limpar", [r1, r2]) == "r1"
    assert manager.resolve_conflict(r1, r2) == "r1"
