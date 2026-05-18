import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from substrate_240_vitalik.redundant_checker.intention_checker import RedundantIntentionChecker

def py_transfer(amount: int): return amount * 2
def c_transfer(amount: int): return amount * 2
def sol_transfer(amount: int): return amount * 2

class TestPolyglotIntent(unittest.TestCase):
    def test_polyglot_intent(self):
        checker = RedundantIntentionChecker()
        checker.register_implementation("Python", py_transfer)
        checker.register_implementation("C", c_transfer)
        checker.register_implementation("Solidity", sol_transfer)

        result = checker.check_intention("transferir 100 USDC", {"amount": 100})
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()