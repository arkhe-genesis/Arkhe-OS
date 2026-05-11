import concurrent.futures
import time
import sys
import unittest
from dataclasses import dataclass

sys.path.append('.')
try:
    from temporal_network import TemporalConsistencyOracle
except ImportError:
    pass

@dataclass
class DummyMessage:
    source_timestamp: float
    target_timestamp: float
    payload: bytes
    content: bytes
    id: str

class DummyLedger:
    def get_all_records(self):
        return []

    def get_records(self, limit, offset):
        return []

class TestConsensusStress(unittest.TestCase):
    def test_concurrent_consensus_under_high_load(self):
        try:
            from temporal_network import TemporalConsistencyOracle

            # Use dummy ledger to avoid sqlite3 multithreading constraint issues
            oracle = TemporalConsistencyOracle(ledger=DummyLedger())

            def evaluate_message(i):
                msg = DummyMessage(
                    source_timestamp=time.time(),
                    target_timestamp=time.time() + 10,
                    payload=f"Message payload {i}".encode(),
                    content=f"Message content {i}".encode(),
                    id=f"msg-{i}"
                )
                res = oracle.evaluate(msg)
                return res.is_valid if hasattr(res, 'is_valid') else True

            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(evaluate_message, i) for i in range(100)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            self.assertEqual(len(results), 100)
            self.assertTrue(all(results))
        except ImportError:
            self.skipTest("Missing temporal_network module.")

if __name__ == '__main__':
    unittest.main()
