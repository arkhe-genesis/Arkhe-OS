import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.proof import Severity, VerificationResult, ConstitutionalProof
from core.constants import GHOST, LOOPSEAL, GAP_SOV, PHI_AUREA
from core.invariants import InvariantVerifier

class TestInvariants(unittest.TestCase):

    def setUp(self):
        self.verifier = InvariantVerifier()
        self.result = VerificationResult(module="TEST")

    def test_ghost_pure(self):
        """Ghost deve ser 1.0 quando nao ha falhas nem avisos."""
        checks = [("T1", Severity.PASS, "OK", {})]
        value, passed = self.verifier.check_ghost(checks)
        self.assertEqual(value, 1.0)
        self.assertTrue(passed)

    def test_ghost_with_warnings(self):
        """Ghost deve cair para 0.5 com advertencias."""
        checks = [("T1", Severity.PASS, "OK", {}),
                  ("T2", Severity.WARN, "Warning", {})]
        value, passed = self.verifier.check_ghost(checks)
        self.assertEqual(value, 0.5)
        self.assertFalse(passed)

    def test_loopseal_chain(self):
        """Loopseal requer pelo menos 2 elementos na cadeia."""
        chain_short = ["A"]
        value, passed = self.verifier.check_loopseal(chain_short)
        self.assertEqual(value, 0.5)

        chain_valid = ["A", "B", "C"]
        value, passed = self.verifier.check_loopseal(chain_valid)
        self.assertEqual(value, 1.0)
        self.assertTrue(passed)

    def test_phi_ratio(self):
        """Proporcao aurea deve ser proxima de phi."""
        value, passed = self.verifier.check_phi(PHI_AUREA, 1.0)
        self.assertGreater(value, 0.99)
        self.assertTrue(passed)

    def test_proof_generation(self):
        """Provas constitucionais devem ser geradas corretamente."""
        self.result.checks = [("T1", Severity.PASS, "Test passed", {"key": "value"})]
        proofs = self.result.generate_proofs("test_hash")
        self.assertEqual(len(proofs), 1)
        self.assertTrue(proofs[0].verify())

    def test_proof_tampering(self):
        """Provas devem ser inviolaveis."""
        self.result.checks = [("T1", Severity.PASS, "Original", {})]
        proofs = self.result.generate_proofs("test_hash")
        # Tentativa de adulteracao
        with self.assertRaises(ValueError):
            ConstitutionalProof(
                timestamp=proofs[0].timestamp,
                platform_hash="test_hash",
                module="TEST",
                invariant="T1",
                severity="PASS",
                message="Tampered",
                details="{}",
                signature=proofs[0].signature  # assinatura original, payload diferente
            )

if __name__ == "__main__":
    unittest.main(verbosity=2)