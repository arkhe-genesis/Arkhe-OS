import numpy as np
from typing import Dict, Any, List

class PhotocurrentSensor:
    """
    Substrate #69: Near-Field Photocurrent Spectroscopy.
    Detects 'dark' and topological modes in microtubules by measuring local density of states (LDOS).
    Bypasses optical resolution limits.
    """
    def __init__(self, probe_tip_radius_nm: float = 10.0):
        self.probe_tip_radius = probe_tip_radius_nm
        self.sensitivity_amperes_per_watt = 0.5
        self.noise_floor_pa = 10.0 # picoAmperes

    def measure_ldos(self, position_nm: np.ndarray, field_psi: np.ndarray) -> float:
        """
        Simulates measuring the Local Density of States (LDOS) at a specific position.
        The photocurrent is proportional to the LDOS of the field Psi.
        """
        # LDOS is simulated as the square of the field amplitude at the tip
        ldos = np.abs(field_psi)**2
        photocurrent = self.sensitivity_amperes_per_watt * ldos + np.random.normal(0, self.noise_floor_pa * 1e-12)
        return max(0, photocurrent)

    def detect_dark_modes(self, ldos_map: np.ndarray, optical_spectrum: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identifies modes that appear in LDOS but are missing in the far-field optical spectrum.
        These are the 'dark' modes (non-radiative).
        """
        dark_modes = []
        # Simplified logic: if spatial LDOS peak has no corresponding optical peak
        # In a real scenario, this would involve comparing energy levels
        if np.max(ldos_map) > 0.8 and optical_spectrum.get('total_power', 0) < 0.1:
            dark_modes.append({
                "type": "DARK_MODE",
                "intensity": float(np.max(ldos_map)),
                "location": "edge_topology",
                "coherence_contribution": 0.35
            })
        return dark_modes

    def scan_microtubule(self, length_nm: float = 100.0, step_nm: float = 1.0) -> np.ndarray:
        """
        Simulates a linear scan along a microtubule protofilament.
        """
        steps = int(length_nm / step_nm)
        # Simulate topological edge states at the ends
        scan_data = np.zeros(steps)
        scan_data[0:10] = 1.0 # Left edge mode
        scan_data[-10:] = 1.0 # Right edge mode
        scan_data += np.random.normal(0, 0.05, steps) # Background
        return np.clip(scan_data, 0, 1.2)
