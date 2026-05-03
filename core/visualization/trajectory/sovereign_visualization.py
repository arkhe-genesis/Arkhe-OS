from dataclasses import dataclass, field
from typing import List, Tuple, Set, Optional
import time
import hashlib
import numpy as np

# Mocks to allow it to run
@dataclass
class DecryptedTrajectory:
    participant_did: str = "did:mock"
    current_session_hash: str = "hash"
    def epsilon_at(self, current_time_ms: float) -> float: return 0.07
    def pdi_at(self, current_time_ms: float) -> float: return 0.5
    def theta_at(self, current_time_ms: float) -> float: return np.pi / 2
    def history_before(self, current_time_ms: float, window_ms: float): return []
    def site_transitions(self): return []
    def revoked_segments(self): return []
    def intervention_epochs(self): return []
    def active_faces_at(self, current_time_ms: float): return []

@dataclass
class ZKSiteTransitionProof:
    pass

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
class RenderedFrame:
    framebuffer: np.ndarray
    watermark: bool
    exportable: bool

class Modality:
    EEG = "EEG"
    FNIRS = "fNIRS"
    HRV = "HRV"
    BEHAVIORAL = "Behavioral"

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

@dataclass
class SovereignTimelineSegment:
    segment_id: str
    session_hash: str
    site_did: str
    relative_start_ms: float
    duration_ms: float
    encrypted_trajectory: bytes
    pdi_range: Tuple[float, float]
    epsilon_range: Tuple[float, float]
    theta_phase_centroid: float
    modality_presence: Set[str]
    consent_vc_id: str
    consent_scope_hash: bytes
    prev_segment_hash: Optional[bytes]
    next_segment_hash: Optional[bytes]
    segment_hash: bytes
    participant_signature: bytes

@dataclass
class RenderConfiguration:
    time_window: Optional[Tuple[float, float]] = None
    session_filter: Optional[List[str]] = None
    modalities: Set[str] = field(default_factory=lambda: {
        Modality.EEG, Modality.FNIRS, Modality.HRV, Modality.BEHAVIORAL
    })
    pdi_encoding: str = PDIDisplayMode.MANDALA_EXPANSION
    epsilon_encoding: str = EpsilonDisplayMode.AMBIENT_GLOW
    theta_encoding: str = ThetaDisplayMode.PHASE_COLOR_WHEEL
    show_site_transitions: bool = True
    site_transition_style: str = TransitionStyle.GRADIENT_BRIDGE
    show_consent_layers: bool = True
    show_intervention_markers: bool = True
    show_collaborative_faces: bool = True
    allow_screenshot: bool = False
    allow_export: bool = False
    clinician_share_token: Optional[str] = None
    narrative_mode: str = NarrativeMode.CHRONOLOGICAL

    def covers(self, segment: SovereignTimelineSegment) -> bool:
        if self.time_window:
            start, end = self.time_window
            seg_start = segment.relative_start_ms
            seg_end = seg_start + segment.duration_ms
            if seg_end < start or seg_start > end:
                return False
        if self.session_filter and segment.session_hash not in self.session_filter:
            return False
        return True

@dataclass
class RenderToken:
    participant_did: str
    config_hash: bytes
    not_before: float
    not_after: float
    max_renders: int
    render_count: int = 0

    def is_valid(self, config: RenderConfiguration) -> bool:
        if time.time() > self.not_after:
            return False
        if self.render_count >= self.max_renders:
            return False
        if hashlib.sha3_256(str(config).encode()).digest() != self.config_hash:
            return False
        return True

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

class StitchedTrajectory:
    def __init__(self):
        self.segments = []
        self.transitions = []
        self.site_transitions = []

    def add_segment(self, segment):
        self.segments.append(segment)

    def add_transition(self, transition):
        self.transitions.append(transition)

    def add_site_transition(self, transition):
        self.site_transitions.append(transition)

