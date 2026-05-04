from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import numpy as np

# Mock signal processing functions for architecture blueprint
def bandpass_filter(signal: np.ndarray, low: float, high: float, fs: int) -> np.ndarray:
    return signal

def hilbert(signal: np.ndarray) -> np.ndarray:
    return signal + 1j * signal

def wavelet_coherence(signal: np.ndarray, reference: str, fs: int) -> Tuple[np.ndarray, float]:
    return np.array([]), 0.0

def extract_rr_intervals(signal: np.ndarray) -> np.ndarray:
    return np.array([1.0])

def compute_lf_hf_phase(rr_intervals: np.ndarray) -> float:
    return 0.0

@dataclass
class BehavioralEvent:
    timestamp: float

def detect_behavioral_events(signal: np.ndarray) -> List[BehavioralEvent]:
    return [BehavioralEvent(timestamp=0.0)]

def compute_pdi_from_phase(phase: float) -> float:
    return 0.95

def compute_cross_modality_plv(phases: Dict[str, float]) -> float:
    return 0.1

@dataclass
class MultiModalPhaseAlignedStateVector:
    """Unified phase geometry across EEG, fNIRS, HRV, behavioral without collision."""

    # Modality-specific phases (normalized, lag-compensated)
    eeg_theta: float           # [-pi, pi], Hilbert phase at 4-8Hz
    fnirs_phi: float           # [-pi, pi], wavelet coherence phase (lag-compensated)
    hrv_psi: float             # [-pi, pi], autonomic phase from Poincaré angle
    behavioral_beta: float     # [-pi, pi], intention-aligned event phase

    # Unified dissolution metrics (computed from orthogonal modalities)
    pdi_multi: float           # Weighted consensus PDI across modalities
    epsilon_multi: float       # Inter-modality phase variance (mercy gap across senses)

    # Orthogonality preservation fields
    modality_weights: Dict[str, float]  # Adaptive weights based on signal quality
    cross_modality_coherence: float     # PLV between modalities (should be low for orthogonality)

    # Temporal context (relative, not absolute)
    phase_cycle_index: int     # Monotonic counter per participant
    relative_timestamp: float  # Seconds since session start

    # Integrity
    state_hash: str
    prev_state_hash: str

    def compute_orthogonal_witness(self, other: 'MultiModalPhaseAlignedStateVector') -> bool:
        """Checks if two multi-modal states can form valid triangular face."""
        # Compute phase differences per modality
        diffs = {
            'eeg': abs(self.eeg_theta - other.eeg_theta),
            'fnirs': abs(self.fnirs_phi - other.fnirs_phi),
            'hrv': abs(self.hrv_psi - other.hrv_psi),
            'behavioral': abs(self.behavioral_beta - other.behavioral_beta)
        }

        # Orthogonality window per modality (allow natural resonance, prevent rigid lock)
        for mod, diff in diffs.items():
            diff = min(diff, 2*math.pi - diff)  # Normalize to [-pi, pi]
            if diff < 0.02 or diff > 0.20:  # Modality-specific bounds
                return False

        # Inter-modality mercy gap must be preserved
        if not (0.04 <= self.epsilon_multi <= 0.10):
            return False

        # PDI consensus must be compatible
        if abs(self.pdi_multi - other.pdi_multi) > 0.25:
            return False

        return True

