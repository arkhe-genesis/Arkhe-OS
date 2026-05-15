import unittest
import os
import subprocess

class TestSubstrato9045(unittest.TestCase):
    def test_hsm_script_exists(self):
        self.assertTrue(os.path.exists("deploy/hsm/production_hsm_setup.sh"))

    def test_dashboard_script_exists(self):
        self.assertTrue(os.path.exists("deploy/dashboard/production_dashboard_setup.sh"))

    def test_cluster_script_exists(self):
        self.assertTrue(os.path.exists("deploy/kubernetes/production-cluster-setup.sh"))

    def test_load_test_script_exists(self):
        self.assertTrue(os.path.exists("tests/load/production_load_test.sh"))

    def test_audience_bridge_yaml_exists(self):
        self.assertTrue(os.path.exists("deploy/audience-bridge/production-audience-bridge.yaml"))

    def test_execution(self):
        # Just test the dummy execution file
        result = subprocess.run(["python3", "substrato_9045_production_execution.py"], capture_output=True, text=True)
        self.assertIn("ARKHE", result.stdout)

if __name__ == '__main__':
    unittest.main()
