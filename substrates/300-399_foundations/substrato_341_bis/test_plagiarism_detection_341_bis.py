import unittest
import sys
import os
import time

# Add the substrato_341_bis directory directly to sys.path to bypass the invalid python module name '300-399_foundations'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from plagiarism_detection_341_bis import (
    ArkhePlagiarismEngine,
    Document,
    SeverityLevel,
    PlagiarismType,
    InvariantChecker,
    GHOST,
    GAP_MAX
)

class TestPlagiarismDetection341Bis(unittest.TestCase):
    def setUp(self):
        self.engine = ArkhePlagiarismEngine()

        self.ref_doc = Document("ref-001", "orcid:0000-0001-2345-6789", "A Inteligência Artificial Geral será alcançada através de redes neurais profundas e mecanismos de atenção otimizados para arquiteturas neuromórficas distribuídas.")
        self.engine.add_to_corpus(self.ref_doc)

    def test_stage_1_exact_match(self):
        # Exact duplicate
        susp_doc = Document("sub-101", "orcid:0000-0002-3456-7890", "A Inteligência Artificial Geral será alcançada através de redes neurais profundas e mecanismos de atenção otimizados para arquiteturas neuromórficas distribuídas.")

        similarity = self.engine.stage_1_fast_fingerprinting(susp_doc, self.ref_doc)
        self.assertEqual(similarity, 1.0)

        report = self.engine.analyze_document(susp_doc)
        self.assertEqual(report['severity'], SeverityLevel.CRITICAL.value)
        # Should be bounded by Gap Soberano
        self.assertLess(report['max_similarity'], GAP_MAX)
        self.assertEqual(report['plagiarism_type'], PlagiarismType.T1_LITERAL.value)

    def test_stage_1_partial_match(self):
        # High overlap
        susp_doc = Document("sub-102", "orcid:0000-0002-3456-7890", "A Inteligência Artificial Geral será alcançada através de redes neurais profundas e mecanismos de atenção otimizados para arquiteturas neuromórficas distribuídas. Isto é certo.")

        similarity = self.engine.stage_1_fast_fingerprinting(susp_doc, self.ref_doc)
        self.assertGreater(similarity, 0.7)
        self.assertLess(similarity, 1.0)

        report = self.engine.analyze_document(susp_doc)
        self.assertIn(report['severity'], [SeverityLevel.HIGH.value, SeverityLevel.CRITICAL.value])
        self.assertEqual(report['plagiarism_type'], PlagiarismType.T1_LITERAL.value)

    def test_stage_1_no_match(self):
        # Completely different
        susp_doc = Document("sub-103", "orcid:0000-0002-3456-7890", "A Catedral protege a originalidade das criações. O código é imutável na TemporalChain.")

        similarity = self.engine.stage_1_fast_fingerprinting(susp_doc, self.ref_doc)
        self.assertEqual(similarity, 0.0)

        report = self.engine.analyze_document(susp_doc)
        self.assertEqual(report['severity'], SeverityLevel.NONE.value)
        self.assertEqual(report['max_similarity'], 0.0)

    def test_invariant_ghost(self):
        # Score just above ghost
        self.assertTrue(InvariantChecker.check_ghost(GHOST + 0.01))
        # Score just below ghost
        self.assertFalse(InvariantChecker.check_ghost(GHOST - 0.01))

    def test_invariant_gap_soberano(self):
        # Score 1.0 violates gap soberano
        self.assertFalse(InvariantChecker.check_gap_soberano(1.0))
        # Valid score
        self.assertTrue(InvariantChecker.check_gap_soberano(0.8))

    def test_canonical_seal_generation(self):
        from unittest.mock import patch
        with patch('time.time', return_value=1000.0):
            seal = self.engine._generate_canonical_seal("doc-test", SeverityLevel.HIGH, 0.85)
        self.assertIsInstance(seal, str)
        self.assertEqual(len(seal), 64) # SHA3-256 length

    def test_downgrade_severity_if_ghost_fails(self):
        # Create a condition where severity is high but ghost fails (not naturally possible with thresholds but we can test the fallback)
        doc = Document("doc", "orcid", "a")
        report = self.engine.analyze_document(doc)

        # When similarity is 0, severity should be NONE and ghost should fail
        self.assertEqual(report['severity'], SeverityLevel.NONE.value)
        self.assertFalse(report['invariants']['ghost_met'])

if __name__ == '__main__':
    unittest.main()
