# =========================================================
# Optical DAQ: FPGA + Killer E2500
# Substrato 390-OPT
# =========================================================
import math, time, struct, json, random
from dataclasses import dataclass

@dataclass
class DAQEvent:
    timestamp_ns: int
    channel: int
    amplitude_mV: float
    integral_nVs: float
    flags: int

class OpticalDAQSystem:
    def __init__(self, n_channels: int = 128):
        self.n_channels = n_channels
        self.adc_resolution_bits = 12
        self.adc_sampling_rate_Msps = 100
        self.adc_input_range_mV = 1000
        self.adc_lsb_mV = 1000 / (2**12)
        self.fpga = "Xilinx Artix-7"
        self.fpga_logic_cells = 33000
        self.fpga_pcie_gen = 2
        self.nic = "Killer E2500 (Qualcomm Atheros AR8161)"
        self.pci_id = "1969:e0b1"
        self.driver = "alx-event"
        self.event_buffer = []
        self.max_buffer_size = 100000

    def compute_event_size_bytes(self) -> int:
        return 16  # 8B timestamp + 2B amplitude + 4B integral + 2B flags

    def compute_max_event_rate_hz(self) -> float:
        return (500 * 0.8 * 1e6) / self.compute_event_size_bytes()

    def read_event(self, channel: int = 0) -> DAQEvent:
        """Simula leitura de evento da FIFO da FPGA."""
        event = DAQEvent(
            timestamp_ns=int(time.time_ns()),
            channel=channel,
            amplitude_mV=random.gauss(500, 100),
            integral_nVs=random.gauss(2000, 400),
            flags=0x01
        )
        if len(self.event_buffer) >= self.max_buffer_size:
            self.event_buffer.pop(0)
        self.event_buffer.append(event)
        return event

    def get_status(self) -> dict:
        return {
            "n_channels": self.n_channels,
            "adc_bits": self.adc_resolution_bits,
            "adc_rate_Msps": self.adc_sampling_rate_Msps,
            "buffer_size": len(self.event_buffer),
            "max_rate_MHz": self.compute_max_event_rate_hz() / 1e6,
            "fpga": self.fpga,
            "nic": self.nic,
            "driver": self.driver
        }

    def serialize_event(self, event: DAQEvent) -> bytes:
        return struct.pack("<QHfH",
            event.timestamp_ns,
            event.channel,
            event.amplitude_mV,
            event.flags)

    def deserialize_event(self, data: bytes) -> DAQEvent:
        ts, ch, amp, fl = struct.unpack("<QHfH", data)
        return DAQEvent(timestamp_ns=ts, channel=ch,
                       amplitude_mV=amp, integral_nVs=0, flags=fl)
