#!/usr/bin/env python3
"""
Unit tests for Substrato 341-BIS (Plagiarism Detection Concept).
"""

import sys
import pytest
import math

sys.path.insert(0, "substrates/300-399_foundations/substrato_341_bis")
from plagiarism_detection_341_bis import (
    ArkhePlagiarismEngine,
    GHOST,
    LOOPSEAL,
    GAP_SOBERANO,
    PHI
)

class TestPlagiarismDetection341Bis:
    def setup_method(self):
        self.engine = ArkhePlagiarismEngine()

    def test_ghost_invariant_violation(self):
        """Test that accusation fails if Phi_C < GHOST."""
        text1 = "Some random text."
        text2 = "Some random text."
        with pytest.raises(ValueError, match="Ghost Invariant Violated"):
            self.engine.verify_plagiarism(text1, text2, GHOST - 0.01)

    def test_stage_1_fingerprinting_identical(self):
        """Test identical texts max out at GAP_SOBERANO in stage 1."""
        text = "This is a simple text meant to check the fingerprinting mechanism."
        sim = self.engine.stage_1_fingerprinting(text, text)
        assert sim == GAP_SOBERANO

    def test_stage_1_fingerprinting_different(self):
        """Test different texts have low similarity."""
        text1 = "This is a simple text meant to check the fingerprinting mechanism."
        text2 = "Completely unrelated words that share nothing with the other sentence."
        sim = self.engine.stage_1_fingerprinting(text1, text2)
        assert sim < 0.1

    def test_stage_2_semantic_similarity_identical(self):
        """Test identical texts max out at GAP_SOBERANO in stage 2."""
        text = "This is a simple text meant to check the semantic similarity mechanism."
        sim = self.engine.stage_2_semantic_similarity(text, text)
        assert sim == GAP_SOBERANO

    def test_verify_plagiarism_success(self):
        """Test full pipeline with Phi_C > GHOST."""
        text = "A Catedral não tolera a usurpação da criação. A originalidade é sagrada."
        report = self.engine.verify_plagiarism(text, text, GHOST + 0.1)

        assert report.phi_c_accuser == GHOST + 0.1
        assert report.similarity_score == GAP_SOBERANO
        assert report.severity == "HIGH"
        assert report.stage_reached == 2
        assert len(report.temporal_seal) == 64  # SHA3-256 hex length
