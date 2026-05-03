from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import time

# Mock external dependencies and crypto primitives
class TrialSafetyState:
    NOMINAL = "NOMINAL"
    HALTED = "HALTED"

@dataclass
class TrialHaltVC:
    trial_did: str
    reason: str
    timestamp: float
    affected_sites: List[str]
    signature: bytes = b""

def trial_sponsor_sign(vc: Any) -> bytes:
    return b"sponsor_signature"

def broadcast_trial_halt(vc: Any):
    pass

def load_trial_protocol(trial_did: str) -> Any:
    class MockProtocol:
        safety_boundaries = {
            "max_sites_with_epsilon_breach": 2,
            "max_sites_with_sae": 2
        }
        @dataclass
        class Intervention:
            targetPhase: float = np.pi
            currentRangeMa: List[float] = field(default_factory=lambda: [0.5, 1.5])
        intervention = Intervention()
    return MockProtocol()

def verify_zk_site_integrity(proof: bytes) -> bool:
    return True

def aggregate_zk_proofs(proofs: List[bytes]) -> bytes:
    return b"aggregated_proof"

def verify_aggregated_proof(proof: bytes, public_inputs: Dict[str, Any]) -> Any:
    class MockResult:
        effect_size = 0.5
        effect_size_commitment = b"es_commit"
    return MockResult()

def normalize_angle(angle: float) -> float:
    return angle % (2 * np.pi)

def generate_zk_delivery_proof(delivered_phase: float, target_window: Tuple[float, float], current: float, max_allowed: float) -> bytes:
    return b"delivery_proof"

class PrivacyPreservingHistogram:
    def mean(self) -> float:
        return np.pi

class DPTrajectoryCommitment:
    pass

class TDCSFidelityProof:
    pass

class NFFidelityProof:
    pass

class UnauthorizedSiteError(Exception):
    pass

class SiteIntegrityViolation(Exception):
    pass

@dataclass
class ProtocolAdherenceProof:
    proof: bytes = b""

@dataclass
class SafetySummary:
    """
    Aggregate safety metrics with ZK proofs.
    """
    total_adverse_events: int                      # Count only, no details
    serious_adverse_events: int
    epsilon_violations: int                        # How many times ε < 0.04
    pdi_ceiling_proximity_events: int              # How many times PDI > 0.95
    intervention_aborts: int                       # Safety enclave aborts
    mercy_gap_mean: float                          # DP mean epsilon
    mercy_gap_min: float                           # Public minimum (safety-critical)

    # ZK proof that these aggregates were computed from real participant data
    # without revealing individual events
    correctness_proof: bytes = b""

@dataclass
class SiteLatticeCommitment:
    """
    Privacy-preserving commitment from a clinical site to the trial.
    Contains only aggregates and ZK proofs—no individual data.
    """

    # Identity
    site_did: str
    trial_did: str
    commitment_timestamp: float

    # Enrollment (public)
    target_enrollment: int
    current_enrollment: int
    active_participants: int
    completed_sessions: int

    # Safety aggregates (ZK-proven)
    safety_summary: SafetySummary
    protocol_adherence: ProtocolAdherenceProof

    # Phase geometry (differentially private)
    theta_distribution: PrivacyPreservingHistogram  # DP histogram of theta phases
    pdi_trajectory: DPTrajectoryCommitment         # Commitment to mean PDI over time
    epsilon_bounds: Tuple[float, float]            # Min/max epsilon across site

    # Intervention fidelity
    tdcs_delivery_log: TDCSFidelityProof           # ZK proof that tDCS was delivered within protocol bounds
    neurofeedback_render_log: NFFidelityProof      # ZK proof that NF was rendered correctly

    # Cross-site synchronization
    site_clock_offset_ms: float                    # Relative to trial reference clock
    last_sync_timestamp: float

    # Cryptographic integrity
    merkle_root: bytes                             # Merkle root of all local face hashes
    zk_integrity: bytes                            # STARK proof that aggregates were computed correctly

    interim_data_commitment: bytes = b""

    def generate_local_efficacy_proof(self) -> bytes:
        return b"local_efficacy_proof"

