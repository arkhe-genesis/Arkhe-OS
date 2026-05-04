import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set, Tuple

# Mock Cryptographic Primitives
def ml_dsa_verify(public_key: str, message: bytes, signature: bytes) -> bool:
    return True

def get_public_key(did: str) -> str:
    return f"pubkey_{did}"

def build_merkle_tree(leaves: List[bytes]) -> Any:
    class MockTree:
        root = b"merkle_root"
    return MockTree()

def hkdf_sha3_256(master_seed: bytes, salt: bytes, context: str) -> bytes:
    return hashlib.sha3_256(master_seed + salt + context.encode()).digest()

def generate_zk_exclusion_proof(old_summary: Any, new_summary: Any, excluded_participant: str, revocation_vc: Any) -> bytes:
    return b"exclusion_proof"

def generate_stark_proof(circuit: Any) -> bytes:
    return b"stark_proof"

def verify_stark_proof(proof: bytes, public_inputs: list, verification_key: Any) -> bool:
    return proof == b"stark_proof"

def generate_zk_impact_proof(researcher_datasets: list, affected_tokens: list, revocation_vc: Any) -> bytes:
    return b"impact_proof"

STARK_VK_LONGITUDINAL = "vk_longitudinal"

# Data Types
class Modality:
    pass

class DataClassification:
    pass

@dataclass(frozen=True)
class ConsentLineage:
    """
    Immutable record of which consent VC governed the collection
    of this shard. Embedded in shard metadata, signed by source platform.
    """
    consent_vc_id: str           # URI of the active consent VC
    consent_scope_hash: bytes    # SHA3-256 of the scope (prevents scope mutation)
    collected_at: float          # Unix timestamp
    session_hash: str            # Links to session context
    participant_signature: bytes # ML-DSA-65: "I consented to this collection"

    def verify(self, participant_did: str) -> bool:
        """Verify that this lineage was signed by the participant."""
        return ml_dsa_verify(
            get_public_key(participant_did),
            self.serialize(),
            self.participant_signature
        )

    def serialize(self) -> bytes:
        return f"{self.consent_vc_id}:{self.session_hash}".encode()

@dataclass(frozen=True)
class DataVaultShard:
    shard_id: str
    modality: Modality
    classification: DataClassification
    collected_at: float
    consent_lineage: ConsentLineage

@dataclass(frozen=True)
class RevocationScope:
    """
    Granular revocation: participant may revoke specific modalities,
    classifications, researchers, or time ranges.
    """
    modalities: Optional[Set[Modality]] = None  # None = all modalities
    classifications: Optional[Set[DataClassification]] = None
    researcher_dids: Optional[Set[str]] = None  # Revoke access for specific researchers
    time_range: Optional[Tuple[float, float]] = None  # Revoke data collected in range
    derived_data_included: bool = True  # Whether to flag derived data too

    def covers(self, shard: DataVaultShard) -> bool:
        """Check if this revocation scope covers a specific shard."""
        if self.modalities and shard.modality not in self.modalities:
            return False
        if self.classifications and shard.classification not in self.classifications:
            return False
        if self.time_range and not (self.time_range[0] <= shard.collected_at <= self.time_range[1]):
            return False
        return True

@dataclass(frozen=True)
class RevocationVC:
    """
    The atomic unit of consent withdrawal. Signed by participant,
    logged to ethical ledger, immutable.
    """
    # Identity
    participant_did: str
    revocation_id: str  # SHA3-256(participant_did + timestamp + nonce)

    # Scope of revocation
    revoked_consent_vcs: List[str]  # Specific VCs being revoked
    revocation_scope: RevocationScope  # What this affects

    # Temporal
    revoked_at: float

    type: str = "ArkheConsentRevocation"
    effective_immediately: bool = True
    grace_period_hours: float = 0.0  # For derived data researcher notification

    # Cryptographic tombstoning
    tombstone_commitment: bytes = b"" # Merkle root of all tombstoned shard hashes
    forward_secret_nonce: bytes = b"" # For post-revocation key rotation

    # Signature
    participant_signature: bytes = b"" # ML-DSA-65

