import numpy as np

class VectorizedAdaptiveSPSA:
    def __init__(self, bounds: list, a: float = 0.4, c: float = 0.2):
        self.bounds = np.array(bounds)
        self.a = a
        self.c = c
        self.best_score = -np.inf

    def step(self, current_theta: np.ndarray, evaluate_fn, epoch: int) -> np.ndarray:
        delta = np.random.choice([-1, 1], size=current_theta.shape)

        # Perturbações vetorizadas via np.where / np.clip
        theta_plus = np.clip(current_theta + self.c * delta, self.bounds[:, 0], self.bounds[:, 1])
        theta_minus = np.clip(current_theta - self.c * delta, self.bounds[:, 0], self.bounds[:, 1])

        score_plus = evaluate_fn(theta_plus)
        score_minus = evaluate_fn(theta_minus)

        grad_est = (score_plus - score_minus) / (2 * self.c * delta)

        ak = self.a / (epoch ** 0.602)
        new_theta = np.clip(current_theta + ak * grad_est, self.bounds[:, 0], self.bounds[:, 1])

        return new_theta
