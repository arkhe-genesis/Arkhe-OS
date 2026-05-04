import unittest
from src.arkhe_core.quantum_registry import QuantumSyndromeRegistry
from scripts.ritual_calibracao_criogenica import ritual_calibracao

class TestArkheQuantum(unittest.TestCase):
    def test_registry(self):
        reg = QuantumSyndromeRegistry()
        w = reg.register_syndrome("Q_TEST", "BIT_FLIP", 0.1)
        self.assertEqual(len(reg.get_audit_log()), 1)
        self.assertFalse(reg.get_audit_log()[0]["correction_applied"])
        self.assertEqual(len(w), 64)

    def test_calibration(self):
        # Just ensure it runs without error
        selo = ritual_calibracao()
        self.assertEqual(len(selo), 64)

if __name__ == "__main__":
    unittest.main()
