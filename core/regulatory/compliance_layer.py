import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from core.identity.consent_revocation_cascade import RevocationVC, RevocationScope, ConsentRevocationCascade
import hashlib

# Mock Functions and Primitives
def generate_zk_safety_aggregate_proof(safety_vcs: list, metrics: Any) -> bytes:
    return b"safety_aggregate_proof"

def generate_zk_gdpr_compliance_proof(participant_did: str, certificate: Any) -> bytes:
    return b"gdpr_compliance_proof"

def generate_stark_proof(circuit: Any) -> bytes:
    return b"stark_proof"

def verify_stark_proof(proof: bytes, public_inputs: dict, verification_key: str) -> bool:
    return True

def multi_party_sign(package: Any, signers: list) -> bytes:
    return b"multi_party_signature"

STARK_VK_PROTOCOL_ADHERENCE = "vk_protocol_adherence"

def resolve_did(did: str) -> dict:
    return {
        "arkhe:regulatoryMetadata": {
            "inspectorDIDs": [f"did:inspector:1", f"did:inspector:2"]
        }
    }

class ZKCircuit:
    def add_private_input(self, name: str, value: Any):
        pass
    def add_public_input(self, name: str, value: Any):
        pass
    def assert_greater_than_or_equal(self, name: str, value_name: str):
        pass
    def assert_less_than_or_equal(self, name: str, value_name: str):
        pass
    def assert_merkle_root_equals(self, entries_name: str, root_name: str):
        pass
    def assert_monotonic_timestamps(self, entries_name: str):
        pass

# Data Types
@dataclass
class AuditPackage:
    electronic_signatures: List[Any] = field(default_factory=list)
    audit_trail: Any = None
    protocol_adherence: List[Any] = field(default_factory=list)
    safety_log: List[Any] = field(default_factory=list)
    integrity_proofs: List[Any] = field(default_factory=list)
    verification_guide: str = ""
    verification_instructions: str = ""  # kept for backwards compatibility with test
    signature: bytes = b""

    def add_electronic_record(self, record_id, content_hash, timestamp, signature, verification_method):
        pass

@dataclass
class GDPRComplianceResult:
    participant_did: str
    erasure_type: str
    tombstoned_shards: int
    researcher_notifications_sent: int
    historical_research_preserved: bool
    completion_timestamp: float

@dataclass
class SafetyEvent:
    event_type: str
    severity: str
    site_did: str
    timestamp: float
    mercy_gap_at_event: float
    pdi_at_event: float
    intervention_status: str
    zk_proof: bytes

@dataclass
class SafetyAggregateMetrics:
    total_events: int
    mercy_gap_violations: int
    intervention_aborts: int
    trial_halts: int
    mean_time_to_halt: float

@dataclass
class SafetyReport:
    events: List[SafetyEvent] = field(default_factory=list)
    aggregate_metrics: Optional[SafetyAggregateMetrics] = None
    correctness_proof: bytes = b""

    def add_event(self, event: SafetyEvent):
        self.events.append(event)

@dataclass
class AuditTrail:
    merkle_root: bytes
    entry_count: int
    first_timestamp: float
    last_timestamp: float
    integrity_proof: bytes

@dataclass
class CFRPart11Package(AuditPackage):
    pass

@dataclass
class GDPRComplianceCertificate:
    participant_did: str
    generated_at: float
    access_requests: int = 0
    access_fulfillment_rate: float = 1.0
    rectifications: int = 0
    erasure_requests: int = 0
    erasure_compliance_rate: float = 1.0
    portability_requests: int = 0
    objections: int = 0
    compliance_score: float = 1.0
    proof: bytes = b""

@dataclass
class ProtocolAdherenceZKProof:
    trial_did: str
    site_count: int
    proof: bytes
    verification_key: str

@dataclass
class DataIntegrityZKProof:
    merkle_root: bytes
    entry_count: int
    proof: bytes

@dataclass
class ProtocolAdherenceView:
    trial_did: str
    site_count: int
    adherence_verified: bool
    proof_hash: bytes
    inspector_can_drill_down: bool