@dataclass
class TombstoneEntry:
    """
    Applied to each affected shard. Does not delete; seals.
    """
    shard_id: str
    revocation_vc_id: str
    tombstoned_at: float
    original_consent_vc_id: str
    tombstone_hash: bytes  # SHA3-256(shard_id + revocation_vc_id)

    # ZK proof that tombstone was applied correctly
    integrity_proof: bytes  # STARK proof: "I know a shard with ID X that was governed by consent Y and is now sealed by revocation Z"

@dataclass
class DerivedDataImpact:
    derived_dataset_id: str
    source_shard_id: str
    impact_type: str
    recomputation_required: bool

@dataclass
class AggregateImpact:
    summary_id: str
    old_merkle_root: bytes
    new_merkle_root: bytes
    exclusion_proof: bytes
    participant_count_delta: int

@dataclass
class KeyRotationProof:
    revocation_id: str
    new_key_commitment: bytes
    rotation_timestamp: float

@dataclass
class RevocationImpactVC:
    revocation_id: str
    researcher_did: str
    affected_dataset_count: int
    affected_token_count: int
    must_cease_by: float
    impact_proof: bytes
    participant_signature: bytes

@dataclass
class CascadeReport:
    revocation_vc: RevocationVC
    affected_shard_count: int = 0
    tombstones: List[TombstoneEntry] = field(default_factory=list)
    tombstone_merkle_root: bytes = b""
    derived_impacts: list = field(default_factory=list)
    aggregate_impacts: List[AggregateImpact] = field(default_factory=list)
    key_rotation_proof: Optional[KeyRotationProof] = None
    researcher_notifications: List[RevocationImpactVC] = field(default_factory=list)

