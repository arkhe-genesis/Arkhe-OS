from enum import Enum

class ProofType(Enum):
    MONITORING = 1
    CERTIFICATION = 2
    TRANSITION = 3

class ProofMeta:
    def __init__(self, proof_type, priority):
        self.proof_type = proof_type
        self.priority = priority

class ProofTagger:
    def __init__(self, monitoring_threshold, certification_threshold, transition_sensitivity):
        self.monitoring_threshold = monitoring_threshold
        self.certification_threshold = certification_threshold
        self.transition_sensitivity = transition_sensitivity

    def classify_proof(self, capture_fraction, epoch, parameter_change):
        if capture_fraction >= self.certification_threshold:
            return ProofMeta(ProofType.CERTIFICATION, "HIGH")
        return ProofMeta(ProofType.MONITORING, "LOW")
