class DiscourseDetector:
    def __init__(self, threshold: float):
        self.threshold = threshold

    def analyze(self, text: str) -> dict:
        if "malicious" in text.lower():
            return {"flagged": True, "state": "MASTER", "deviation_score": 0.95}
        return {"flagged": False, "state": "NORMAL", "deviation_score": 0.1}
