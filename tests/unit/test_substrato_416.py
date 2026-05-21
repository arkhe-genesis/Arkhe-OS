import os
import json
import unittest
import sys
import importlib.util

# Load module from path because of hyphens in directory name
module_name = 'substrato_416_arkhe_cosmos'
module_path = 'substrates/400-499_advanced/substrato_416_arkhe_cosmos/substrato_416_arkhe_cosmos.py'
spec = importlib.util.spec_from_file_location(module_name, module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = module
spec.loader.exec_module(module)
Substrato416ArkheCosmos = module.Substrato416ArkheCosmos

class TestSubstrato416(unittest.TestCase):
    def test_canonize_outputs_correct_json(self):
        substrate = Substrato416ArkheCosmos()
        path = substrate.canonize()

        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertIn("SEAL_416_ARKHE_COSMOS", data)
        seal = data["SEAL_416_ARKHE_COSMOS"]

        self.assertEqual(seal["Hash"], "d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5")
        self.assertEqual(seal["Phi_C"], 0.976)
        self.assertEqual(seal["Integration"], "Arkhe Chain (Cosmos SDK) + IBC Eureka + CosmWasm + MCP")
        self.assertEqual(seal["Status"], "CANONIZED -- A Catedral tem agora uma blockchain soberana")

        os.remove(path)

if __name__ == "__main__":
    unittest.main()
