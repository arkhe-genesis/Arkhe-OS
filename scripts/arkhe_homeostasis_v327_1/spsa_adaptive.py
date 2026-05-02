import numpy as np

class AdaptiveSPSA:
    def __init__(self, param_bounds, mode='adaptive', plateau_threshold=5, min_improvement=0.015):
        self.param_bounds = param_bounds
        self.current_params = {'a': 0.4, 'c': 0.2}
        self.stagnation_counter = 0

    def step(self, evaluate_fn, epoch, current_theta):
        score = evaluate_fn(current_theta)
        # Mock step logic
        new_theta = np.clip(current_theta + np.random.normal(0, 0.01, size=len(current_theta)),
                            [b[0] for b in self.param_bounds],
                            [b[1] for b in self.param_bounds])
        return new_theta, score
