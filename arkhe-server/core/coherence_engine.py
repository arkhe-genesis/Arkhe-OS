class CoherenceEngine:
    def __init__(self):
        self.coherence_score = 0.0

    def aggregate_phi_c(self, scores):
        if not scores:
            return 0.0
        self.coherence_score = sum(scores) / len(scores)
        return self.coherence_score

    def export_prometheus(self):
        return f"coherence_score {self.coherence_score}"

def calculate_coherence():
    engine = CoherenceEngine()
    return engine
