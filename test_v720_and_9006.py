import sys
import unittest

class TestV720And9006(unittest.TestCase):
    def test_v720_import(self):
        import arkhe_v720_core
        self.assertTrue(hasattr(arkhe_v720_core, 'deploy_v720'))

    def test_9006_import(self):
        import substrate_9006_multi_llm_mesh
        self.assertTrue(hasattr(substrate_9006_multi_llm_mesh, 'LLMNode'))

if __name__ == '__main__':
    unittest.main()
