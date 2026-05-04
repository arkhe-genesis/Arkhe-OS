import numpy as np
from typing import Dict, Optional, Tuple

class AdaptiveSPSA:
    def __init__(self, param_bounds, mode='adaptive', plateau_threshold=5, min_improvement=0.015):
        self.param_bounds = param_bounds
        self.current_params = {'a': 0.4, 'c': 0.2}
        self.stagnation_counter = 0

    def initialize_with_tabula_prior(self, nuclear_features: Dict,
                                     tabula_prior) -> np.ndarray:
        """Initialize parameters using Tabula Oracle prior."""
        return tabula_prior.initialize_spsa_with_prior(
            nuclear_features, self.param_bounds
        )

    def step(self, evaluate_fn, epoch: int, current_theta: np.ndarray = None,
             nuclear_features: Optional[Dict] = None,
             tabula_prior = None) -> Tuple[np.ndarray, float]:
        if current_theta is None and tabula_prior is not None and nuclear_features is not None:
            current_theta = self.initialize_with_tabula_prior(nuclear_features, tabula_prior)
            print(f"🌲 Initialized SPSA with Tabula prior: kappa={current_theta[0]:.3f}")
        elif current_theta is None:
            current_theta = np.array([np.random.uniform(b[0], b[1]) for b in self.param_bounds])

        score = evaluate_fn(current_theta)
        # Mock step logic
        new_theta = np.clip(current_theta + np.random.normal(0, 0.01, size=len(current_theta)),
                            [b[0] for b in self.param_bounds],
                            [b[1] for b in self.param_bounds])
        return new_theta, score