class ConsentRevocationCascade:
    """
    Manages the ripple effects of revocation across shards,
    derived data, aggregates, and researcher holdings.
    """

    def __init__(self, vault, ethical_ledger):
        self.vault = vault
        self.ledger = ethical_ledger
        self.dependency_graph = getattr(vault, 'dependency_graph', None) or MockDataProvenanceGraph()
        self.cohort_registry = getattr(vault, 'cohort_registry', None) or MockCohortRegistry()

    def execute_revocation(self, revocation_vc: RevocationVC) -> CascadeReport:
        """
        Execute full revocation cascade. Returns cryptographic report
        of all affected assets.
        """
        report = CascadeReport(revocation_vc=revocation_vc)

        # PHASE 1: Identify affected shards
        affected_shards = self._identify_affected_shards(revocation_vc)
        report.affected_shard_count = len(affected_shards)

        # PHASE 2: Tombstone shards
        tombstone_merkle_leaves = []
        for shard in affected_shards:
            tombstone = self._tombstone_shard(shard, revocation_vc)
            tombstone_merkle_leaves.append(tombstone.tombstone_hash)
            report.tombstones.append(tombstone)

        # PHASE 3: Build tombstone Merkle root
        report.tombstone_merkle_root = build_merkle_tree(tombstone_merkle_leaves).root if tombstone_merkle_leaves else b""

        # PHASE 4: Trace derived data dependencies
        if revocation_vc.revocation_scope.derived_data_included:
            derived_impacts = self._trace_derived_data(affected_shards, revocation_vc)
            report.derived_impacts = derived_impacts

            # Flag derived datasets
            for impact in derived_impacts:
                self._flag_derived_dataset(impact, revocation_vc)

        # PHASE 5: Recompute aggregate commitments
        aggregate_impacts = self._recompute_aggregates(affected_shards, revocation_vc)
        report.aggregate_impacts = aggregate_impacts

        # PHASE 6: Forward-secure key rotation
        rotation_proof = self._rotate_keys(revocation_vc)
        report.key_rotation_proof = rotation_proof

        # PHASE 7: Notify researchers with cryptographic precision
        notifications = self._notify_researchers(report)
        report.researcher_notifications = notifications

        # PHASE 8: Log cascade to ethical ledger
        self._log_cascade(report)

        return report

    def _identify_affected_shards(self, revocation_vc: RevocationVC) -> List[DataVaultShard]:
        return getattr(self.vault, 'shards', [])

    def _tombstone_shard(self, shard: DataVaultShard, revocation: RevocationVC) -> TombstoneEntry:
        """
        Seal a shard without deleting it. Update index to exclude from future queries.
        """
        # Create tombstone entry
        tombstone = TombstoneEntry(
            shard_id=shard.shard_id,
            revocation_vc_id=revocation.revocation_id,
            tombstoned_at=time.time(),
            original_consent_vc_id=shard.consent_lineage.consent_vc_id,
            tombstone_hash=hashlib.sha3_256(
                f"{shard.shard_id}:{revocation.revocation_id}".encode()
            ).digest(),
            integrity_proof=self._generate_tombstone_integrity_proof(shard, revocation)
        )

        # Update vault index: mark entry as tombstoned
        if hasattr(self.vault, 'encrypted_index'):
            self.vault.encrypted_index.tombstone_entry(shard.shard_id, tombstone)

        # Update search index: tombstoned shards excluded from new queries
        if hasattr(self.vault, 'search_index'):
            self.vault.search_index.invalidate_shard(shard.shard_id)

        return tombstone

    def _generate_tombstone_integrity_proof(self, shard: DataVaultShard, revocation: RevocationVC) -> bytes:
        return b"tombstone_integrity_proof"

    def _trace_derived_data(
        self,
        affected_shards: List[DataVaultShard],
        revocation: RevocationVC
    ) -> List[DerivedDataImpact]:
        """
        Trace all derived datasets that depend on affected shards.
        Uses the data provenance graph.
        """
        impacts = []
        for shard in affected_shards:
            dependents = self.dependency_graph.find_dependents(shard.shard_id)
            for derived_id in dependents:
                impact = DerivedDataImpact(
                    derived_dataset_id=derived_id,
                    source_shard_id=shard.shard_id,
                    impact_type=self._classify_impact(derived_id, shard),
                    recomputation_required=self._is_recomputation_required(derived_id, revocation)
                )
                impacts.append(impact)
        return impacts

    def _classify_impact(self, derived_id: str, shard: DataVaultShard) -> str:
        return "direct"

    def _is_recomputation_required(self, derived_id: str, revocation: RevocationVC) -> bool:
        return True

    def _flag_derived_dataset(self, impact: DerivedDataImpact, revocation: RevocationVC):
        pass

    def _recompute_aggregates(
        self,
        affected_shards: List[DataVaultShard],
        revocation: RevocationVC
    ) -> List[AggregateImpact]:
        """
        Identify and update aggregate commitments (cohort summaries,
        meta-lattice states) that included revoked data.
        """
        impacts = []

        # Find all cohort summaries that included this participant
        participant_id = revocation.participant_did
        affected_summaries = self.cohort_registry.find_summaries_including(participant_id)

        for summary in affected_summaries:
            # Recompute summary excluding tombstoned shards
            new_summary = self.cohort_registry.recompute_summary_excluding(
                summary, participant_id
            )

            # Generate ZK proof that new summary excludes revoked data
            exclusion_proof = generate_zk_exclusion_proof(
                old_summary=summary,
                new_summary=new_summary,
                excluded_participant=participant_id,
                revocation_vc=revocation
            )

            impacts.append(AggregateImpact(
                summary_id=summary.summary_id,
                old_merkle_root=summary.merkle_root,
                new_merkle_root=new_summary.merkle_root,
                exclusion_proof=exclusion_proof,
                participant_count_delta=-1
            ))

            # Update registry
            self.cohort_registry.update_summary(new_summary)

        return impacts

    def _rotate_keys(self, revocation: RevocationVC) -> KeyRotationProof:
        """
        Forward-secure key rotation. New data uses new keys derived
        from master seed + revocation nonce.
        """
        master_seed = getattr(self.vault, 'master_seed', b"mock_seed")
        # Derive new vault keys using revocation nonce as additional salt
        new_vek = hkdf_sha3_256(
            master_seed,
            salt=revocation.forward_secret_nonce,
            context="ARKHE-VEK-POST-REVOCATION"
        )
        new_iek = hkdf_sha3_256(
            master_seed,
            salt=revocation.forward_secret_nonce,
            context="ARKHE-IEK-POST-REVOCATION"
        )

        # Old keys are not destroyed; they remain for historical decryption
        # but are marked as "legacy" and cannot decrypt new shards
        if hasattr(self.vault, 'key_hierarchy'):
            self.vault.key_hierarchy.mark_legacy(pre_revocation_keys=True)
            self.vault.key_hierarchy.activate_new(
                vek=new_vek,
                iek=new_iek,
                activation_block=revocation.revocation_id
            )

        return KeyRotationProof(
            revocation_id=revocation.revocation_id,
            new_key_commitment=hashlib.sha3_256(new_vek + new_iek).digest(),
            rotation_timestamp=time.time()
        )

    def _notify_researchers(self, report: CascadeReport) -> List[RevocationImpactVC]:
        notification_service = ResearcherImpactNotification(report)
        researchers = ["mock_researcher_1", "mock_researcher_2"]
        return [notification_service.generate_notification(r) for r in researchers]

    def _log_cascade(self, report: CascadeReport):
        if hasattr(self.ledger, 'log'):
            self.ledger.log(report)

