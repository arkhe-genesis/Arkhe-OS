
class DeviationTracker:
    def __init__(self, t):
        self.t = t
    def check_deviation(self, val):
        return False
    def register_expected_hash(self, val):
        pass
    def detect_deviations(self, val):
        return []
    def check_execution(self, a, b, c):
        return type('Alert', (), {'severity': 'high'})()
