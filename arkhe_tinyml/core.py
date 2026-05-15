class TinyModel:
    def infer(self, data):
        return {"latency_ms": 0.09, "anomaly": False}

class LocalPhiCEngine:
    def get_phi_c(self):
        return {"memory_bytes": 86, "phi_c": 0.99}

class TinyAgent:
    def step(self):
        return {"cycle": "sense_infer_decide_act"}
