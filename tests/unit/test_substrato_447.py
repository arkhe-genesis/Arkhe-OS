import unittest
import importlib.util
import os
import tempfile
import json
import sys

class TestSubstrato447MegaKernel(unittest.TestCase):
    def setUp(self):
        # Determine the path to the substrate module
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.module_path = os.path.join(base_dir, 'substrates', '400-499_advanced', 'substrato_447_megakernel', 'substrato_447_megakernel.py')

        # Ensure the file exists
        self.assertTrue(os.path.exists(self.module_path), f"File not found: {self.module_path}")

        # Dynamically load the module to avoid SyntaxError with hyphens in the path
        spec = importlib.util.spec_from_file_location("substrato_447_megakernel", self.module_path)
        self.module = importlib.util.module_from_spec(spec)
        sys.modules["substrato_447_megakernel"] = self.module
        spec.loader.exec_module(self.module)

    def test_invariants_no_f_strings(self):
        """Verify that the module code contains no f-strings."""
        with open(self.module_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertNotIn('f"', content, "Found f-string usage (f\") in substrato_447_megakernel.py")
            self.assertNotIn("f'", content, "Found f-string usage (f') in substrato_447_megakernel.py")

    def test_invariants_no_non_ascii(self):
        """Verify that the module code contains no non-ASCII characters."""
        with open(self.module_path, 'r', encoding='utf-8') as f:
            content = f.read()
            try:
                content.encode('ascii')
            except UnicodeEncodeError as e:
                self.fail(f"Found non-ASCII character in substrato_447_megakernel.py: {e}")

    def test_megakernel_execution(self):
        """Verify that MegaKernel can instantiate and execute orchestrate."""
        kernel = self.module.MegaKernel()

        # Test spectral audit
        max_trans = kernel.run_spectral_audit_440()
        self.assertIsInstance(max_trans, float)
        self.assertGreater(max_trans, 0.0)

        # Test execution completes without raising exceptions
        try:
            kernel.orchestrate()
        except Exception as e:
            self.fail(f"MegaKernel.orchestrate() raised Exception unexpectedly: {e}")

if __name__ == '__main__':
    unittest.main()