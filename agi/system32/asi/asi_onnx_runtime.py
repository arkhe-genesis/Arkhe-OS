import numpy as np

class ASIOnnxRuntime:
    pass

class ASIONNXRuntime:
    def __init__(self, registry, coherence):
        self.registry = registry
        self.coherence = coherence
        self.active_models = {}
    def load_model(self, a, b):
        self.active_models[a] = type('ActiveModel', (), {'model_hash': b})()
        return True
    def run_inference(self, a, b):
        return [np.array([1, 2, 3], dtype=np.float32)]
    def run(self, a, b):
        return np.array([1, 2, 3], dtype=np.float32).tobytes()
    def hot_swap_model(self, a, b):
        self.active_models[a] = type('ActiveModel', (), {'model_hash': b})()
        return True
    def get_model_status(self):
        return {"test_func": {"calls": 1}}