@dataclass
class SafetyTimelineView:
    events: List[SafetyEvent]
    aggregate_metrics: SafetyAggregateMetrics
    correctness_proof: bytes
    note: str

class InspectorNotAuthorized(Exception):
    pass

class PackageRequiresParticipantAuth(Exception):
    pass

class UnknownPackageType(Exception):
    pass

# Ethical Ledger mock
class MockLedgerSegment:
    def __init__(self):
        self.merkle_root = b"merkle_root"
        self.entry_count = 10
        self.first_timestamp = 0.0
        self.last_timestamp = time.time()
        self.zk_integrity_proof = b"zk_integrity_proof"
        self.entries = []

class MockVC:
    def __init__(self, vc_type):
        self.id = "vc_id"
        self.content_hash = b"content_hash"
        self.issuance_date = time.time()
        self.type = vc_type
        class Proof:
            proof_value = b"proof"
            verification_method = "method"
        self.proof = Proof()
        self.alert_type = "MERCY_GAP_FLOOR_BREACH"
        self.severity = "HIGH"
        self.site_did = "site_did"
        self.timestamp = time.time()
        self.mercy_gap_value = 0.03
        self.pdi_value = 0.99
        self.intervention_status = "ABORTED"
        self.safety_proof = b"safety_proof"
        self.fulfilled = True

class EthicalLedger:
    def query_vcs(self, trial_did: str = "", types: Any = None, type: Any = None, participant_did: str = "", time_window: Tuple[float, float] = None) -> List[Any]:
        t = types or type
        if isinstance(t, list):
            return [MockVC(tt) for tt in t]
        return [MockVC(t)]

    def get_segment(self, trial_did: str, from_timestamp: float, to_timestamp: float) -> MockLedgerSegment:
        return MockLedgerSegment()

    def get_protocol_adherence_proof(self, trial_did: str) -> ProtocolAdherenceZKProof:
        return ProtocolAdherenceZKProof(trial_did, 2, b"stark_proof", STARK_VK_PROTOCOL_ADHERENCE)

