import numpy as np
from typing import Dict, Any

class ExternalHubFrontend:
    """
    Models the RF Front-End for the External Hub.
    Targets 441 MHz (Tzinor Swarm Sync frequency).
    Includes antenna characterization and SAW filter modeling.
    """
    def __init__(self, f_center_mhz: float = 441.0):
        self.f_center = f_center_mhz * 1e6
        self.bandwidth = 2.0e6 # 2 MHz
        self.antenna_gain_dbi = 1.5
        self.vswr = 1.2
        self.noise_figure_db = 2.5

    def get_saw_filter_response(self, frequency_hz: float) -> float:
        """
        Calculates SAW filter attenuation (dB) at a given frequency.
        Simulates a high-selectivity bandpass filter.
        """
        df = abs(frequency_hz - self.f_center)
        if df < (self.bandwidth / 2):
            return -1.5 # Insertion loss in passband
        elif df < self.bandwidth:
            return -20.0 # Transition band
        else:
            return -50.0 # Stopband attenuation

    def calculate_link_budget(self,
                             tx_power_dbm: float,
                             distance_m: float,
                             tissue_loss_db: float) -> float:
        """
        Estimates received power (dBm) at the nanobot swarm.
        P_rx = P_tx + G_tx - PathLoss - TissueLoss
        """
        c = 3e8
        path_loss_db = 20 * np.log10(distance_m) + 20 * np.log10(self.f_center) + 20 * np.log10(4 * np.pi / c)
        p_rx = tx_power_dbm + self.antenna_gain_dbi - path_loss_db - tissue_loss_db
        return float(p_rx)

    def model_antenna_mismatch(self) -> float:
        """
        Calculates return loss (dB) from VSWR.
        """
        gamma = (self.vswr - 1) / (self.vswr + 1)
        return float(-20 * np.log10(abs(gamma)))

    def status(self) -> Dict[str, Any]:
        return {
            "center_frequency_mhz": self.f_center / 1e6,
            "bandwidth_mhz": self.bandwidth / 1e6,
            "antenna_gain_dbi": self.antenna_gain_dbi,
            "vswr": self.vswr,
            "return_loss_db": self.model_antenna_mismatch(),
            "status": "READY"
        }

if __name__ == "__main__":
    frontend = ExternalHubFrontend()
    print(f"Front-End Status: {frontend.status()}")
    saw_resp = frontend.get_saw_filter_response(441e6)
    print(f"SAW Filter Response at 441MHz: {saw_resp} dB")
    saw_resp_off = frontend.get_saw_filter_response(445e6)
    print(f"SAW Filter Response at 445MHz: {saw_resp_off} dB")
    rx_power = frontend.calculate_link_budget(20.0, 0.1, 15.0) # 20dBm, 10cm, 15dB tissue loss
    print(f"Predicted Rx Power at Swarm: {rx_power:.2f} dBm")
