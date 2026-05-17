import numpy as np

def add_gaussian_noise(value: float, epsilon: float, delta: float = 1e-5) -> float:
    # Dummy DP implementation
    sensitivity = 1.0
    sigma = np.sqrt(2 * np.log(1.25 / delta)) * sensitivity / epsilon
    noise = np.random.normal(0, sigma)
    return value + noise