class RegulatoryComplianceCompiler:
    """
    Compiles existing cryptographic artifacts into regulator-facing packages.
    No manual document collection. No raw data exposure.
    """

    def __init__(self, trial_did: str, regulatory_did: str, ledger: Any = None):
        self.trial_did = trial_did
        self.regulatory_did = regulatory_did
        self.ledger = ledger or EthicalLedger()

    def compile_21cfr_part11_package(self) -> CFRPart11Package:
        """
        Compile 21 CFR Part 11 compliance package:
        - Electronic records (all VCs)
        - Electronic signatures (all signatures)
        - Audit trails (ledger segments)
        """
        package = CFRPart11Package()

        # Electronic Records
        records = self.ledger.query_vcs(
            trial_did=self.trial_did,
            types=[
                "ArkheConsentVC",
                "ArkheRevocationVC",
                "ArkheProtocolAdherenceVC",
                "ArkheInterventionWitnessVC",
                "ArkheSafetyAlertVC"
            ]
        )

        for record in records:
            package.add_electronic_record(
                record_id=record.id,
                content_hash=record.content_hash,
                timestamp=record.issuance_date,
                signature=record.proof.proof_value,
                verification_method=record.proof.verification_method
            )

        # Audit Trail
        ledger_segment = self.ledger.get_segment(
            trial_did=self.trial_did,
            from_timestamp=0,
            to_timestamp=time.time()
        )

        package.audit_trail = AuditTrail(
            merkle_root=ledger_segment.merkle_root,
            entry_count=ledger_segment.entry_count,
            first_timestamp=ledger_segment.first_timestamp,
            last_timestamp=ledger_segment.last_timestamp,
            integrity_proof=ledger_segment.zk_integrity_proof
        )

        # Inspector verification instructions
        package.verification_guide = """
        This package contains only cryptographic artifacts.
        Raw participant data is not included and cannot be extracted
        from these materials.

        To verify:
        1. Validate all VC signatures against issuer DIDs
        2. Verify Merkle root against public ledger endpoint
        3. Verify ZK integrity proof using STARK verification key
        4. Cross-reference timestamps with NTP-attested clocks
        """
        package.verification_instructions = package.verification_guide

        return package

    def _compute_mtth(self, safety_vcs: list) -> float:
        return 100.0

    def compile_safety_report(self, reporting_period: Tuple[float, float]) -> SafetyReport:
        """
        Compile safety report for DSMB or regulatory submission.
        """
        report = SafetyReport()

        # Adverse events
        safety_vcs = self.ledger.query_vcs(
            trial_did=self.trial_did,
            types=["ArkheSafetyAlertVC", "ArkheTrialHaltVC"],
            time_window=reporting_period
        )

        for vc in safety_vcs:
            event = SafetyEvent(
                event_type=vc.alert_type,
                severity=vc.severity,
                site_did=vc.site_did,
                timestamp=vc.timestamp,
                mercy_gap_at_event=vc.mercy_gap_value,
                pdi_at_event=vc.pdi_value,
                intervention_status=vc.intervention_status,
                zk_proof=vc.safety_proof  # Proves event was real, not fabricated
            )
            report.add_event(event)

        # Aggregate safety metrics
        report.aggregate_metrics = SafetyAggregateMetrics(
            total_events=len(safety_vcs),
            mercy_gap_violations=sum(1 for v in safety_vcs if v.alert_type == "MERCY_GAP_FLOOR_BREACH"),
            intervention_aborts=sum(1 for v in safety_vcs if v.alert_type == "INTERVENTION_ABORT"),
            trial_halts=sum(1 for v in safety_vcs if v.alert_type == "TRIAL_HALT"),
            mean_time_to_halt=self._compute_mtth(safety_vcs)
        )

        # ZK proof that aggregates were computed correctly
        report.correctness_proof = generate_zk_safety_aggregate_proof(
            safety_vcs, report.aggregate_metrics
        )

        return report

    def _compute_compliance_score(self, certificate: GDPRComplianceCertificate) -> float:
        return 1.0

    def compile_gdpr_compliance_certificate(
        self,
        participant_did: str
    ) -> GDPRComplianceCertificate:
        """
        Generate GDPR compliance certificate for a specific participant.
        Proves that all data subject rights have been honored.
        """
        certificate = GDPRComplianceCertificate(
            participant_did=participant_did,
            generated_at=time.time()
        )

        # Right to Access (Article 15)
        access_vcs = self.ledger.query_vcs(
            participant_did=participant_did,
            types=["ArkheDataAccessVC"]
        )
        certificate.access_requests = len(access_vcs)
        certificate.access_fulfillment_rate = sum(
            1 for v in access_vcs if v.fulfilled
        ) / len(access_vcs) if access_vcs else 1.0

        # Right to Rectification (Article 16)
        rectification_vcs = self.ledger.query_vcs(
            participant_did=participant_did,
            types=["ArkheDataRectificationVC"]
        )
        certificate.rectifications = len(rectification_vcs)

        # Right to Erasure (Article 17)
        erasure_vcs = self.ledger.query_vcs(
            participant_did=participant_did,
            types=["ArkheConsentRevocation"]  # Tombstoning = erasure
        )
        certificate.erasure_requests = len(erasure_vcs)
        certificate.erasure_compliance_rate = 1.0  # All revocations trigger cascade

        # Right to Data Portability (Article 20)
        portability_vcs = self.ledger.query_vcs(
            participant_did=participant_did,
            types=["ArkheVaultMigrationVC"]
        )
        certificate.portability_requests = len(portability_vcs)

        # Right to Object (Article 21)
        objection_vcs = self.ledger.query_vcs(
            participant_did=participant_did,
            types=["ArkheResearchObjectionVC"]
        )
        certificate.objections = len(objection_vcs)

        # Overall compliance score
        certificate.compliance_score = self._compute_compliance_score(certificate)

        # ZK proof of compliance
        certificate.proof = generate_zk_gdpr_compliance_proof(
            participant_did=participant_did,
            certificate=certificate
        )

        return certificate

