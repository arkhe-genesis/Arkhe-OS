import os
import sys
import unittest
from unittest.mock import patch
import numpy as np

# Adicionar caminhos para os imports funcionarem devido a nomes de diretório não-padrão
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../substrates/300-399_foundations/substrato_342')))

from code_plagiarism_engine import CodePlagiarismEngine

class TestCodePlagiarismEngine(unittest.TestCase):
    def setUp(self):
        self.engine = CodePlagiarismEngine()

    def test_jaccard_similarity_identical(self):
        code_a = "function add(a, b) { return a + b; }"
        code_b = "function add(a, b) { return a + b; }"
        sim = self.engine._jaccard_similarity(code_a, code_b)
        self.assertEqual(sim, 1.0)

    def test_jaccard_similarity_different(self):
        code_a = "function add(a, b) { return a + b; }"
        code_b = "def subtract(x, y):\n    return x - y"
        sim = self.engine._jaccard_similarity(code_a, code_b)
        self.assertEqual(sim, 0.0)

    def test_ast_similarity(self):
        code_a = "function add(a, b) { return a + b; }"
        code_b = "function add(a, b) { return a + b; }"
        # Default mock in code generates values between 0.75 and 1.0
        sim = self.engine._ast_similarity(code_a, code_b, "solidity")
        self.assertTrue(0.75 <= sim <= 1.0)

    def test_graph_similarity(self):
        code_a = "function add(a, b) { return a + b; }"
        code_b = "function add(a, b) { return a + b; }"
        # Default mock in code generates values between 0.8 and 1.0
        sim = self.engine._graph_similarity(code_a, code_b)
        self.assertTrue(0.8 <= sim <= 1.0)

    def test_detect_plagiarism_none(self):
        code_a = "function add(a, b) { return a + b; }"
        code_b = "def subtract(x, y):\n    return x - y"
        result = self.engine.detect_plagiarism(code_a, code_b)
        self.assertEqual(result["verdict"], "NONE")
        self.assertEqual(result["stage"], 1)
        self.assertEqual(result["similarity"], 0.0)

    def test_detect_plagiarism_low(self):
        code_a = "function add(a, b) { return a + b; }"
        code_b = "function add(a, b) { return a + b; }"

        # Patch the ast_similarity to return below semantic threshold (0.75)
        with patch.object(self.engine, '_ast_similarity', return_value=0.5):
            result = self.engine.detect_plagiarism(code_a, code_b)
            self.assertEqual(result["verdict"], "LOW")
            self.assertEqual(result["stage"], 2)
            self.assertEqual(result["similarity"], 0.5)

    def test_detect_plagiarism_medium(self):
        code_a = "function add(a, b) { return a + b; }"
        code_b = "function add(a, b) { return a + b; }"

        # Patch the ast_similarity to pass stage 2 (> 0.75), graph_similarity below structural threshold (0.80)
        with patch.object(self.engine, '_ast_similarity', return_value=0.8):
            with patch.object(self.engine, '_graph_similarity', return_value=0.75):
                result = self.engine.detect_plagiarism(code_a, code_b)
                self.assertEqual(result["verdict"], "MEDIUM")
                self.assertEqual(result["stage"], 3)
                self.assertIn("canonical_seal", result)

    def test_detect_plagiarism_high(self):
        code_a = "function add(a, b) { return a + b; }"
        code_b = "function add(a, b) { return a + b; }"

        # Patch the ast_similarity to pass stage 2 (> 0.75), graph_similarity above structural threshold (0.80)
        with patch.object(self.engine, '_ast_similarity', return_value=0.8):
            with patch.object(self.engine, '_graph_similarity', return_value=0.9):
                result = self.engine.detect_plagiarism(code_a, code_b)
                self.assertEqual(result["verdict"], "HIGH")
                self.assertEqual(result["stage"], 3)
                self.assertIn("canonical_seal", result)

if __name__ == '__main__':
    unittest.main()
