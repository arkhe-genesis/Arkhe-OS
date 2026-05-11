import numpy as np
from typing import Dict, Any
from arkhe_os.core.photocurrent_module import PhotocurrentSensor

class BayesianCoherenceFusion:
    """
    Integrates optical (AWG) and electrical (Photocurrent) sensors.
    Calculates unified coherence index Ω_total using Bayesian weighted fusion.
    """
    def __init__(self):
        self.sensor_pc = PhotocurrentSensor()
        # Weights represent confidence in each sensor's resolution for different modes
        self.weights = {
            'optical_awg': 0.6,
            'photocurrent_nearfield': 0.4
        }

    def calculate_unified_omega(self,
                                awg_results: Dict[str, Any],
                                pc_scan_data: np.ndarray) -> Dict[str, Any]:
        """
        Combines Ω_spec (optical) and Ω_dark (electrical).
        """
        omega_spec = awg_results.get('omega_spec', 0.0)

        # Calculate Ω_dark from photocurrent scan (topological edge modes)
        # Higher activity at edges indicates protected topological coherence
        edge_activity = (np.mean(pc_scan_data[:10]) + np.mean(pc_scan_data[-10:])) / 2
        omega_dark = np.clip(edge_activity, 0, 1)

        # Bayesian fusion: Weighted average normalized by confidence
        # Photocurrent is given more weight if dark modes are detected
        dark_modes = self.sensor_pc.detect_dark_modes(pc_scan_data, {'total_power': omega_spec})

        w_pc = self.weights['photocurrent_nearfield']
        if dark_modes:
            w_pc += 0.2 # Increase weight if hidden topology is found

        w_opt = self.weights['optical_awg']

        total_w = w_pc + w_opt
        omega_total = (omega_spec * w_opt + omega_dark * w_pc) / total_w

        return {
            'omega_total': float(omega_total),
            'omega_spec': float(omega_spec),
            'omega_dark': float(omega_dark),
            'dark_modes_detected': len(dark_modes) > 0,
            'confidence_index': float(total_w / 1.2) # Normalizado
        }

if __name__ == "__main__":
    fusion = BayesianCoherenceFusion()
    # Mock data from AWG (e.g. failed to resolve narrow peaks)
    mock_awg = {'omega_spec': 0.12}
    # Data from Photocurrent (detected topological modes)
    mock_pc = fusion.sensor_pc.scan_microtubule()

    result = fusion.calculate_unified_omega(mock_awg, mock_pc)
    print(f"Ω_total (ARKHE-04 Extended): {result['omega_total']:.4f}")
    print(f"Dark Modes found: {result['dark_modes_detected']}")