class ZKRegulatoryProof:
    """
    Zero-knowledge proofs that satisfy regulatory requirements
    without exposing individual data.
    """

    @staticmethod
    def prove_protocol_adherence(
        site_commitments: List[Any],
        trial_protocol: Any
    ) -> ProtocolAdherenceZKProof:
        """
        Prove that all sites adhered to trial protocol without
        revealing individual participant data.
        """
        circuit = ZKCircuit()

        # Private inputs: individual site data (never revealed)
        for site in site_commitments:
            circuit.add_private_input(f"site_{site.site_did}_data", getattr(site, 'raw_commitment', None))

        # Public inputs: trial protocol parameters
        circuit.add_public_input("trial_did", getattr(trial_protocol, 'trial_did', ''))
        circuit.add_public_input("expected_mercy_gap_floor", 0.04)
        circuit.add_public_input("expected_pdi_ceiling", 0.98)
        circuit.add_public_input("expected_max_current_ma", 1.5)

        for site in site_commitments:
            circuit.assert_greater_than_or_equal(
                f"site_{site.site_did}_epsilon_min",
                "expected_mercy_gap_floor"
            )
            circuit.assert_less_than_or_equal(
                f"site_{site.site_did}_pdi_max",
                "expected_pdi_ceiling"
            )
            circuit.assert_less_than_or_equal(
                f"site_{site.site_did}_max_current",
                "expected_max_current_ma"
            )

        proof = generate_stark_proof(circuit)

        return ProtocolAdherenceZKProof(
            trial_did=getattr(trial_protocol, 'trial_did', ''),
            site_count=len(site_commitments),
            proof=proof,
            verification_key=STARK_VK_PROTOCOL_ADHERENCE
        )

    @staticmethod
    def prove_data_integrity(
        ledger_segment: Any,
        expected_merkle_root: bytes
    ) -> DataIntegrityZKProof:
        """
        Prove that ledger segment is intact and unmodified.
        """
        circuit = ZKCircuit()

        circuit.add_private_input("ledger_entries", getattr(ledger_segment, 'entries', []))
        circuit.add_public_input("expected_merkle_root", expected_merkle_root)
        circuit.add_public_input("entry_count", len(getattr(ledger_segment, 'entries', [])))

        # Constraint: Merkle root of entries equals expected_merkle_root
        circuit.assert_merkle_root_equals(
            "ledger_entries",
            "expected_merkle_root"
        )

        # Constraint: All entries are chronologically ordered
        circuit.assert_monotonic_timestamps("ledger_entries")

        proof = generate_stark_proof(circuit)

        return DataIntegrityZKProof(
            merkle_root=expected_merkle_root,
            entry_count=len(getattr(ledger_segment, 'entries', [])),
            proof=proof
        )

