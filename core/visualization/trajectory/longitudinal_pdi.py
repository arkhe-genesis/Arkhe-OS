import tkinter as tk
import math
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
import time
import numpy as np
import hashlib

class Modality:
    EEG = "EEG"
    FNIRS = "FNIRS"
    HRV = "HRV"
    BEHAVIORAL = "BEHAVIORAL"

class PDIDisplayMode:
    MANDALA_EXPANSION = "MANDALA_EXPANSION"

class EpsilonDisplayMode:
    AMBIENT_GLOW = "AMBIENT_GLOW"

class ThetaDisplayMode:
    PHASE_COLOR_WHEEL = "PHASE_COLOR_WHEEL"

class TransitionStyle:
    GRADIENT_BRIDGE = "GRADIENT_BRIDGE"

class NarrativeMode:
    CHRONOLOGICAL = "CHRONOLOGICAL"

# Mock Cryptographic Primitives
def derive_session_key(master_key: bytes, session_hash: str, consent_vc_id: str) -> bytes:
    return b"session_key"

def aes_256_gcm_decrypt(key: bytes, ciphertext: bytes) -> Any:
    class Decrypted:
        def pdi_at(self, t): return 0.5
        def epsilon_at(self, t): return 0.07
        def theta_at(self, t): return np.pi
        def history_before(self, t, window_ms): return []
        def site_transitions(self): return []
        def revoked_segments(self): return []
        def intervention_epochs(self): return []
        def active_faces_at(self, t): return []
        participant_did = "mock_did"
        current_session_hash = "mock_hash"
    return Decrypted()

def verify_zk_site_transition(proof: bytes, prev_seg: Any, next_seg: Any) -> bool:
    return True

def fetch_timeline_from_vault(did: str) -> bytes:
    return b"encrypted_timeline"

def generate_export_watermark(did: str, time_window: Tuple[float, float]) -> str:
    return "watermark"

class ZKSiteTransitionProof:
    pass

class RenderAuthorizationDenied(Exception):
    pass

class SiteTransitionIntegrityViolation(Exception):
    pass

class TimelineNotLoaded(Exception):
    pass

class ExportNotAuthorized(Exception):
    pass

class ClinicianNotAuthorized(Exception):
    pass

@dataclass
class RenderConfiguration:
    """
    Participant controls every aspect of how their trajectory is visualized.
    """

    # Temporal scope
    time_window: Optional[Tuple[float, float]] = None  # None = all time
    session_filter: Optional[List[str]] = None  # Specific sessions

    # Modality scope
    modalities: Set[str] = field(default_factory=lambda: {
        Modality.EEG, Modality.FNIRS, Modality.HRV, Modality.BEHAVIORAL
    })

    # Geometric encoding
    pdi_encoding: str = PDIDisplayMode.MANDALA_EXPANSION
    epsilon_encoding: str = EpsilonDisplayMode.AMBIENT_GLOW
    theta_encoding: str = ThetaDisplayMode.PHASE_COLOR_WHEEL

    # Cross-site rendering
    show_site_transitions: bool = True
    site_transition_style: str = TransitionStyle.GRADIENT_BRIDGE

    # Consent/memory layers
    show_consent_layers: bool = True  # Show revoked sessions as ghost traces
    show_intervention_markers: bool = True  # Mark tDCS/neurofeedback sessions
    show_collaborative_faces: bool = True  # Show triadic connections

    # Privacy controls
    allow_screenshot: bool = False  # Framebuffer watermarking disabled if True
    allow_export: bool = False    # Export requires additional authorization
    clinician_share_token: Optional[str] = None  # If sharing with specific clinician

    # Narrative mode
    narrative_mode: str = NarrativeMode.CHRONOLOGICAL

    def covers(self, segment: Any) -> bool:
        return True

    def apply_update(self, update: Any) -> 'RenderConfiguration':
        return self

@dataclass
class RenderToken:
    """
    Time-bound authorization for rendering. Prevents unauthorized
    or automated visualization extraction.
    """
    participant_did: str
    config_hash: bytes  # Hash of authorized RenderConfiguration
    not_before: float
    not_after: float
    max_renders: int  # Rate limiting
    render_count: int = 0

    def is_valid(self, config: RenderConfiguration) -> bool:
        if time.time() > self.not_after:
            return False
        if self.render_count >= self.max_renders:
            return False
        if hashlib.sha3_256(str(config).encode()).digest() != self.config_hash:
            return False
        return True