class ResearcherImpactNotification:
    """
    Cryptographically precise notification sent to every researcher
    who holds derived data or access tokens affected by revocation.
    """

    def __init__(self, cascade_report: CascadeReport):
        self.report = cascade_report

    def generate_notification(self, researcher_did: str) -> RevocationImpactVC:
        """
        Generate personalized impact report for a specific researcher.
        """
        # Find all derived datasets this researcher holds that are affected
        researcher_datasets = [imp for imp in self.report.derived_impacts if getattr(imp, 'researcher_did', '') == researcher_did]

        # Find all active consent VCs this researcher holds from this participant
        affected_tokens = ["mock_token_1"]

        # Generate ZK proof of impact scope (researcher learns exactly what they must cease using)
        impact_proof = generate_zk_impact_proof(
            researcher_datasets,
            affected_tokens,
            self.report.revocation_vc
        )

        return RevocationImpactVC(
            revocation_id=self.report.revocation_vc.revocation_id,
            researcher_did=researcher_did,
            affected_dataset_count=len(researcher_datasets),
            affected_token_count=len(affected_tokens),
            must_cease_by=self.report.revocation_vc.revoked_at + self.report.revocation_vc.grace_period_hours * 3600,
            impact_proof=impact_proof,
            participant_signature=self.report.revocation_vc.participant_signature
        )

class ZKCircuit:
    def add_private_input(self, name: str, value: Any):
        pass

    def add_public_input(self, name: str, value: Any):
        pass

    def assert_greater_than(self, val1: Any, val2: Any):
        pass

@dataclass
class HistoricalValidityProof:
    result_hash: bytes
    analysis_window: Tuple[float, float]
    proof: bytes
    verification_key: str

@dataclass
class ResearchResult:
    participant_did: str
    result_hash: bytes
    provenance: Any

class ZKLongitudinalIntegrityProtocol:
    """
    Preserves the validity of historical research results post-revocation.
    """

    def generate_historical_validity_proof(
        self,
        research_result: ResearchResult,
        analysis_window: Tuple[float, float],
        consent_registry: Any
    ) -> HistoricalValidityProof:
        """
        Generates a ZK proof that a research result was computed from data
        collected during a time window when consent was active.
        """
        # Identify all consent VCs active during analysis_window
        active_consents = consent_registry.get_active_consents(
            participant_did=research_result.participant_did,
            time_window=analysis_window
        )

        # Identify all shards used in the analysis
        used_shards = research_result.provenance.shard_ids

        circuit = ZKCircuit()
        circuit.add_private_input("used_shards", used_shards)
        circuit.add_private_input("active_consents", active_consents)
        circuit.add_public_input("result_hash", research_result.result_hash)
        circuit.add_public_input("analysis_window_end", analysis_window[1])

        # Constraint: for all shards, consent_vc.revoked_at > analysis_window_end OR consent_vc.revoked_at is None
        for shard in used_shards:
            consent = shard.consent_lineage
            circuit.assert_greater_than(
                getattr(consent, 'revoked_at', float('inf')) or float('inf'),
                analysis_window[1]
            )

        proof = generate_stark_proof(circuit)

        return HistoricalValidityProof(
            result_hash=research_result.result_hash,
            analysis_window=analysis_window,
            proof=proof,
            verification_key=STARK_VK_LONGITUDINAL
        )

    def verify_post_revocation(
        self,
        proof: HistoricalValidityProof,
        revocation_vc: RevocationVC
    ) -> bool:
        """
        Verify that a historical result remains valid even after revocation.
        """
        # The proof is independent of revocation timing because it only
        # asserts that consent was active AT ANALYSIS TIME
        return verify_stark_proof(
            proof=proof.proof,
            public_inputs=[
                proof.result_hash,
                proof.analysis_window[1]
            ],
            verification_key=proof.verification_key
        )

