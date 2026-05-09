import unittest
import io
import json
import math
from arkhe_os.parser.frontends.ml_framework_parser import MLFrameworkParser

class TestMLParser(unittest.TestCase):
    def setUp(self):
        self.parser = MLFrameworkParser()

    def test_pytorch_fallback(self):
        graph = self.parser.parse(b"", "model.pt")
        node = list(graph.nodes.values())[0]
        self.assertEqual(node.name, "pytorch_model")
        self.assertIn("total_params", node.metadata)
        self.assertIn("coherence", node.metadata)
        # Should fallback to 25.6M params
        self.assertEqual(node.metadata["total_params"], 25600000)

    def test_xgboost(self):
        config = {
            "learner": {
                "gradient_booster": {
                    "gbtree_train_param": {
                        "num_parallel_tree": "50",
                        "max_depth": "4"
                    }
                }
            }
        }
        data = json.dumps(config).encode('utf-8')
        graph = self.parser.parse(data, "model.json")
        node = list(graph.nodes.values())[0]
        self.assertEqual(node.name, "xgboost_model")
        self.assertEqual(node.metadata["n_estimators"], 50)
        self.assertEqual(node.metadata["max_depth"], 4)

    def test_tensorflow(self):
        graph = self.parser.parse(b"", "model.pb")
        node = list(graph.nodes.values())[0]
        self.assertEqual(node.name, "tensorflow_model")
        self.assertEqual(node.metadata["total_params"], 1000000)

    def test_scikit(self):
        graph = self.parser.parse(b"", "model.pkl")
        node = list(graph.nodes.values())[0]
        self.assertEqual(node.name, "sklearn_model")
        self.assertEqual(node.metadata["total_params"], 1000)

    def test_phi_c_calculation(self):
        # Phi_c = alpha * AUC - beta * log10(params) + gamma * (1 - bias) + delta * exp(-lambda * latency)
        # alpha=1.0, beta=0.05, gamma=0.5, delta=0.1, lambda=0.01
        auc = 0.942
        params = 25600000
        bias = 0.03
        latency = 2.3

        perf = 1.0 * auc
        comp = 0.05 * math.log10(params)
        equity = 0.5 * (1.0 - bias)
        eff = 0.1 * math.exp(-0.01 * latency)
        expected_phi = perf - comp + equity + eff
        expected_phi = max(0.0, min(1.0, expected_phi))

        phi_calc = self.parser._compute_phi_c(auc, params, bias, latency)
        self.assertAlmostEqual(phi_calc, expected_phi, places=5)

if __name__ == "__main__":
    unittest.main()
