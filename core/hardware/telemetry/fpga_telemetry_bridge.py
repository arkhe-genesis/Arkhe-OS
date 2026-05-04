# ============================================================================
# ARKHE OS v∞.Ω.∇+++.14.4 — FPGA Telemetry Bridge
# Purpose: Interfaces the Python consensus engine with the FPGA hardware registers
#          via memory-mapped I/O (AXI Lite) to poll 7D telemetry packets
# ============================================================================

import mmap
import os
import struct
import time
import numpy as np
from dataclasses import dataclass
from typing import Optional

from consensus_engine_7d import CoherenceTensor7D

# Constants for memory-mapped I/O (mock addresses for simulation/demonstration)
FPGA_AXI_BASE_ADDR = 0x40000000
FPGA_MEM_SIZE = 0x1000

# Offsets for the AXI-Lite control registers (matching HLS synthesis)
CTRL_REG_CURRENT_TIMESTAMP = 0x10
CTRL_REG_ACTIVE_VERTEX_DID_LOW = 0x18
CTRL_REG_ACTIVE_VERTEX_DID_HIGH = 0x20
CTRL_REG_TRIGGER_SAMPLE = 0x28

# Offset for the output packet struct (assuming AXI Master writes here)
MEM_OFFSET_PACKET = 0x100

@dataclass
class TelemetrySample:
    """Single telemetry sample across all 7 dimensions."""
    timestamp: float
    phase: float
    latency_us: float
    power_mw: float
    mercy_gap: float
    security: float
    privacy: float
    interpretability: float
    vertex_did: str

class FPGATelemetryBridge:
    """Bridge for reading 7D coherence metrics directly from FPGA hardware."""

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self._mm = None
        self._fd = None

        if not self.mock_mode:
            self._setup_mmap()

    def _setup_mmap(self):
        """Sets up memory-mapped I/O to communicate with FPGA /dev/mem."""
        try:
            self._fd = os.open('/dev/mem', os.O_RDWR | os.O_SYNC)
            self._mm = mmap.mmap(self._fd, FPGA_MEM_SIZE, offset=FPGA_AXI_BASE_ADDR)
        except PermissionError:
            print("Warning: Requires root privileges to access /dev/mem. Falling back to mock mode.")
            self.mock_mode = True
        except FileNotFoundError:
            print("Warning: /dev/mem not found. Falling back to mock mode.")
            self.mock_mode = True

    def _read_ap_fixed(self, offset: int) -> float:
        """Reads a 32-bit ap_fixed<32, 16> value and converts it to a Python float."""
        if self.mock_mode:
            return 0.0

        self._mm.seek(offset)
        raw_bytes = self._mm.read(4)
        raw_int = struct.unpack('<i', raw_bytes)[0]
        # ap_fixed<32, 16> means 16 fractional bits
        return float(raw_int) / (1 << 16)

    def trigger_and_read_sample(self, vertex_did: str) -> TelemetrySample:
        """Triggers the FPGA to sample its registers and returns the parsed TelemetrySample."""
        if self.mock_mode:
            return self._mock_read_sample(vertex_did)

        # 1. Write current timestamp to control register
        current_ts = int(time.time() * 1000)
        self._mm.seek(CTRL_REG_CURRENT_TIMESTAMP)
        self._mm.write(struct.pack('<Q', current_ts))

        # 2. Trigger the sample
        self._mm.seek(CTRL_REG_TRIGGER_SAMPLE)
        self._mm.write(struct.pack('<I', 1))

        # Small wait for FPGA to process and AXI master to write back
        time.sleep(0.001)

        # 3. Read back the struct (ignoring timestamp and did for now, just reading tensor)
        # Assuming the struct format packs the ap_fixed<32, 16> sequentially
        base_offset = MEM_OFFSET_PACKET + 40 # Skip 8 byte TS + 32 byte DID

        return TelemetrySample(
            timestamp=time.time(),
            vertex_did=vertex_did,
            phase=self._read_ap_fixed(base_offset + 0),
            latency_us=self._read_ap_fixed(base_offset + 4),
            power_mw=self._read_ap_fixed(base_offset + 8),
            mercy_gap=self._read_ap_fixed(base_offset + 12),
            security=self._read_ap_fixed(base_offset + 16),
            privacy=self._read_ap_fixed(base_offset + 20),
            interpretability=self._read_ap_fixed(base_offset + 24)
        )

    def _mock_read_sample(self, vertex_did: str) -> TelemetrySample:
        """Simulates FPGA telemetry generation with some random jitter around targets."""
        target = CoherenceTensor7D.target()
        stds = CoherenceTensor7D.nominal_stds() * 0.1 # Small jitter

        return TelemetrySample(
            timestamp=time.time(),
            vertex_did=vertex_did,
            phase=target.phase + np.random.normal(0, stds[0]),
            latency_us=target.latency_us + np.random.normal(0, stds[1]),
            power_mw=target.power_mw + np.random.normal(0, stds[2]),
            mercy_gap=target.mercy_gap + np.random.normal(0, stds[3]),
            security=target.security + np.random.normal(0, stds[4]),
            privacy=target.privacy + np.random.normal(0, stds[5]),
            interpretability=target.interpretability + np.random.normal(0, stds[6])
        )

    def close(self):
        """Clean up memory-mapped files."""
        if self._mm:
            self._mm.close()
        if self._fd:
            os.close(self._fd)

if __name__ == "__main__":
    # Test the bridge
    bridge = FPGATelemetryBridge(mock_mode=True)
    sample = bridge.trigger_and_read_sample("vertex-abc123")
    print(f"Sampled 7D Coherence from FPGA Bridge:")
    print(f"  Phase: {sample.phase:.4f}")
    print(f"  Latency: {sample.latency_us:.2f} us")
    print(f"  Power: {sample.power_mw:.2f} mW")
    bridge.close()
