import unittest
import torch
import numpy as np

from core.metacognition.metacognition_module import (
    ContraFactualWorldModel,
    ContraFactualSafetyChecker,
    CatedralManifoldConfirmed,
    CurvatureAdjustedValuation,
    ResourceBundle,
    AsyncResourceNegotiator,
    RiemannianCurriculumGenerator,
    MissionGoal
)

class TestSubstrate147(unittest.TestCase):
    def test_counterfactual_model(self):
        model = ContraFactualWorldModel(state_dim=4, action_dim=4)
        state = torch.zeros(4)
        mean, std, reward, done = model.predict(state, 0)
        self.assertEqual(mean.shape, (4,))
        self.assertEqual(std.shape, (4,))

    def test_resource_bundle(self):
        r1 = ResourceBundle(1.0, 1.0, 1.0, 1.0)
        r2 = ResourceBundle(2.0, 2.0, 2.0, 2.0)
        r3 = r1 + r2
        self.assertEqual(r3.energy_gj, 3.0)

    def test_curriculum_generator(self):
        manifold = CatedralManifoldConfirmed()
        gen = RiemannianCurriculumGenerator(manifold, {})
        mission = MissionGoal(id="test", description="explore", priority=1.0, constraints={})
        stages = gen.generate_curriculum(mission, ["zone_1", "zone_2"])
        self.assertTrue(len(stages) > 0)

if __name__ == "__main__":
    unittest.main()
