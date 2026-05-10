# arkhe_os/neural/bci_real_drivers.py

import numpy as np
import time
import threading
from typing import Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto

try:
    from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
    from brainflow.data_filter import DataFilter, FilterTypes, AggOperations
    BRAINFLOW_AVAILABLE = True
except ImportError:
    BRAINFLOW_AVAILABLE = False
    print("⚠️ BrainFlow not installed. Install with: pip install brainflow")

@dataclass
class OpenBCIConfig:
    board_id: int = 0
    serial_port: str = '/dev/ttyUSB0'
    sampling_rate: int = 250
    channels: List[int] = field(default_factory=lambda: list(range(8)))
    impedance_check: bool = True
    stream_buffer_size: int = 1000

    def to_brainflow_params(self):
        if not BRAINFLOW_AVAILABLE:
            raise ImportError("BrainFlow not available")
        params = BrainFlowInputParams()
        params.serial_port = self.serial_port
        return params

class BCIHardwareInterface:
    def connect(self): pass
    def send_stimulation(self, pattern): pass

class BrainflowBCIDriver(BCIHardwareInterface):
    def __init__(self, config: Optional[OpenBCIConfig] = None):
        self.config = config or OpenBCIConfig()
        self.board = None
        self.streaming = False
        self.data_buffer = np.zeros((self.config.stream_buffer_size, len(self.config.channels)), dtype=np.float32)
        self.timestamps = np.zeros(self.config.stream_buffer_size)
        self.buffer_idx = 0
        self.data_callbacks = []
        self._stream_thread = None
        self._stop_streaming = False

    def connect(self, timeout: float = 10.0) -> bool:
        if not BRAINFLOW_AVAILABLE:
            return False
        try:
            params = self.config.to_brainflow_params()
            self.board = BoardShim(self.config.board_id, params)
            return True
        except Exception:
            return False

    def start_streaming(self, callback=None):
        if not self.board or self.streaming:
            return False
        if callback:
            self.data_callbacks.append(callback)
        self.streaming = True
        self._stop_streaming = False
        self.board.prepare_session()
        self.board.start_stream()
        self._stream_thread = threading.Thread(target=self._streaming_loop, daemon=True)
        self._stream_thread.start()
        return True

    def _streaming_loop(self):
        while not self._stop_streaming and self.streaming and self.board:
            try:
                n_samples = min(10, self.config.stream_buffer_size // 10)
                data = self.board.get_current_board_data(n_samples)
                if data is None or data.shape[1] == 0:
                    time.sleep(0.01)
                    continue
                for i, ch_idx in enumerate(self.config.channels):
                    if ch_idx < data.shape[0]:
                        channel_data = data[ch_idx, -n_samples:]
                        for sample in channel_data:
                            self.data_buffer[self.buffer_idx, i] = sample
                            self.timestamps[self.buffer_idx] = time.time()
                            self.buffer_idx = (self.buffer_idx + 1) % self.config.stream_buffer_size
                time.sleep(0.004)
            except Exception:
                time.sleep(0.1)

    def get_status(self) -> Dict[str, any]:
        return {
            'connected': self.board is not None,
            'brainflow_available': BRAINFLOW_AVAILABLE
        }

class OpenBCIDriver(BrainflowBCIDriver):
    pass

class NeuralinkDriver(BCIHardwareInterface):
    def connect(self): return True
    def send_stimulation(self, pattern): return True
    def get_status(self): return {'connected': True}
    async def connect_async(self): return True
