import numpy as np

class DummyPPO:
    def predict(self, obs, deterministic=True):
        return np.zeros(len(obs)//6 * 3), None
