from dataclasses import dataclass
from typing import List, Dict, Any
import numpy as np

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
