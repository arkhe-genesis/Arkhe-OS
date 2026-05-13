# src/arkhe/layers/engineering/test_hardening.py
import unittest
import hashlib, json
from pathlib import Path

class CanonicalTestRunner:
    def __init__(self, test_dir, ledger):
        self.test_dir = Path(test_dir)
        self.ledger = ledger
        self.results = []

    def run_all(self):
        loader = unittest.TestLoader()
        suite = loader.discover(str(self.test_dir), pattern='test_*.py')
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        # produce canonical seal of all test results
        seal_data = {
            'passed': result.testsRun - len(result.failures) - len(result.errors),
            'total': result.testsRun,
            'failures': [str(e) for e in result.failures],
            'errors': [str(e) for e in result.errors],
        }
        seal = hashlib.sha3_256(json.dumps(seal_data, default=str).encode()).hexdigest()[:16]
        self.ledger.record('test_run', {'seal': seal, 'summary': seal_data})
        return seal_data, seal
