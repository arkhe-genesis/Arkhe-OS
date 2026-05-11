import sys
import time
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

class TestOracleEvaluationBenchmark(unittest.TestCase):
    def test_oracle_evaluation_latency(self):
        try:
            from temporal_network import TemporalConsistencyOracle

            oracle = TemporalConsistencyOracle(ledger=DummyLedger())
            msg = DummyMessage(
                source_timestamp=time.time(),
                target_timestamp=time.time() + 10,
                payload=b"benchmark payload",
                content=b"benchmark content",
                id="msg-bench"
            )

            # Warmup
            for _ in range(10):
                oracle.evaluate(msg)

            # Benchmark 1000 executions
            start_time = time.time()
            for _ in range(1000):
                oracle.evaluate(msg)
            elapsed = time.time() - start_time

            # Assume 1000 evaluations should easily take < 1 second.
            self.assertLess(elapsed, 1.0, f"Oracle evaluation latency scale exceeded 1 second for 1000 runs ({elapsed}s)")
        except ImportError:
            self.skipTest("Missing temporal_network module.")

if __name__ == '__main__':
    unittest.main()
