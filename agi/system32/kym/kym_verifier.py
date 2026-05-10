class KYMVerifier:
    def calculate_phi_risk(self, entity):
        risk = 1.0 - (0.35 * entity.phi_c + 0.25 * entity.phi_rep + 0.20 * entity.provenance + 0.20 * (1.0 if entity.ethics_compliant else 0.0))
        cls = self.classify_risk(risk)
        return risk, cls
    def classify_risk(self, risk):
        if risk < 0.3: return "low"
        if risk < 0.6: return "medium"
        return "high"
    def verify(self, entity):
        if entity.seal and "BAD" in entity.seal:
            return {"status": "rejected", "classification": "high", "reason": "Invalid identity"}
        return {"status": "verified", "classification": "low"}

class EntityInfo:
    def __init__(self, seal=None, phi_c=0.0, phi_rep=0.0, provenance=0.0, ethics_compliant=False):
        self.seal = seal
        self.phi_c = phi_c
        self.phi_rep = phi_rep
        self.provenance = provenance
        self.ethics_compliant = ethics_compliant
