from dataclasses import dataclass
from typing import Optional

@dataclass
class SyncNodeSpec:
    """Especificação técnica do nó de sincronização para rede Hubble."""

    # Oscilador local
    ocxo_model: str = "Vectron VCOM-901"  # ou equivalente
    ocxo_freq_mhz: float = 10.0
    ocxo_allan_1s: float = 1e-11
    ocxo_holdover_24h_ns: float = 0.8

    # Recebimento GNSS
    gnss_receiver: str = "Septentrio PolaRx5TR"  # multi-constellation, multi-frequency
    gnss_antenna: str = "Trimble Zephyr 3 Geodetic"
    gnss_pps_accuracy_ns: float = 5.0  # RMS, after calibration

    # Distribuição White Rabbit
    wr_switch: str = "Seven Solutions WR-SPS"  # ou FPGA custom com WR stack
    wr_fiber_max_km: int = 10
    wr_sync_accuracy_ns: float = 0.2  # RMS, single hop
    wr_cascade_max_hops: int = 3

    # Time-tagging FPGA
    fpga_model: str = "Xilinx Kintex-7 XC7K325T"
    tdc_resolution_ps: int = 25
    tdc_jitter_rms_ps: int = 5
    timestamp_width_bits: int = 64  # TAI nanoseconds since epoch

    # Métricas de validação
    target_jitter_intercontinental_ns: float = 1.0  # RMS entre continentes
    target_phase_coherence_rad: float = 1e-11  # Δφ máximo para fingerprint 0.58
    target_holdover_outage_hours: int = 72  # Sem GNSS, mantendo < 1 ns drift

    # Monitoramento
    monitoring_interval_s: int = 1
    alert_threshold_jitter_ns: float = 0.8
    alert_threshold_phase_error_rad: float = 5e-12
