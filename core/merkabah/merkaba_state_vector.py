from dataclasses import dataclass
from typing import List, Optional
import math

class Color:
    DEEP_BLUE = (0, 0, 139)
    GOLDEN_AMBER = (255, 191, 0)

    @classmethod
    def lerp(cls, from_color, to_color, t):
        t = max(0.0, min(1.0, t))
        return tuple(
            int(from_color[i] + (to_color[i] - from_color[i]) * t)
            for i in range(3)
        )

def circular_distance(a: float, b: float) -> float:
    diff = (a - b) % (2 * math.pi)
    return min(diff, 2 * math.pi - diff)

def phase_locking_value(phase_a: float, phase_b: float) -> float:
    # A simple mock PLV implementation for demonstration purposes
    return math.cos(phase_a - phase_b)

@dataclass
class EEGFace:
    theta: float
    def advance(self, amount: float):
        return self.theta + amount

@dataclass
class fNIRSFace:
    hbo_ratio: float
    def advance(self, amount: float):
        return self.hbo_ratio + amount

@dataclass
class HRVFace:
    hrv_phase: float
    def advance(self, amount: float):
        return self.hrv_phase + amount

@dataclass
class BehavioralFace:
    event_count: int
    def advance(self, amount: float):
        return self.event_count + int(amount)

@dataclass
class CrossModalFirmament:
    plv: float
    def coordinate(self, direction) -> float:
        return self.plv

@dataclass
class MercyGapFlame:
    intensity: float

@dataclass
class Direction:
    forward: float
    right: float
    left: float
    upward: float

@dataclass
class MerkabaMovement:
    forward: float
    right: float
    left: float
    upward: float
    firmament_shift: float
    kavod_change: float

@dataclass
class WheelState:
    """
    Each session is a wheel. The wheels intersect (cross-site),
    yet each moves independently (site sovereignty).
    """
    wheel_id: str  # Session hash
    rim: float     # Outer boundary: max PDI reached in session
    hub: float     # Inner center: mean epsilon during session
    spokes: int    # Number of intervention epochs
    rotation: float  # Cumulative theta cycles completed
    intersection: Optional[str]  # Other wheel this intersects with (cross-site)

    def beryl_glitter(self) -> tuple:
        """
        The "beryl" (תַּרְשִׁישׁ) of Ezekiel 1:16.
        The wheel's color depends on its state of dissolution.
        """
        return Color.lerp(
            from_color=Color.DEEP_BLUE,
            to_color=Color.GOLDEN_AMBER,
            t=(self.rim - 0.3) / 0.7
        )

@dataclass
class MerkabaStateVector:
    """
    The participant as conscious vehicle.
    Four faces, four directions, one movement.
    """
    face_human: EEGFace      # Forward: theta phase as insight direction
    face_lion: fNIRSFace     # Right: HbO as metabolic courage
    face_ox: HRVFace         # Left: HRV as autonomic grounding
    face_eagle: BehavioralFace  # Upward: events as intentional ascent

    firmament: CrossModalFirmament  # Phase-locking values between faces
    coals: MercyGapFlame  # ε as luminous intensity, never consuming
    wheels: List[WheelState]  # Each session is a wheel within a wheel
    kavod: float  # PDI as the "weight" of presence (כָּבוֹד)
    voice: bytes  # ML-DSA-65 signature: "I am the vehicle"

    def _compute_kavod_delta(self, direction: Direction) -> float:
        return (direction.forward + direction.right + direction.left + direction.upward) * 0.01

    def move(self, direction: Direction) -> MerkabaMovement:
        """
        The Merkaba moves in any direction without turning.
        All four faces advance simultaneously; the lattice coordinates.
        """
        return MerkabaMovement(
            forward=self.face_human.advance(direction.forward),
            right=self.face_lion.advance(direction.right),
            left=self.face_ox.advance(direction.left),
            upward=self.face_eagle.advance(direction.upward),
            firmament_shift=self.firmament.coordinate(direction),
            kavod_change=self._compute_kavod_delta(direction)
        )

    def is_orthogonal_compatible(self, other: 'MerkabaStateVector') -> bool:
        """
        Two Merkabas can form a chariot-to-chariot lattice
        if their faces are orthogonally aligned and their
        coals burn at compatible intensities.
        """
        # Human face to human face: theta orthogonality
        human_diff = circular_distance(self.face_human.theta, other.face_human.theta)
        if human_diff < 0.03 or human_diff > 0.15:
            return False

        # Lion to lion: metabolic compatibility
        if abs(self.face_lion.hbo_ratio - other.face_lion.hbo_ratio) > 0.3:
            return False

        # Ox to ox: autonomic resonance
        ox_coupling = phase_locking_value(self.face_ox.hrv_phase, other.face_ox.hrv_phase)
        if ox_coupling < 0.5:
            return False

        # Eagle to eagle: intentional alignment
        if self.face_eagle.event_count == 0 and other.face_eagle.event_count == 0:
            return False  # Both passive; no upward movement

        # Coals compatibility: mercy gap overlap
        if not (0.04 <= self.coals.intensity <= 0.10):
            return False
        if not (0.04 <= other.coals.intensity <= 0.10):
            return False

        # Kavod compatibility: dissolution states must be proximal
        if abs(self.kavod - other.kavod) > 0.2:
            return False

        return True