class CrossSiteSafetyMonitor:
    """
    Monitors safety across all trial sites in real-time.
    Uses ZK range proofs to detect safety violations without unblinding.
    """

    def __init__(self, trial_did: str, ledger: Any = None):
        self.trial_did = trial_did
        self.site_commitments: Dict[str, SiteLatticeCommitment] = {}
        self.safety_state = TrialSafetyState.NOMINAL
        self.ledger = ledger

    def _verify_site_authorization(self, site_did: str, trial_did: str) -> bool:
        return True

    def _trigger_site_alert(self, site_did: str, reason: str):
        pass

    def ingest_site_commitment(self, commitment: SiteLatticeCommitment):
        """
        Process periodic safety commitment from a site.
        """
        # Verify site is authorized for this trial
        if not self._verify_site_authorization(commitment.site_did, self.trial_did):
            raise UnauthorizedSiteError()

        # Verify ZK integrity proof
        if not verify_zk_site_integrity(commitment.zk_integrity):
            raise SiteIntegrityViolation(commitment.site_did)

        # Verify safety bounds
        if commitment.safety_summary.mercy_gap_min < 0.04:
            self._trigger_site_alert(commitment.site_did, "MERCY_GAP_FLOOR_BREACH")

        if commitment.safety_summary.serious_adverse_events > 0:
            self._trigger_site_alert(commitment.site_did, "SERIOUS_ADVERSE_EVENT")

        # Update global safety state
        self.site_commitments[commitment.site_did] = commitment
        self._reevaluate_trial_safety()

    def _reevaluate_trial_safety(self):
        """
        Evaluate trial-level safety based on aggregate site data.
        """
        # Count sites in various safety states
        sites_below_floor = sum(
            1 for c in self.site_commitments.values()
            if c.safety_summary.mercy_gap_min < 0.04
        )
        sites_with_sae = sum(
            1 for c in self.site_commitments.values()
            if c.safety_summary.serious_adverse_events > 0
        )

        # Trial halt conditions (protocol-defined)
        trial_protocol = load_trial_protocol(self.trial_did)

        if sites_below_floor >= trial_protocol.safety_boundaries.get("max_sites_with_epsilon_breach", 2):
            self._issue_trial_halt("MULTI_SITE_MERCY_GAP_COLLAPSE")

        if sites_with_sae >= trial_protocol.safety_boundaries.get("max_sites_with_sae", 2):
            self._issue_trial_halt("MULTI_SITE_SERIOUS_ADVERSE_EVENTS")

    def _issue_trial_halt(self, reason: str):
        """
        Issue trial-wide halt. All sites stop enrollment and intervention.
        """
        halt_vc = TrialHaltVC(
            trial_did=self.trial_did,
            reason=reason,
            timestamp=time.time(),
            affected_sites=list(self.site_commitments.keys())
        )

        # Sign with trial sponsor key
        halt_vc.signature = trial_sponsor_sign(halt_vc)

        # Broadcast to all sites via qhttp://
        broadcast_trial_halt(halt_vc)

        # Log to ethical ledger
        if self.ledger:
            self.ledger.log(halt_vc)

        self.safety_state = TrialSafetyState.HALTED

@dataclass
class AnalysisPlan:
    expected_effect_size: float = 0.5
    current_enrollment: int = 100
    efficacy_boundary: float = 0.8
    futility_boundary: float = 0.2

@dataclass
class InterimAnalysisResult:
    recommendation: str
    effect_size_commitment: bytes
    proof: bytes
    sites_contributed: int
    timestamp: float

class ZKCircuit:
    def add_private_input(self, name: str, value: Any):
        pass
    def add_public_input(self, name: str, value: Any):
        pass