class MultiModalPhaseAligner:
    """Aligns heterogeneous modalities to unified phase manifold without forcing synchronization."""

    def __init__(self, participant_id: str):
        self.participant_id = participant_id
        # Lag compensation parameters (learned per participant)
        self.fnirs_lag_ms = 4500  # Typical hemodynamic lag
        self.hrv_smoothing_window = 30  # Seconds for autonomic phase stability
        self._cycle_index = 0

    def _increment_cycle_index(self) -> int:
        self._cycle_index += 1
        return self._cycle_index

    def _compute_modality_weights(self, signals: Dict[str, np.ndarray]) -> Dict[str, float]:
        # Equal weighting placeholder
        return {mod: 1.0 / len(signals) for mod in signals}

    def extract_normalized_phase(self, modality: str, raw_signal: np.ndarray, timestamp: float) -> float:
        """Extracts normalized phase [-pi, pi] for specific modality with lag compensation."""
        if modality == "eeg":
            # Hilbert transform on theta band (4-8Hz)
            theta_band = bandpass_filter(raw_signal, 4, 8, fs=256)
            analytic = hilbert(theta_band)
            if len(analytic) > 0:
                phase = np.angle(analytic[-1])  # Latest sample
            else:
                phase = 0.0
            return phase

        elif modality == "fnirs":
            # Wavelet coherence phase with lag compensation
            coherence, phase = wavelet_coherence(raw_signal, reference="theta_band", fs=10)
            # Compensate for hemodynamic lag
            compensated_phase = (phase + 2*math.pi * self.fnirs_lag_ms / 1000) % (2*math.pi)
            return compensated_phase - math.pi  # Normalize to [-pi, pi]

        elif modality == "hrv":
            # Poincaré plot angle + spectral phase
            rr_intervals = extract_rr_intervals(raw_signal)
            if len(rr_intervals) > 1:
                diff_rr = np.diff(rr_intervals)
                poincare_angle = np.arctan2(np.std(diff_rr), np.mean(diff_rr)) if np.mean(diff_rr) != 0 else 0
            else:
                poincare_angle = 0.0
            # Combine with LF/HF spectral phase
            lf_hf_phase = compute_lf_hf_phase(rr_intervals)
            # Weighted combination
            return 0.7 * poincare_angle + 0.3 * lf_hf_phase

        elif modality == "behavioral":
            # Event-based phase embedding aligned to intention
            events = detect_behavioral_events(raw_signal)  # e.g., keypress, gaze shift
            if not events:
                return 0.0  # Default phase when no events
            # Compute phase relative to last intention marker
            time_since_intention = timestamp - events[-1].timestamp
            phase = (2*math.pi * time_since_intention / 5.0) % (2*math.pi)  # 5s intention window
            return phase - math.pi

        else:
            raise ValueError(f"Unknown modality: {modality}")

    def compute_multi_modal_state(self, signals: Dict[str, np.ndarray], timestamp: float) -> MultiModalPhaseAlignedStateVector:
        """Computes unified MM-PASV from heterogeneous modality signals."""
        # Extract normalized phases
        phases = {
            mod: self.extract_normalized_phase(mod, sig, timestamp)
            for mod, sig in signals.items()
        }

        # Compute inter-modality phase variance (epsilon_multi)
        phase_values = list(phases.values())
        epsilon_multi = float(np.std(phase_values)) if phase_values else 0.0 # Should be in [0.04, 0.10] for orthogonality

        # Compute weighted PDI consensus
        weights = self._compute_modality_weights(signals)  # Based on SNR, artifact rejection
        pdi_multi = sum(weights.get(mod, 0) * compute_pdi_from_phase(phases.get(mod, 0)) for mod in phases)

        # Compute cross-modality coherence (should be low for orthogonality)
        cross_coh = compute_cross_modality_plv(phases)

        return MultiModalPhaseAlignedStateVector(
            eeg_theta=phases.get("eeg", 0.0),
            fnirs_phi=phases.get("fnirs", 0.0),
            hrv_psi=phases.get("hrv", 0.0),
            behavioral_beta=phases.get("behavioral", 0.0),
            pdi_multi=pdi_multi,
            epsilon_multi=epsilon_multi,
            modality_weights=weights,
            cross_modality_coherence=cross_coh,
            phase_cycle_index=self._increment_cycle_index(),
            relative_timestamp=timestamp,
            state_hash="calculated_afterwards",
            prev_state_hash="previous_hash"
        )
