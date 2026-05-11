#!/usr/bin/env python3
"""
Edge of Chaos Controller – SBM-inspired adaptive coupling for Arkhe daemon.
"""

import numpy as np
from collections import deque

class EdgeOfChaosController:
    def __init__(self, initial_K=0.618, target_lambda=0.95,
                 K_min=0.3, K_max=1.2, adaptation_rate=0.02,
                 history_len=50, use_derivative=True):
        self.K = initial_K
        self.target = target_lambda
        self.K_min = K_min
        self.K_max = K_max
        self.alpha = adaptation_rate
        self.use_derivative = use_derivative

        self.lambda_history = deque(maxlen=history_len)
        self.dlambda_history = deque(maxlen=history_len)
        self.step_count = 0

    def update(self, current_lambda: float) -> float:
        self.lambda_history.append(current_lambda)

        if len(self.lambda_history) >= 2:
            dlambda = self.lambda_history[-1] - self.lambda_history[-2]
            self.dlambda_history.append(dlambda)
        else:
            dlambda = 0.0

        error = current_lambda - self.target

        if self.use_derivative and len(self.dlambda_history) > 0:
            avg_dlambda = np.mean(self.dlambda_history)
        else:
            avg_dlambda = 0.0

        delta_K = -self.alpha * error
        if self.use_derivative:
            delta_K -= 0.5 * self.alpha * avg_dlambda

        self.K = np.clip(self.K + delta_K, self.K_min, self.K_max)
        self.step_count += 1
        return self.K