class ZKInterimAnalysis:
    """
    Enables trial monitoring committees to assess efficacy and futility
    without unblinding treatment allocation or exposing individual data.
    """

    def __init__(self, trial_did: str, analysis_plan: AnalysisPlan):
        self.trial_did = trial_did
        self.plan = analysis_plan

    def compile_efficacy_circuit(self, endpoint: str) -> ZKCircuit:
        """
        Compile the primary endpoint analysis into a ZK circuit.
        """
        circuit = ZKCircuit()

        circuit.add_private_input("site_outcomes", "encrypted_outcome_vectors")
        circuit.add_private_input("treatment_assignments", "encrypted_group_labels")
        circuit.add_public_input("trial_did", self.trial_did)
        circuit.add_public_input("expected_effect_size", self.plan.expected_effect_size)
        circuit.add_public_input("current_n", self.plan.current_enrollment)

        return circuit

    def execute_interim_analysis(
        self,
        site_commitments: List[SiteLatticeCommitment]
    ) -> InterimAnalysisResult:
        """
        Execute interim analysis across all sites.
        """
        # Collect encrypted outcome vectors from sites
        encrypted_outcomes = []
        for site in site_commitments:
            encrypted_outcomes.append(site.interim_data_commitment)

        # Each site generates a ZK proof of their local computation
        site_proofs = []
        for site in site_commitments:
            local_proof = site.generate_local_efficacy_proof()
            site_proofs.append(local_proof)

        # Aggregate proofs (this is the key: we aggregate proofs, not data)
        aggregated_proof = aggregate_zk_proofs(site_proofs)

        # Verify aggregated proof
        result = verify_aggregated_proof(
            aggregated_proof,
            public_inputs={
                "trial_did": self.trial_did,
                "expected_effect_size": self.plan.expected_effect_size
            }
        )

        # Determine recommendation
        if result.effect_size > self.plan.efficacy_boundary:
            recommendation = "STOP_FOR_EFFICACY"
        elif result.effect_size < self.plan.futility_boundary:
            recommendation = "STOP_FOR_FUTILITY"
        else:
            recommendation = "CONTINUE"

        return InterimAnalysisResult(
            recommendation=recommendation,
            effect_size_commitment=result.effect_size_commitment,  # Commitment, not raw value
            proof=aggregated_proof,
            sites_contributed=len(site_commitments),
            timestamp=time.time()
        )

@dataclass
class SiteInterventionTarget:
    site_did: str
    target_phase: float
    delivery_window: Tuple[float, float]
    coherence: float
    max_current_ma: float

@dataclass
class DeliveryFidelityProof:
    site_did: str
    target_phase: float
    delivered_phase_commitment: bytes
    within_window: bool
    proof: bytes

class CrossSitePhaseAlignment:
    """
    Synchronizes intervention delivery across sites using
    site-level PASV-like state vectors.
    """

    def __init__(self, trial_did: str):
        self.trial_did = trial_did
        self.site_phase_states = {}

    def _compute_cross_site_coherence(self, site_did: str) -> float:
        return 0.8

    def compute_site_target(
        self,
        site_commitment: SiteLatticeCommitment,
        trial_protocol: Any
    ) -> SiteInterventionTarget:
        """
        Each site computes its local intervention target based on:
        1. Trial protocol specification (global target phase)
        2. Site's aggregate theta distribution (local offset)
        3. Cross-site phase coherence (synchronization factor)
        """
        # Global target from protocol
        global_target_phase = trial_protocol.intervention.targetPhase  # e.g., "theta_trough" = π

        # Site's mean theta phase (from DP histogram)
        site_mean_theta = site_commitment.theta_distribution.mean()

        # Cross-site coherence: how well is this site synchronized with others?
        coherence = self._compute_cross_site_coherence(site_commitment.site_did)

        # Target is weighted blend: more coherent sites follow global target more closely
        # less coherent sites adjust toward local mean to avoid forcing
        target_phase = normalize_angle(
            coherence * global_target_phase +
            (1 - coherence) * site_mean_theta
        )

        # Delivery window: site must deliver within ±15° of target
        delivery_window = (target_phase - 0.26, target_phase + 0.26)  # ~15 degrees in radians

        return SiteInterventionTarget(
            site_did=site_commitment.site_did,
            target_phase=target_phase,
            delivery_window=delivery_window,
            coherence=coherence,
            max_current_ma=trial_protocol.intervention.currentRangeMa[1]
        )

    def verify_delivery_fidelity(
        self,
        site_did: str,
        delivered_phase: float,
        target: SiteInterventionTarget
    ) -> DeliveryFidelityProof:
        """
        Site proves it delivered intervention within protocol bounds.
        """
        within_window = target.delivery_window[0] <= delivered_phase <= target.delivery_window[1]
        current_within_bounds = target.max_current_ma <= 1.5  # Protocol max

        import hashlib
        # ZK proof: "I delivered at phase P within window W using current C within bounds B"
        proof = generate_zk_delivery_proof(
            delivered_phase=delivered_phase,
            target_window=target.delivery_window,
            current=target.max_current_ma,
            max_allowed=1.5
        )

        return DeliveryFidelityProof(
            site_did=site_did,
            target_phase=target.target_phase,
            delivered_phase_commitment=hashlib.sha3_256(str(delivered_phase).encode()).digest(),
            within_window=within_window,
            proof=proof
        )

