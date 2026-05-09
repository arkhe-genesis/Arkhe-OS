"""
Substrate 285: Global Redox Coherence Atlas
Constructs a global map of redox coherence by tissue, condition, and demography,
fed by federated institutional data and validated through consensus.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import hashlib
import time

@dataclass
class AtlasEntry:
    tissue: str
    condition: str
    demography: str # e.g., "adult_female", "pediatric"
    phi_c_mean: float
    phi_c_variance: float
    sample_size: int
    last_updated: float
    contributing_institutions: List[str]

class GlobalRedoxCoherenceAtlas:
    """Maintains a globally consensus-validated atlas of redox coherence."""

    def __init__(self):
        # Key format: tissue:condition:demography
        self.atlas: Dict[str, AtlasEntry] = {}
        self.pending_updates: List[Dict] = []
        self.consensus_threshold: int = 3 # Minimum number of institutional attestations required

    def submit_federated_data(
        self,
        institution_id: str,
        tissue: str,
        condition: str,
        demography: str,
        phi_c_mean: float,
        phi_c_variance: float,
        sample_size: int,
        signature: str
    ):
        """Submits localized redox metrics from an institution for atlas inclusion."""
        # In a full implementation, signature validation would happen here
        update = {
            "institution_id": institution_id,
            "tissue": tissue,
            "condition": condition,
            "demography": demography,
            "phi_c_mean": phi_c_mean,
            "phi_c_variance": phi_c_variance,
            "sample_size": sample_size,
            "timestamp": time.time()
        }
        self.pending_updates.append(update)

    def trigger_consensus_round(self):
        """Processes pending updates and integrates them into the atlas if consensus is reached."""
        # Group updates by key
        grouped_updates = {}
        for update in self.pending_updates:
            key = f"{update['tissue']}:{update['condition']}:{update['demography']}"
            if key not in grouped_updates:
                grouped_updates[key] = []
            grouped_updates[key].append(update)

        for key, updates in grouped_updates.items():
            # Check if we have enough distinct institutional attestations
            institutions = set(u["institution_id"] for u in updates)
            if len(institutions) >= self.consensus_threshold:
                self._integrate_updates(key, updates)

        # Clear integrated updates from pending
        integrated_keys = [k for k, v in grouped_updates.items() if len(set(u["institution_id"] for u in v)) >= self.consensus_threshold]
        self.pending_updates = [u for u in self.pending_updates if f"{u['tissue']}:{u['condition']}:{u['demography']}" not in integrated_keys]

    def _integrate_updates(self, key: str, updates: List[Dict]):
        """Mathematically merges validated updates into the atlas entry."""
        total_new_samples = sum(u["sample_size"] for u in updates)

        # Calculate pooled mean and variance for the new updates
        weighted_mean_sum = sum(u["phi_c_mean"] * u["sample_size"] for u in updates)
        new_mean = weighted_mean_sum / total_new_samples

        # Simplified pooled variance
        new_variance = sum(u["phi_c_variance"] * u["sample_size"] for u in updates) / total_new_samples

        institutions = list(set(u["institution_id"] for u in updates))

        if key in self.atlas:
            entry = self.atlas[key]
            # Merge with existing
            total_samples = entry.sample_size + total_new_samples

            merged_mean = (entry.phi_c_mean * entry.sample_size + new_mean * total_new_samples) / total_samples
            merged_variance = (entry.phi_c_variance * entry.sample_size + new_variance * total_new_samples) / total_samples

            entry.phi_c_mean = merged_mean
            entry.phi_c_variance = merged_variance
            entry.sample_size = total_samples
            entry.last_updated = time.time()
            entry.contributing_institutions = list(set(entry.contributing_institutions + institutions))
        else:
            # Create new entry
            tissue, condition, demography = key.split(":")
            self.atlas[key] = AtlasEntry(
                tissue=tissue,
                condition=condition,
                demography=demography,
                phi_c_mean=new_mean,
                phi_c_variance=new_variance,
                sample_size=total_new_samples,
                last_updated=time.time(),
                contributing_institutions=institutions
            )

    def query_atlas(self, tissue: str, condition: str, demography: str) -> Optional[AtlasEntry]:
        """Retrieves consensus redox coherence data for a specific demographic."""
        key = f"{tissue}:{condition}:{demography}"
        return self.atlas.get(key)

    def generate_global_report(self) -> Dict:
        """Generates a summary report of the global atlas state."""
        return {
            "total_entries": len(self.atlas),
            "total_samples_represented": sum(e.sample_size for e in self.atlas.values()),
            "last_updated": max((e.last_updated for e in self.atlas.values()), default=0),
            "entries": [
                {
                    "tissue": e.tissue,
                    "condition": e.condition,
                    "demography": e.demography,
                    "phi_c_mean": e.phi_c_mean,
                    "sample_size": e.sample_size
                }
                for e in self.atlas.values()
            ]
        }
