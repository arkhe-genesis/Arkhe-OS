from enum import Enum

class ProofType(Enum):
    COHERENCE_CERTIFICATION = 1
    GEOMETRY_MONITORING = 2
    COHERENCE_TRACKING = 3
    REGIME_TRANSITION = 4

class ProofMetadata:
    def __init__(self, proof_type, priority):
        self.proof_type = proof_type
        self.priority = priority

class ProofTagger:
    def __init__(self, monitoring_threshold, certification_threshold, transition_sensitivity):
        self.monitoring_threshold = monitoring_threshold
        self.certification_threshold = certification_threshold
        self.transition_sensitivity = transition_sensitivity
        self.previous_state = None

    def classify_proof(self, capture_fraction, cohesion_rho, manifold_dim, epoch):
        if self.previous_state and abs(capture_fraction - self.previous_state.get('capture_fraction', 0)) > self.transition_sensitivity:
            return ProofMetadata(ProofType.REGIME_TRANSITION, 'high')

        if capture_fraction >= self.certification_threshold:
            return ProofMetadata(ProofType.COHERENCE_CERTIFICATION, 'high')
        elif capture_fraction >= self.monitoring_threshold:
            return ProofMetadata(ProofType.GEOMETRY_MONITORING, 'medium')
        else:
            return ProofMetadata(ProofType.COHERENCE_TRACKING, 'low')
