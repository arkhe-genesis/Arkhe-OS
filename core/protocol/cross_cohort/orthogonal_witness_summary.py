from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import hashlib

# Mock classes for encrypted statistics
class EncryptedHistogram:
    pass

class EncryptedPhaseStats:
    pass

# Helper mock functions
def verify_participant_consents(participant_consent_vcs: List[str], analysis_spec: dict) -> bool:
    return True

def cohort_compute_orthogonal_summary(cohort_did: str, analysis_spec: dict, privacy_budget: float) -> 'OrthogonalWitnessSummary':
    return OrthogonalWitnessSummary(
        cohort_did=cohort_did,
        analysis_id=analysis_spec.get("id", "default_analysis"),
        participant_count=100,
        pdi_distribution=EncryptedHistogram(),
        epsilon_bounds=(0.04, 0.10),
        phase_coherence_metrics=EncryptedPhaseStats(),
        differential_privacy_epsilon=privacy_budget,
        zk_proof_of_correctness="mock_zk_proof",
        summary_hash="mock_hash",
        prev_summary_hash="mock_prev_hash"
    )

def verify_zk_proof_of_correctness(zk_proof: str) -> bool:
    return zk_proof == "mock_zk_proof"

def weighted_combine_histograms(histograms: List[EncryptedHistogram], weights: List[int]) -> EncryptedHistogram:
    return EncryptedHistogram()

def compute_combined_epsilon_bounds(bounds: List[Tuple[float, float]], weights: List[int]) -> Tuple[float, float]:
    # Mock aggregation preserving bounds
    return (0.04, 0.10)

def compute_phase_offset(phase_stats: EncryptedPhaseStats, reference_phase: float) -> float:
    return 0.0

def align_phase_statistics(summary: 'OrthogonalWitnessSummary', phase_offset: float) -> 'OrthogonalWitnessSummary':
    return summary

def combine_aligned_summaries(summaries: List['OrthogonalWitnessSummary']) -> 'PhaseAlignedMetaResult':
    return PhaseAlignedMetaResult()

@dataclass
class PhaseAlignedMetaResult:
    """Mock result of phase-aligned aggregation."""
    pass

@dataclass
class MetaAnalysisResult:
    """Combined meta-analysis result across cohorts."""
    pdi_distribution: EncryptedHistogram
    epsilon_bounds: Tuple[float, float]
    cohort_count: int
    total_participants: int
    privacy_budget_used: float

@dataclass
class OrthogonalWitnessSummary:
    """A privacy-preserving aggregate summary from a research cohort."""

    # Cohort identity
    cohort_did: str  # DID of the cohort (derived from participant root hashes)
    analysis_id: str  # Unique identifier for the analysis
    participant_count: int  # Number of participants (public)

    # Aggregate statistics (encrypted or ZK-proven)
    pdi_distribution: EncryptedHistogram  # Histogram of PDI values, encrypted or ZK-proven
    epsilon_bounds: Tuple[float, float]  # Global mercy gap bounds (must be [0.04, 0.10])
    phase_coherence_metrics: EncryptedPhaseStats  # Encrypted phase coherence statistics

    # Privacy guarantees
    differential_privacy_epsilon: float  # DP parameter for aggregate statistics
    zk_proof_of_correctness: str  # ZK proof that aggregates were computed correctly

    # Integrity
    summary_hash: str
    prev_summary_hash: str  # For hash chain across analysis iterations

    def verify_mercy_gap(self) -> bool:
        """Verifies that the summary preserves the global mercy gap."""
        return 0.04 <= self.epsilon_bounds[0] <= self.epsilon_bounds[1] <= 0.10

class CrossCohortAggregator:
    def __init__(self, analysis_spec: dict, privacy_budget: float):
        self.analysis_spec = analysis_spec  # e.g., {"metric": "PDI_mean", "group_by": "age_group"}
        self.privacy_budget = privacy_budget  # Total DP epsilon for the analysis

    def request_summary(self, cohort_did: str, participant_consent_vcs: List[str]) -> OrthogonalWitnessSummary:
        """
        Requests an orthogonal witness summary from a cohort.
        participant_consent_vcs: List of VCs proving participants consented to this analysis.
        """
        # Verify participant consent via VCs
        if not verify_participant_consents(participant_consent_vcs, self.analysis_spec):
            raise PermissionError("Insufficient participant consent")

        # Cohort computes aggregate statistics locally using MPC or homomorphic encryption
        summary = cohort_compute_orthogonal_summary(
            cohort_did,
            self.analysis_spec,
            self.privacy_budget / len(participant_consent_vcs) if participant_consent_vcs else self.privacy_budget
        )

        # Verify summary's mercy gap and ZK proof
        if not summary.verify_mercy_gap():
            raise ValueError("Summary does not preserve mercy gap")
        if not verify_zk_proof_of_correctness(summary.zk_proof_of_correctness):
            raise ValueError("Invalid ZK proof of aggregate correctness")

        return summary

    def combine_summaries(self, summaries: List[OrthogonalWitnessSummary]) -> MetaAnalysisResult:
        """
        Combines orthogonal witness summaries from multiple cohorts into a meta-analysis.
        Uses phase-aligned aggregation to preserve orthogonality.
        """
        # Verify all summaries preserve mercy gap
        if not all(s.verify_mercy_gap() for s in summaries):
            raise ValueError("Not all summaries preserve mercy gap")

        # Combine aggregate statistics using weighted average (weights = participant count)
        combined_pdi = weighted_combine_histograms(
            [s.pdi_distribution for s in summaries],
            weights=[s.participant_count for s in summaries]
        )
        combined_epsilon = compute_combined_epsilon_bounds(
            [s.epsilon_bounds for s in summaries],
            weights=[s.participant_count for s in summaries]
        )

        # Verify combined result still preserves mercy gap
        if not (0.04 <= combined_epsilon[0] <= combined_epsilon[1] <= 0.10):
            raise ValueError("Combined result does not preserve mercy gap")

        return MetaAnalysisResult(
            pdi_distribution=combined_pdi,
            epsilon_bounds=combined_epsilon,
            cohort_count=len(summaries),
            total_participants=sum(s.participant_count for s in summaries),
            privacy_budget_used=self.privacy_budget
        )

def phase_aligned_aggregate(cohort_summaries: List[OrthogonalWitnessSummary],
                           reference_phase: float) -> PhaseAlignedMetaResult:
    """
    Aggregates cohort summaries while aligning to a reference phase geometry.
    Preserves orthogonality by normalizing phase differences before aggregation.
    """
    aligned_summaries = []
    for summary in cohort_summaries:
        # Compute phase offset between cohort and reference
        phase_offset = compute_phase_offset(summary.phase_coherence_metrics, reference_phase)
        # Align summary statistics to reference phase
        aligned_summary = align_phase_statistics(summary, phase_offset)
        aligned_summaries.append(aligned_summary)

    # Aggregate aligned summaries
    return combine_aligned_summaries(aligned_summaries)
