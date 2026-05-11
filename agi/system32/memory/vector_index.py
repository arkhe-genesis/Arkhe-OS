class SemanticVectorIndex:
    def __init__(self, dim):
        self.dim = dim
    def add(self, id, vec, coherence=None):
        return True
    def search(self, vec, k=5, min_coherence=0.7):
        return [{"state_id": "state1", "similarity": 0.9}]
