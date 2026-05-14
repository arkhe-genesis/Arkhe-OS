#!/usr/bin/env python3
"""
arkhe_pulse_injector.py
Generates binary QCircuitSchedule for testbench and, on real hardware,
streams via PYNQ AXI DMA to the Arkhe Pulse Sequencer.
"""

import struct, hashlib, json, time, numpy as np
from dataclasses import dataclass
from typing import List, Optional

# ── Binary Packing (matches Verilog struct) ──────────────────────────────────
@dataclass
class QPulseBinary:
    target_qubit: int
    frequency_hz: float
    amplitude: float
    duration_ns: float
    phase: float
    drag_coeff: float
    envelope_sigma: float
    sample_count: int
    samples: List[float]  # I/Q interleaved? We'll just store I for simplicity
    flags: int

    def pack(self) -> bytes:
        # Pack header (32 bytes before samples)
        header = struct.pack('<IffIfffII',
            self.target_qubit,
            self.frequency_hz,
            self.amplitude,
            int(self.duration_ns * 1e3),  # picoseconds
            self.phase,
            self.drag_coeff,
            self.envelope_sigma,
            self.sample_count,
            self.flags)
        sample_bytes = b''.join(struct.pack('<f', s) for s in self.samples)
        return header + sample_bytes

def build_qcircuitschedule(gates: List[dict], drag_alpha=0.1, phi_c_threshold=0.99) -> bytes:
    """Convert abstract gates into a binary schedule packet."""
    # Simplified: we'll generate one pulse per single-qubit gate
    pulses = []
    for gate in gates:
        if gate['type'] in ('SINGLE_X', 'RX', 'RY'):
            qubit = gate['qubit']
            dur = 40.0  # ns
            amp = 0.3
            sigma = dur / 4.0
            sample_period = 1.0 / 14e9 * 1e9  # ns
            num_samples = int(dur / sample_period)
            mu = dur / 2.0
            samples_i = []
            for i in range(num_samples):
                t = i * sample_period
                I = amp * np.exp(-((t-mu)**2)/(2*sigma*sigma))
                samples_i.append(I)
            # Build QPulseBinary
            pulse = QPulseBinary(
                target_qubit=qubit,
                frequency_hz=5e9,
                amplitude=amp,
                duration_ns=dur,
                phase=gate.get('phase', 0.0),
                drag_coeff=drag_alpha,
                envelope_sigma=sigma,
                sample_count=num_samples,
                samples=samples_i,
                flags=0x0
            )
            pulses.append(pulse)
    # Serialize list of pulses
    data = struct.pack('<I', len(pulses))  # pulse count
    for p in pulses:
        data += p.pack()
    # Footer: Phi_C threshold, total_time_ns (placeholder)
    data += struct.pack('<fI', phi_c_threshold, int(sum(p.duration_ns for p in pulses)))
    return data

# ── Simulation file writer ──────────────────────────────────────────────────
def write_stimulus_file(filename: str, gates: List[dict]):
    schedule_bin = build_qcircuitschedule(gates)
    with open(filename, 'wb') as f:
        f.write(schedule_bin)
    print(f"Stimulus written to {filename} ({len(schedule_bin)} bytes)")
    sha = hashlib.sha256(schedule_bin).hexdigest()
    print(f"SHA256: {sha[:16]}...")

# ── PYNQ Hardware Injection ─────────────────────────────────────────────────
try:
    from pynq import Overlay, allocate
    HAS_PYNQ = True
except ImportError:
    HAS_PYNQ = False

class PulseSequencerDriver:
    """Driver for Arkhe Pulse Sequencer on Zynq via PYNQ."""
    def __init__(self, bitstream_path: str):
        if not HAS_PYNQ:
            raise RuntimeError("PYNQ not available. Install pynq on the board.")
        self.overlay = Overlay(bitstream_path)
        self.dma = self.overlay.axi_dma_0
        self.control = self.overlay.pulse_sequencer_control

    def load_schedule(self, schedule_bin: bytes):
        # Allocate buffer
        buf = allocate(shape=(len(schedule_bin),), dtype=np.uint8)
        buf[:] = np.frombuffer(schedule_bin, dtype=np.uint8)
        # Transfer via DMA
        self.dma.sendchannel.transfer(buf)
        self.dma.sendchannel.wait()
        # Trigger FSM
        self.control.write(0x00, 0x1)  # start
        # Wait for done
        while (self.control.read(0x04) & 0x1) == 0:
            pass
        # Read status
        status = self.control.read(0x08)
        print(f"Pulse sequencer status: 0x{status:08X}")

if __name__ == '__main__':
    # Example: build a small circuit
    gates = [
        {'type': 'SINGLE_X', 'qubit': 0, 'phase': 0.0},
        {'type': 'SINGLE_X', 'qubit': 2, 'phase': np.pi/2},
    ]
    write_stimulus_file("test_stimulus.bin", gates)
    # On board: PulseSequencerDriver("arkhe_pulse_sequencer.bit").load_schedule(...)
