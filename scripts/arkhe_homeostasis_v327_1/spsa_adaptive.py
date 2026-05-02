import numpy as np

class AdaptiveSPSA:
    def __init__(self, param_bounds, mode='adaptive', plateau_threshold=4, min_improvement=0.02):
        self.param_bounds = param_bounds
        self.mode = mode
        self.plateau_threshold = plateau_threshold
        self.min_improvement = min_improvement
        self.current_params = {'a': 0.1, 'c': 0.05}
        self.best_score = -float('inf')
        self.plateau_counter = 0

    def step(self, evaluate_fn, epoch, current_theta):
        a = self.current_params['a']
        c = self.current_params['c']

        delta = np.random.choice([-1, 1], size=len(current_theta))
        theta_plus = np.clip(current_theta + c * delta, *zip(*self.param_bounds))
        theta_minus = np.clip(current_theta - c * delta, *zip(*self.param_bounds))

        y_plus = evaluate_fn(theta_plus)
        y_minus = evaluate_fn(theta_minus)
        grad_est = (y_plus - y_minus) / (2 * c * delta)

        ak = a / (epoch ** 0.602)
        next_theta = current_theta + ak * grad_est
        next_theta = np.clip(next_theta, *zip(*self.param_bounds))

        current_score = evaluate_fn(next_theta)

        if self.mode == 'adaptive':
            if current_score <= self.best_score + self.min_improvement:
                self.plateau_counter += 1
            else:
                self.plateau_counter = 0
                self.best_score = max(self.best_score, current_score)
                self.current_params['a'] = 0.1 # reset to stable

            if self.plateau_counter >= self.plateau_threshold:
                self.current_params['a'] = 0.4 # SHOCK
                self.plateau_counter = 0

        return next_theta, current_score
