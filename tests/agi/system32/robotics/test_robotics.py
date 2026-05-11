import unittest
import numpy as np
from robotics.physical_safety_evaluator import calculate_hic15, calculate_nij, evaluate_safety
from robotics.skill_executor import parse_skill_contract, validate_agent_capability
from robotics.fleet_orchestrator import TaskDecomposer, LeWorldModel, ConflictResolver

class TestRoboticsAutonomy(unittest.TestCase):
    def test_calculate_hic15(self):
        # Create a simple pulse acceleration trace (e.g., 50g for 10ms)
        dt = 0.001
        trace = np.zeros(50)
        trace[10:20] = 50.0  # 10ms duration
        hic = calculate_hic15(trace, dt)

        # Exact calculation:
        # t_diff = 0.01
        # avg_a = 50.0
        # expected_hic = 0.01 * (50.0 ** 2.5) = 0.01 * 17677.6695 = 176.776695

        self.assertAlmostEqual(hic, 176.77, places=1)

    def test_calculate_nij(self):
        # Fz = 3403 (half of Fzc), My = 155 (half of Myc)
        # Expected Nij = 0.5 + 0.5 = 1.0
        critical_values = {'Fzc': 6806.0, 'Myc': 310.0}
        nij = calculate_nij(3403.0, 155.0, critical_values)
        self.assertAlmostEqual(nij, 1.0, places=2)

    def test_evaluate_safety(self):
        metrics = {'hic15': 600, 'nij': 0.8}
        thresholds = {'hic15_max': 700, 'nij_max': 1.0}
        self.assertTrue(evaluate_safety(metrics, thresholds))

        metrics_unsafe = {'hic15': 800, 'nij': 0.8}
        self.assertFalse(evaluate_safety(metrics_unsafe, thresholds))

    def test_parse_skill_contract(self):
        contract_text = '''
        (contract MazeNavigation
          (state
            (skill_id: string = "maze-bench-v1")
            (required_hardware: list = ["lidar", "rgbd_camera"])
          )
        )
        '''
        parsed = parse_skill_contract(contract_text)
        self.assertEqual(parsed['skill_id'], 'maze-bench-v1')
        self.assertEqual(parsed['required_hardware'], ['lidar', 'rgbd_camera'])

    def test_validate_agent_capability(self):
        agent_seal = {'capabilities': ['lidar', 'rgbd_camera', 'arm']}
        required_hardware = ['lidar', 'rgbd_camera']
        self.assertTrue(validate_agent_capability(agent_seal, required_hardware))

        required_hardware_missing = ['lidar', 'sonar']
        self.assertFalse(validate_agent_capability(agent_seal, required_hardware_missing))

    def test_task_decomposer(self):
        decomposer = TaskDecomposer()
        robots = [{'id': 'r1'}, {'id': 'r2'}]
        allocations = decomposer.decompose("clean warehouse", robots)
        self.assertEqual(len(allocations), 2)
        self.assertIn('r1', allocations)
        self.assertIn('r2', allocations)

    def test_le_world_model(self):
        model = LeWorldModel()
        model.update_observation('r1', 'obj_1', {'type': 'obstacle', 'x': 10})
        state = model.get_world_state()
        self.assertIn('obj_1', state)
        self.assertEqual(state['obj_1']['reported_by'], 'r1')
        self.assertEqual(state['obj_1']['data']['type'], 'obstacle')

    def test_conflict_resolver(self):
        resolver = ConflictResolver()
        # robot_a has lower risk, should win if priorities are equal
        robot_a = {'id': 'r1', 'task_priority': 1, 'phi_risk': 0.1} # score = 1 / 0.2 = 5
        robot_b = {'id': 'r2', 'task_priority': 1, 'phi_risk': 0.4} # score = 1 / 0.5 = 2

        winner = resolver.arbitrate({}, robot_a, robot_b)
        self.assertEqual(winner, 'r1')

        # robot_b has higher priority, should win despite slightly higher risk
        robot_a2 = {'id': 'r1', 'task_priority': 1, 'phi_risk': 0.1} # score = 1 / 0.2 = 5
        robot_b2 = {'id': 'r2', 'task_priority': 4, 'phi_risk': 0.3} # score = 4 / 0.4 = 10

        winner2 = resolver.arbitrate({}, robot_a2, robot_b2)
        self.assertEqual(winner2, 'r2')

if __name__ == '__main__':
    unittest.main()
