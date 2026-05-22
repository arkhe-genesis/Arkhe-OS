import unittest
import os
import json
import importlib.util

class TestSubstrato531(unittest.TestCase):
    def setUp(self):
        # Dynamically import the module because of the invalid identifier name 500-599_advanced
        file_path = "substrates/500-599_advanced/substrato_531_pnpm_supply_chain/substrato_531_pnpm_supply_chain.py"
        spec = importlib.util.spec_from_file_location("substrato_531_pnpm_supply_chain", file_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.substrate = self.module.Substrato531PnpmSupplyChain()

    def test_canonize(self):
        path, seal = self.substrate.canonize()
        self.assertTrue(os.path.exists(path))
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data["substrate"], "531-PNPM-SUPPLY-CHAIN")
        self.assertEqual(data["strict_mode"], "CANONIZED_CLEAN")
        self.assertEqual(data["canonical_seal"], seal)
        os.remove(path)

if __name__ == '__main__':
    unittest.main()