class SovereignTimeline:
    participant_did: str
    segments: List[SovereignTimelineSegment]
    site_transition_proofs: List[ZKSiteTransitionProof]
    render_token: Optional[RenderToken]

    def decrypt_segment(
        self,
        segment: SovereignTimelineSegment,
        participant_master_key: bytes
    ) -> DecryptedTrajectory:
        return DecryptedTrajectory()

    def _stitch_segments(self, decrypted_segments):
        pass

    def _compute_trajectory_geometry(self, stitched, render_config):
        pass

    def _render_to_framebuffer(self, geometry, render_config):
        return np.zeros((1080, 1920, 4), dtype=np.uint8)

    def render(
        self,
        render_config: RenderConfiguration,
        participant_master_key: bytes
    ) -> RenderedTrajectory:
        if not self.render_token or not self.render_token.is_valid(render_config):
            raise Exception("RenderAuthorizationDenied")

        decrypted_segments = []
        for segment in self.segments:
            if render_config.covers(segment):
                decrypted_segments.append(self.decrypt_segment(segment, participant_master_key))

        stitched = self._stitch_segments(decrypted_segments)
        geometry = self._compute_trajectory_geometry(stitched, render_config)
        framebuffer = self._render_to_framebuffer(geometry, render_config)

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
    def __init__(self, canvas_size: Tuple[int, int] = (1920, 1080)):
        self.width, self.height = canvas_size
        self.center = (self.width // 2, self.height // 2)

    def _ambient_color(self, intensity: float):
        return [int(intensity * 255)] * 3

    def _draw_mandala(self, fb, center, radius, complexity, color, opacity):
        pass

    def _draw_phase_rim(self, fb, center, radius, hue):
        pass

    def _draw_trajectory_trail(self, fb, history, color_gradient, fade_alpha):
        pass

    def _pdi_gradient(self):
        pass

    def _draw_site_bridge(self, fb, from_site, to_site, timestamp, proof_valid):
        pass

    def _draw_ghost_trace(self, fb, segment, opacity):
        pass

    def _draw_intervention_glow(self, fb, center, intensity, modality):
        pass

    def _draw_triadic_connection(self, fb, face, participant_position, partner_positions):
        pass

    def _compute_partner_positions(self, face):
        return []

    def _embed_invisible_watermark(self, fb, participant_did, session_hash, timestamp):
        pass

    def _pdi_to_complexity(self, pdi: float):
        return int(pdi * 10)

    def render_frame(
        self,
        trajectory: DecryptedTrajectory,
        current_time_ms: float,
        config: RenderConfiguration
    ) -> np.ndarray:
        framebuffer = np.zeros((self.height, self.width, 4), dtype=np.uint8)

        current_epsilon = trajectory.epsilon_at(current_time_ms)
        ambient_intensity = self._epsilon_to_ambient(current_epsilon)
        framebuffer[:, :, :3] = self._ambient_color(ambient_intensity)

        current_pdi = trajectory.pdi_at(current_time_ms)
        mandala_radius = self._pdi_to_radius(current_pdi)
        mandala_complexity = self._pdi_to_complexity(current_pdi)

        self._draw_mandala(
            framebuffer,
            center=self.center,
            radius=mandala_radius,
            complexity=mandala_complexity,
            color=self._pdi_to_color(current_pdi),
            opacity=0.8
        )

        current_theta = trajectory.theta_at(current_time_ms)
        rim_hue = self._theta_to_hue(current_theta)
        self._draw_phase_rim(framebuffer, self.center, mandala_radius, rim_hue)

        history = trajectory.history_before(current_time_ms, window_ms=30000)
        self._draw_trajectory_trail(
            framebuffer,
            history,
            color_gradient=self._pdi_gradient,
            fade_alpha=0.3
        )

        if config.show_site_transitions:
            transitions = trajectory.site_transitions()
            for trans in transitions:
                if trans.time_ms <= current_time_ms:
                    self._draw_site_bridge(
                        framebuffer,
                        from_site=trans.from_site,
                        to_site=trans.to_site,
                        timestamp=trans.time_ms,
                        proof_valid=trans.zk_proof_valid
                    )

        if config.show_consent_layers:
            revoked_segments = trajectory.revoked_segments()
            for seg in revoked_segments:
                if seg.start_ms <= current_time_ms <= seg.end_ms:
                    self._draw_ghost_trace(
                        framebuffer,
                        segment=seg,
                        opacity=0.15
                    )

        if config.show_intervention_markers:
            interventions = trajectory.intervention_epochs()
            for iv in interventions:
                if iv.start_ms <= current_time_ms <= iv.end_ms:
                    self._draw_intervention_glow(
                        framebuffer,
                        center=self.center,
                        intensity=iv.current_ma / 2.0,
                        modality=iv.modality
                    )

        if config.show_collaborative_faces:
            faces = trajectory.active_faces_at(current_time_ms)
            for face in faces:
                self._draw_triadic_connection(
                    framebuffer,
                    face=face,
                    participant_position=self.center,
                    partner_positions=self._compute_partner_positions(face)
                )

        if not config.allow_screenshot:
            self._embed_invisible_watermark(
                framebuffer,
                participant_did=trajectory.participant_did,
                session_hash=trajectory.current_session_hash,
                timestamp=current_time_ms
            )

        return framebuffer

    def _epsilon_to_ambient(self, epsilon: float) -> float:
        distance_from_center = abs(epsilon - 0.07)
        intensity = np.exp(-(distance_from_center / 0.02)**2)
        return 0.3 + 0.7 * intensity

    def _pdi_to_radius(self, pdi: float) -> float:
        base_radius = 100
        max_expansion = 400
        return base_radius + (max_expansion * pdi)

    def _pdi_to_color(self, pdi: float) -> Tuple[int, int, int]:
        blue = (100, 150, 255)
        gold = (255, 200, 50)
        return tuple(int(b + (g - b) * pdi) for b, g in zip(blue, gold))

    def _theta_to_hue(self, theta: float) -> float:
        normalized = (theta + np.pi) / (2 * np.pi)
        return normalized * 360

class CrossSiteTrajectoryStitcher:
    def __init__(self, timeline: SovereignTimeline):
        self.timeline = timeline

    def stitch(self) -> StitchedTrajectory:
        segments = sorted(self.timeline.segments, key=lambda s: s.relative_start_ms)

        stitched = StitchedTrajectory()
        current_end_ms = 0

        for i, segment in enumerate(segments):
            if i > 0:
                gap_ms = segment.relative_start_ms - current_end_ms
                if gap_ms > 60000:
                    transition = self._create_transition_bridge(
                        prev_segment=segments[i-1],
                        next_segment=segment,
                        gap_ms=gap_ms
                    )
                    stitched.add_transition(transition)

            if i > 0 and segment.site_did != segments[i-1].site_did:
                proof = self.timeline.site_transition_proofs[i-1]
                # Mock verify_zk_site_transition
                # if not verify_zk_site_transition(proof, segments[i-1], segment):
                #    raise Exception("SiteTransitionIntegrityViolation")

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
        prev_end_pdi = prev_segment.pdi_range[1]
        next_start_pdi = next_segment.pdi_range[0]

        bridge_epsilon = 0.07

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

class SecureEnclave:
    def decrypt_timeline(self, encrypted_timeline, master_key):
        return SovereignTimeline()

    def generate_render_token(self, participant_did, config, max_renders, validity_hours):
        return RenderToken(
            participant_did=participant_did,
            config_hash=hashlib.sha3_256(str(config).encode()).digest(),
            not_before=time.time(),
            not_after=time.time() + validity_hours * 3600,
            max_renders=max_renders
        )

    def render_frame(self, timeline, config, current_time_ms):
        return np.zeros((1080, 1920, 4), dtype=np.uint8)

    def compose_gif(self, frames):
        return b"gif_data"

def fetch_timeline_from_vault(participant_did):
    return b"encrypted_timeline"

def generate_export_watermark(participant_did, time_window):
    return "watermark"

class RenderConfigUpdate:
    pass

class SovereignWitnessDashboard:
    def __init__(self, participant_did: str, secure_enclave: SecureEnclave):
        self.participant_did = participant_did
        self.enclave = secure_enclave
        self.timeline = None
        self.render_config = RenderConfiguration()

    def load_timeline(self, master_key: bytes):
        encrypted_timeline = fetch_timeline_from_vault(self.participant_did)
        self.timeline = self.enclave.decrypt_timeline(encrypted_timeline, master_key)

    def update_render_config(self, config_update: RenderConfigUpdate):
        # Apply update to current config (mock)
        new_config = self.render_config

        render_token = self.enclave.generate_render_token(
            participant_did=self.participant_did,
            config=new_config,
            max_renders=100,
            validity_hours=1
        )

        self.render_config = new_config
        return render_token

    def render_current_frame(self, current_time_ms: float) -> RenderedFrame:
        if not self.timeline:
            raise Exception("TimelineNotLoaded")

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

    def _verify_clinician_token(self, clinician_did):
        return True

    def export_trajectory_gif(
        self,
        time_window: Tuple[float, float],
        fps: int = 30,
        clinician_did: Optional[str] = None
    ) -> ExportPackage:
        if not self.render_config.allow_export:
            raise Exception("ExportNotAuthorized")

        if clinician_did and not self._verify_clinician_token(clinician_did):
            raise Exception("ClinicianNotAuthorized")

        frames = []
        for t in np.arange(time_window[0], time_window[1], 1000/fps):
            frame = self.enclave.render_frame(
                self.timeline, self.render_config, t
            )
            frames.append(frame)

        gif = self.enclave.compose_gif(frames)

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