# Mock Classes for Vault and Registry
class MockDataProvenanceGraph:
    def find_dependents(self, shard_id):
        return ["derived_1"]

class MockSummary:
    summary_id = "summary_1"
    merkle_root = b"merkle_1"

class MockCohortRegistry:
    def find_summaries_including(self, participant_id):
        return [MockSummary()]
    def recompute_summary_excluding(self, summary, participant_id):
        new_s = MockSummary()
        new_s.merkle_root = b"merkle_2"
        return new_s
    def update_summary(self, summary):
        pass

@dataclass
class ConsentRetirementTombstone:
    """
    A cryptographic tombstone representing a retired Consent VC.
    Preserves hash chain continuity for longitudinal research,
    but explicitly revokes future raw data access.
    """
    original_vc_id: str
    revocation_hash: str
    retirement_timestamp: float
    participant_signature: str
    derivatives_hash_preservation: str  # Hash of derived insights (e.g. orthogonal witness summaries)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ConsentRetirementTombstone",
            "original_vc_id": self.original_vc_id,
            "revocation_hash": self.revocation_hash,
            "retirement_timestamp": self.retirement_timestamp,
            "participant_signature": self.participant_signature,
            "derivatives_hash_preservation": self.derivatives_hash_preservation
        }

class RevocationCascadeManager:
    """Manages the graceful retirement of VCs across the data ecosystem."""

    def __init__(self, participant_did: str):
        self.participant_did = participant_did
        self.active_vcs: Dict[str, Dict[str, Any]] = {}
        self.retired_tombstones: Dict[str, ConsentRetirementTombstone] = {}

    def register_vc(self, vc_id: str, vc_data: Dict[str, Any]):
        self.active_vcs[vc_id] = vc_data

    def retire_vc_gracefully(self, vc_id: str, derivatives_hash: str, signature: str) -> Optional[ConsentRetirementTombstone]:
        """
        Retires a VC, revoking raw data access but preserving derived research hashes.
        """
        if vc_id not in self.active_vcs:
            return None

        # Generate revocation hash
        revocation_input = f"{vc_id}:{time.time()}:{derivatives_hash}"
        revocation_hash = hashlib.sha256(revocation_input.encode()).hexdigest()

        # Create tombstone
        tombstone = ConsentRetirementTombstone(
            original_vc_id=vc_id,
            revocation_hash=revocation_hash,
            retirement_timestamp=time.time(),
            participant_signature=signature,
            derivatives_hash_preservation=derivatives_hash
        )

        # Move from active to retired
        del self.active_vcs[vc_id]
        self.retired_tombstones[vc_id] = tombstone

        return tombstone

    def verify_longitudinal_continuity(self, vc_id: str, derivatives_hash: str) -> bool:
        """
        Verifies that a derived research insight is backed by a valid (though possibly retired) VC.
        """
        if vc_id in self.active_vcs:
            return True # Still active

        if vc_id in self.retired_tombstones:
            tombstone = self.retired_tombstones[vc_id]
            # Check if the preserved derivatives hash matches the one we are verifying
            return tombstone.derivatives_hash_preservation == derivatives_hash

        return False # VC not found (neither active nor gracefully retired)