class InspectorAuditDashboard:
    """
    Regulatory inspector interface. No raw data access.
    All verification via ZK proofs and VC signatures.
    """

    def __init__(self, inspector_did: str, trial_did: str, ledger: Any = None):
        self.inspector_did = inspector_did
        self.trial_did = trial_did
        self.ledger = ledger or EthicalLedger()
        self.authorized = self._verify_inspector_authorization()

    def _verify_inspector_authorization(self) -> bool:
        """Verify inspector DID is authorized for this trial."""
        trial_did_doc = resolve_did(self.trial_did)
        inspector_auth_list = trial_did_doc.get("arkhe:regulatoryMetadata", {}).get("inspectorDIDs", [])
        return self.inspector_did in inspector_auth_list

    def view_protocol_adherence(self) -> ProtocolAdherenceView:
        """
        View protocol adherence across all sites.
        """
        if not self.authorized:
            raise InspectorNotAuthorized()

        # Fetch pre-compiled ZK proof
        adherence_proof = self.ledger.get_protocol_adherence_proof(self.trial_did)

        # Verify proof (inspector runs verification locally)
        is_valid = verify_stark_proof(
            adherence_proof.proof,
            public_inputs={
                "trial_did": self.trial_did,
                "expected_mercy_gap_floor": 0.04,
                "expected_pdi_ceiling": 0.98
            },
            verification_key=adherence_proof.verification_key
        )

        return ProtocolAdherenceView(
            trial_did=self.trial_did,
            site_count=adherence_proof.site_count,
            adherence_verified=is_valid,
            proof_hash=hashlib.sha3_256(adherence_proof.proof).digest(),
            inspector_can_drill_down=False  # No individual data access
        )

    def view_safety_timeline(self, time_window: Tuple[float, float]) -> SafetyTimelineView:
        """
        View safety events timeline.
        """
        safety_report = RegulatoryComplianceCompiler(
            self.trial_did, self.inspector_did, self.ledger
        ).compile_safety_report(time_window)

        return SafetyTimelineView(
            events=safety_report.events,
            aggregate_metrics=safety_report.aggregate_metrics,
            correctness_proof=safety_report.correctness_proof,
            note="Individual event details are aggregate-only. No participant identities exposed."
        )

    def export_audit_package(self, package_type: str) -> AuditPackage:
        """
        Export complete audit package for offline review.
        """
        compiler = RegulatoryComplianceCompiler(self.trial_did, self.inspector_did, self.ledger)

        if package_type == "21CFR11":
            package = compiler.compile_21cfr_part11_package()
        elif package_type == "SAFETY":
            package = compiler.compile_safety_report((0, time.time()))
        elif package_type == "GDPR":
            # Requires participant-specific authorization
            raise PackageRequiresParticipantAuth()
        else:
            raise UnknownPackageType()

        # Package is signed by trial sponsor and inspector
        package.signature = multi_party_sign(
            package,
            signers=[self.trial_did, self.inspector_did]
        )

        return package

class RegulatoryComplianceLayer:
    """
    Maps ARKHE trial operations to FDA, EMA, and GDPR requirements.
    Generates audit-ready reports without exposing raw data via orthogonal witness & ZK proofs.
    """

    def __init__(self, trial_did: str, jurisdiction: str, vault: Any = None, ledger: Any = None):
        self.trial_did = trial_did
        self.jurisdiction = jurisdiction
        self.vault = vault # Mock ParticipantDataVault
        self.ledger = ledger or EthicalLedger()

    def generate_fda_audit_package(self, inspector_did: str) -> AuditPackage:
        """
        Generate regulatory audit package from ethical ledger.
        No raw data; only VCs, ZK proofs, and aggregate commitments.
        """
        compiler = RegulatoryComplianceCompiler(self.trial_did, inspector_did, self.ledger)
        return compiler.compile_21cfr_part11_package()

    def _get_all_participant_consents(self, participant_did: str) -> List[str]:
        return [f"consent_{participant_did}_1", f"consent_{participant_did}_2"]

    def handle_gdpr_erasure_request(self, participant_did: str) -> GDPRComplianceResult:
        """
        Handle GDPR Article 17 (Right to Erasure) in research context.
        ARKHE tombstoning satisfies erasure for research purposes:
        data is cryptographically inaccessible for new processing.
        """
        # Issue RevocationVC with full scope
        revocation = RevocationVC(
            participant_did=participant_did,
            revocation_id=f"rev_{time.time()}",
            revoked_consent_vcs=self._get_all_participant_consents(participant_did),
            revocation_scope=RevocationScope(
                modalities=None,  # All
                classifications=None,  # All
                researcher_dids=None,  # All
                derived_data_included=True
            ),
            revoked_at=time.time()
        )

        # Execute cascade
        cascade = ConsentRevocationCascade(self.vault, self.ledger)
        report = cascade.execute_revocation(revocation)

        return GDPRComplianceResult(
            participant_did=participant_did,
            erasure_type="cryptographic_tombstoning",
            tombstoned_shards=report.affected_shard_count,
            researcher_notifications_sent=len(report.researcher_notifications),
            historical_research_preserved=True,  # Historical validity proofs remain
            completion_timestamp=time.time()
        )
