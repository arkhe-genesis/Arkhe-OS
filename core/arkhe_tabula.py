import json

class TabulaOracle:
    def __init__(self):
        self.model = None
        self.feature_names = []

    def save_model(self, path):
        # mock save
        with open(path, 'w') as f:
            json.dump({'model': 'xgboost', 'features': self.feature_names}, f)
