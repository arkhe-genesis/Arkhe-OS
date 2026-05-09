import numpy as np
from collections import deque
from typing import Dict, List, Tuple

class DataCoherenceMetrics:
    """
    Calculates lambda2-data: temporal coherence of data pipelines.
    """
    def __init__(self):
        self.history = deque(maxlen=100)

    def calculate_lambda2(self, latency_p99: float, throughput_ratio: float,
                         error_rate: float, freshness_seconds: float) -> float:
        """
        Calculates a coherence score [0, 1] based on normalized pipeline metrics.
        """
        # Normalization
        l_score = 1.0 - min(latency_p99 / 60.0, 1.0)
        t_score = min(throughput_ratio, 1.0)
        e_score = 1.0 - error_rate
        f_score = 1.0 - min(freshness_seconds / 300.0, 1.0)

        # Weighted average
        lambda_data = (0.3 * l_score + 0.3 * t_score + 0.2 * e_score + 0.2 * f_score)
        self.history.append(lambda_data)
        return float(np.clip(lambda_data, 0.0, 1.0))

class DataSBMController:
    """
    Stabilized by Memory (SBM) controller for cloud data infrastructure.
    """
    def __init__(self, target: float = 0.95):
        self.target = target
        self.state_history = deque(maxlen=300)

    def decide_action(self, current_lambda: float) -> str:
        self.state_history.append(current_lambda)
        if current_lambda < 0.90:
            return "CIRCUIT_BREAK" # Pause ingestion to prevent corruption
        elif current_lambda > 0.98:
            return "SCALE_UP"      # Increase parallelism at edge-of-chaos
        else:
            return "MAINTAIN"      # Optimal critical regime