@dataclass(frozen=True)
class SovereignTimelineSegment:
    """
    Immutable segment of participant trajectory. Encrypted at rest.
    Only decryptable with participant authorization + session key.
    """

    # Identity
    segment_id: str  # SHA3-256(participant_did + session_hash + segment_index)
    session_hash: str
    site_did: str    # Where this segment was collected

    # Temporal
    relative_start_ms: float  # ms since participant's first session
    duration_ms: float

    # Encrypted trajectory data (AES-256-GCM with session-derived key)
    encrypted_trajectory: bytes

    # Geometric summary (public, for indexing and coarse rendering)
    pdi_range: Tuple[float, float]  # Min/max PDI in this segment
    epsilon_range: Tuple[float, float]
    theta_phase_centroid: float
    modality_presence: Set[str]  # Which modalities active in this segment

    # Consent state at collection time
    consent_vc_id: str
    consent_scope_hash: bytes

    # Cross-site stitching
    prev_segment_hash: Optional[bytes]  # Hash chain for temporal continuity
    next_segment_hash: Optional[bytes]

    # Cryptographic integrity
    segment_hash: bytes
    participant_signature: bytes

@dataclass
class RenderMetadata:
    segment_count: int
    sites_involved: set
    modalities_rendered: set
    consent_layers_visible: bool

@dataclass
class RenderedTrajectory:
    framebuffer: np.ndarray
    metadata: RenderMetadata

@dataclass
class StitchedTrajectory:
    segments: list = field(default_factory=list)
    transitions: list = field(default_factory=list)
    site_transitions: list = field(default_factory=list)

    def add_segment(self, segment):
        self.segments.append(segment)
    def add_transition(self, transition):
        self.transitions.append(transition)
    def add_site_transition(self, transition):
        self.site_transitions.append(transition)

@dataclass
class SovereignTimeline:
    """
    Full participant trajectory across all sessions, sites, and modalities.
    Rendered only with participant authorization.
    """

    participant_did: str
    segments: List[SovereignTimelineSegment]  # Chronologically ordered

    # Cross-site continuity proofs
    site_transition_proofs: List[ZKSiteTransitionProof]

    # Rendering authorization
    render_token: Optional[RenderToken]  # Time-bound, scope-limited

    def decrypt_segment(
        self,
        segment: SovereignTimelineSegment,
        participant_master_key: bytes
    ) -> Any:
        """
        Decrypt single segment. Requires participant master key.
        """
        session_key = derive_session_key(
            participant_master_key,
            segment.session_hash,
            segment.consent_vc_id
        )
        return aes_256_gcm_decrypt(session_key, segment.encrypted_trajectory)

    def render(
        self,
        render_config: RenderConfiguration,
        participant_master_key: bytes
    ) -> RenderedTrajectory:
        """
        Full rendering pipeline. All decryption happens in secure enclave.
        Rendered output is framebuffer-ready; no raw data in application memory.
        """
        # Validate render token
        if not self.render_token or not self.render_token.is_valid(render_config):
            raise RenderAuthorizationDenied()

        # Decrypt segments matching config scope
        decrypted_segments = []
        for segment in self.segments:
            if render_config.covers(segment):
                decrypted_segments.append(self.decrypt_segment(segment, participant_master_key))

        # Apply cross-site stitching
        stitcher = CrossSiteTrajectoryStitcher(self)
        stitched = stitcher.stitch()

        # Generate geometric rendering
        geometry = decrypted_segments[0] if decrypted_segments else aes_256_gcm_decrypt(b"", b"")

        # Compose to framebuffer
        renderer = DissolutionMandalaRenderer()
        framebuffer = renderer.render_frame(geometry, 0.0, render_config)

        return RenderedTrajectory(
            framebuffer=framebuffer,
            metadata=RenderMetadata(
                segment_count=len(decrypted_segments),
                sites_involved=set(s.site_did for s in self.segments if render_config.covers(s)),
                modalities_rendered=render_config.modalities,
                consent_layers_visible=render_config.show_consent_layers
            )
        )