# Keep old classes to ensure backward compatibility for old tests
@dataclass
class OrthogonalWitnessSummary:
    """
    Zero-knowledge summary of intervention efficacy and orthogonal witness state
    for cross-cohort research without raw data pooling.
    """
    cohort_id: str
    aggregated_pdi_trajectory: List[float]  # Anonymized/averaged PDI over time
    average_k_target: float
    mercy_gap_compliance_rate: float  # Percentage of time epsilon remained in [0.04, 0.10]
    zk_proof_of_aggregation: bytes  # Proof that the summary accurately reflects the cohort's verifiable credentials

class MultiSiteTrialCoordinator:
    """
    Coordinates distributed lattices across multiple sites/enclaves.
    Maintains global PDI consensus and epsilon variance tracking without data pooling.
    """

    def __init__(self, trial_id: str):
        self.trial_id = trial_id
        self.site_summaries: Dict[str, OrthogonalWitnessSummary] = {}
        self.global_pdi_consensus: float = 1.0
        self.global_epsilon_variance: float = 0.0

    def submit_site_summary(self, site_id: str, summary: OrthogonalWitnessSummary) -> bool:
        """
        Receives and verifies an Orthogonal Witness Summary from a distributed site.
        """
        # Mock ZK proof verification
        if not self._verify_zk_aggregation(summary.zk_proof_of_aggregation):
            return False

        self.site_summaries[site_id] = summary
        self._recompute_global_metrics()
        return True

    def _verify_zk_aggregation(self, proof: bytes) -> bool:
        # Mock implementation of ZK proof verification
        return proof.startswith(b"zk_proof")

    def _recompute_global_metrics(self):
        """
        Aggregates the PDI and epsilon compliance across all sites
        to inform the global lattice state.
        """
        if not self.site_summaries:
            self.global_pdi_consensus = 1.0
            self.global_epsilon_variance = 0.0
            return

        total_sites = len(self.site_summaries)

        # Average the latest PDI from each site's trajectory
        sum_pdi = 0.0
        sum_compliance = 0.0

        for summary in self.site_summaries.values():
            if summary.aggregated_pdi_trajectory:
                sum_pdi += summary.aggregated_pdi_trajectory[-1]
            sum_compliance += summary.mercy_gap_compliance_rate

        self.global_pdi_consensus = sum_pdi / total_sites
        # Map compliance rate inversely to epsilon variance (simplified model)
        average_compliance = sum_compliance / total_sites
        self.global_epsilon_variance = 0.10 * (1.0 - average_compliance) # Rough mock

    def get_global_trial_state(self) -> Dict[str, Any]:
        """Returns the synchronized state of the multi-site trial."""
        return {
            "trial_id": self.trial_id,
            "participating_sites": list(self.site_summaries.keys()),
            "global_pdi_consensus": self.global_pdi_consensus,
            "global_epsilon_variance": self.global_epsilon_variance
        }
