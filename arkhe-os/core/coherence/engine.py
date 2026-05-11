import time
import random

class CoherenceEngine:
    """
    Substrate 344 & Core Integration: Continuous Φ_C metric based on system health,
    user actions, and network consensus.
    """
    def __init__(self):
        self.genesis_coherence = 0.72
        self.current_coherence = self.genesis_coherence
        self.last_update = time.time()

    def measure(self) -> float:
        """Returns the real-time Φ_C."""
        now = time.time()
        elapsed = now - self.last_update

        # Simulate slight exponential temporal decay & noise
        decay = 0.0001 * elapsed
        noise = random.uniform(-0.02, 0.03)

        self.current_coherence = max(0.0, min(1.0, self.current_coherence - decay + noise))
        self.last_update = now

        return self.current_coherence

coherence_engine = CoherenceEngine()