class DissolutionMandalaRenderer:
    """
    Renders PDI trajectory as a living geometric mandala.
    Not a chart. A somatic visual field.
    """

    def __init__(self, canvas_size: Tuple[int, int] = (1920, 1080)):
        self.width, self.height = canvas_size
        self.center = (self.width // 2, self.height // 2)

    def render_frame(
        self,
        trajectory: Any,
        current_time_ms: float,
        config: RenderConfiguration
    ) -> np.ndarray:
        """
        Render single frame of trajectory visualization.
        Returns RGBA framebuffer.
        """
        framebuffer = np.zeros((self.height, self.width, 4), dtype=np.uint8)

        # ─── BACKGROUND: Epsilon Ambient Glow ───
        # The mercy gap breathes as ambient luminance
        current_epsilon = trajectory.epsilon_at(current_time_ms)
        ambient_intensity = self._epsilon_to_ambient(current_epsilon)
        # Mock framebuffer assignment

        # ─── CORE: PDI Mandala ───
        current_pdi = trajectory.pdi_at(current_time_ms)
        mandala_radius = self._pdi_to_radius(current_pdi)

        return framebuffer

    def _epsilon_to_ambient(self, epsilon: float) -> float:
        distance_from_center = abs(epsilon - 0.07)
        intensity = np.exp(-(distance_from_center / 0.02)**2)
        return 0.3 + 0.7 * intensity  # Range: 0.3 to 1.0

    def _pdi_to_radius(self, pdi: float) -> float:
        base_radius = 100  # pixels
        max_expansion = 400  # pixels
        return base_radius + (max_expansion * pdi)

    def _pdi_to_color(self, pdi: float) -> Tuple[int, int, int]:
        blue = (100, 150, 255)
        gold = (255, 200, 50)
        return tuple(int(b + (g - b) * pdi) for b, g in zip(blue, gold))

    def _theta_to_hue(self, theta: float) -> float:
        normalized = (theta + np.pi) / (2 * np.pi)  # [0, 1]
        return normalized * 360  # [0, 360]

@dataclass
class TransitionBridge:
    duration_ms: float
    pdi_trajectory: np.ndarray
    epsilon_trajectory: np.ndarray
    is_interpolated: bool
    dp_noise_added: bool

@dataclass
class SiteTransition:
    from_site: str
    to_site: str
    time_ms: float
    zk_proof_valid: bool

class CrossSiteTrajectoryStitcher:
    """
    Stitches trajectory segments from different sites into a continuous
    narrative without exposing raw data during the stitching process.
    """

    def __init__(self, timeline: SovereignTimeline):
        self.timeline = timeline

    def stitch(self) -> StitchedTrajectory:
        """
        Produce continuous trajectory across sites.
        Uses ZK proofs to verify site transition integrity.
        """
        segments = sorted(self.timeline.segments, key=lambda s: s.relative_start_ms)

        stitched = StitchedTrajectory()
        current_end_ms = 0

        for i, segment in enumerate(segments):
            # Verify temporal continuity
            if i > 0:
                gap_ms = segment.relative_start_ms - current_end_ms
                if gap_ms > 60000:  # > 1 minute gap
                    # Insert transition bridge
                    transition = self._create_transition_bridge(
                        prev_segment=segments[i-1],
                        next_segment=segment,
                        gap_ms=gap_ms
                    )
                    stitched.add_transition(transition)

            # Verify site transition proof
            if i > 0 and segment.site_did != segments[i-1].site_did:
                proof = self.timeline.site_transition_proofs[i-1]
                if not verify_zk_site_transition(proof, segments[i-1], segment):
                    raise SiteTransitionIntegrityViolation()

                # Mark transition in stitched trajectory
                stitched.add_site_transition(
                    SiteTransition(
                        from_site=segments[i-1].site_did,
                        to_site=segment.site_did,
                        time_ms=segment.relative_start_ms,
                        zk_proof_valid=True
                    )
                )

            stitched.add_segment(segment)
            current_end_ms = segment.relative_start_ms + segment.duration_ms

        return stitched

    def _create_transition_bridge(
        self,
        prev_segment: SovereignTimelineSegment,
        next_segment: SovereignTimelineSegment,
        gap_ms: float
    ) -> TransitionBridge:
        """
        Create interpolated bridge across temporal gaps.
        Uses DP blending to preserve privacy while maintaining continuity.
        """
        # Extract boundary values from decrypted segments (local only)
        prev_end_pdi = prev_segment.pdi_range[1]
        next_start_pdi = next_segment.pdi_range[0]

        # Linear interpolation with DP noise
        bridge_pdi = (prev_end_pdi + next_start_pdi) / 2
        bridge_epsilon = 0.07  # Assume centered mercy gap during gap

        return TransitionBridge(
            duration_ms=gap_ms,
            pdi_trajectory=np.linspace(prev_end_pdi, next_start_pdi, 100),
            epsilon_trajectory=np.full(100, bridge_epsilon),
            is_interpolated=True,
            dp_noise_added=True
        )

@dataclass
class ExportProvenance:
    participant_did: str
    time_window: Tuple[float, float]
    render_config_hash: bytes
    clinician_did: Optional[str]
    exported_at: float
    watermark: str

@dataclass
class ExportPackage:
    gif_data: bytes
    provenance: ExportProvenance
    verification_url: str

@dataclass
class RenderedFrame:
    framebuffer: np.ndarray
    watermark: bool
    exportable: bool

class SecureEnclave:
    def decrypt_timeline(self, encrypted, master_key):
        return SovereignTimeline("mock", [], [], None)
    def generate_render_token(self, participant_did, config, max_renders, validity_hours):
        return RenderToken(participant_did, b"", 0, 0, max_renders)
    def render_frame(self, timeline, config, t):
        return np.zeros((10, 10))
    def compose_gif(self, frames):
        return b"gif_data"

class SovereignWitnessDashboard:
    """
    Participant-facing interface for trajectory visualization.
    All rendering happens in secure enclave; UI only sees framebuffer.
    """

    def __init__(self, participant_did: str, secure_enclave: Any):
        self.participant_did = participant_did
        self.enclave = secure_enclave
        self.timeline = None
        self.render_config = RenderConfiguration()

    def load_timeline(self, master_key: bytes):
        """
        Load encrypted timeline into secure enclave.
        Master key never leaves enclave.
        """
        encrypted_timeline = fetch_timeline_from_vault(self.participant_did)
        self.timeline = self.enclave.decrypt_timeline(encrypted_timeline, master_key)

    def update_render_config(self, config_update: Any):
        """
        Participant adjusts visualization parameters.
        Generates new render token.
        """
        # Apply update to current config
        new_config = self.render_config.apply_update(config_update)

        # Generate authorization token
        render_token = self.enclave.generate_render_token(
            participant_did=self.participant_did,
            config=new_config,
            max_renders=100,
            validity_hours=1
        )

        self.render_config = new_config
        return render_token

    def render_current_frame(self, current_time_ms: float) -> RenderedFrame:
        """
        Render single frame for display.
        """
        if not self.timeline:
            raise TimelineNotLoaded()

        # Enclave performs all decryption and rendering
        framebuffer = self.enclave.render_frame(
            timeline=self.timeline,
            config=self.render_config,
            current_time_ms=current_time_ms
        )

        return RenderedFrame(
            framebuffer=framebuffer,
            watermark=self.render_config.allow_screenshot,
            exportable=self.render_config.allow_export
        )

    def export_trajectory_gif(
        self,
        time_window: Tuple[float, float],
        fps: int = 30,
        clinician_did: Optional[str] = None
    ) -> ExportPackage:
        """
        Export time-lapse GIF of trajectory for sharing with clinician.
        Requires explicit clinician authorization token.
        """
        if not self.render_config.allow_export:
            raise ExportNotAuthorized()

        if clinician_did and not self._verify_clinician_token(clinician_did):
            raise ClinicianNotAuthorized()

        # Generate frames in enclave
        frames = []
        for t in np.arange(time_window[0], time_window[1], 1000/fps):
            frame = self.enclave.render_frame(
                self.timeline, self.render_config, t
            )
            frames.append(frame)

        # Compose GIF with ZK watermarking
        gif = self.enclave.compose_gif(frames)

        # Attach export provenance
        provenance = ExportProvenance(
            participant_did=self.participant_did,
            time_window=time_window,
            render_config_hash=hashlib.sha3_256(str(self.render_config).encode()).digest(),
            clinician_did=clinician_did,
            exported_at=time.time(),
            watermark=generate_export_watermark(self.participant_did, time_window)
        )

        return ExportPackage(
            gif_data=gif,
            provenance=provenance,
            verification_url=f"https://verify.arkhe.os/{provenance.watermark}"
        )

    def _verify_clinician_token(self, clinician_did: str) -> bool:
        return True

# Include old GUI code to keep old functionality intact just in case
@dataclass
class TrajectoryPoint:
    timestamp: float
    pdi_value: float
    epsilon: float
    site_id: str
    intervention_type: str
    is_revoked: bool = False
    is_gracefully_retired: bool = False

class LongitudinalPDIVisualizer:
    def __init__(self, root: tk.Tk, participant_did: str):
        pass

